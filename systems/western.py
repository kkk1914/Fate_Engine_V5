"""Western Tropical Astrology Engine."""
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional

import swisseph as swe

from core.ephemeris import ephe
from core.primary_directions import PrimaryDirections
from core.solar_return import SolarReturnEngine
from core.lunar_return import LunarReturnEngine
from core.syzygy import SyzygyEngine
from core.essential_dignities import EssentialDignities

# Constants
ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

ASPECTS = [(0, "Conjunction"), (60, "Sextile"), (90, "Square"),
           (120, "Trine"), (180, "Opposition")]
OOB_LIMIT = 23.4392911

# Outer planets to scan for transit aspects
OUTER_PLANETS = {
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    "Uranus":  swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto":   swe.PLUTO,
}

# Natal points that matter for life events
TRANSIT_TARGETS = ["Sun", "Moon", "Mercury", "Venus", "Mars",
                   "Ascendant", "Midheaven"]

# Orb for transit hits (degrees)
TRANSIT_ORB = 1.0


def clamp360(x: float) -> float:
    return x % 360.0


def midpoint(d1: float, d2: float) -> float:
    a, b = clamp360(d1), clamp360(d2)
    diff = abs(a - b)
    if diff > 180:
        return clamp360((a + b + 360) / 2)
    return clamp360((a + b) / 2)


def _angular_distance(a: float, b: float) -> float:
    """Smallest arc between two ecliptic longitudes."""
    diff = abs(clamp360(a) - clamp360(b))
    return min(diff, 360.0 - diff)


def _aspect_orb(lon_transit: float, lon_natal: float, angle: float) -> float:
    """Return orb of transit to aspect angle, or 999 if not within range."""
    sep = _angular_distance(lon_transit, lon_natal)
    return abs(sep - angle)


