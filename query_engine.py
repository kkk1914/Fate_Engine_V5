"""
Query Engine — extracts themes from user questions and produces
steering instructions that reshape every section of the report.

Flow:
  1. User submits up to 5 questions before generation
  2. QueryEngine scans for themes (wealth, career, relationship, health, timing, identity)
  3. Returns a QueryContext dict with:
     - questions (cleaned list)
     - themes (detected)
     - per-section steering blocks (injected into every prompt)
     - part_iv_instructions (for the direct Q&A section)

No API call needed — keyword-based theme detection is instant and cheap.
The steering blocks are plain English instructions appended to each section's
focus field, so the LLM naturally prioritizes the user's topics throughout.
"""

from typing import List, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Theme definitions
# ─────────────────────────────────────────────────────────────────────────────

THEMES = {
    "wealth": {
        "keywords": [
            "wealthy", "wealth", "rich", "money", "millionaire", "financial",
            "income", "invest", "asset", "savings", "afford", "earn", "profit",
            "business", "startup", "entrepreneur", "fund", "capital", "net worth",
        ],
        "label": "Wealth & Financial Success",
        "color": "💰",
    },
    "career": {
        "keywords": [
            "career", "job", "work", "quit", "resign", "promotion", "boss",
            "company", "office", "profession", "vocation", "calling", "purpose",
            "start a business", "entrepreneur", "freelance", "salary", "hired",
            "fired", "industry", "role", "position", "leadership",
        ],
        "label": "Career & Professional Path",
        "color": "🏛️",
    },
    "relationship": {
        "keywords": [
            "marry", "marriage", "partner", "love", "relationship", "soulmate",
            "divorce", "dating", "meet", "girlfriend", "boyfriend", "wife",
            "husband", "romantic", "single", "commitment", "family", "children",
            "kids", "pregnant", "baby",
        ],
        "label": "Relationships & Love",
        "color": "❤️",
    },
    "health": {
        "keywords": [
            "health", "sick", "illness", "disease", "body", "medical", "doctor",
            "recovery", "mental health", "anxiety", "depression", "wellbeing",
            "energy", "vitality", "fitness", "longevity",
        ],
        "label": "Health & Vitality",
        "color": "🌿",
    },
    "timing": {
        "keywords": [
            "when", "which year", "how soon", "how long", "how many years",
            "timeline", "timing", "next year", "this year", "decade",
            "before", "after", "age",
        ],
        "label": "Timing & Key Dates",
        "color": "⏱️",
    },
    "identity": {
        "keywords": [
            "who am i", "purpose", "meaning", "destiny", "soul", "path",
            "life purpose", "why am i", "talent", "gift", "potential",
            "authentic", "true self", "calling", "mission",
        ],
        "label": "Identity & Life Purpose",
        "color": "🔮",
    },
    "relocation": {
        "keywords": [
            "move", "relocate", "country", "city", "abroad", "emigrate",
            "travel", "where should i live", "location", "foreign",
        ],
        "label": "Relocation & Geography",
        "color": "🌍",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Section → theme relevance map
# Controls which sections get amplified for which themes.
# ─────────────────────────────────────────────────────────────────────────────

SECTION_THEME_AMPLIFICATION: Dict[str, Dict[str, str]] = {

    "oracle_opening": {
        "wealth":       "The user asked specifically about wealth. If this chart has strong wealth indicators, name the pattern in the Oracle — make the financial architecture visible in the cold read.",
        "career":       "The user asked about their career path. The Oracle should surface the professional identity pattern — what kind of work this person is built for and what keeps holding them back.",
        "relationship": "The user asked about love and partnership. Surface the relational pattern that most defines how this person finds and loses connection.",
        "health":       "The user asked about health. Surface the body-mind connection in the Oracle — the physical pattern that reflects the emotional architecture.",
        "identity":     "The user is asking who they fundamentally are. Make the core paradox of this chart particularly vivid — this is the central question of their life.",
        "timing":       "The user is asking about timing. The Oracle should acknowledge that the timing of their life is structured, not random.",
        "relocation":   "The user asked about relocation. Surface any geographical restlessness or need for environmental change in the Oracle.",
    },

    "architecture_of_self": {
        "wealth":       "PRIORITY: The wealth-generating mechanisms of this chart must be named explicitly. What does this chart's architecture produce in terms of financial capacity? Which mechanism is the primary driver of income?",
        "career":       "PRIORITY: Lead with the career mechanism. What is this chart structurally designed to do professionally? Name the specific professional archetype this chart produces.",
        "relationship": "Include a mechanism that names the core relational architecture — not just the wound but the design. What partnership structure does this chart actually need to function?",
        "health":       "Include a mechanism on the body-mind connection specific to this chart. What is the somatic signature of this person's stress pattern?",
        "identity":     "PRIORITY: The identity mechanisms are the central focus of this section. What is this person fundamentally made of? What is the design beneath the personality?",
        "timing":       "Note which mechanisms activate on a timeline — which parts of this architecture are already fully online vs which come online later in life.",
        "relocation":   "Include any Ascendant or Angular indicators of geographic themes — does this chart perform better in certain environments or cultures?",
    },

    "material_world": {
        "wealth":       "PRIORITY: This is the user's primary question. Go deeper than usual. Name the specific wealth ceiling, the specific sabotage pattern, and the specific conditions under which this chart crosses into upper-tier wealth. Be concrete: which decade? Which career structure?",
        "career":       "PRIORITY: The career design mechanism must dominate this section. Name the specific industry, role type, and organizational structure that matches this chart. Be industry-specific.",
        "relationship": "Note any 2nd-house or partnership-linked income patterns — how do relationships affect this person's financial trajectory?",
        "health":       "Note any health-related career implications — does this chart need physical working conditions, or is sedentary work a health risk?",
        "identity":     "Connect the legacy asset to identity — what is the body of work this life is designed to produce?",
        "timing":       "PRIORITY: Name the specific financial windows in the five-year period. When is the earning inflection point? When is the loss risk highest?",
        "relocation":   "Note any geographic career implications — does this chart benefit from working internationally or in a specific cultural context?",
    },

    "inner_world": {
        "wealth":       "Note the emotional relationship with money — is there a scarcity wound? A security pattern that drives financial behavior?",
        "career":       "Note the emotional relationship with work and recognition — what does career success feel like from the inside for this person?",
        "relationship": "PRIORITY: This is the user's primary question. Expand the relationship section. Name the specific partner type that works, the specific dynamic that consistently fails, and the window in the five-year period when relationship events are most likely.",
        "health":       "PRIORITY: Go deeper than usual on the constitutional section. Name the specific physical vulnerabilities, the specific stress-to-illness pathway, and the specific practices that counter it.",
        "identity":     "The emotional self is the true self for this chart. Which mechanism most defines how this person experiences their own inner life?",
        "timing":       "Note the emotional seasonality — are there periods when this chart's emotional resources are strongest vs most depleted?",
        "relocation":   "Note the 4th house and Moon patterns — what home environment does this person fundamentally need to feel emotionally regulated?",
    },

    "karmic_mandate": {
        "wealth":       "Connect the karmic mandate to the wealth question — is financial success a karmic goal, a karmic test, or both for this chart?",
        "career":       "Connect the North Node direction to the career question — what career path is karmically aligned vs which one is the South Node default that must be left behind?",
        "relationship": "Connect the nodal axis to the relationship question — what is the karmic pattern in love, and what does the North Node demand in terms of relational evolution?",
        "health":       "Note any karmic health themes — is there a body-related lesson built into this incarnation?",
        "identity":     "PRIORITY: The karmic mandate IS the identity question for this person. What is this life for? What is the soul curriculum in plain language?",
        "timing":       "Connect the Maha Dasha to the user's timeline question — which dasha delivers which life chapter, and when does the current one end?",
        "relocation":   "Note any karmic geographic themes — are there places this chart is cosmically drawn to or warned away from?",
    },

    "current_configuration": {
        "wealth":       "How is the current configuration affecting financial matters right now? What is the immediate wealth implication of the current transits?",
        "career":       "What does the current configuration mean for career decisions right now? Is this a time to move or consolidate?",
        "relationship": "What is the current configuration doing to relationships right now? Is there an active relational transit that makes this moment significant?",
        "health":       "What does the current configuration mean for health and vitality right now?",
        "identity":     "How is the current configuration reshaping the person's sense of self and direction right now?",
        "timing":       "What is the single most important timing signal right now — what is imminent?",
        "relocation":   "Is there any current transit activating relocation themes right now?",
    },

    "year_2026": {
        "wealth":       "PRIORITY: Open by naming the specific financial event of 2026. What is the income opportunity, and what is the loss risk? Give amounts or percentages if the chart supports it.",
        "career":       "PRIORITY: Open by naming the career-specific event of 2026. What job move, business launch, or professional restructure is most likely?",
        "relationship": "PRIORITY: Name the relationship-specific event of 2026. Is there a meeting window? A decision point in an existing partnership?",
        "health":       "Name the health-relevant windows of 2026. What body system needs attention and when?",
        "identity":     "What identity shift does 2026 initiate? What aspect of the self is being rebuilt?",
        "timing":       "Make the timing as precise as possible — which specific months are the most critical for the user's question?",
        "relocation":   "Is 2026 a relocation year? Name any geographic activation.",
    },

    "year_2027": {
        "wealth":       "PRIORITY: Name the financial-specific event of 2027. Income, loss, or structural change?",
        "career":       "PRIORITY: Name the career-specific event of 2027. Test, pivot, or consolidation?",
        "relationship": "PRIORITY: Name the relationship-specific event of 2027.",
        "health":       "Health-relevant windows of 2027.",
        "identity":     "Identity shift in 2027.",
        "timing":       "Most precise timing for the user's question in 2027.",
        "relocation":   "Any geographic activation in 2027.",
    },

    "year_2028": {
        "wealth":       "PRIORITY: Name the financial-specific event of 2028.",
        "career":       "PRIORITY: Name the career-specific event of 2028.",
        "relationship": "PRIORITY: Name the relationship-specific event of 2028.",
        "health":       "Health-relevant windows of 2028.",
        "identity":     "Identity shift in 2028.",
        "timing":       "Most precise timing for the user's question in 2028.",
        "relocation":   "Any geographic activation in 2028.",
    },

    "year_2029": {
        "wealth":       "PRIORITY: Name the financial-specific event of 2029.",
        "career":       "PRIORITY: Name the career-specific event of 2029.",
        "relationship": "PRIORITY: Name the relationship-specific event of 2029.",
        "health":       "Health-relevant windows of 2029.",
        "identity":     "Identity shift in 2029.",
        "timing":       "Most precise timing for the user's question in 2029.",
        "relocation":   "Any geographic activation in 2029.",
    },

    "year_2030": {
        "wealth":       "PRIORITY: Name the financial-specific event of 2030.",
        "career":       "PRIORITY: Name the career-specific event of 2030.",
        "relationship": "PRIORITY: Name the relationship-specific event of 2030.",
        "health":       "Health-relevant windows of 2030.",
        "identity":     "Identity shift in 2030.",
        "timing":       "Most precise timing for the user's question in 2030.",
        "relocation":   "Any geographic activation in 2030.",
    },

    "directive": {
        "wealth":       "The five-year orders must be financially concrete. Each year's order should name a specific financial action, not just a career move. Include the HARD RULE about sole asset control if the wealth trap supports it.",
        "career":       "Each year's order should name a specific career action in a specific industry. Not 'advance professionally' — 'launch the advisory practice' or 'leave the corporate role by Q2.'",
        "relationship": "Include at least one year's order that is relationship-specific — a decision deadline, a conversation to have, or an alliance to formalize.",
        "health":       "Include a health-specific order in the years where body stress peaks.",
        "identity":     "The Red Thread must directly answer the identity question — who is this person, in one sentence.",
        "timing":       "Each order must have a specific deadline month, not just a year.",
        "relocation":   "If relocation is supported by the chart, include it as one of the five-year orders.",
    },

    "warning": {
        "wealth":       "If the primary threat is financial, make the warning about the specific wealth-destruction mechanism this chart carries.",
        "career":       "If the primary threat is professional, make the warning about the career-specific trap.",
        "relationship": "If the primary threat is relational, make the warning about the specific relational pattern that causes the most damage.",
        "health":       "If the primary threat is health-related, make the warning about the somatic pattern and when it peaks.",
        "identity":     "If the primary threat is identity-related, make the warning about the core self-sabotage pattern.",
        "timing":       "Name the exact window of maximum risk — month and year.",
        "relocation":   "If geographic decisions are relevant to the warning, name them.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# QueryEngine
# ─────────────────────────────────────────────────────────────────────────────

class QueryEngine:
    """
    Extracts themes from user questions and builds per-section steering blocks.
    No API call — pure keyword matching + rule-based amplification.
    """

    def __init__(self):
        pass

    def process(self, questions: List[str]) -> Optional[Dict]:
        """
        Main entry point.

        Args:
            questions: Raw question strings from the user (up to 5).

        Returns:
            QueryContext dict, or None if no valid questions.
        """
        # Clean and cap
        cleaned = [q.strip() for q in (questions or []) if q and q.strip()][:5]
        if not cleaned:
            return None

        themes = self._detect_themes(cleaned)
        steering = self._build_steering_blocks(cleaned, themes)
        header_block = self._build_header_block(cleaned, themes)

        return {
            "questions":     cleaned,
            "themes":        themes,
            "steering":      steering,        # dict keyed by section id
            "header_block":  header_block,    # injected at top of every section prompt
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Theme detection
    # ─────────────────────────────────────────────────────────────────────────

    def _detect_themes(self, questions: List[str]) -> List[str]:
        """Return list of detected theme keys, ordered by relevance."""
        full_text = " ".join(questions).lower()
        scores: Dict[str, int] = {}

        for theme_key, theme_def in THEMES.items():
            hits = sum(1 for kw in theme_def["keywords"] if kw in full_text)
            if hits > 0:
                scores[theme_key] = hits

        # Sort by hit count descending
        return sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Steering block builder
    # ─────────────────────────────────────────────────────────────────────────

    def _build_steering_blocks(self,
                                questions: List[str],
                                themes: List[str]) -> Dict[str, str]:
        """
        Build a steering instruction string for each section.
        Sections that have no relevant theme get a minimal reminder only.
        """
        steering: Dict[str, str] = {}

        for section_id, theme_map in SECTION_THEME_AMPLIFICATION.items():
            section_instructions = []

            for theme in themes:
                if theme in theme_map:
                    section_instructions.append(theme_map[theme])

            if section_instructions:
                block = (
                    "\n=== QUERY STEERING — USER QUESTIONS SHAPE THIS SECTION ===\n"
                    "The user asked these specific questions before the report was generated.\n"
                    "This section must address these questions implicitly throughout — not by\n"
                    "breaking format, but by prioritizing the mechanisms most relevant to them.\n\n"
                    "Questions asked:\n"
                    + "\n".join(f"  Q{i+1}: {q}" for i, q in enumerate(questions))
                    + "\n\nThemes detected: "
                    + ", ".join(THEMES[t]["label"] for t in themes if t in THEMES)
                    + "\n\nSection-specific steering:\n"
                    + "\n".join(f"• {inst}" for inst in section_instructions)
                    + "\n=== END QUERY STEERING ==="
                )
            else:
                # Minimal reminder — keep the questions in view even for less-relevant sections
                block = (
                    "\n=== CONTEXT: USER QUESTIONS ===\n"
                    "The user asked: "
                    + " | ".join(questions)
                    + "\nKeep these in mind. Where relevant, connect your writing to these themes."
                    + "\n=== END CONTEXT ==="
                )

            steering[section_id] = block

        return steering

    # ─────────────────────────────────────────────────────────────────────────
    # Header block (injected at top of every section, brief)
    # ─────────────────────────────────────────────────────────────────────────

    def _build_header_block(self, questions: List[str], themes: List[str]) -> str:
        """
        A compact block injected at the very top of every section's data payload.
        Keeps the user's intent visible to the model throughout generation.
        """
        theme_labels = ", ".join(
            f"{THEMES[t]['color']} {THEMES[t]['label']}"
            for t in themes if t in THEMES
        ) or "General"

        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║  THIS REPORT WAS COMMISSIONED TO ANSWER SPECIFIC QUESTIONS  ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            "The user submitted these questions before generation:",
        ]
        for i, q in enumerate(questions):
            lines.append(f"  Q{i+1}: {q}")
        lines += [
            "",
            f"Primary themes detected: {theme_labels}",
            "",
            "Every section of this report must implicitly address these questions.",
            "Prioritize mechanisms, windows, and patterns most relevant to what was asked.",
            "The Q&A section at the end gives direct verdicts — do not give the verdict here,",
            "but make the relevant evidence visible throughout.",
            "══════════════════════════════════════════════════════════════════",
            "",
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function
# ─────────────────────────────────────────────────────────────────────────────

def build_query_context(questions: List[str]) -> Optional[Dict]:
    """Shortcut: QueryEngine().process(questions)"""
    return QueryEngine().process(questions)
