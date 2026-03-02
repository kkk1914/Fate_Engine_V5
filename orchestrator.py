"""Main orchestration layer - Version 2 with Primary Directions, Ashtakavarga, and Validation Matrix."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import logging
logger = logging.getLogger(__name__)
import swisseph as swe
import os

# Core mathematical engines
from core.ephemeris import ephe
from core.primary_directions import PrimaryDirections
from core.solar_return import SolarReturnEngine
from core.tajaka import TajakaEngine
from core.vedic_engines import AshtakavargaEngine, DivisionalCharts
from core.house_lords import HouseLordMapper
from core.lunar_return import LunarReturnEngine
from core.syzygy import SyzygyEngine
from core.essential_dignities import EssentialDignities
from core.dodecatemoria import DodecatemoriaEngine  # Phase 5

# System calculation engines
from systems.western import WesternEngine
from systems.hellenistic import HellenisticEngine
from systems.vedic import calculate_vedic
from systems.saju import calculate_bazi

# Expert analysis layer
from experts.western_expert import WesternExpert
from experts.vedic_expert import VedicExpert
from experts.saju_expert import SajuExpert
from experts.hellenistic_expert import HellenisticExpert

# Synthesis layer
from synthesis.validation_matrix import ValidationMatrix, PredictionEvent
from synthesis.temporal_aligner import TemporalAligner
from synthesis.arbiter import Arbiter
from synthesis.archon import Archon
from query_engine import build_query_context


class FatesOrchestrator:
    """Coordinates calculation, analysis, and synthesis with V2 mathematical rigor."""

    def __init__(self):
        # Traditional engines
        self.western_engine = WesternEngine()
        self.hellenistic_engine = HellenisticEngine()
        self.dignity_engine = EssentialDignities()

        # Expert LLM layer
        self.western_expert = WesternExpert()
        self.vedic_expert = VedicExpert()
        self.saju_expert = SajuExpert()
        self.hellenistic_expert = HellenisticExpert()

        # Synthesis layer
        self.arbiter = Arbiter()
        self.archon = Archon()

    def generate_report(self,
                       birth_datetime: str,
                       location: str,
                       gender: str = "unspecified",
                       name: str = "Unknown",
                       output_dir: str = "./reports",
                       user_questions: list = None) -> str:
        """
        Generate complete master report with V2 predictive engines.
        user_questions: list of up to 5 question strings (optional).
          When provided, QueryEngine extracts themes and steers every section
          of the report toward what the user asked about, then adds a direct
          Q&A section (Part IV) with verdicts at the end.
        """
        print("🔮 Fates Engine v2.0: Initializing Mathematical Core...")
        print(f"   Subject: {name}")
        print(f"   Birth: {birth_datetime}")
        print(f"   Location: {location}")

        # 1. Parse inputs and calculate charts (V2 with Primary Directions, Ashtakavarga, etc.)
        print("\n📊 Layer 1: Mathematical Calculations (4 systems + Vargas + Directions)...")
        chart_data = self._calculate_charts(birth_datetime, location, gender)

        print("   ✓ Western (Tropical) + Primary Directions + Solar Returns")
        print("   ✓ Vedic (Sidereal) + Full Ashtakavarga + Divisional Charts (D7,D9,D10,D12,D16,D30,D60)")
        print("   ✓ Saju (Bazi) + Da Yun")
        print("   ✓ Hellenistic + Zodiacal Releasing + Dodecatemoria")
        # Note: Event count will be displayed after extraction in Layer 2

        # 2. Algorithmic Validation Matrix (NEW V2)
        print("\n⚖️  Layer 2: Algorithmic Reconciliation (Validation Matrix)...")
        validation_matrix = ValidationMatrix()

        # Extract all predictive events into standardized format
        events = self._extract_prediction_events(chart_data)
        for event in events:
            validation_matrix.add_prediction(event)

        # Find convergences and contradictions
        convergences = validation_matrix.find_convergences(tolerance_days=30)
        contradictions = validation_matrix.find_contradictions()

        print(f"   ✓ Processed {len(events)} predictions")
        print(f"   ✓ Found {len(convergences)} multi-system convergences")
        print(f"   ✓ Flagged {len(contradictions)} contradictions for resolution")

        # Temporal alignment check
        aligner = TemporalAligner(chart_data["meta"]["jd"])
        clusters = aligner.find_temporal_clusters(
            aligner.align_predictions(chart_data["predictive"]),
            window_days=45
        )
        print(f"   ✓ Identified {len(clusters)} temporal 'storm windows'")

        # 3. Expert analysis (with validation data + question focus)
        print("\n🎭 Layer 3: Expert Swarm Analysis...")
        analyses = self._gather_expert_analyses(chart_data, convergences, contradictions,
                                                user_questions=user_questions)
        print(f"   ✓ Western Expert ({analyses[0].get('model_used')})")
        print(f"   ✓ Vedic Expert ({analyses[1].get('model_used')})")
        print(f"   ✓ Saju Expert ({analyses[2].get('model_used')})")
        print(f"   ✓ Hellenistic Expert ({analyses[3].get('model_used')})")

        # 4. Arbiter synthesis with pre-validated data + question focus
        print("\n🌐 Layer 4: Cross-System Synthesis...")
        synthesis = self.arbiter.reconcile(
            analyses,
            chart_data,
            convergences=convergences,
            contradictions=contradictions,
            temporal_clusters=clusters,
            user_questions=user_questions,
        )

        consensus_count = len(synthesis.get('consensus_points', []))
        critical_count = len(synthesis.get('critical_periods', []))
        print(f"   ✓ Synthesized {consensus_count} consensus themes")
        print(f"   ✓ Validated {critical_count} critical periods")

        # 5. Master narrative generation
        print("\n📜 Layer 5: Archon Generating Master Report...")
        metadata = {
            "name": name,
            "location": location,
            "birth_time": birth_datetime,
            "birth_year": chart_data.get("meta", {}).get("birth_year"),
        }

        # Build query context — steers every section toward user's questions
        query_context = None
        if user_questions:
            clean_qs = [q.strip() for q in user_questions if q and q.strip()][:5]
            if clean_qs:
                query_context = build_query_context(clean_qs)
                themes = query_context.get("themes", [])
                print(f"   ✓ Query context built — {len(clean_qs)} questions, "
                      f"themes: {', '.join(themes) if themes else 'general'}")

        report = self.archon.generate_report(
                   synthesis,
                   chart_data,
                   metadata,
                   temporal_clusters=clusters,
                   user_questions=user_questions,
                   query_context=query_context)

        # 6. Save with timestamp
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"master_report_v2_{safe_name}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✨ Complete! Report generated with V2 mathematical precision.")
        print(f"   Report saved: {filepath}")
        print(f"   Length: {len(report):,} characters")
        print(f"   Convergences detected: {len(convergences)}")

        return filepath

    def _calculate_charts(self, birth_dt: str, location: str, gender: str) -> Dict:
        """Calculate all systems with V2 mathematical engines."""
        # Parse datetime
        try:
            if ' ' in birth_dt:
                date_part, time_part = birth_dt.split(' ')
                year, month, day = map(int, date_part.split('-'))
                hour, minute = map(int, time_part.split(':')[:2])
            else:
                dt = datetime.fromisoformat(birth_dt.replace('Z', '+00:00'))
                year, month, day = dt.year, dt.month, dt.day
                hour, minute = dt.hour, dt.minute
        except Exception as e:
            raise ValueError(f"Could not parse datetime: {birth_dt}. Use format: YYYY-MM-DD HH:MM")

        dt = datetime(year, month, day, hour, minute, 0, tzinfo=ZoneInfo("UTC"))

        # Geocoding
        try:
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

            geolocator = Nominatim(user_agent="fates_engine_v2/2.0")
            location_obj = geolocator.geocode(location, timeout=10)

            if location_obj:
                lat, lon = location_obj.latitude, location_obj.longitude
                print(f"   📍 Geocoded '{location}' → {lat:.4f}, {lon:.4f}")
            else:
                raise ValueError(f"Location not found: '{location}'")

        except ImportError:
            raise ImportError("geopy required. Install: pip install geopy")
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            raise ConnectionError(f"Geocoding error: {e}")

        # Julian Day
        jd = ephe.julian_day(dt)

        # Initialize predictive container
        predictive_events = []
        all_predictive = {}

        # WESTERN (V2: Primary Directions + Solar Returns + Lunar Returns + Syzygy + Dignities)
        print("   → Calculating Western (Primary Directions)...")
        western = self.western_engine.calculate(jd, lat, lon, True, year)

        # Add Primary Directions (Gold Standard)
        pd_engine = PrimaryDirections(jd, lat, lon)
        primary_dirs = pd_engine.get_critical_directions(years_ahead=5)
        western["predictive"]["primary_directions"] = primary_dirs

        print("   → Validating Essential Dignities...")
        try:
            dignity_engine = EssentialDignities()
            is_day = self._is_day_chart(western['natal']['placements'], western['natal']['angles'])

            # Filter placements to only include those with proper sign/degree data
            valid_placements = {
                p: d for p, d in western['natal']['placements'].items()
                if isinstance(d, dict) and 'sign' in d and 'degree' in d
            }

            western['natal']['dignities'] = dignity_engine.calculate_dignities(
                valid_placements, is_day=is_day
            )
            western['natal']['receptions'] = dignity_engine.find_receptions(
                {p: (d['sign'], d['degree']) for p, d in valid_placements.items()},
                is_day=is_day
            )
            # Log pattern detection
            patterns = western.get('natal', {}).get('patterns', {})
            pattern_summary = patterns.get('summary', {})
            if pattern_summary.get('dominant_pattern'):
                print(f"   ✓ Dominant pattern: {pattern_summary['dominant_pattern']} "
                      f"(tension: {pattern_summary.get('chart_tension', 0)}, "
                      f"harmony: {pattern_summary.get('chart_harmony', 0)})")
        except Exception as e:
            print(f"   ⚠️  Dignity calculation error: {e}")
            western['natal']['dignities'] = {}
            western['natal']['receptions'] = {}

        # Lunar Returns (Phase 3)
        print("   → Calculating Lunar Returns...")
        moon_lon = western['natal']['placements']['Moon']['longitude']
        western['predictive']['lunar_returns'] = self.western_engine.calculate_lunar_returns(
            jd, moon_lon, years=5
        )

        # Pre-natal Syzygy (Phase 3)
        print("   → Calculating Pre-natal Syzygy...")
        syzygy_engine = SyzygyEngine(jd)
        western['natal']['syzygy'] = syzygy_engine.calculate_syzygy()

        # Solar Returns
        sr_engine = SolarReturnEngine(jd, lat, lon)
        current_year = datetime.now().year
        solar_returns = sr_engine.get_return_series(current_year, years=5)
        western["predictive"]["solar_returns"] = solar_returns
        western["predictive"]["solar_return_analysis"] = [
            sr_engine.analyze_return_vs_natal(sr) for sr in solar_returns
        ]

        # VEDIC (V2: Full Ashtakavarga + Divisional Charts + Tajaka)
        print("   → Calculating Vedic (Ashtakavarga + Vargas)...")
        try:
            vedic = calculate_vedic(jd, lat, lon, True, dt)
        except Exception as e:
            print(f"   ⚠️  Vedic calculation error: {e}")
            vedic = {"natal": {"placements": {}}, "predictive": {}, "strength": {}}

        # Kakshya Transit Analysis (Ashtakavarga-driven)
        print("   → Calculating Kakshya Transit Quality...")
        try:
            from systems.kakshya_transit import calculate_kakshya_transits
            av_engine = vedic.get("_av_engine")  # see PATCH 3 below
            if av_engine:
                bhinna = av_engine.bhinna_ashtakavarga
                sarva = av_engine.sarva_ashtakavarga
            else:
                # Fall back to vedic strength dict if engine not stored
                bhinna = {}
                sarva = [20] * 12
            kakshya_data = calculate_kakshya_transits(
                natal_jd=jd, lat=lat, lon=lon,
                bhinna_av=bhinna, sarva_av=sarva, years_ahead=5
            )
            vedic["predictive"]["kakshya_transits"] = kakshya_data
        except Exception as e:
            print(f"   ⚠️  Kakshya error: {e}")
            vedic["predictive"]["kakshya_transits"] = {"error": str(e)}

        # SAJU (Bazi)
        print("   → Calculating Saju (Four Pillars)...")
        try:
            saju = calculate_bazi(dt, True, gender, jd, lon=lon)
        except ImportError:
            saju = {"natal": {}, "strength": {}, "predictive": {}}

        # Fixed Star Parans (Phase 4 — full heliacal + natal parans)
        print("   → Calculating Fixed Star Parans...")
        try:
            from core.fixed_star_parans import calculate_parans
            parans_data = calculate_parans(jd, lat, lon, time_known=True)
            western["natal"]["fixed_stars"] = parans_data.get("conjunctions", [])  # replaces basic fixed_stars
            western["natal"]["parans"] = parans_data.get("natal_parans", [])
            western["natal"]["heliacal_events"] = parans_data.get("heliacal_events", [])
            western["natal"]["star_windows"] = parans_data.get("five_year_windows", [])
            western["natal"]["significant_stars"] = parans_data.get("significant_stars", [])
        except Exception as e:
            print(f"   ⚠️  Parans error: {e}")
            western["natal"].setdefault("fixed_stars", [])
            western["natal"]["parans"] = []
            western["natal"]["heliacal_events"] = []
            western["natal"]["star_windows"] = []

        # HELLENISTIC
        print("   → Calculating Hellenistic (Profections + ZR)...")
        hellenistic = self.hellenistic_engine.calculate(jd, lat, lon, True, year)

        # Dodecatemoria (Phase 5)
        print("   → Calculating Dodecatemoria (12th parts)...")
        try:
            dodec_engine = DodecatemoriaEngine()
            hellenistic["dodecatemoria"] = dodec_engine.calculate(jd, lat, lon, True)
        except Exception as e:
            print(f"   ⚠️  Dodecatemoria error: {e}")
            hellenistic["dodecatemoria"] = {"error": str(e)}

        # Cross-system House Lord Validation (Phase 3)
        print("   → Validating Cross-System House Lords...")
        mapper = HouseLordMapper()
        lord_validations = mapper.validate_cross_system(
            western['natal'],
            vedic.get('natal', {})
        )

        return {
            "western": western,
            "vedic": vedic,
            "bazi": saju,
            "hellenistic": hellenistic,
            "meta": {
                "jd": jd,
                "lat": lat,
                "lon": lon,
                "birth_year": year,
                "birth_datetime": dt.isoformat()
            },
            "lord_validations": lord_validations,
            "predictive": {
                "western": western.get("predictive", {}),
                "vedic": vedic.get("predictive", {}),
                "saju": saju.get("predictive", {}),
                "hellenistic": hellenistic.get("predictive", {})
            }
        }

    def _is_day_chart(self, placements: Dict, angles: Dict) -> bool:
        """Determine if day or night chart.

        Day chart: Sun ABOVE horizon = Sun in houses 7-12 (upper hemisphere).
        Sun is above the horizon when it is 0-180° ahead of the Ascendant
        in zodiac order.  Matches the Hellenistic engine formula exactly.
        """
        if 'Ascendant' not in angles or 'Sun' not in placements:
            return True  # Default to day
        asc = angles['Ascendant']['longitude']
        sun = placements['Sun']['longitude']
        diff = (sun - asc) % 360
        return 0.0 < diff < 180.0

    def _extract_prediction_events(self, chart_data: Dict) -> List[PredictionEvent]:
        """
        Extract standardized prediction events from all systems for Validation Matrix.
        Uses canonical weights from ValidationMatrix.TECHNIQUE_WEIGHTS.
        """
        from synthesis.validation_matrix import ValidationMatrix

        events = []
        now = datetime.now()
        WEIGHTS = ValidationMatrix.TECHNIQUE_WEIGHTS

        # --- Western Events ---
        w_pred = chart_data["western"].get("predictive", {})

        # Primary Directions (Gold Standard: 0.95)
        for category, directions in w_pred.get("primary_directions", {}).items():
            if isinstance(directions, list):
                for pd in directions:
                    try:
                        event_date = now + timedelta(days=pd.get("years", 0) * 365.25)
                        events.append(PredictionEvent(
                            system="Western",
                            technique="Primary Direction",
                            date_range=(event_date, event_date + timedelta(days=30)),
                            theme=category.capitalize(),
                            confidence=WEIGHTS.get("Primary Direction", 0.95),
                            description=f"{pd.get('promissor', '?')} to {pd.get('significator', '?')} ({pd.get('arc_degrees', 0):.2f}°)",
                            house_involved=10 if pd.get("significator") == "MC" else (1 if pd.get("significator") == "Asc" else 5),
                            planets_involved=[pd.get("promissor", "?"), pd.get("significator", "?")]
                        ))
                    except Exception as e:
                        logger.warning(f"Error processing PD: {e}")

        # Solar Returns (0.90)
        for sr in w_pred.get("solar_returns", []):
            if isinstance(sr, dict) and "date" in sr:
                try:
                    sr_date = datetime.fromisoformat(sr["date"].replace('Z', '+00:00'))
                    events.append(PredictionEvent(
                        system="Western",
                        technique="Solar Return",
                        date_range=(sr_date, sr_date + timedelta(days=365)),
                        theme="Annual Theme",
                        confidence=WEIGHTS.get("Solar Return", 0.90),
                        description=f"Solar Return {sr.get('year')} with Asc in natal house {sr.get('dominant_house', 'unknown')}",
                        house_involved=sr.get("dominant_house", 1),
                        planets_involved=["Sun"]
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Solar Return: {e}")

        # Lunar Returns (0.82)
        for lr in w_pred.get("lunar_returns", []):
            if isinstance(lr, dict) and "date" in lr:
                try:
                    lr_date = datetime.fromisoformat(lr["date"].replace('Z', '+00:00'))
                    events.append(PredictionEvent(
                        system="Western",
                        technique="LUNAR_RETURN",
                        date_range=(lr_date, lr_date + timedelta(days=28)),
                        theme="Monthly Focus",
                        confidence=WEIGHTS.get("LUNAR_RETURN", 0.82),
                        description=f"Lunar Return {lr.get('year')}-{lr.get('month')}",
                        house_involved=1,
                        planets_involved=["Moon"]
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Lunar Return: {e}")

        # --- Vedic Events ---
        v_pred = chart_data.get("vedic", {}).get("predictive", {})

        # Vimshottari Dasha (0.88)
        dasha = v_pred.get("vimshottari", {})
        if dasha:
            try:
                remaining = dasha.get("approx_remaining_years", 1)
                events.append(PredictionEvent(
                    system="Vedic",
                    technique="Vimshottari Dasha",
                    date_range=(now, now + timedelta(days=remaining * 365)),
                    theme=f"{dasha.get('maha_lord', 'Unknown')} Period",
                    confidence=WEIGHTS.get("Vimshottari Dasha", 0.88),
                    description=f"Maha Dasha of {dasha.get('maha_lord')}",
                    house_involved=1,
                    planets_involved=[dasha.get("maha_lord", "Sun")]
                ))
            except Exception as e:
                logger.warning(f"Error processing Dasha: {e}")

        # Tajaka (0.85)
        for taj in v_pred.get("tajaka", []):
            if isinstance(taj, dict):
                try:
                    taj_date = datetime(taj.get("year", now.year), 1, 1)
                    muntha = taj.get("muntha", 0)
                    house = int(muntha // 30) + 1 if muntha else 1
                    events.append(PredictionEvent(
                        system="Vedic",
                        technique="Tajaka",
                        date_range=(taj_date, taj_date + timedelta(days=365)),
                        theme="Muntha Year",
                        confidence=WEIGHTS.get("Tajaka", 0.85),
                        description=f"Muntha in {taj.get('muntha_sign', 'Unknown')}, Lord: {taj.get('lord_of_year', 'Unknown')}",
                        house_involved=house,
                        planets_involved=[taj.get("lord_of_year", "Sun")]
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Tajaka: {e}")

        # --- Saju Events ---
        s_pred = chart_data.get("bazi", {}).get("predictive", {})

        # Da Yun (Major Luck)
        da_yun = s_pred.get("da_yun", {})
        if isinstance(da_yun, dict):
            for pillar in da_yun.get("pillars", [])[:3]:
                try:
                    start_age = pillar.get("start_age", 0)
                    birth_year = chart_data.get("meta", {}).get("birth_year", now.year)
                    start_year = birth_year + int(start_age)
                    start_date = datetime(start_year, 1, 1)

                    events.append(PredictionEvent(
                        system="Saju",
                        technique="Da Yun",
                        date_range=(start_date, start_date + timedelta(days=10 * 365)),
                        theme=f"Luck Pillar {pillar.get('stem', '?')}{pillar.get('branch', '?')}",
                        confidence=0.80,
                        description=f"10-year luck pillar: {pillar.get('stem_element', '?')} {pillar.get('branch_element', '?')}",
                        house_involved=1,
                        planets_involved=[pillar.get("stem_element", "Wood")]
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Da Yun: {e}")

        # Profections (0.70) — use birthday-relative date, not Jan 1
        profs = w_pred.get("profections_timeline", [])
        birth_year = chart_data.get("meta", {}).get("birth_year", now.year)
        birth_jd   = chart_data.get("meta", {}).get("jd", 0)
        # Approximate birth month/day from JD
        try:
            import swisseph as swe
            _y, _m, _d, _h = swe.revjul(birth_jd)
            birth_month, birth_day = int(_m), int(_d)
        except Exception:
            birth_month, birth_day = 7, 1  # safe fallback

        for prof in profs[:5]:
            if isinstance(prof, dict):
                try:
                    year = prof.get("year", now.year)
                    age  = prof.get("age", 0)
                    # Profection activates on the birthday in that year
                    try:
                        start_date = datetime(year, birth_month, birth_day)
                    except ValueError:
                        start_date = datetime(year, birth_month, 28)
                    events.append(PredictionEvent(
                        system="Western",
                        technique="Profection",
                        date_range=(start_date, start_date + timedelta(days=365)),
                        theme=f"Profected {prof.get('profected_sign', 'Unknown')}",
                        confidence=WEIGHTS.get("Profection", 0.70),
                        description=f"Annual Profection age {age}: {prof.get('time_lord', '?')} rules year {year}",
                        house_involved=prof.get("activated_house", 1),
                        planets_involved=[prof.get("time_lord", "Sun")]
                    ))
                except Exception as e:
                    logger.warning(f"Error processing Profection: {e}")

        chart_data["predictive_event_count"] = len(events)

        # Outer Planet Transit Exact Hits (0.62 weight — individual aspect dates)
        # These are the most precise timing data in the chart: exact dates from ephemeris.
        outer = w_pred.get("outer_transit_aspects", {})
        for hit in outer.get("hits") or outer.get("all_hits", []):
            try:
                # Prefer ISO format; fall back to parsing "Mon DD, YYYY"
                iso_date = hit.get("exact_date_iso", "")
                if iso_date:
                    y, mo, d = map(int, iso_date.split("-"))
                    exact_dt = datetime(y, mo, d)
                else:
                    from datetime import datetime as _dt
                    exact_dt = _dt.strptime(hit.get("exact_date", ""), "%b %d, %Y")

                if exact_dt <= now:
                    continue   # past — skip

                # Entry/exit window from the hit dict (already ISO if present)
                entry_str = hit.get("entry_date", "")
                exit_str  = hit.get("exit_date", "")
                try:
                    entry_dt = datetime.strptime(entry_str, "%Y-%m-%d") if entry_str else exact_dt - timedelta(days=45)
                    exit_dt  = datetime.strptime(exit_str,  "%Y-%m-%d") if exit_str  else exact_dt + timedelta(days=45)
                except Exception:
                    entry_dt = exact_dt - timedelta(days=45)
                    exit_dt  = exact_dt + timedelta(days=45)

                transiting = hit.get("transiting") or hit.get("planet", "Unknown")
                natal_pt   = hit.get("natal_point", "Unknown")
                aspect     = hit.get("aspect", "?")

                house_map = {
                    "Sun": 5, "Moon": 4, "Mercury": 3, "Venus": 7,
                    "Mars": 1, "Ascendant": 1, "Midheaven": 10
                }
                house = house_map.get(natal_pt, 1)

                events.append(PredictionEvent(
                    system="Western",
                    technique="Transit_Aspect",
                    date_range=(entry_dt, exit_dt),
                    theme=f"{transiting} {aspect} {natal_pt}",
                    confidence=WEIGHTS.get("Transit_Aspect", 0.62),
                    description=(
                        f"{transiting} {aspect} natal {natal_pt} "
                        f"exact {exact_dt.strftime('%Y-%m-%d')} (orb {hit.get('orb_at_exact','?')}°)"
                    ),
                    house_involved=house,
                    planets_involved=[transiting, natal_pt]
                ))
            except Exception as e:
                logger.warning(f"Error processing transit hit: {e}")

        if not events:
            logger.warning("No predictive events extracted - check chart data structure")

        logger.info(f"Extracted {len(events)} predictive events for Validation Matrix")
        return events

    def _gather_expert_analyses(self, chart_data: Dict, convergences: List[Dict],
                               contradictions: List[Dict],
                               user_questions: list = None) -> list:
        """Gather analyses with pre-validated context and question focus."""
        print("   Analyzing with Western Expert (Primary Directions emphasis)...")
        western = self.western_expert.analyze(chart_data, "natal",
                                              user_questions=user_questions)

        print("   Analyzing with Vedic Expert (Ashtakavarga + Vargas)...")
        vedic = self.vedic_expert.analyze(chart_data, "natal",
                                          user_questions=user_questions)

        print("   Analyzing with Saju Expert...")
        saju = self.saju_expert.analyze(chart_data, "natal",
                                        user_questions=user_questions)

        print("   Analyzing with Hellenistic Expert...")
        hellenistic = self.hellenistic_expert.analyze(chart_data, "natal",
                                                      user_questions=user_questions)

        return [western, vedic, saju, hellenistic]


# Global instance
orchestrator = FatesOrchestrator()
