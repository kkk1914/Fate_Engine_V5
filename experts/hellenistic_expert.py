"""Hellenistic Expert."""
from experts.gateway import gateway
from config import settings

class HellenisticExpert:
    """Expert in Ancient/Hellenistic astrology."""

    SYSTEM_PROMPT = """You are a Hellenistic astrologer (Valens/Dorotheus tradition).
    You speak of Fate (Heimarmene) and Fortune (Tyche) as real forces.
    You are deterministic but not depressing—you reveal the script so the actor can play it well.
    
    WRITING STYLE:
    - Ancient, stark, philosophical. "The Lot of Fortune falls in..."
    - Use technical terms: Sect (Day/Night), Profection, Loosing of the Bond, Chronokrator.
    - Focus on: What is inevitable vs. what is negotiable?
    - The Lot of Fortune = What happens TO them. The Lot of Spirit = What they DO about it.
    
    TECHNICAL REQUIREMENTS:
    - MUST state Day/Night sect and how it changes Saturn/Mars interpretation.
    - MUST identify the current Profection year (Time Lord).
    - MUST locate the Hyleg (giver of life) and Alcocoden (if visible).
    - Mention any "Loosing of the Bond" periods in Zodiacal Releasing.
    
    FORMAT:
    1. THE SECT (Day vs Night chart - how planets behave)
    2. THE LOTS (Fortune vs Spirit - Circumstance vs Agency)
    3. THE TIME LORD (Current Profection year ruler and its testimony)
    4. THE FATED PERIODS (Critical years/climacterics ahead)"""

    def analyze(self, chart_data: dict, mode: str = "natal", user_questions: list = None) -> dict:
        prompt = self._question_prefix(user_questions) + self._build_prompt(chart_data, mode)

        response = gateway.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            model=settings.hellenistic_expert_model,
            reasoning_effort="high"
        )

        return {
            "system": "Hellenistic",
            "mode": mode,
            "analysis": response.get("content"),
            "confidence": 0.85 if response.get("success") else 0.0,
            "model_used": settings.hellenistic_expert_model
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
        hell = data.get('hellenistic', {})
        lots = hell.get('lots', {})
        prof = hell.get('annual_profections', {})

        return f"""Analyze this Hellenistic chart (Whole Sign) across 6 domains fatefully.

**1. IDENTITY** (Sect: {'Day' if lots.get('fortune', {}).get('is_day_chart') else 'Night'}, Predominator {hell.get('predominator')}, Hyleg {hell.get('hyleg')})
The "Owner" of the chart. Vital force.

**2. FINANCES** (Lot of Fortune {lots.get('fortune', {}).get('sign')}, its ruler, 2nd/11th Whole Sign places)
Tyche (Chance). Material flow. What is given?

**3. CAREER** (Lot of Spirit {lots.get('spirit', {}).get('sign')}, 10th Place, MC {hell.get('mc', 'N/A')})
Agency. The intentional career. What is chosen?

**4. RELATIONSHIPS** (7th Place, Descendant ruler, Venus sect)
The Other. Contracts and open enemies.

**5. HEALTH** (6th Place, Mars condition, Ascendant ruler vitality)
Slavery/Service. The body in toil.

**6. FATE** (Nodal axis, 4th/8th/12th places, Peak/Crisis periods in ZR)
Ananke (Necessity). The unmovable.

**CHRONOCRATOR:** Currently Profected to {prof.get('profected_sign')} (House {prof.get('activated_house')}). Time Lord is {prof.get('time_lord')}.
Which domain is the "Lord of the Year" currently managing?

**PRE-NATAL SYZYGY:** {data.get('western', {}).get('natal', {}).get('syzygy', {}).get('type', 'Unknown')} in {data.get('western', {}).get('natal', {}).get('syzygy', {}).get('sign', 'Unknown')} — the ancestral lunar imprint.

Stoic reading. What is inevitable vs. negotiable in each domain?"""