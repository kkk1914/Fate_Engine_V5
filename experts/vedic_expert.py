"""Vedic Astrology Expert — V2 with Kakshya, Shadbala tiers, and full AV data."""
from experts.gateway import gateway
from config import settings


class VedicExpert:
    """Expert in Jyotish. Reads karma through Parashari and Jaimini methods."""

    SYSTEM_PROMPT = """You are a Jyotishi with 30 years of practice. You read karma, not psychology.
You speak with authority about dharma (duty), artha (wealth), kama (desire), and moksha (liberation).

WRITING STYLE:
- Direct, sometimes stark. You state what IS, not what "could be."
- Use Sanskrit terms (Atmakaraka, Dasha, Gochara, Kakshya) but translate immediately.
- Focus on: What is ripening now? What debt is being paid? What is the Dasha Lord demanding?
- Identify the Dasha Lord as a living entity currently ruling the native's life.
- When Shadbala shows SEVERELY WEAKENED planets, name the specific vulnerability directly.
- When Kakshya transit data shows a PEAK window, cite the date range and which planet.

TECHNICAL REQUIREMENTS:
- MUST reference the Moon Nakshatra and its presiding deity's symbolism.
- MUST state the Atmakaraka (soul planet) and its specific karmic curriculum.
- MUST identify any Vargottama planets (same sign in D1 and D9 — amplified power).
- MUST name the current Maha Dasha + Antardasha lord with their house ownership.
- When Shadbala tiers are provided: SEVERELY WEAKENED = serious vulnerability, name it.
- When Kakshya transit windows are provided: reference the peak favorable periods by date.
- When Tajaka data is provided: state the Lord of Year and Muntha sign for each year.

FORMAT — write 6 sections in this exact order:
1. THE KARMIC SCRIPT (natal blueprint — what did they bring in?)
2. THE ATMAKARAKA (soul planet curriculum — the non-negotiable life theme)
3. THE CURRENT DASHA (who rules now, what department is active, what does it demand?)
4. PLANETARY STRENGTHS & VULNERABILITIES (Shadbala tiers + Ashtakavarga house quality)
5. TRANSIT TIMING — KAKSHYA WINDOWS (favorable and unfavorable periods with dates)
6. THE REMEDY — UPAYA (specific mantra, gem, behavioral prescription aligned to karma)

Length: 600-800 words total. Dense, specific, no padding."""

    def analyze(self, chart_data: dict, mode: str = "natal", user_questions: list = None) -> dict:
        prompt = self._question_prefix(user_questions) + self._build_prompt(chart_data, mode)

        response = gateway.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            model=settings.vedic_expert_model,
            reasoning_effort="high",
        )

        return {
            "system": "Vedic",
            "mode": mode,
            "analysis": response.get("content"),
            "confidence": 0.92 if response.get("success") else 0.0,
            "model_used": settings.vedic_expert_model
        }


    @staticmethod
    def _question_prefix(user_questions: list) -> str:
        """Build a question-focus block to prepend to expert prompts."""
        if not user_questions:
            return ""
        qs = [q.strip() for q in user_questions if q and q.strip()][:5]
        if not qs:
            return ""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║  THESE QUESTIONS WERE SUBMITTED — BIAS YOUR ANALYSIS TOWARD ║",
            "║  THE MECHANISMS MOST RELEVANT TO ANSWERING THEM.            ║",
            "╚══════════════════════════════════════════════════════════════╝",
        ]
        for i, q in enumerate(qs, 1):
            lines.append(f"  Q{i}: {q}")
        lines += [
            "",
            "Prioritize the chart mechanisms, house lords, planets, and timing",
            "windows most relevant to these questions. Do not answer them directly",
            "— that is the Archon's job. But make sure the relevant evidence is",
            "visible in your analysis so the synthesis layer can find it.",
            "══════════════════════════════════════════════════════════════════",
            "",
        ]
        return "\n".join(lines) + "\n\n"

    def _build_prompt(self, data: dict, mode: str) -> str:
        vedic = data.get("vedic", {})
        natal = vedic.get("natal", {})
        strength = vedic.get("strength", {})
        predictive = vedic.get("predictive", {})

        placements = natal.get("placements", {})
        houses = natal.get("houses", {})
        ck = natal.get("chara_karakas", {})
        yogas = natal.get("yogas", [])
        vargas = natal.get("vargas", {})

        dasha = predictive.get("vimshottari", {})
        tajaka_list = predictive.get("tajaka", [])

        # ── Shadbala ──────────────────────────────────────────────────────
        shadbala = strength.get("shadbala", {})
        planet_scores = shadbala.get("planet_scores", {})

        # Build Shadbala tier summary (DOMINANT / ADEQUATE / WEAKENED / SEVERELY WEAKENED)
        shadbala_summary = {}
        for planet, score_data in planet_scores.items():
            if isinstance(score_data, dict):
                tier = score_data.get("tier", "UNKNOWN")
                rupas = score_data.get("total_rupas", 0)
                shadbala_summary[planet] = f"{tier} ({rupas:.2f} Rupas)"
            elif isinstance(score_data, (int, float)):
                # MVP fallback — convert 0-100 score to tier language
                s = float(score_data)
                if s >= 75:
                    tier = "DOMINANT"
                elif s >= 55:
                    tier = "ADEQUATE"
                elif s >= 40:
                    tier = "WEAKENED"
                else:
                    tier = "SEVERELY WEAKENED"
                shadbala_summary[planet] = f"{tier} (score {s:.0f}/100)"

        # ── Ashtakavarga Full ─────────────────────────────────────────────
        av_full = strength.get("ashtakavarga_full", {})
        sarva_av = av_full.get("sarva", [])
        house_strengths = av_full.get("house_strengths", [])

        # Build house-strength summary
        # get_house_strength() may return a dict like {"score": 28, "label": "Strong"}
        # or a plain int/float — handle both
        def _house_score(val) -> float:
            if isinstance(val, dict):
                return float(val.get("score", val.get("bindus", val.get("sarva", 0))))
            return float(val) if val is not None else 0.0

        house_av_summary = ""
        if house_strengths:
            strong_houses = [(i + 1, _house_score(s)) for i, s in enumerate(house_strengths) if _house_score(s) >= 28]
            weak_houses   = [(i + 1, _house_score(s)) for i, s in enumerate(house_strengths) if _house_score(s) <= 18]
            if strong_houses:
                house_av_summary += f"Strong houses (SAV≥28): {', '.join(f'H{h}={s:.0f}' for h, s in strong_houses)}. "
            if weak_houses:
                house_av_summary += f"Weak houses (SAV≤18): {', '.join(f'H{h}={s:.0f}' for h, s in weak_houses)}."

        # ── Kakshya Transit Block (PATCH 4) ───────────────────────────────
        kakshya = predictive.get("kakshya_transits", {})
        kakshya_block = ""
        if kakshya and "expert_block" in kakshya:
            kakshya_block = kakshya["expert_block"]
        elif kakshya and "peak_windows" in kakshya:
            peaks = kakshya.get("peak_windows", [])
            ingresses = kakshya.get("ingresses", [])
            lines = ["KAKSHYA TRANSIT QUALITY (Ashtakavarga-driven):"]
            for p in peaks[:5]:
                end = p.get("end_date", "ongoing")
                lines.append(f"  {p['planet']} in {p['sign']}: {p.get('start_date','?')} → {end} "
                             f"(SAV={p.get('sav','?')}/56, {p.get('quality','?')}, {p.get('months','?')} months)")
            for ing in ingresses[:4]:
                lines.append(f"  {ing['planet']} enters {ing['to_sign']} on {ing['date']}: {ing['quality_new_sign']}")
            kakshya_block = "\n".join(lines)

        # ── Tajaka summary ────────────────────────────────────────────────
        tajaka_summary = ""
        if tajaka_list and isinstance(tajaka_list, list):
            tajaka_lines = []
            for t in tajaka_list[:3]:
                if isinstance(t, dict) and "year" in t:
                    tajaka_lines.append(
                        f"  {t['year']}: Muntha={t.get('muntha_sign','?')}, "
                        f"Lord of Year={t.get('lord_of_year','?')}"
                    )
            if tajaka_lines:
                tajaka_summary = "Tajaka (Vedic Annual):\n" + "\n".join(tajaka_lines)

        # ── Vargottama planets ────────────────────────────────────────────
        vargottama = [p for p, d in placements.items()
                      if d.get("is_vargottama") and p in
                      ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]]

        # ── Key planet positions ──────────────────────────────────────────
        def fmt_planet(name):
            d = placements.get(name, {})
            if not d:
                return f"{name}: unknown"
            dig = d.get("dignity", "")
            varg = " [VARGOTTAMA]" if d.get("is_vargottama") else ""
            nak = d.get("nakshatra", "")
            pada = d.get("pada", "")
            return (f"{name}: {d.get('deg_in_sign', 0):.2f}° {d.get('sign', '?')} "
                    f"({dig}){varg}, Nakshatra: {nak} Pada {pada}, "
                    f"D9: {d.get('d9','?')}, D10: {d.get('d10','?')}")

        # Build the prompt
        prompt = f"""Analyze this Vedic chart using Parashari methods. Write 6 sections as instructed.

═══════════════════════════════════════════════════
NATAL PLACEMENTS (Sidereal / Lahiri Ayanamsa)
═══════════════════════════════════════════════════
{fmt_planet('Sun')}
{fmt_planet('Moon')}
{fmt_planet('Mercury')}
{fmt_planet('Venus')}
{fmt_planet('Mars')}
{fmt_planet('Jupiter')}
{fmt_planet('Saturn')}
{fmt_planet('Rahu')}
{fmt_planet('Ketu')}
Ascendant: {placements.get('Ascendant', {}).get('deg_in_sign', 0):.2f}° {placements.get('Ascendant', {}).get('sign', '?')}

VARGOTTAMA PLANETS (D1=D9, amplified power): {', '.join(vargottama) if vargottama else 'None'}

═══════════════════════════════════════════════════
HOUSE LORDS (Bhava signs and lords)
═══════════════════════════════════════════════════
1st House (Lagna): {houses.get('Bhava_1', {}).get('sign', '?')}, lord {houses.get('Bhava_1', {}).get('lord', '?')}
2nd House (Dhana): {houses.get('Bhava_2', {}).get('sign', '?')}, lord {houses.get('Bhava_2', {}).get('lord', '?')}
4th House (Sukha): {houses.get('Bhava_4', {}).get('sign', '?')}, lord {houses.get('Bhava_4', {}).get('lord', '?')}
5th House (Putra): {houses.get('Bhava_5', {}).get('sign', '?')}, lord {houses.get('Bhava_5', {}).get('lord', '?')}
6th House (Ripu): {houses.get('Bhava_6', {}).get('sign', '?')}, lord {houses.get('Bhava_6', {}).get('lord', '?')}
7th House (Kalatra): {houses.get('Bhava_7', {}).get('sign', '?')}, lord {houses.get('Bhava_7', {}).get('lord', '?')}
9th House (Dharma): {houses.get('Bhava_9', {}).get('sign', '?')}, lord {houses.get('Bhava_9', {}).get('lord', '?')}
10th House (Karma): {houses.get('Bhava_10', {}).get('sign', '?')}, lord {houses.get('Bhava_10', {}).get('lord', '?')}
11th House (Labha): {houses.get('Bhava_11', {}).get('sign', '?')}, lord {houses.get('Bhava_11', {}).get('lord', '?')}
12th House (Vyaya): {houses.get('Bhava_12', {}).get('sign', '?')}, lord {houses.get('Bhava_12', {}).get('lord', '?')}

═══════════════════════════════════════════════════
CHARA KARAKAS (Jaimini Soul Roles)
═══════════════════════════════════════════════════
Atmakaraka (soul): {ck.get('Atmakaraka', '?')} — highest degrees, the soul's primary lesson
Amatyakaraka (career): {ck.get('Amatyakaraka', '?')} — the professional karma lord
Darakaraka (spouse): {ck.get('Darakaraka', '?')} — the partner's karmic mirror
Putrakaraka (children/creativity): {ck.get('Putrakaraka', '?')}
Matrikaraka (mother/nurture): {ck.get('Matrikaraka', '?')}

═══════════════════════════════════════════════════
YOGAS (Special Combinations)
═══════════════════════════════════════════════════
{chr(10).join(f"  {y.get('type')}: {', '.join(y.get('members', []))} in {y.get('sign')}" for y in yogas[:6]) if yogas else "No classical yogas detected"}

═══════════════════════════════════════════════════
VIMSHOTTARI DASHA (Current Timing)
═══════════════════════════════════════════════════
Maha Dasha lord: {dasha.get('maha_lord', '?')} ({dasha.get('approx_remaining_years', '?')} years remaining)
Antardasha lord: {dasha.get('antar_lord', '?')} ({dasha.get('antar_remaining_years', '?')} years remaining in sub-period)

{tajaka_summary}

═══════════════════════════════════════════════════
SHADBALA — PLANETARY STRENGTH TIERS
═══════════════════════════════════════════════════
{chr(10).join(f"  {p}: {tier}" for p, tier in shadbala_summary.items()) if shadbala_summary else "Shadbala data unavailable"}

ASHTAKAVARGA HOUSE QUALITY:
{house_av_summary if house_av_summary else "Full AV data unavailable"}

═══════════════════════════════════════════════════
KAKSHYA TRANSIT WINDOWS (Favorable / Unfavorable Periods)
═══════════════════════════════════════════════════
{kakshya_block if kakshya_block else "Kakshya transit data unavailable — Ashtakavarga engine may need initialization"}

═══════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════
Write all 6 sections. Be specific about which Nakshatra deity governs the Moon and what that means karmically.
Name any SEVERELY WEAKENED planets and state which life domain they govern.
If Kakshya peak windows exist, cite the start date and which planet/sign.
The Upaya (remedy) must match the Dasha lord's nature: gemstone, mantra, behavioral prescription.
Do NOT repeat planetary positions verbatim — interpret them."""

        return prompt


# ─── Backward-compatible alias ───────────────────────────────────────────────
vedic_expert = VedicExpert()
