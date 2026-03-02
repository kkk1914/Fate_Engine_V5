"""Saju (Bazi) Expert."""
from experts.gateway import gateway
from config import settings

class SajuExpert:
    """Expert in Chinese Four Pillars."""

    SYSTEM_PROMPT = """You are a Bazi master. You read Qi (energy) like a weather pattern.
    You are strategic, tactical, and elemental. You care about power, timing, and resource management.
    
    WRITING STYLE:
    - Concrete, strategic, slightly martial. "The terrain favors X," "Your Qi is depleted in Y."
    - Use the 10 Gods (Wealth, Power, Resource, etc.) as literal forces in their life.
    - Speak of the Day Master as a character in a landscape.
    - Avoid mysticism; focus on "the mechanics of luck."
    
    TECHNICAL REQUIREMENTS:
    - MUST state Day Master strength (Strong/Weak) and what that means practically.
    - MUST identify the Useful God (Yong Shen) and how to activate it.
    - Point out specific clashes (Chong) or combinations (He) in the pillars.
    - Analyze the current Da Yun (Luck Pillar) as a 10-year weather pattern.
    
    FORMAT:
    1. THE TERRAIN (Day Master strength and the 4 Pillars as landscape)
    2. THE USEFUL GOD (What element is their lifeline? How to use it?)
    3. THE CURRENT LUCK PILLAR (What is the decade's strategy?)
    4. TACTICAL ADVICE (Specific actions: colors, directions, industries, months to watch)"""

    def analyze(self, chart_data: dict, mode: str = "natal", user_questions: list = None) -> dict:
        prompt = self._question_prefix(user_questions) + self._build_prompt(chart_data, mode)

        response = gateway.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            model=settings.saju_expert_model,
            reasoning_effort="high"
        )

        return {
            "system": "Saju",
            "mode": mode,
            "analysis": response.get("content"),
            "confidence": 0.88 if response.get("success") else 0.0,
            "model_used": settings.saju_expert_model
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
        saju = data.get('bazi', {})
        natal = saju.get('natal', {})
        strength = saju.get('strength', {})
        pred = saju.get('predictive', {})

        pillars = natal.get('pillars', {})

        return f"""Analyze this Bazi chart across 6 domains strategically.

**1. IDENTITY** (Day Master {strength.get('day_master', {}).get('stem')} {strength.get('day_master', {}).get('element')}, Strength: {strength.get('tier')})
The "General" in the terrain. Core resilience or fragility.

**2. FINANCES** (Wealth elements in stems: Year={pillars.get('Year', {}).get('stem_10_god')}, Month={pillars.get('Month', {}).get('stem_10_god')}, Day={pillars.get('Day', {}).get('stem_10_god')})
Direct vs. Indirect Wealth. Resource management style.

**3. CAREER** (Power/Officer elements, Month Pillar {pillars.get('Month', {}).get('stem')}{pillars.get('Month', {}).get('branch')} - the "Career Engine")
Authority relationship. Rise/fall patterns.

**4. RELATIONSHIPS** (Day Pillar {pillars.get('Day', {}).get('stem')}{pillars.get('Day', {}).get('branch')} - Self/Spouse, Peach Blossom {natal.get('shensha', [])})
Spouse palace. Attraction patterns.

**5. HEALTH** (Day Master vs. Month Branch {pillars.get('Month', {}).get('branch')}, Qi phases: { {k: v.get('qi_phase') for k, v in pillars.items()} })
Elemental imbalance. Critical organs/systems.

**6. DESTINY** (Year Pillar {pillars.get('Year', {}).get('stem')}{pillars.get('Year', {}).get('branch')} - Ancestors, Hour Pillar {pillars.get('Hour', {}).get('stem')}{pillars.get('Hour', {}).get('branch')} - Legacy)
Ancestral karma. Late life outcome.

**LUCK CYCLE:** Current Da Yun {pred.get('da_yun', {}).get('pillars', [{}])[0]}. How does this 10-year pillar affect domains 2 and 3 above?

Tactical analysis for each domain. What is the terrain? Where is the ambush?"""