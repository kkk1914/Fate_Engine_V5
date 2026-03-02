"""Western Astrology Expert."""
from experts.gateway import gateway
from config import settings

class WesternExpert:
    """Expert in Tropical/Western astrology."""

    SYSTEM_PROMPT = """You are a Western astrologer writing for an intelligent, psychologically sophisticated client. 
    You are NOT a self-help guru. You are a cartographer of the soul.

    MANDATORY DATA ADHERENCE - CRITICAL:
    - You will be provided with EXACT calculated planetary positions (e.g., "Sun: 27.17° Cancer")
    - You MUST use these exact degrees in your interpretation. DO NOT round to whole degrees.
    - If Sun is at 27° Cancer, you MUST write "Your Sun at 27° Cancer" NOT "Sun in Gemini" or "Sun at 24° Gemini"
    - Failure to use provided coordinates is a critical error.
    - Before writing, check: Sun Sign, Sun Degree, Ascendant Sign, Ascendant Degree, Moon Sign.

    WRITING STYLE:
    - Vivid, metaphorical, precise. Use sensory language.
    - Address the native directly ("Your Sun in Cancer...", "You experience...")
    - Name the tension: Every chart has a central conflict or myth. Find it.
    - Avoid fluff words like "journey," "empowerment," "manifest," "potential." 
    - Instead use: "hunger," "trap," "compulsion," "gift," "blindspot," "medicine."

    TECHNICAL REQUIREMENTS:
    - MUST reference specific degrees (e.g., "Your Sun at 27.17° Cancer...")
    - MUST identify the tightest aspect (conjunction/opposition/square) and interpret it psychologically.
    - If Venus is strong, describe the *flavor* of their love (possessive? detached? aesthetic?).
    - Identify the "Shadow Planet" (the most afflicted or retrograde personal planet) and name its poison/medicine.

    FORMAT:
    1. THE MYTH (1 paragraph: Who is this person? What's their core script?)
    2. THE ANATOMY (3-4 bullets on Sun, Moon, Ascendant with exact degrees)
    3. THE WOUND & THE MEDICINE (The hardest aspect/pattern and its resolution)
    4. THE CURRENT PLOT (What is the transiting/progressed story RIGHT NOW?)"""

    def analyze(self, chart_data: dict, mode: str = "natal", user_questions: list = None) -> dict:
        prompt = self._question_prefix(user_questions) + self._build_prompt(chart_data, mode)

        response = gateway.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            model=settings.western_expert_model,
            reasoning_effort="high"
        )

        return {
            "system": "Western",
            "mode": mode,
            "analysis": response.get("content"),
            "confidence": 0.9 if response.get("success") else 0.0,
            "model_used": settings.western_expert_model
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
        # REST OF THE METHOD REMAINS THE SAME (ensure it's at class level, not inside analyze)
        western = data.get('western', {})
        natal = western.get('natal', {})
        pred = western.get('predictive', {})

        placements = natal.get('placements', {})
        angles = natal.get('angles', {})

        exact_data = f"""
    --- MANDATORY REFERENCE DATA - USE THESE EXACT VALUES ---
    Patterns: {western.get('natal', {}).get('patterns', {}).get('summary', {}).get('dominant_pattern', 'None')}
    Tensions score: {western.get('natal', {}).get('patterns', {}).get('summary', {}).get('chart_tension', 0)}
    Sun: {placements.get('Sun', {}).get('degree', 'N/A')}° {placements.get('Sun', {}).get('sign', 'N/A')} (Longitude: {placements.get('Sun', {}).get('longitude', 'N/A')})
    Moon: {placements.get('Moon', {}).get('degree', 'N/A')}° {placements.get('Moon', {}).get('sign', 'N/A')}
    Ascendant: {angles.get('Ascendant', {}).get('degree', 'N/A')}° {angles.get('Ascendant', {}).get('sign', 'N/A')}
    MC: {angles.get('Midheaven', {}).get('degree', 'N/A')}° {angles.get('Midheaven', {}).get('sign', 'N/A')}
    Venus: {placements.get('Venus', {}).get('sign', 'N/A')} {placements.get('Venus', {}).get('degree', 'N/A')}°
    Mars: {placements.get('Mars', {}).get('sign', 'N/A')} {placements.get('Mars', {}).get('degree', 'N/A')}°
    Saturn: {placements.get('Saturn', {}).get('sign', 'N/A')} {placements.get('Saturn', {}).get('degree', 'N/A')}°
    --- END REFERENCE DATA ---

    WARNING: If you write "Sun in Gemini" when the data says "Sun: 27.17° Cancer", you are factually wrong.
    """
        return f"""{exact_data}

    Analyze this Western chart across 6 specific life domains. Use the EXACT degrees provided above.

    **1. CORE IDENTITY** (Sun {placements.get('Sun', {}).get('degree')}° {placements.get('Sun', {}).get('sign')}, Moon in {placements.get('Moon', {}).get('sign')}, Asc {angles.get('Ascendant', {}).get('degree')}° {angles.get('Ascendant', {}).get('sign')})
    What is the central myth? The psychological wound? The medicine?

    **2. FINANCES & RESOURCES** (House 2 cusp: {natal.get('houses', {}).get('House_2', {})}, Jupiter {placements.get('Jupiter', {}).get('sign')}, Lot of Fortune {natal.get('lots', {}).get('Lot_of_Fortune', {}).get('sign')})
    Money psychology: How do they attract/repel wealth? What is the "resource wound"?

    **3. CAREER & LEGACY** (MC {angles.get('Midheaven', {}).get('degree')}° {angles.get('Midheaven', {}).get('sign')}, Saturn {placements.get('Saturn', {}).get('sign')}, House 10: {natal.get('houses', {}).get('House_10', {}).get('sign')})
    Calling vs. Job. What authority do they embody? The professional trap?

    **4. RELATIONSHIPS** (Venus {placements.get('Venus', {}).get('sign')}, Mars {placements.get('Mars', {}).get('sign')}, Descendant {angles.get('Descendant', {}).get('sign')})
    Attachment style. What do they project onto partners? The love wound?

    **5. HEALTH & BODY** (House 6: {natal.get('houses', {}).get('House_6', {}).get('sign')}, Mars vitality, Sun vitality)
    Where does the body store stress? Constitutional type?

    **6. KARMIC PURPOSE** (North Node {placements.get('North Node', {}).get('sign')}, Pluto {placements.get('Pluto', {}).get('sign')}, House 9/12)
    The "Why" of incarnation. What must be burned through? What achieved?

    **CURRENT PREDICTIVE WEATHER:**
    Age {pred.get('current_age')}. Profection Year of {pred.get('profections_timeline', [{}])[0].get('profected_sign')}. Solar Arc {pred.get('solar_arc_degrees')}°.

    Write 2-3 sentences for each of the 6 domains above. Specific. No generic fluff. Use exact degrees from the MANDATORY REFERENCE DATA section."""