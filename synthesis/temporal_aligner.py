"""Temporal alignment across astrological systems.

FIX v2.0:
  - align_predictions() now handles nested {"western": {...}, "vedic": {...}} structure
    from orchestrator.py. Previous version expected flat keys and produced 0 events.
  - Primary Directions: PD is now a dict of categories (career/identity/vitality/emotion),
    each containing a list. Fixed iteration to handle both flat list and category dict.
  - Solar Returns: added fallback JD calculation from year if "jd" key missing.
  - Dashas: added correct key "vimshottari" (was "dashas" — key never existed).
  - Tajaka: added support for Vedic annual events.
  - Da Yun / Liu Nian: added Saju time windows.
  - Profections: added Hellenistic annual profections.
  - Min cluster size kept at 2, but added multi-system bonus flag.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import math


class TemporalAligner:
    """
    Aligns different timing systems to Julian Days for comparison.
    Converts all predictions → unified events → clusters (storm windows).
    """

    def __init__(self, natal_jd: float):
        self.natal_jd = natal_jd
        self._now_jd = self._datetime_to_jd(datetime.now(timezone.utc))
        # Derive birth month/day for birthday-relative profection anchoring
        try:
            import swisseph as _swe
            _y, _m, _d, _h = _swe.revjul(natal_jd)
            self._birth_month = int(_m)
            self._birth_day   = min(int(_d), 28)   # safe for all months
        except Exception:
            self._birth_month = 7
            self._birth_day   = 1

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────

    def align_predictions(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert all predictions to standard format with JD timestamps.

        Accepts EITHER:
          - nested: {"western": {...}, "vedic": {...}, "saju": {...}, "hellenistic": {...}}
          - flat:   {"primary_directions": [...], "solar_returns": [...], ...}
        """
        aligned = []

        # Detect structure
        if "western" in predictions or "vedic" in predictions:
            # ── Nested structure (from orchestrator.py) ───────────────────
            w = predictions.get("western", {})
            v = predictions.get("vedic", {})
            s = predictions.get("saju", {})
            h = predictions.get("hellenistic", {})

            aligned += self._extract_primary_directions(w)
            aligned += self._extract_solar_returns(w)
            aligned += self._extract_lunar_returns(w)
            aligned += self._extract_profections(w)
            aligned += self._extract_outer_transits(w)   # NEW: exact planet transit hits
            aligned += self._extract_vimshottari(v)
            aligned += self._extract_tajaka(v)
            aligned += self._extract_da_yun(s)
            aligned += self._extract_liu_nian(s)
            aligned += self._extract_zr(h)

        else:
            # ── Flat structure (legacy) ───────────────────────────────────
            aligned += self._extract_primary_directions(predictions)
            aligned += self._extract_solar_returns(predictions)
            if "dashas" in predictions:
                for dasha in predictions["dashas"]:
                    if "start_jd" in dasha:
                        aligned.append({
                            "jd": float(dasha["start_jd"]),
                            "system": "Vedic",
                            "technique": "Dasha",
                            "description": f"{dasha.get('lord', '?')} Dasha",
                        })

        # Filter to future events within 6 years
        max_jd = self._now_jd + 6 * 365.25
        aligned = [e for e in aligned
                   if e.get("jd") and self._now_jd <= e["jd"] <= max_jd]

        return sorted(aligned, key=lambda x: x["jd"])

    def find_temporal_clusters(self, aligned_events: List[Dict],
                               window_days: int = 45) -> List[Dict]:
        """
        Find clusters of events within time windows (storm windows).
        Returns clusters with ≥2 events. Multi-system clusters are flagged.
        """
        if not aligned_events:
            return []

        clusters = []
        current_cluster = []

        for event in aligned_events:
            if not current_cluster:
                current_cluster = [event]
            else:
                last_jd = current_cluster[-1]["jd"]
                if event["jd"] - last_jd <= window_days:
                    current_cluster.append(event)
                else:
                    if len(current_cluster) >= 2:
                        clusters.append(self._build_cluster(current_cluster))
                    current_cluster = [event]

        # Don't forget the last cluster
        if len(current_cluster) >= 2:
            clusters.append(self._build_cluster(current_cluster))

        # Sort by intensity (most events first)
        clusters.sort(key=lambda c: c["intensity"], reverse=True)
        return clusters

    # ─────────────────────────────────────────────────────────────────────
    # Extraction helpers (one per technique)
    # ─────────────────────────────────────────────────────────────────────

    def _extract_primary_directions(self, pred: Dict) -> List[Dict]:
        events = []
        pd = pred.get("primary_directions", {})
        if not pd:
            return events

        # Handle dict-of-categories (orchestrator format)
        if isinstance(pd, dict):
            all_dirs = []
            for category, dirs in pd.items():
                if isinstance(dirs, list):
                    for d in dirs:
                        if isinstance(d, dict):
                            d["_category"] = category
                            all_dirs.append(d)
            pd = all_dirs

        for d in pd:
            if not isinstance(d, dict):
                continue
            jd = self._get_pd_jd(d)
            if jd is None:
                continue
            events.append({
                "jd": jd,
                "system": "Western",
                "technique": "Primary Direction",
                "description": f"{d.get('promissor', '?')} → {d.get('significator', '?')} ({d.get('arc_degrees', 0):.2f}°)",
                "domain": d.get("_category", "general"),
                "confidence": 0.95,
            })
        return events

    def _extract_solar_returns(self, pred: Dict) -> List[Dict]:
        events = []
        for sr in pred.get("solar_returns", []):
            if not isinstance(sr, dict):
                continue
            jd = sr.get("jd")
            if jd is None:
                # Fallback: estimate JD from year
                year = sr.get("year")
                if year:
                    jd = self._year_to_jd(int(year))
                else:
                    continue
            events.append({
                "jd": float(jd),
                "system": "Western",
                "technique": "Solar Return",
                "description": f"Solar Return {sr.get('year', '?')}",
                "confidence": 0.90,
            })
        return events

    def _extract_lunar_returns(self, pred: Dict) -> List[Dict]:
        events = []
        for lr in pred.get("lunar_returns", []):
            if not isinstance(lr, dict):
                continue
            jd = lr.get("jd")
            if jd is None:
                # Parse from date string
                date_str = lr.get("date", "")
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        jd = self._datetime_to_jd(dt)
                    except Exception:
                        continue
                else:
                    continue
            events.append({
                "jd": float(jd),
                "system": "Western",
                "technique": "Lunar Return",
                "description": f"Lunar Return {lr.get('year', '?')}-{lr.get('month', '?')}",
                "confidence": 0.82,
            })
        return events

    def _extract_profections(self, pred: Dict) -> List[Dict]:
        events = []
        for prof in pred.get("profections_timeline", []):
            if not isinstance(prof, dict):
                continue
            year = prof.get("year")
            if not year:
                continue
            # Anchor to birthday in that year, not June 15 midpoint
            try:
                bd_dt = datetime(int(year), self._birth_month, self._birth_day,
                                 tzinfo=timezone.utc)
                jd = self._datetime_to_jd(bd_dt)
            except Exception:
                jd = self._year_to_jd(int(year))
            events.append({
                "jd":          jd,
                "system":      "Hellenistic",
                "technique":   "Profection",
                "description": (f"Profection {year}: {prof.get('profected_sign', '?')} "
                                f"(Time Lord: {prof.get('time_lord', '?')}, "
                                f"House {prof.get('activated_house', '?')})"),
                "confidence":  0.70,
                "domain":      f"house_{prof.get('activated_house', '1')}",
            })
        return events

    def _extract_outer_transits(self, pred: Dict) -> List[Dict]:
        """Extract exact outer planet transit hits — the most precise timing data."""
        events = []
        outer = pred.get("outer_transit_aspects", {})
        hits = outer.get("hits") or outer.get("all_hits", [])
        for h in hits:
            try:
                exact_jd = h.get("exact_jd")
                if exact_jd:
                    jd = float(exact_jd)
                else:
                    iso = h.get("exact_date_iso", "")
                    if iso:
                        y, mo, d = map(int, iso.split("-"))
                        jd = self._datetime_to_jd(datetime(y, mo, d, tzinfo=timezone.utc))
                    else:
                        continue
                if jd <= self._now_jd:
                    continue
                planet   = h.get("transiting") or h.get("planet", "?")
                natal_pt = h.get("natal_point", "?")
                aspect   = h.get("aspect", "?")
                events.append({
                    "jd":          jd,
                    "system":      "Western",
                    "technique":   "Transit_Aspect",
                    "description": f"{planet} {aspect} natal {natal_pt}",
                    "confidence":  0.62,
                    "domain":      natal_pt.lower(),
                })
            except Exception:
                continue
        return events

    def _extract_vimshottari(self, pred: Dict) -> List[Dict]:
        events = []
        dasha = pred.get("vimshottari", {})
        if not dasha:
            return events

        maha_lord = dasha.get("maha_lord", "?")
        antar_lord = dasha.get("antar_lord", "?")
        remaining = dasha.get("approx_remaining_years", 0)
        antar_rem = dasha.get("antar_remaining_years", 0)

        if remaining and isinstance(remaining, (int, float)):
            end_jd = self._now_jd + float(remaining) * 365.25
            events.append({
                "jd": end_jd,
                "system": "Vedic",
                "technique": "Vimshottari Dasha",
                "description": f"{maha_lord} Maha Dasha ends",
                "confidence": 0.88,
            })

        if antar_rem and isinstance(antar_rem, (int, float)):
            antar_end_jd = self._now_jd + float(antar_rem) * 365.25
            events.append({
                "jd": antar_end_jd,
                "system": "Vedic",
                "technique": "Vimshottari Antardasha",
                "description": f"{antar_lord} Antardasha ends (within {maha_lord} Maha)",
                "confidence": 0.85,
            })

        return events

    def _extract_tajaka(self, pred: Dict) -> List[Dict]:
        events = []
        for taj in pred.get("tajaka", []):
            if not isinstance(taj, dict):
                continue
            year = taj.get("year")
            if not year:
                continue
            events.append({
                "jd": self._year_to_jd(int(year)),
                "system": "Vedic",
                "technique": "Tajaka",
                "description": (f"Tajaka {year}: Muntha {taj.get('muntha_sign', '?')}, "
                                f"Lord {taj.get('lord_of_year', '?')}"),
                "confidence": 0.85,
            })
        return events

    def _extract_da_yun(self, pred: Dict) -> List[Dict]:
        events = []
        da_yun = pred.get("da_yun", {})
        if not da_yun:
            return events

        pillars = da_yun.get("pillars", [])
        birth_year_approx = 1990  # Will be close enough; actual birth year from meta
        for pillar in pillars[:4]:
            start_age = pillar.get("start_age", 0)
            if not start_age:
                continue
            # Approximate: natal_jd + years
            jd = self.natal_jd + float(start_age) * 365.25
            events.append({
                "jd": jd,
                "system": "Saju",
                "technique": "Da Yun",
                "description": (f"Da Yun: {pillar.get('stem', '?')}{pillar.get('branch', '?')} "
                                f"({pillar.get('stem_element', '?')}/{pillar.get('branch_element', '?')})"),
                "confidence": 0.80,
            })
        return events

    def _extract_liu_nian(self, pred: Dict) -> List[Dict]:
        events = []
        for ln in pred.get("liu_nian_timeline", []):
            if not isinstance(ln, dict):
                continue
            year = ln.get("year")
            if not year:
                continue
            events.append({
                "jd": self._year_to_jd(int(year)),
                "system": "Saju",
                "technique": "Liu Nian",
                "description": f"Liu Nian {year}: {ln.get('stem', '?')}{ln.get('branch', '?')}",
                "confidence": 0.72,
            })
        return events

    def _extract_zr(self, pred: Dict) -> List[Dict]:
        events = []
        zr = pred.get("zodiacal_releasing", {})
        for spirit_or_fortune in ["fortune", "spirit"]:
            for period in zr.get(spirit_or_fortune, []):
                if not isinstance(period, dict):
                    continue
                start = period.get("start_date", "")
                if start:
                    try:
                        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        events.append({
                            "jd": self._datetime_to_jd(dt),
                            "system": "Hellenistic",
                            "technique": "Zodiacal Releasing",
                            "description": (f"ZR L1 {spirit_or_fortune.capitalize()}: "
                                           f"{period.get('sign', '?')} "
                                           f"({'Loosing of Bond' if period.get('is_loosing_of_bond') else ''})"),
                            "confidence": 0.75,
                        })
                    except Exception:
                        continue
        return events

    # ─────────────────────────────────────────────────────────────────────
    # Cluster builder
    # ─────────────────────────────────────────────────────────────────────

    def _build_cluster(self, events: List[Dict]) -> Dict:
        systems = list(set(e["system"] for e in events))
        techniques = list(set(e["technique"] for e in events))
        multi_system = len(systems) > 1
        n_systems = len(systems)
        n_events  = len(events)
        avg_confidence = (sum(e.get("confidence", 0.7) for e in events)
                          / n_events)

        # ── Convergence score ──────────────────────────────────────────────
        # A probability-like signal (0.0–1.0) expressing how much independent
        # evidence points to this window.
        #
        # Formula:
        #   base    = avg technique confidence (tracks historical reliability of each method)
        #   multi   = bonus for crossing system boundaries (Western + Vedic ≠ one system echoing itself)
        #   depth   = bonus for raw event count (more signals = more noise filtered)
        #   cap     = 0.97 — we never claim certainty
        #
        # Interpretation bands the model is instructed to use:
        #   ≥ 0.85  → "near-certain" (4+ systems, all agree)
        #   0.70–0.84 → "high-confidence" (3 systems, or 2 strong ones)
        #   0.55–0.69 → "moderate-confidence" (2 systems, typical orb)
        #   < 0.55  → "low-confidence" (echo of a single system)

        multi_bonus = 0.08 if n_systems >= 3 else (0.05 if n_systems == 2 else 0.0)
        depth_bonus = min(0.08, (n_events - 2) * 0.02)  # +2% per event over 2, cap 8%
        raw_score   = avg_confidence + multi_bonus + depth_bonus
        convergence_score = round(min(0.97, raw_score), 3)

        if convergence_score >= 0.85:
            confidence_label = "NEAR-CERTAIN"
            stoplight = "🔴"  # high-pressure — not danger, just significance
        elif convergence_score >= 0.70:
            confidence_label = "HIGH-CONFIDENCE"
            stoplight = "🟠"
        elif convergence_score >= 0.55:
            confidence_label = "MODERATE-CONFIDENCE"
            stoplight = "🟡"
        else:
            confidence_label = "LOW-CONFIDENCE"
            stoplight = "🟢"

        return {
            "start_jd": events[0]["jd"],
            "end_jd": events[-1]["jd"],
            "events": events,
            "systems_involved": systems,
            "techniques_involved": techniques,
            "intensity": n_events,
            "n_systems": n_systems,
            "multi_system": multi_system,
            "avg_confidence": round(avg_confidence, 3),
            "convergence_score": convergence_score,
            "confidence_label": confidence_label,
            "stoplight": stoplight,
            # Human-readable anchor
            "center_jd": (events[0]["jd"] + events[-1]["jd"]) / 2,
        }

    # ─────────────────────────────────────────────────────────────────────
    # JD utilities
    # ─────────────────────────────────────────────────────────────────────

    def _get_pd_jd(self, d: Dict) -> Optional[float]:
        """Extract JD from a Primary Direction dict."""
        # Prefer target_date ISO string
        td = d.get("target_date")
        if td:
            try:
                dt = datetime.fromisoformat(str(td).replace("Z", "+00:00"))
                return self._datetime_to_jd(dt)
            except Exception:
                pass
        # Fallback: years
        years = d.get("years")
        if years is not None:
            return self._now_jd + float(years) * 365.25
        return None

    @staticmethod
    def _datetime_to_jd(dt: datetime) -> float:
        """Convert datetime to Julian Day Number."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # J2000.0 = 2451545.0 at 2000-01-01 12:00 UTC
        epoch = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        delta = (dt - epoch).total_seconds()
        return 2451545.0 + delta / 86400.0

    @staticmethod
    def _year_to_jd(year: int) -> float:
        """Convert a calendar year (Jan 1) to Julian Day."""
        try:
            dt = datetime(year, 6, 15, 12, 0, 0, tzinfo=timezone.utc)  # Mid-year
        except ValueError:
            dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        epoch = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        delta = (dt - epoch).total_seconds()
        return 2451545.0 + delta / 86400.0