class WesternEngine:
    """Tropical astrology with predictive techniques."""

    def __init__(self):
        self.dignity_engine = EssentialDignities()

    def calculate(self, jd: float, lat: float, lon: float,
                  time_known: bool, birth_year: int) -> Dict[str, Any]:
        """Calculate complete Western chart."""
        natal = self._calc_natal(jd, lat, lon, time_known)
        predictive = self._calc_predictive(jd, birth_year, natal, time_known, lat, lon)

        # Primary Directions (5-year)
        pd_engine = PrimaryDirections(jd, lat, lon)
        primary_dirs = pd_engine.get_critical_directions(years_ahead=5)

        # Solar Returns (5-year)
        sr_engine = SolarReturnEngine(jd, lat, lon)
        current_year = datetime.now().year
        solar_returns = sr_engine.get_return_series(current_year, years=5)

        # Analyze each return
        sr_analysis = [sr_engine.analyze_return_vs_natal(sr) for sr in solar_returns]

        predictive["primary_directions"] = primary_dirs
        predictive["solar_returns"] = solar_returns
        predictive["solar_return_analysis"] = sr_analysis

        # Phase 4: Void of Course Moon (next 30 days)
        try:
            from core.void_of_course import VoidOfCourseMoon
            voc_engine = VoidOfCourseMoon()
            now_jd = ephe.julian_day(datetime.now(timezone.utc))
            predictive["voc_current"] = voc_engine.is_void_at(now_jd)
            predictive["voc_periods_30d"] = voc_engine.get_voc_periods(now_jd, days_ahead=30)
        except Exception as e:
            predictive["voc_current"] = {"error": str(e)}
            predictive["voc_periods_30d"] = []

        return {"natal": natal, "predictive": predictive}

    def _calc_natal(self, jd: float, lat: float, lon: float,
                    time_known: bool) -> Dict[str, Any]:
        """Calculate natal positions."""
        placements = {}

        # Planet positions
        for name, code in PLANETS.items():
            lon_val, lat_val = ephe.planet_longitude(jd, code)
            dec = self._calc_declination(jd, code)

            placements[name] = {
                "longitude": lon_val,
                "sign": ZODIAC[int(clamp360(lon_val) // 30)],
                "degree": clamp360(lon_val) % 30,
                "latitude": lat_val,
                "declination": dec,
                "out_of_bounds": abs(dec) > OOB_LIMIT,
                "retrograde": ephe.is_retrograde(jd, code)
            }

        # Houses & Angles
        houses, angles = {}, {}
        if time_known:
            cusps, ascmc = ephe.houses(jd, lat, lon, b'P')  # Placidus default
            asc = float(ascmc[0])
            mc = float(ascmc[1])

            angles = {
                "Ascendant": {
                    "longitude": asc,
                    "sign": ZODIAC[int(clamp360(asc) // 30)],
                    "degree": clamp360(asc) % 30
                },
                "Midheaven": {
                    "longitude": mc,
                    "sign": ZODIAC[int(clamp360(mc) // 30)],
                    "degree": clamp360(mc) % 30
                }
            }

            for i in range(12):
                c = float(cusps[i])
                houses[f"House_{i+1}"] = {
                    "longitude": c,
                    "sign": ZODIAC[int(clamp360(c) // 30)],
                    "degree": clamp360(c) % 30
                }

        # Add North/South Nodes
        from swisseph import MEAN_NODE
        node_pos, _ = swe.calc_ut(jd, MEAN_NODE)
        placements["North Node"] = {
            "longitude": node_pos[0],
            "sign": ZODIAC[int(clamp360(node_pos[0]) // 30)],
            "degree": clamp360(node_pos[0]) % 30,
            "latitude": 0.0,
            "declination": 0.0,
            "out_of_bounds": False,
            "retrograde": True
        }
        placements["South Node"] = {
            "longitude": clamp360(node_pos[0] + 180),
            "sign": ZODIAC[int(clamp360(node_pos[0] + 180) // 30)],
            "degree": clamp360(node_pos[0] + 180) % 30,
            "latitude": 0.0,
            "declination": 0.0,
            "out_of_bounds": False,
            "retrograde": True
        }

        # Add Descendant (opposite Ascendant)
        if "Ascendant" in angles:
            desc_lon = clamp360(angles["Ascendant"]["longitude"] + 180)
            angles["Descendant"] = {
                "longitude": desc_lon,
                "sign": ZODIAC[int(desc_lon // 30)],
                "deg_in_sign": desc_lon % 30
            }

        # Aspects
        aspects = self._calc_aspects(placements)

        # Lots (Fortune & Spirit)
        lots = {}
        if time_known and "Ascendant" in angles:
            lots = self._calc_lots(
                angles["Ascendant"]["longitude"],
                placements["Sun"]["longitude"],
                placements["Moon"]["longitude"]
            )

        # Fixed Stars (Royal)
        fixed_stars = self._calc_fixed_stars(jd, placements)

        # Phase 4: Geometric Pattern Detection
        try:
            from core.pattern_detection import PatternDetector
            detector = PatternDetector()
            patterns = detector.detect_all(placements, angles)
        except Exception as e:
            patterns = {"error": str(e), "summary": {}}

        return {
            "placements": placements,
            "houses": houses,
            "angles": angles,
            "aspects": aspects,
            "lots": lots,
            "fixed_stars": fixed_stars,
            "patterns": patterns
        }

    def _calc_declination(self, jd: float, planet: int) -> float:
        """Calculate declination."""
        pos_equ, _ = swe.calc_ut(jd, planet, swe.FLG_EQUATORIAL)
        return float(pos_equ[1])

    def _calc_aspects(self, placements: Dict) -> List[Dict]:
        """Calculate Ptolemaic aspects with 8° orb."""
        aspects = []
        names = list(placements.keys())

        for i in range(len(names)):
            for j in range(i+1, len(names)):
                p1, p2 = names[i], names[j]
                lon1 = placements[p1]["longitude"]
                lon2 = placements[p2]["longitude"]

                diff = abs(clamp360(lon1) - clamp360(lon2))
                dist = min(diff, 360 - diff)

                for angle, name in ASPECTS:
                    if abs(dist - angle) <= 8.0:
                        aspects.append({
                            "p1": p1,
                            "p2": p2,
                            "type": name,
                            "orb": round(abs(dist - angle), 2),
                            "degrees": round(dist, 2)
                        })
        return aspects

    def _calc_lots(self, asc: float, sun: float, moon: float) -> Dict[str, Any]:
        """Calculate Arabic Parts (Lots of Fortune and Spirit)."""
        diff = (sun - asc) % 360
        is_day = 0.0 < diff < 180.0

        if is_day:
            fortune = clamp360(asc + moon - sun)
            spirit = clamp360(asc + sun - moon)
        else:
            fortune = clamp360(asc + sun - moon)
            spirit = clamp360(asc + moon - sun)

        return {
            "Lot_of_Fortune": {
                "longitude": fortune,
                "sign": ZODIAC[int(clamp360(fortune) // 30)],
                "degree": clamp360(fortune) % 30
            },
            "Lot_of_Spirit": {
                "longitude": spirit,
                "sign": ZODIAC[int(clamp360(spirit) // 30)],
                "degree": clamp360(spirit) % 30
            }
        }

    def _calc_fixed_stars(self, jd: float, placements: Dict) -> List[Dict]:
        """Check conjunctions to Royal Fixed Stars."""
        royal_stars = ["Regulus", "Spica", "Aldebaran", "Antares", "Fomalhaut"]
        hits = []

        for star in royal_stars:
            s_lon = ephe.fixstar(star, jd)
            if s_lon is None:
                continue

            for pname, pdata in placements.items():
                lon = pdata["longitude"]
                diff = abs(clamp360(lon) - clamp360(s_lon))
                dist = min(diff, 360 - diff)

                if dist <= 1.0:
                    hits.append({
                        "planet": pname,
                        "star": star,
                        "orb": round(dist, 3)
                    })
        return hits

    # ─────────────────────────────────────────────────────────────────────────
    # OUTER TRANSIT ASPECT SCANNER
    # Replaces the Jan-1 snapshot with exact-date aspect hits.
    # ─────────────────────────────────────────────────────────────────────────

    def _scan_outer_transit_aspects(
        self,
        natal: Dict,
        scan_years: int = 5,
        orb: float = TRANSIT_ORB,
    ) -> Dict[str, Any]:
        """
        Scan day-by-day over `scan_years` to find every moment an outer planet
        forms an exact aspect (±orb) to a natal point.

        Returns:
            {
              "by_year":      {str(year): [hit, ...]},
              "all_hits":     [hit, ...],       # sorted by exact_jd
              "summary_block": str              # dense text for LLM context
            }

        Each hit dict:
            planet, natal_point, aspect, orb_at_exact, exact_date,
            exact_jd, year, applying (bool), natal_lon, transit_lon
        """
        now     = datetime.now(timezone.utc)
        start_jd = ephe.julian_day(now)
        end_jd   = start_jd + scan_years * 365.25

        # Build natal point longitudes
        natal_lons: Dict[str, float] = {}
        for p in TRANSIT_TARGETS:
            if p in natal.get("placements", {}):
                natal_lons[p] = natal["placements"][p]["longitude"]
            elif p in natal.get("angles", {}):
                natal_lons[p] = natal["angles"][p]["longitude"]

        if not natal_lons:
            return {"by_year": {}, "all_hits": [], "summary_block": "No natal points found."}

        all_hits: List[Dict] = []

        # Step 3 days at a time (outer planets move <0.15°/day — safe for 1° orb)
        # Then do binary refinement when a crossing is detected.
        step_jd = 3.0

        for t_name, t_code in OUTER_PLANETS.items():
            for n_name, n_lon in natal_lons.items():
                for ang, asp_name in ASPECTS:
                    # Track sign of (current_orb - target) to detect zero crossings
                    jd_scan = start_jd
                    prev_orb: Optional[float] = None
                    prev_jd:  Optional[float] = None

                    while jd_scan <= end_jd:
                        t_lon, _ = ephe.planet_longitude(jd_scan, t_code)
                        cur_orb = _aspect_orb(t_lon, n_lon, ang)

                        if prev_orb is not None and prev_orb > orb and cur_orb <= orb:
                            # Entered orb — refine exact with binary search
                            exact_jd = self._refine_exact(
                                t_code, n_lon, ang, prev_jd, jd_scan
                            )
                            if exact_jd is not None:
                                t_lon_exact, _ = ephe.planet_longitude(exact_jd, t_code)
                                final_orb = _aspect_orb(t_lon_exact, n_lon, ang)

                                # Determine applying vs separating
                                t_lon_plus1, _ = ephe.planet_longitude(exact_jd + 1, t_code)
                                orb_plus1 = _aspect_orb(t_lon_plus1, n_lon, ang)
                                applying = orb_plus1 < final_orb

                                dt_exact = datetime(*swe.revjul(exact_jd)[:3])
                                exact_date_str    = dt_exact.strftime("%b %d, %Y")
                                exact_date_iso    = dt_exact.strftime("%Y-%m-%d")   # ISO for parsers
                                year = dt_exact.year

                                # Approximate entry/exit window (±ORB days at outer planet speed)
                                # Outer planets move ~0.03–0.25°/day; 3° orb ≈ 12–100 days either side.
                                # Use a simple ±45-day estimate as a safe conservative window.
                                dt_entry = datetime(*swe.revjul(exact_jd - 45)[:3])
                                dt_exit  = datetime(*swe.revjul(exact_jd + 45)[:3])

                                hit = {
                                    # Canonical names
                                    "planet":        t_name,
                                    "natal_point":   n_name,
                                    "aspect":        asp_name,
                                    "orb_at_exact":  round(final_orb, 3),
                                    "exact_date":    exact_date_str,     # human: "Mar 14, 2027"
                                    "exact_date_iso": exact_date_iso,    # machine: "2027-03-14"
                                    "exact_jd":      round(exact_jd, 4),
                                    "year":          year,
                                    "applying":      applying,
                                    "natal_lon":     round(n_lon, 4),
                                    "transit_lon":   round(t_lon_exact, 4),
                                    # Aliases for downstream consumers
                                    "transiting":    t_name,             # alias for "planet"
                                    "entry_date":    dt_entry.strftime("%Y-%m-%d"),
                                    "exit_date":     dt_exit.strftime("%Y-%m-%d"),
                                }
                                all_hits.append(hit)

                        elif prev_orb is not None and prev_orb <= orb and cur_orb > orb:
                            # Exiting orb — capture separating exact if we missed ingress
                            pass  # already captured on entry

                        prev_orb = cur_orb
                        prev_jd  = jd_scan
                        jd_scan += step_jd

        # Sort by date
        all_hits.sort(key=lambda h: h["exact_jd"])

        # Group by year
        by_year: Dict[str, List] = {}
        for hit in all_hits:
            yr = str(hit["year"])
            by_year.setdefault(yr, []).append(hit)

        # Build dense summary block for LLM
        summary_lines = ["=== OUTER PLANET TRANSIT ASPECTS (exact dates) ==="]
        for hit in all_hits[:60]:  # cap to avoid context bloat
            app = "applying" if hit["applying"] else "separating"
            summary_lines.append(
                f"{hit['exact_date']}: {hit['planet']} {hit['aspect']} "
                f"natal {hit['natal_point']} (orb {hit['orb_at_exact']:.2f}°, {app})"
            )
        summary_block = "\n".join(summary_lines)

        return {
            "by_year":       by_year,
            "all_hits":      all_hits,
            "hits":          all_hits,   # alias — some consumers read "hits", others "all_hits"
            "summary_block": summary_block,
        }

    def _refine_exact(
        self,
        planet_code: int,
        natal_lon: float,
        aspect_angle: float,
        jd_lo: float,
        jd_hi: float,
        max_iter: int = 20,
    ) -> Optional[float]:
        """
        Binary search between jd_lo and jd_hi for the JD where
        _aspect_orb(transit, natal, angle) is minimised (closest to exact).
        Returns JD of minimum orb, or None if something goes wrong.
        """
        try:
            for _ in range(max_iter):
                mid = (jd_lo + jd_hi) / 2.0
                t_lon_lo, _ = ephe.planet_longitude(jd_lo, planet_code)
                t_lon_hi, _ = ephe.planet_longitude(jd_hi, planet_code)
                t_lon_mid, _ = ephe.planet_longitude(mid, planet_code)

                orb_lo  = _aspect_orb(t_lon_lo,  natal_lon, aspect_angle)
                orb_mid = _aspect_orb(t_lon_mid, natal_lon, aspect_angle)
                orb_hi  = _aspect_orb(t_lon_hi,  natal_lon, aspect_angle)

                if orb_mid <= orb_lo and orb_mid <= orb_hi:
                    return mid
                elif orb_lo < orb_hi:
                    jd_hi = mid
                else:
                    jd_lo = mid

                if (jd_hi - jd_lo) < (1.0 / 1440):  # converged to < 1 minute
                    break

            return (jd_lo + jd_hi) / 2.0
        except Exception:
            return None

    def _calc_predictive(self, jd: float, birth_year: int,
                         natal: Dict, time_known: bool,
                         birth_lat: float = 0.0, birth_lon: float = 0.0) -> Dict[str, Any]:
        """Calculate predictive elements (5-year timeline)."""
        now = datetime.now(timezone.utc)
        current_age = max(0, now.year - birth_year)

        # ── SECONDARY PROGRESSIONS — Full Implementation ─────────────────────
        # Accurate elapsed time: use JD arithmetic, not calendar year integer.
        # 1 day of ephemeris = 1 year of life (Ptolemy's "day-for-a-year" rule).
        now_jd      = ephe.julian_day(now)
        elapsed_yrs = (now_jd - jd) / 365.25   # precise fractional years
        prog_jd     = jd + elapsed_yrs          # progressed moment in ephemeris

        progressions: Dict[str, Any] = {}

        # All 7 classical planets (outer planets progress imperceptibly fast
        # but Jupiter/Saturn still move ~5°/~2° per year — worth including)
        PROG_PLANETS = [
            ("Sun",     swe.SUN),     ("Moon",    swe.MOON),
            ("Mercury", swe.MERCURY), ("Venus",   swe.VENUS),
            ("Mars",    swe.MARS),    ("Jupiter", swe.JUPITER),
            ("Saturn",  swe.SATURN),
        ]

        for name, code in PROG_PLANETS:
            p_lon, _ = ephe.planet_longitude(prog_jd, code)
            progressions[f"Progressed_{name}"] = {
                "longitude":  p_lon,
                "sign":       ZODIAC[int(clamp360(p_lon) // 30)],
                "degree":     round(clamp360(p_lon) % 30, 4),
                "retrograde": ephe.is_retrograde(prog_jd, code),
            }

        # Progressed Ascendant and Midheaven
        # Cast the full house chart at prog_jd using natal geographic coordinates.
        # This is the correct modern method (not Solar Arc MC approximation).
        if time_known and birth_lat and birth_lon:
            try:
                prog_cusps, prog_ascmc = ephe.houses(prog_jd, birth_lat, birth_lon, b'P')
                p_asc = float(prog_ascmc[0])
                p_mc  = float(prog_ascmc[1])
                progressions["Progressed_Ascendant"] = {
                    "longitude": p_asc,
                    "sign":      ZODIAC[int(clamp360(p_asc) // 30)],
                    "degree":    round(clamp360(p_asc) % 30, 4),
                }
                progressions["Progressed_MC"] = {
                    "longitude": p_mc,
                    "sign":      ZODIAC[int(clamp360(p_mc) // 30)],
                    "degree":    round(clamp360(p_mc) % 30, 4),
                }
            except Exception:
                pass  # Skip quietly if coordinates unavailable

        # Progressed lunar phase (secondary progression Moon-Sun relationship)
        # Tells the broad developmental chapter the native is in
        if "Progressed_Sun" in progressions and "Progressed_Moon" in progressions:
            p_sun_lon  = progressions["Progressed_Sun"]["longitude"]
            p_moon_lon = progressions["Progressed_Moon"]["longitude"]
            prog_elongation = clamp360(p_moon_lon - p_sun_lon)
            if prog_elongation < 45:
                prog_phase = "New (Emergence)"
            elif prog_elongation < 90:
                prog_phase = "Crescent (Building)"
            elif prog_elongation < 135:
                prog_phase = "First Quarter (Action)"
            elif prog_elongation < 180:
                prog_phase = "Gibbous (Refining)"
            elif prog_elongation < 225:
                prog_phase = "Full (Culmination)"
            elif prog_elongation < 270:
                prog_phase = "Disseminating (Sharing)"
            elif prog_elongation < 315:
                prog_phase = "Last Quarter (Reorientation)"
            else:
                prog_phase = "Balsamic (Release)"
            progressions["lunar_phase"] = {
                "phase":       prog_phase,
                "elongation":  round(prog_elongation, 2),
            }

        # Progressed-to-natal aspects (the primary timing engine for progressions)
        # Orb of 1° is standard for progressed aspects.
        PROG_ORB = 1.0
        prog_natal_aspects = []

        # Build the lookup tables
        prog_lons = {
            k.replace("Progressed_", ""): v["longitude"]
            for k, v in progressions.items()
            if k.startswith("Progressed_")
        }
        natal_lons: Dict[str, float] = {}
        natal_lons.update({k: v["longitude"] for k, v in natal.get("placements", {}).items()
                           if isinstance(v, dict) and "longitude" in v})
        natal_lons.update({k: v["longitude"] for k, v in natal.get("angles", {}).items()
                           if isinstance(v, dict) and "longitude" in v})

        for prog_point, p_lon in prog_lons.items():
            for natal_point, n_lon in natal_lons.items():
                # Avoid planet aspecting its own natal position (too many trivial hits)
                if prog_point == natal_point:
                    continue
                diff = abs(clamp360(p_lon) - clamp360(n_lon))
                dist = min(diff, 360.0 - diff)
                for angle, asp_name in [
                    (0,   "Conjunction"), (60,  "Sextile"),
                    (90,  "Square"),      (120, "Trine"),
                    (180, "Opposition"),
                ]:
                    orb = abs(dist - angle)
                    if orb <= PROG_ORB:
                        prog_natal_aspects.append({
                            "progressed":  prog_point,
                            "natal":       natal_point,
                            "aspect":      asp_name,
                            "orb":         round(orb, 3),
                        })

        # Sort by exactness (tightest first)
        prog_natal_aspects.sort(key=lambda x: x["orb"])
        progressions["prog_natal_aspects"] = prog_natal_aspects

        # Solar Arc
        solar_arc = 0
        if "Sun" in natal["placements"]:
            natal_sun = natal["placements"]["Sun"]["longitude"]
            prog_sun = progressions["Progressed_Sun"]["longitude"]
            solar_arc = clamp360(prog_sun - natal_sun)

        # Solar Arc Directions — extend to all personal points + progressed angles
        directed = {}
        if solar_arc > 0:
            # Apply SA to all natal planets and angles
            all_natal_pts = {}
            all_natal_pts.update(natal.get("placements", {}))
            all_natal_pts.update(natal.get("angles", {}))
            for key, base in all_natal_pts.items():
                if isinstance(base, dict) and "longitude" in base:
                    dlon = clamp360(base["longitude"] + solar_arc)
                    directed[key] = {
                        "longitude": dlon,
                        "sign":      ZODIAC[int(clamp360(dlon) // 30)],
                        "degree":    clamp360(dlon) % 30
                    }

        # Annual Profections (5-year)
        # Use fractional age so profection year activates on birthday, not Jan 1.
        profections = []
        rulers = {
            "Aries": "Mars",    "Taurus": "Venus",   "Gemini": "Mercury",
            "Cancer": "Moon",   "Leo": "Sun",         "Virgo": "Mercury",
            "Libra": "Venus",   "Scorpio": "Mars",    "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }

        for offset in range(5):
            year = now.year + offset
            # Age at the start of each target calendar year (birthday-precise)
            age = int(elapsed_yrs) + offset

            asc_sign_idx = 0
            if time_known and "Ascendant" in natal.get("angles", {}):
                asc_sign = natal["angles"]["Ascendant"]["sign"]
                asc_sign_idx = ZODIAC.index(asc_sign)

            prof_idx  = (asc_sign_idx + age) % 12
            prof_sign = ZODIAC[prof_idx]

            profections.append({
                "year":            year,
                "age":             age,
                "profected_sign":  prof_sign,
                "time_lord":       rulers[prof_sign],
                "activated_house": (age % 12) + 1,
            })

        # ── OUTER PLANET TRANSIT ASPECT SCANNER (replaces Jan-1 snapshot) ──
        # Scans day-by-day for exact hits with binary refinement.
        # Produces outer_transit_aspects.by_year and .summary_block.
        outer_transit_aspects = self._scan_outer_transit_aspects(natal, scan_years=5)

        # Legacy snapshot transits (kept for backwards compat with any old callers)
        transits = []
        for offset in range(5):
            target_year = now.year + offset
            target_dt   = datetime(target_year, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            target_jd   = ephe.julian_day(target_dt)
            yearly_transits = {}
            for name in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                lon, _ = ephe.planet_longitude(target_jd, PLANETS[name])
                yearly_transits[name] = {
                    "sign": ZODIAC[int(clamp360(lon) // 30)],
                    "degree": clamp360(lon) % 30
                }
            transits.append({"year": target_year, "positions": yearly_transits})

        return {
            "current_age":           current_age,
            "elapsed_years":         round(elapsed_yrs, 4),   # precise fractional age
            "prog_jd":               round(prog_jd, 6),        # for external callers
            "progressions":          progressions,
            "solar_arc_degrees":     round(solar_arc, 2),
            "directed_positions":    directed,
            "profections_timeline":  profections,
            "transits_timeline":     transits,          # legacy snapshots
            "outer_transit_aspects": outer_transit_aspects,  # NEW: exact dates
        }

    def calculate_lunar_returns(self, natal_jd: float, natal_moon_lon: float,
                                 years: int = 1) -> List[Dict]:
        """Calculate lunar returns for monthly precision."""
        from core.lunar_return import LunarReturnEngine
        engine = LunarReturnEngine(natal_jd, natal_moon_lon)
        return engine.get_return_series(datetime.now().year, months=12 * years)

    def calculate_syzygy(self, natal_jd: float) -> Dict[str, Any]:
        """Calculate pre-natal syzygy."""
        from core.syzygy import SyzygyEngine
        engine = SyzygyEngine(natal_jd)
        return engine.calculate_syzygy()

    def calculate_dignities(self, placements: Dict[str, Any],
                             is_day: bool = True) -> Dict[str, Any]:
        """Calculate essential dignities for all planets."""
        from core.essential_dignities import EssentialDignities
        dignity_engine = EssentialDignities()

        positions = {p: (data['sign'], data['degree'])
                     for p, data in placements.items()
                     if 'sign' in data and 'degree' in data}

        dignities = {}
        for planet, (sign, deg) in positions.items():
            dignities[planet] = dignity_engine.calculate_dignity(
                planet, sign, deg, is_day
            ).__dict__

        receptions = dignity_engine.find_receptions(positions, is_day)
        almuten    = dignity_engine.calculate_almuten(positions, is_day)

        return {
            'planet_dignities': dignities,
            'receptions':       receptions,
            'almuten':          almuten
        }


# Export for other modules
__all__ = ['WesternEngine', 'ZODIAC', 'clamp360']
