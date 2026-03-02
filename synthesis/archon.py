"""
Archon v2 — The Celestial Dossier
Master narrative architect for the 13-Section premium astrological report.

STRUCTURE:
  PART I:   THE NATIVITY     (5 sections — natal portrait)
  PART II:  THE ALMANAC      (6 sections — year-by-year chronological forecast)
  PART III: THE DIRECTIVE    (2 sections — mandate and warning)

UPGRADE FROM v1:
  v1: 10 chapters; predictive split by domain (finances/career/health × 3 years)
  v2: 13 sections; predictive chronological (all domains per year × 5 years)
      + Oracle Opening hook, Current Configuration bridge, merged natal chapters
"""

import logging
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from experts.gateway import gateway
from config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Section Definitions
# ─────────────────────────────────────────────────────────────────────────────

SECTION_DEFS = {

    # ── PART I: THE NATIVITY ─────────────────────────────────────────────────

    0: {
        "id": "oracle_opening",
        "part": "I",
        "title": "THE ORACLE'S OPENING",
        "header": "◈ THE ORACLE'S OPENING",
        "type": "oracle",
        "words": (200, 230),
        "focus": (
            "Cold read. 5-6 surgical observations. NO explanation, NO astrology, NO jargon. "
            "Each sentence names a behavior, compulsion, or wound that would make the reader say "
            "'how does it know that?' about their private self. "
            "NOT personality description — behavioral tells. The things they do in private. "
            "The patterns they haven't named yet. "
            "FINAL SENTENCE ONLY: the core paradox of this chart in plain language. "
            "Format: 'The trap is: [specific paradox that could only be this person].'"
        ),
        "domains": [],
    },

    1: {
        "id": "architecture_of_self",
        "part": "I",
        "title": "I. THE ARCHITECTURE OF SELF",
        "header": "I. THE ARCHITECTURE OF SELF",
        "type": "natal",
        "words": (420, 480),
        "focus": (
            "BLUEPRINT — not a portrait. Oracle already painted the human picture. "
            "This section explains the MECHANICS. "
            "Use 4-6 labeled mechanisms with bold headers. Each mechanism: "
            "[NAME] → placement evidence → behavior this produces → real-world life outcome. "
            "Every claim needs a consequence: 'X placement PRODUCES/CREATES/FORCES Y in real life.' "
            "MANDATORY: Include at least one mechanism named as a clear STRENGTH (e.g. **THE STRUCTURAL "
            "AUTHORITY**, **THE COMMUNICATION GIFT**) — not a gift-with-a-cost, a flat-out advantage. "
            "State what Saturn-as-dignified-Almuten actually BUILDS over a lifetime. "
            "Cover: core identity engine (Sun+Moon+Asc), the authority structure (Almuten/Saturn "
            "as the chart's most dignified planet = must be presented as the greatest long-term asset), "
            "the mind's specific pattern (Mercury), the soul curriculum (Atmakaraka). "
            "Include fixed star parans if present — named as fate signatures. "
            "Final sentence: the chart's single greatest structural advantage — what this person has "
            "that most people do not, written in plain language."
        ),
        "domains": ["Sun", "Moon", "Ascendant", "Atmakaraka", "Fixed Stars", "Almuten"],
    },

    2: {
        "id": "material_world",
        "part": "I",
        "title": "II. THE MATERIAL WORLD",
        "header": "II. THE MATERIAL WORLD",
        "type": "natal",
        "words": (420, 480),
        "focus": (
            "Use 4-5 labeled mechanisms with bold headers. Blueprint format, not essay. "
            "Each mechanism: [NAME] → placement → behavior it creates → real-world financial/career consequence. "
            "REQUIRED opening: The WEALTH CAPACITY SCORE BLOCK appears verbatim at the top, "
            "before any mechanism. It is provided in the section data — reproduce it exactly as shown. "
            "REQUIRED mechanisms (after the score block): "
            "(1) THE INCOME ENGINE — exactly how this chart generates money in plain English. "
            "Name the specific industries where this chart is competitive (from the FINANCIAL PROFILE). "
            "(2) THE CAREER DESIGN — what the chart is actually built for. "
            "State the specific career structure that will WORK, including the industry domain. "
            "(3) THE WEALTH TRAP — the one financial pattern that sabotages income, with the HARD RULE "
            "for avoiding it (e.g. 'never do X'). State it as a rule, not a warning. "
            "(4) THE LEGACY ASSET — what specifically gets built over decades. "
            "Make it concrete: what product, institution, or IP does this chart's design produce? "
            "BALANCE: For every trap, name the corresponding strength. "
            "INDUSTRY SPECIFICITY: Every mechanism that touches career or money must name at least one "
            "specific industry from the FINANCIAL PROFILE data."
        ),
        "domains": ["House 2", "MC", "Saturn", "Lot of Fortune", "Amatyakaraka", "Useful God"],
    },

    3: {
        "id": "inner_world",
        "part": "I",
        "title": "III. THE INNER WORLD",
        "header": "III. THE INNER WORLD",
        "type": "natal",
        "words": (420, 480),
        "focus": (
            "Use 4-5 labeled mechanisms with bold headers. Blueprint format. "
            "Each mechanism: [NAME] → placement → what it compels → real-world relationship or health outcome. "
            "REQUIRED mechanisms: "
            "(1) THE LOVE PATTERN — what Venus+Darakaraka is actually designed for (not just where it traps). "
            "Name the specific type of partner who would WORK for this chart, not only who fails. "
            "(2) THE RELATIONAL DESIGN — what the 7th house and Descendant are built to give and receive. "
            "What does genuine compatibility look like for this specific chart? "
            "(3) THE PHYSICAL CONSTITUTION — the 2-3 specific vulnerabilities, but ALSO the body's "
            "innate strengths (what this constitution handles well under stress). "
            "(4) THE HEALING MECHANISM — what specifically repairs this chart's emotional patterns. "
            "Not abstract 'medicine' — the concrete behavior or practice that converts the wound into skill. "
            "BALANCE: Do not name every section 'trap' or 'wound'. "
            "The inner world contains genuine capacity for love and connection — name it alongside the challenge."
        ),
        "domains": ["Venus", "Mars", "Moon", "Darakaraka", "House 6", "House 7", "Constitution"],
    },

    4: {
        "id": "karmic_mandate",
        "part": "I",
        "title": "IV. THE KARMIC MANDATE",
        "header": "IV. THE KARMIC MANDATE",
        "type": "natal",
        "words": (380, 440),
        "focus": (
            "The WHY of this incarnation. Elevated tone but still outcome-anchored. "
            "Name the karmic debt (South Node — the default pattern being overused and why it fails), "
            "the karmic payment required (North Node — the specific behavior and attitude change demanded), "
            "the Atmakaraka curriculum (what Mercury at highest degree means the soul is here to MASTER — "
            "frame this as a GIFT to develop, not only a burden to carry), "
            "the current dasha arc: CRITICAL — do not only describe what Ketu is stripping. "
            "State: (a) what Ketu is stripping and why, (b) WHAT THE VENUS DASHA THAT FOLLOWS WILL BUILD. "
            "The Ketu period is preparation. The reader must understand what they are being prepared FOR, "
            "not only what is being taken. Venus dasha for this chart means [concrete outcomes]. "
            "End with: the karmic DESTINATION — not just the debt, but what this life is building toward "
            "in its final form. State it as a positive fate, not only an obligation. "
            "CAUSAL LANGUAGE: 'The South Node costs X. The North Node builds Y. The Venus dasha delivers Z.' "
        ),
        "domains": ["Nodes", "Ketu", "Atmakaraka", "Lot of Spirit", "Syzygy", "Fixed Stars"],
    },

    # ── PART II: THE ALMANAC ─────────────────────────────────────────────────

    5: {
        "id": "current_configuration",
        "part": "II",
        "title": "◈ THE CURRENT CONFIGURATION",
        "header": "◈ THE CURRENT CONFIGURATION",
        "type": "current",
        "words": (130, 160),
        "focus": (
            "Where are we RIGHT NOW? A weather briefing, not a forecast. "
            "State: active Maha Dasha + Antardasha, current profection year + time lord, "
            "dominant outer transit in effect today. "
            "Three sentences max. Dense and precise. "
            "End with the single question this year is asking the native."
        ),
        "domains": ["Maha Dasha", "Profection", "Current Transits"],
    },

    6: {
        "id": "almanac_summary",
        "part": "II",
        "title": "◈ THE FIVE-YEAR WINDOW MAP",
        "header": "◈ THE FIVE-YEAR WINDOW MAP",
        "type": "almanac_summary",
        "words": (350, 420),
        "focus": (
            "A compact, reference-quality chronological map of ALL high-confidence windows "
            "across 2026–2030. NOT year-by-year essays — a single structured list of the "
            "10–14 most significant multi-system convergences, sorted chronologically. "
            "Format each entry EXACTLY as:\n"
            "**[DATE RANGE]** — [CERTAINTY LABEL] — [What this window delivers or tests, "
            "in one plain-English sentence naming the life domain: career / finance / "
            "relationship / home / health]\n"
            "Systems: [which systems agree] | Theme: [single word]\n"
            "---\n"
            "After the window list: one dense paragraph naming the single most important "
            "CHAIN across the 5-year arc — how the windows sequence together to build toward "
            "the life events the user asked about (career launch, house, family, wealth, "
            "passive income). Name the progression explicitly: Window A → enables → Window B → "
            "creates conditions for → Window C. This is the strategic skeleton."
        ),
        "domains": ["All storm windows 2026–2030", "Profections", "Primary Directions", "Outer Transits"],
    },

    # ── PART III: THE DIRECTIVE ───────────────────────────────────────────────

    7: {
        "id": "directive",
        "part": "III",
        "title": "◈ THE FIVE-YEAR DIRECTIVE",
        "header": "◈ THE FIVE-YEAR DIRECTIVE",
        "type": "directive",
        "words": (280, 340),
        "focus": (
            "Three elements, in this order:\n"
            "1. THE RED THREAD: One sentence only. Must name the specific Sun/Moon/Asc combination "
            "and the core paradox. Could ONLY be written about this exact chart. "
            "No vague spiritual language.\n"
            "2. THE FIVE-YEAR ORDERS: One concrete, dated, technical action per year 2026–2030. "
            "Reads like orders, not suggestions. Name the technique, the window, the practice.\n"
            "3. No padding. No encouragement. Only the mandate."
        ),
        "domains": ["Synthesis", "Red Thread", "Dated Actions"],
    },

    8: {
        "id": "warning",
        "part": "III",
        "title": "◈ THE WARNING",
        "header": "◈ THE WARNING",
        "type": "directive",
        "words": (180, 220),
        "focus": (
            "ONE configuration. The specific planetary setup that creates the greatest risk "
            "for this chart. Name: what the planets are, when it peaks (exact date window), "
            "what it destroys if ignored, what it builds if used correctly. "
            "No softening. No generic warnings. Only what is specific to this chart."
        ),
        "domains": ["Peak Risk", "Configuration", "Timing"],
    },

    # ── PART IV: YOUR QUESTIONS ───────────────────────────────────────────────
    # This is the primary deliverable when questions are submitted.
    # Each answer gets full natal + predictive + storm window data routed to it.
    9: {
        "id": "questions",
        "part": "IV",
        "title": "◈ YOUR QUESTIONS ANSWERED",
        "header": "◈ YOUR QUESTIONS ANSWERED",
        "type": "questions",
        "words": (350, 500),  # per question — expanded for depth
        "focus": (
            "Answer each question with precision and depth. Each answer must:\n"
            "1. State a direct verdict in the first sentence (yes/no/when/what form). No hedging.\n"
            "2. Name the 2-3 specific astrological mechanisms that determine this outcome "
            "   — technique name, exact evidence, and what it implies.\n"
            "3. Give the SPECIFIC timing windows that are most relevant to this question — "
            "   drawn from the TEMPORAL STORM WINDOWS data in the prompt. Cite exact date ranges.\n"
            "4. Distinguish between what is near-certain vs. what is probable. If 3+ systems "
            "   agree on a window, say so. If only 1 system flags it, say that too.\n"
            "5. End with a concrete, dated action the person should take.\n"
            "ALL DATES CITED MUST BE AFTER TODAY'S DATE (provided in the data block). "
            "If a window has already passed, do not cite it."
        ),
        "domains": ["User Questions", "All timing data", "Storm windows", "Natal mechanisms"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# System Prompts per section type
# ─────────────────────────────────────────────────────────────────────────────

ORACLE_PROMPT = """You are the Archon, opening a premium astrological dossier with a cold read.

Write THE ORACLE'S OPENING for this specific chart.

WHAT THIS SECTION IS: A cold read. Not an essay. Not an introduction. Five to six razor-sharp
observations that make the reader feel seen — the "how does it know that?" shock. No explanation,
no build-up, no astrology. Pure recognition. Like a stranger reading your mail.

ABSOLUTE RULES:
1. ZERO astrological jargon. Zero. No sign names, no house numbers, no technique names.
   Not even in passing. This section is written for someone who knows nothing about astrology.
2. Each sentence is a standalone observation about behavior, compulsion, or wound.
   Short. Precise. Surgical. No sentence longer than 30 words.
3. DO NOT EXPLAIN WHY. The Architecture of Self section explains the mechanics.
   Oracle only names what it sees. No "because your Mercury..." allowed.
4. Every observation must be specific enough that a stranger reading this would think
   it was written from personal knowledge. NOT "you struggle with emotions." YES:
   "You explain your feelings instead of feeling them — and you mistake the explanation for intimacy."
5. BANNED WORDS: journey, tapestry, dance, explore, cosmic, realm, energy, vibration, deeply, truly.
   USE INSTEAD: compulsion, trap, hunger, pattern, engine, wound, debt, demand, cost, pressure, precision,
   instinct, architecture, capacity, design, asset, blueprint.
6. BALANCE RULE: At least one of your 5-6 observations must name a genuine, specific strength —
   something this person does that most people cannot. Not a softening compliment.
   A precise observation of genuine capacity. Example: "You can hold the structure of an argument
   in your head longer than anyone in the room — and you know exactly when to deploy it."
7. LENGTH: 200-230 words. Short. Every word earns its place.
8. FINAL SENTENCE: The core paradox. One sentence. Could only be this exact person.
   Format: "The trap is: [plain English paradox that is unique to this chart]."
8. Start with: # ◈ THE ORACLE'S OPENING

EXAMPLE OF THE RIGHT TONE (for a different chart — do not copy, only match the precision):
"You are the most capable person in most rooms you enter, and you know it, and it exhausts you.
You rehearse conversations before they happen. You edit what you say in real time.
You have a version of yourself that is always performing, and you cannot remember when it started.
Intimacy frightens you not because you don't want it but because you don't know how to stop performing long enough to have it.
You protect people from your real opinions, then resent them for not knowing what those opinions are.
The trap is: you are brilliant at building connection and terrified of what happens if someone actually gets close enough to see you clearly.\""""

NATAL_PROMPT = """You are the Archon, master synthesizer of four astrological systems writing a premium astrological dossier.

WHAT THIS SECTION IS: A translation layer. Your reader already lived through this chart.
They don't need to learn astrology. They need to understand themselves.
Your job is to take the technical evidence and convert it into plain-English insight
and concrete practical guidance — the kind that makes someone say "this explains everything."

THE GOLDEN RATIO:
  20% astrological evidence (the proof — brief, specific, cited)
  50% what this means in plain English (no jargon — write as if explaining to a sharp friend)
  30% what to do with it (concrete, practical, specific advice)

MANDATORY FORMAT FOR EACH MECHANISM:

  **[NAME OF THE MECHANISM]**
  *Evidence:* [One sentence maximum. Planet, placement, aspect. That's it.]
  **What this means:** [2-4 sentences. Zero jargon. No planet names unless unavoidable.
  Write as if the reader has never heard of astrology. What is their actual experience of this?
  What does it feel like from the inside? What patterns does it produce in their daily life?
  Example: "Your mind is wired to stress-test every idea before you share it — which makes
  you an unusually rigorous thinker, but also someone who over-prepares for conversations
  that never happen and exhausts themselves defending positions no one attacked."]
  **What to do with it:** [1-2 sentences. A concrete, specific practice or decision.
  Example: "Set a 48-hour rule for important communications — draft, wait, then send.
  This converts your natural over-preparation into a competitive advantage rather than anxiety."]

MANDATORY BALANCE RULE:
  Out of 4-6 mechanisms, AT LEAST 2 must be named as genuine strengths.
  Not "gift with a cost" — flat-out advantages this chart has that most people don't.
  Name them: **THE STRUCTURAL AUTHORITY**, **THE COMMUNICATION GIFT**, etc.
  Challenge mechanisms must end with: what strength this pressure builds + when it converts to asset.

ADDITIONAL RULES:
1. USE EXACT DEGREES from the MANDATORY NATAL DATA block. In evidence line only. Never invent.
2. Synthesize ALL FOUR SYSTEMS in one voice — one mechanism can draw from multiple systems.
3. WHEN SYSTEMS CONFLICT, STATE IT plainly: "Eastern astrology reads this as X, Western as Y —
   the real experience is both at once." Then explain what that feels like practically.
4. BANNED IN MEANING/ADVICE SECTIONS: planet names, sign names, house numbers, degree citations,
   technique jargon, Latin terms, Sanskrit terms. The evidence line gets all the technical language.
   Everything after "What this means:" must be readable by someone with zero astrology knowledge.
5. LENGTH: 480-560 words total. Meaning + advice sections should be longer than evidence sections.
6. START with exactly: # {HEADER}
7. Bold key terms only in evidence line: **Atmakaraka**, **Amatyakaraka**, **Almuten**, **Hyleg**
8. When Bazi shows UNAVAILABLE: omit Saju claims entirely.
9. END with one sentence in completely plain language: the single biggest practical takeaway
   from this section — written so a stranger immediately understands the life consequence."""

YEAR_FORECAST_PROMPT = """You are the Archon, writing the predictive almanac section of a premium astrological dossier.

THE FUNDAMENTAL RULE:
People read predictive reports to know what will happen. State the events first.
Explain the astrology second. Never bury a prediction inside a technique explanation.

MANDATORY STRUCTURE:

**{YEAR}: [3–5 word title]**

**What is most likely to happen in {YEAR}:**
3-4 sentences in plain English. No technique names. No jargon.
State the probable events directly — what happens to this person in career, relationships, health, finances.
This is the HEADLINE. The reader must be able to read only this block and understand their year.

**The mechanics — how and when:**
List windows chronologically. For EACH window, state all three:
  "DATE RANGE: [what probably happens in plain English]
   Certainty: [NEAR-CERTAIN / HIGH-CONFIDENCE / MODERATE-CONFIDENCE / LOW-CONFIDENCE]
   — [X] systems agree: [Western], [Vedic], [Saju], [Hellenistic] (list only those that apply)
   Why: [technique attribution with exact date]
   Action: [specific, dated instruction]"

━━━ CRITICAL — CONVERGENCE SCORE PROTOCOL ━━━
The TEMPORAL STORM WINDOWS data includes a convergence_score and confidence_label.
YOU MUST name the certainty level for each window. This is the core upgrade.

LANGUAGE CALIBRATION BY CONFIDENCE LABEL:

NEAR-CERTAIN (score ≥ 0.85):
  "[Date range] is the highest-confidence window of {YEAR}. [X] independent systems
  converge here — [Western], [Vedic], [Saju], [Hellenistic]. This is not speculation;
  it is structural. The question is not whether [event] occurs, but how you are positioned
  when it does. Action by [specific date] is non-negotiable."

HIGH-CONFIDENCE (0.70–0.84):
  "Three systems point to [event] in [date range]. This is likely rather than possible —
  plan around it. The one system that dissents ([name it]) reads this as [divergence],
  which means [what the dissent implies]. Weight the majority; note the outlier."

MODERATE-CONFIDENCE (0.55–0.69):
  "Two systems agree on [date range]: [Western] reads it as X, [Vedic] reads it as Y.
  This window is probable but not certain — treat it as your working scenario
  while remaining open to variance of 2–4 weeks in timing."

LOW-CONFIDENCE (<0.55):
  "A single system flags [date range] as significant. Treat as possible, not probable.
  Act if it arrives; do not plan your year around it."

━━━ ADDITIONAL RULES ━━━
0. MANDATORY BALANCE — YEAR SUMMARY MUST NAME BOTH:
   "The highest-opportunity window of {YEAR}: [date range] — [what becomes available]"
   "The highest-pressure window of {YEAR}: [date range] — [what is tested]"
   These are two separate things. Most years contain both. Name both explicitly up front.
   A near-certain Jupiter transit is a near-certain OPPORTUNITY. Name it as such.
   Do not bury positive windows inside the mechanics — surface them in the headline block.
1. LEAD with the year's highest-confidence window — use it as the structural anchor.
   If it is a positive window (Jupiter, Venus, harmonious Primary Direction), name it as the
   year's primary opportunity, not as a secondary footnote after the challenges.
2. YEAR TITLE: Must reflect the year's dominant character honestly.
   If Jupiter dominates → title should reflect expansion/elevation, not just "pressure."
   If Saturn dominates AND Jupiter also present → name both tensions in the title.
   AVOID titles that only name the difficulty (e.g., "Isolation, Sabotage" when there are
   also Jupiter windows of opportunity in the same year).
3. DO NOT re-diagnose the natal chart. One-sentence anchors only where essential.
4. WHEN SYSTEMS DISAGREE within a window: name both readings, state which to weight and why.
5. END with: **The one action {YEAR} demands:** anchored to the highest-confidence window.
   If the highest-confidence window is an opportunity window, the action is to CLAIM it.
6. BANNED: potential, manifestation, journey, tapestry, energies, suggests (without stated consequence).
7. LENGTH: 580-640 words.
8. START with: # YEAR {YEAR}
9. Bold: **Primary Direction**, **Maha Dasha**, **Tajaka**, **Profection**, **Kakshya**

VOICE AND RATIO:
  20% technical (which systems, exact dates, technique names)
  40% what this means in plain English (what will actually happen in the person's life —
      career, money, relationships, health — stated directly without jargon)
  40% what to do (specific, dated, practical actions)

For the "what this means" part: write as if texting a smart friend who has never heard of astrology.
"This is your best window for a promotion or public move this year — Jupiter crossing your
life-force point is the closest thing astrology has to a green light. Don't waste it job-hunting
quietly; this is when being visible pays off."

NOT: "The Jupiter transit conjunct your natal Sun in Cancer activates the 10th house profection
creating synergistic career potential." That is technique. Tell them what to expect."""

CURRENT_CONFIG_PROMPT = """You are the Archon, writing a situation report for a premium astrological dossier.

Write THE CURRENT CONFIGURATION — exactly 3 short paragraphs, total 140-170 words.

WHAT THIS IS: A weather briefing. Not a forecast — a current conditions report.
Where is this person RIGHT NOW? What is ending? What is building?

STRUCTURE:
Paragraph 1: Active Maha Dasha + Antardasha. Name what it is DOING to the person's life —
  not just what it "represents." "The Ketu Maha Dasha is actively stripping away X.
  The Jupiter Antardasha, now in its final Y months, is the last window to Z before the shift."
Paragraph 2: Current annual profection. Name the activated house, what it has turned the
  spotlight onto this year, what the time lord is demanding.
Paragraph 3: The single most dominant outer transit in effect right now. Name it, name its
  exact date range, state what it is forcing.

FINAL SENTENCE: Not a question. A statement of the current moment's core demand:
  "The immediate pressure is [X], and the only viable response is [Y]."

RULES:
1. START with: # ◈ THE CURRENT CONFIGURATION
2. No jargon explanations. Assume reader has read sections 1-4.
3. All three paragraphs must name a REAL-WORLD EFFECT, not just an astrological condition."""

DIRECTIVE_PROMPT = """You are the Archon, closing a premium astrological dossier with the mandate.

ABSOLUTE RULES:
1. Section 1 — THE RED THREAD: Exactly one sentence. Must name the Sun/Moon/Asc combination.
   Must name the core paradox. Could ONLY be written about this exact chart. No vague spiritual language.
   Format: **Red Thread:** [sentence]

2. Section 2 — HARD FINANCIAL RULES (from CHART FINANCIAL PROFILE in section data):
   State 1-2 non-negotiable rules derived from the chart's wealth structure.
   Not advice — laws. Specific and verifiable.
   Format:
   > **HARD RULE:** [specific rule in plain English]
   Example: "Never enter a 50/50 partnership. Maintain 51%+ control of any business
   you build. Your chart's shared-resources zone creates structural financial loss when
   control is divided equally with a co-founder or investor."
   Use the RISK FLAG and eighth-house planets from the FINANCIAL PROFILE data.

3. Section 3 — THE FIVE-YEAR ORDERS: Five specific, business-level actions. One per year.
   These are not abstract astrology — they are concrete life moves in specific industries/domains.
   Format:
   **2026:** [What to do, in which domain, by when, to what measurable end]
   **2027:** [etc.]
   **2028:** [etc.]
   **2029:** [etc.]
   **2030:** [etc.]
   Use the PRIMARY WEALTH CHANNELS from the FINANCIAL PROFILE when assigning domains.

4. NO padding. NO encouragement. NO "remember that..." NO "trust yourself."
   Reads like a CEO's quarterly brief — ordered, specific, no sentiment.

5. LENGTH: 320-380 words.
6. START with: # ◈ THE FIVE-YEAR DIRECTIVE"""

WARNING_PROMPT = """You are the Archon, writing the final warning of a premium astrological dossier.

Write THE WARNING — 180-220 words.

RULES:
1. ONE configuration only. The specific planetary setup creating the greatest risk OR the greatest
   unrealized opportunity for this chart. (A warning can be: "you are positioned for X and will
   miss it if you do Y" — not only "danger ahead.")
2. State: which planets, which aspect, when it peaks (exact date window from TEMPORAL STORM WINDOWS).
3. State: what it costs or destroys if ignored.
4. State: what it builds or delivers if engaged correctly. THIS IS MANDATORY AND MUST BE SPECIFIC.
   Not "you will forge an indestructible identity" — name the concrete outcome:
   "You will have the professional credibility and earned authority that your Saturn Almuten was
   always designed to produce" or "The Venus dasha that follows will be your most materially
   abundant and relationally fulfilling period — this test is the admission price."
5. FINAL TWO SENTENCES must describe what success looks like on the other side.
   The reader must finish THE WARNING knowing what they are working toward, not only what they risk.
6. NO generic danger language. No "rubble." No "dismantled." Name the specific structure at risk.
7. START with: # ◈ THE WARNING
8. LENGTH: 180-220 words. No more."""

ALMANAC_SUMMARY_PROMPT = """You are the Archon, writing a five-year window reference map for a premium astrological dossier.

Write ◈ THE FIVE-YEAR WINDOW MAP — a compact, precise reference of all high-confidence timing windows.

THIS IS NOT A YEAR-BY-YEAR ESSAY. It is a chronological table of pivotal windows.

FORMAT: For each window, write:
**[DATE RANGE]** — [CERTAINTY LABEL] — [One plain-English sentence: what this window delivers or tests]
Systems: [which systems agree] | Theme: [career / finance / relationship / home / health]

---

List all windows chronologically from the TEMPORAL STORM WINDOWS data.
Only include windows with NEAR-CERTAIN or HIGH-CONFIDENCE labels.
After the list, write ONE paragraph (5-7 sentences) named:

**The Arc:**
Trace how these windows chain together into the larger story — how Window A creates the conditions
for Window B, which enables Window C. Connect the sequence explicitly to the life questions the
user submitted. This is the strategic backbone.

RULES:
1. START with: # ◈ THE FIVE-YEAR WINDOW MAP
2. Only windows from the TEMPORAL STORM WINDOWS data. Do not invent windows.
3. All dates must be in the FUTURE relative to TODAY'S DATE (stated in the data block).
4. Do not explain what astrology is. The reader has already read sections 1-4.
5. LENGTH: 350-420 words total.
6. BANNED: journey, tapestry, energies, cosmic, explore."""


QUESTIONS_PROMPT = """You are the Archon, the final authority delivering precise, data-backed answers.

═══════════════════════════════════════════════════════════════
CRITICAL TEMPORAL RULE — READ FIRST, OBEY ALWAYS
═══════════════════════════════════════════════════════════════
TODAY'S DATE appears at the very top of the data block as "TODAY: YYYY-MM-DD".
This is your hard boundary. It is absolute.

FORBIDDEN: Citing ANY date, window, or period BEFORE today's date.
FORBIDDEN: Citing dates like "October 2024", "early 2025", "mid-2025" — those are IN THE PAST.
REQUIRED: Every date you write must be AFTER today.

If you catch yourself writing a past year — STOP. Find the next future window instead.
If no future window exists, say: "The next window for this opens in [YEAR], when [X] activates."
═══════════════════════════════════════════════════════════════

The data block you received contains a TAILORED EVIDENCE BLOCK for each question.
That evidence block was built by a question-routing engine that already filtered it to:
  - Only future-dated timing windows
  - Only the houses/planets/techniques relevant to that specific question
  - Exact outer planet transit hits from the ephemeris (already future-filtered)
  - The profection years where the relevant house is activated

Your job: read each question's evidence block and translate it into clear, specific prose.

FORMAT FOR EACH QUESTION:

**Q: [exact question as asked]**

*Confidence:* [NEAR-CERTAIN / HIGH-CONFIDENCE / MODERATE-CONFIDENCE / LOW-CONFIDENCE]
*Why:* [One sentence naming the strongest converging technique + the exact data point]

**The direct answer:**
[Give the verdict in the first sentence: yes/no/when/what form.
Then: which specific date range is the primary window, and why it's primary (how many systems agree).
Then: what the secondary window is if the primary window passes.
Language template: "Three independent systems — [technique], [technique], [technique] — all converge
on [Month YEAR]–[Month YEAR]. This is near-certain, not speculative."
Never hedge. If you are uncertain, state the confidence level and give the best estimate.
Narrow every range to a 3-6 month window. Never give a 3-year range without a primary 6-month target.]

**Mechanism:**
[2-3 sentences. Name the specific planets, houses, and techniques from the evidence block.
The reader knows their chart. Be precise: "Your 10th house profects to Pisces in 2026,
activating Jupiter as Time Lord. Simultaneously, Saturn trines your natal Sun on [exact date]."]

**What to do:**
[2-3 actions with specific months. First action = within the next 60 days.
Connect the action to the astrological window: "Before [month], [action], so that you are
positioned when [transit/profection] activates in [month]."]

---

RULES:
1. Answer EVERY question in the order given. Never skip or merge.
2. Read the EVIDENCE block for each question — it contains pre-filtered future dates.
   USE those dates. Do not substitute dates from memory or training data.
3. TODAY IS SHOWN AT THE TOP OF THE DATA BLOCK. Cross-check every date you write against it.
   Any date earlier than TODAY must be deleted and replaced with the next future window.
4. START with: # ◈ YOUR QUESTIONS ANSWERED
5. Separate each answer with ---
6. LENGTH: 400-550 words per question. Every word must carry specific data.
7. BANNED: "it depends", "only time will tell", vague spiritual hedges, dates before today.
8. REQUIRED: Direct verdict + specific future date range + confidence label + concrete action.
9. PROFECTION HOUSE is the master key for timing: a 10th house profection year = career activation.
   If the question matches the profected house — say so explicitly. That's near-certain timing."""


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers (preserved from v1)
# ─────────────────────────────────────────────────────────────────────────────

def _deg_to_dms(decimal_deg: float) -> str:
    try:
        decimal_deg = float(decimal_deg)
        d = int(decimal_deg)
        m = int(round((decimal_deg - d) * 60))
        if m >= 60:
            d += 1
            m -= 60
        return f"{d}° {m:02d}'"
    except (TypeError, ValueError):
        return f"{decimal_deg}°"


def _jd_to_str(jd: float) -> str:
    try:
        jd_adj = jd + 0.5
        Z = int(jd_adj)
        if Z < 2299161:
            A = Z
        else:
            alpha = int((Z - 1867216.25) / 36524.25)
            A = Z + 1 + alpha - alpha // 4
        B = A + 1524
        C = int((B - 122.1) / 365.25)
        D = int(365.25 * C)
        E = int((B - D) / 30.6001)
        day   = B - D - int(30.6001 * E)
        month = E - 1 if E < 14 else E - 13
        year  = C - 4716 if month > 2 else C - 4715
        months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]
        return f"{months[month - 1]} {day}, {year}"
    except Exception:
        return f"JD {jd:.1f}"


# ─────────────────────────────────────────────────────────────────────────────
# Probability / Confidence helpers
# ─────────────────────────────────────────────────────────────────────────────

def _convergence_label(cluster: dict) -> str:
    """Human-readable confidence band for a cluster."""
    return cluster.get("confidence_label", "MODERATE-CONFIDENCE")

def _stoplight(cluster: dict) -> str:
    return cluster.get("stoplight", "🟡")


def _format_clusters(temporal_clusters: list) -> str:
    """
    Format ALL temporal storm windows for the predictive data block.
    Includes convergence scores so the model can rank certainty across all windows.
    """
    if not temporal_clusters:
        return ""
    lines = ["=== TEMPORAL STORM WINDOWS — INCLUDE CONFIDENCE IN PROSE ==="]
    lines.append(
        "Each window = a convergence of multiple independent predictive systems.\n"
        "CONVERGENCE SCORE is a probability-like signal (0-1). Use it to rank certainty:\n"
        "  NEAR-CERTAIN (≥0.85): 4+ systems agree → state as near-certain event\n"
        "  HIGH-CONFIDENCE (0.70-0.84): 3 systems → state as likely\n"
        "  MODERATE-CONFIDENCE (0.55-0.69): 2 systems → state as probable\n"
        "  LOW-CONFIDENCE (<0.55): 1 system echoing → frame as possible\n"
        "NEVER reproduce this table verbatim. Cite naturally in prose."
    )
    for i, cluster in enumerate(temporal_clusters[:14], 1):
        start  = _jd_to_str(cluster.get("start_jd", 0))
        end    = _jd_to_str(cluster.get("end_jd",   0))
        score  = cluster.get("convergence_score", 0.6)
        label  = _convergence_label(cluster)
        light  = _stoplight(cluster)
        n_sys  = cluster.get("n_systems", cluster.get("intensity", 1))
        evts   = cluster.get("events", [])
        sys_list = ", ".join(cluster.get("systems_involved", ["?"]))
        evt_summary = "; ".join(
            f"{ev.get('technique','?')} ({ev.get('system','?')})"
            for ev in evts[:4]
        )
        lines.append(
            f"  {light} [{i}] {start}–{end} | {label} ({score:.2f}) | "
            f"{n_sys} systems: {sys_list}\n"
            f"     Techniques: {evt_summary}"
        )
    lines.append("=== END STORM WINDOWS ===")
    return "\n".join(lines)


def _format_clusters_for_year(temporal_clusters: list, year: int) -> str:
    """
    Extract storm windows for the target year, with full confidence metadata.
    Sorted by convergence score (highest first) so the model leads with the
    most certain windows.
    """
    if not temporal_clusters:
        return ""

    year_clusters = []
    for c in temporal_clusters:
        start_str = _jd_to_str(c.get("start_jd", 0))
        end_str   = _jd_to_str(c.get("end_jd",   0))
        if str(year) in start_str or str(year) in end_str:
            year_clusters.append(c)

    if not year_clusters:
        return f"No multi-system convergences identified for {year}."

    # Sort by convergence score descending (highest certainty first)
    year_clusters.sort(key=lambda c: c.get("convergence_score", 0), reverse=True)

    lines = [
        f"=== {year} STORM WINDOWS — sorted by convergence score (highest = most certain) ===",
        "INSTRUCTION: When writing the year section, state the MOST CERTAIN windows first.",
        "Reference the confidence label explicitly in your prose:",
        '  "This window has the highest convergence of any period this year — [X] independent',
        '   systems agree, making this near-certain rather than speculative."',
        "VS:",
        '  "This window has moderate support from two systems; treat as probable but not certain."',
        "",
    ]

    for i, c in enumerate(year_clusters, 1):
        start  = _jd_to_str(c.get("start_jd", 0))
        end    = _jd_to_str(c.get("end_jd",   0))
        score  = c.get("convergence_score", 0.6)
        label  = _convergence_label(c)
        light  = _stoplight(c)
        n_sys  = c.get("n_systems", len(c.get("systems_involved", [])))
        sys_list = ", ".join(c.get("systems_involved", ["?"]))
        evts   = c.get("events", [])
        evt_lines = [
            f"{ev.get('technique','?')} ({ev.get('system','?')}): {ev.get('description','')}"
            for ev in evts[:5]
        ]
        lines.append(
            f"  {light} Window {i}: {start} → {end}"
        )
        lines.append(
            f"     Confidence: {label} (score {score:.2f}) | "
            f"{n_sys} systems: {sys_list}"
        )
        for el in evt_lines:
            lines.append(f"     • {el}")
        lines.append("")

    lines.append(
        f"INSTRUCTION: Weave windows chronologically but lead with highest-confidence ones. "
        f"DO NOT reproduce this table. State confidence levels naturally in prose."
    )
    return "\n".join(lines)



# ─────────────────────────────────────────────────────────────────────────────
# Year Dashboard generator
# ─────────────────────────────────────────────────────────────────────────────

def _compute_year_dashboard(temporal_clusters: list,
                             years: list = None) -> str:
    """
    Generate an at-a-glance grid showing intensity, financial volatility, and
    relational harmony scores (1–10) for each of the five forecast years.

    Scores are computed purely from the cluster data — no API calls.

    Intensity:           total convergence score of all clusters in the year.
    Financial pressure:  score from clusters whose events involve career/finance domains.
    Relational pressure: score from clusters whose events touch House 7 / Venus / relationships.

    Scale: 1 = very quiet, 10 = peak pressure.
    Stoplight:
      8-10 = 🔴 high pressure / pivotal
      5-7  = 🟠 active / significant
      2-4  = 🟡 steady / building
      1    = 🟢 quiet
    """
    if years is None:
        years = [2026, 2027, 2028, 2029, 2030]

    FINANCE_KEYWORDS  = {"career", "saturn", "jupiter", "money", "2nd", "10th",
                          "profection", "solar return", "primary direction", "tajaka",
                          "amatyakaraka", "useful god", "mc", "midheaven"}
    RELATION_KEYWORDS = {"venus", "7th", "darakaraka", "mars", "relationship",
                          "partner", "lunar return", "peach blossom", "outer transit"}

    def _score_to_light(score: float) -> str:
        if score >= 8:  return "🔴"
        if score >= 5:  return "🟠"
        if score >= 2:  return "🟡"
        return "🟢"

    def _domain_score(clusters_for_year: list, keywords: set) -> float:
        """Score 1-10: how many clusters have events matching this domain."""
        if not clusters_for_year:
            return 1.0
        matched = 0
        for c in clusters_for_year:
            evts = c.get("events", [])
            for ev in evts:
                text = (
                    ev.get("technique", "") + " " +
                    ev.get("description", "") + " " +
                    ev.get("domain", "")
                ).lower()
                if any(kw in text for kw in keywords):
                    matched += c.get("convergence_score", 0.6)
                    break
        raw = matched / max(1, len(clusters_for_year)) * 10
        return round(min(10.0, max(1.0, raw)), 1)

    def _intensity_score(clusters_for_year: list) -> float:
        if not clusters_for_year:
            return 1.0
        total = sum(c.get("convergence_score", 0.6) for c in clusters_for_year)
        # Normalize: 1 cluster at 0.6 = 2, 5 clusters at 0.9 = 10
        raw = total / 0.45  # ~0.45 per unit → scale to 0-10
        return round(min(10.0, max(1.0, raw)), 1)

    rows = []
    for year in years:
        year_clusters = []
        for c in temporal_clusters:
            start_str = _jd_to_str(c.get("start_jd", 0))
            end_str   = _jd_to_str(c.get("end_jd", 0))
            if str(year) in start_str or str(year) in end_str:
                year_clusters.append(c)

        intensity   = _intensity_score(year_clusters)
        finance     = _domain_score(year_clusters, FINANCE_KEYWORDS)
        relational  = _domain_score(year_clusters, RELATION_KEYWORDS)

        # Find the peak window of this year for annotation
        peak_c = max(year_clusters, key=lambda c: c.get("convergence_score", 0), default=None)
        peak_note = ""
        if peak_c:
            peak_start = _jd_to_str(peak_c.get("start_jd", 0))
            peak_end   = _jd_to_str(peak_c.get("end_jd", 0))
            peak_score = peak_c.get("convergence_score", 0)
            peak_label = peak_c.get("confidence_label", "")
            peak_note  = f"Peak window: {peak_start}→{peak_end} ({peak_label}, {peak_score:.2f})"

        rows.append({
            "year":       year,
            "intensity":  intensity,
            "finance":    finance,
            "relational": relational,
            "peak_note":  peak_note,
            "n_windows":  len(year_clusters),
        })

    # Format as a readable table
    lines = [
        "",
        "## ◈ THE FIVE-YEAR AT-A-GLANCE",
        "",
        "*Scores computed from multi-system convergence analysis. "
        "10 = peak pressure / maximum opportunity. 1 = quiet.*",
        "",
        "| Year | Overall Intensity | Financial Pressure | Relational Pressure | Peak Window |",
        "|------|:-----------------:|:------------------:|:-------------------:|-------------|",
    ]

    for r in rows:
        yr      = r["year"]
        i_light = _score_to_light(r["intensity"])
        f_light = _score_to_light(r["finance"])
        rel_light = _score_to_light(r["relational"])
        lines.append(
            f"| **{yr}** | "
            f"{i_light} {r['intensity']:.0f}/10 | "
            f"{f_light} {r['finance']:.0f}/10 | "
            f"{rel_light} {r['relational']:.0f}/10 | "
            f"{r['peak_note']} |"
        )

    lines += [
        "",
        "*Score = intensity of activity, NOT a measure of good or bad luck. "
        "High scores mean pivotal periods — for opportunity AND challenge alike. "
        "A 🔴 10 in a Jupiter year = near-certain breakthrough. A 🔴 10 in a Saturn year = defining test. "
        "Context is in the year sections below.*",
        "",
        "*🔴 8–10 = pivotal / defining  🟠 5–7 = active / significant  "
        "🟡 2–4 = steady / building  🟢 1 = quiet*",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Wealth Capacity Score — computed from chart data, no API call
# ─────────────────────────────────────────────────────────────────────────────

def _compute_wealth_score(chart_data: dict, ref: dict) -> dict:
    """
    Compute a Wealth Capacity Score (1.0–10.0) from the chart's core wealth indicators.
    Returns a dict with score, tier, profile, and a plain-English summary paragraph.

    This is deterministic — no LLM involved. Based on:
      - Almuten dignity (most dignified planet = structural authority)
      - 2nd house lord strength (Shadbala if Vedic available)
      - Lot of Fortune sign and dignity
      - Dhana Yoga count (from Vedic yogas data)
      - Useful God element (Bazi — fire = tech/energy, water = finance/trade, etc.)
      - 8th house risk flag (planets in 8th opposing 2nd = joint-venture risk)
    """
    score = 5.0  # neutral baseline

    v_natal   = chart_data.get("vedic",  {}).get("natal",    {})
    w_natal   = chart_data.get("western",{}).get("natal",    {})
    bazi      = chart_data.get("bazi",   {}).get("natal",    {})
    shadbala  = chart_data.get("vedic",  {}).get("strength", {}).get("shadbala", {})

    # ── Almuten dignity bonus ────────────────────────────────────────────────
    # Saturn in domicile = +1.5, exaltation = +1.0, triplicity = +0.5
    almuten = ref.get("_almuten_planet", "")
    almuten_data = ref.get(almuten, {}) if almuten else {}
    dignity_map = {"domicile": 1.5, "exaltation": 1.0, "triplicity": 0.5,
                   "detriment": -1.0, "fall": -1.5}
    almuten_dignity = almuten_data.get("dignity", "") if isinstance(almuten_data, dict) else ""
    score += dignity_map.get(almuten_dignity.lower(), 0)

    # ── 2nd house lord Shadbala ────────────────────────────────────────────
    planet_scores = shadbala.get("planet_scores", {})
    # Higher shadbala = more strength (typical range 100–200 Rupas)
    lord_2nd = ref.get("_2nd_house_lord", "")
    if lord_2nd and lord_2nd in planet_scores:
        shad = float(planet_scores[lord_2nd].get("total", 0)) if isinstance(planet_scores[lord_2nd], dict) else 0
        if shad > 180:   score += 1.5
        elif shad > 140: score += 0.8
        elif shad > 100: score += 0.3
        elif shad < 60:  score -= 0.5

    # ── Dhana Yoga count ────────────────────────────────────────────────────
    yogas = v_natal.get("yogas", [])
    dhana_yogas = [y for y in yogas if isinstance(y, dict) and
                   any(w in str(y.get("name","")).lower() for w in
                       ["dhana", "wealth", "raja", "lakshmi", "gajakesari", "hamsa"])]
    score += min(2.0, len(dhana_yogas) * 0.5)   # cap at +2

    # ── Useful God element bonus (Bazi) ─────────────────────────────────────
    useful_god = ref.get("_useful_god", "")
    if useful_god:
        # All elements indicate wealth capacity — just different channels
        score += 0.5  # any defined Useful God = chart has clear wealth channel

    # ── 8th house risk flag ─────────────────────────────────────────────────
    # Planets in 8th house (shared resources) = joint-venture risk, NOT a score deduction
    # but informs the risk_flag for the report narrative
    houses = w_natal.get("houses", {})
    eighth_planets = [p for p, d in ref.items()
                      if isinstance(d, dict) and d.get("house") == 8
                      and p not in ("_almuten_planet", "_2nd_house_lord")]
    risk_flag = len(eighth_planets) > 0

    # ── Lot of Fortune dignity ──────────────────────────────────────────────
    lof_sign = ref.get("_lot_fortune_sign", "")
    if lof_sign in ("Taurus", "Cancer", "Pisces"):  # dignified/exalted
        score += 0.4
    elif lof_sign in ("Scorpio", "Capricorn", "Virgo"):  # detriment/fall
        score -= 0.2

    # ── Cap and tier ────────────────────────────────────────────────────────
    score = round(min(10.0, max(1.0, score)), 1)

    if score >= 8.5:
        tier = "EXCEPTIONAL"
        tier_desc = "upper-tier generational wealth potential"
    elif score >= 7.0:
        tier = "HIGH"
        tier_desc = "substantial long-term wealth — multi-million stability is structurally supported"
    elif score >= 5.5:
        tier = "SOLID"
        tier_desc = "above-average earning and asset-building capacity"
    elif score >= 4.0:
        tier = "MODERATE"
        tier_desc = "stable income with selective wealth windows"
    else:
        tier = "CONSTRAINED"
        tier_desc = "wealth requires deliberate structural effort to unlock"

    # ── Industry mapping from available signals ──────────────────────────────
    industry_signals = []
    second_house_sign = ref.get("_2nd_house_sign", "")
    mc_sign = ref.get("_mc_sign", "")

    sign_to_industry = {
        "Cancer":      ["real estate", "food & hospitality", "childcare", "healthcare", "advisory/coaching"],
        "Taurus":      ["real estate", "luxury goods", "agriculture", "finance", "art"],
        "Leo":         ["entertainment", "leadership roles", "luxury brands", "self-employment"],
        "Scorpio":     ["finance/investing", "research", "insurance", "transformation industries"],
        "Virgo":       ["health & wellness", "data/analytics", "consulting", "pharmaceuticals"],
        "Gemini":      ["media", "publishing", "education", "technology", "communications"],
        "Aquarius":    ["technology", "social enterprise", "engineering", "AI/software"],
        "Capricorn":   ["construction", "government", "finance", "established institutions"],
        "Sagittarius": ["education", "publishing", "law", "international business", "philosophy"],
        "Pisces":      ["arts", "spirituality", "healthcare", "film/music", "NGO/non-profit"],
        "Aries":       ["sports", "military/security", "entrepreneurship", "manufacturing"],
        "Libra":       ["law", "design", "luxury goods", "diplomacy", "partnerships"],
    }
    useful_element_to_industry = {
        "Fire":  ["technology", "AI/software", "energy", "entertainment", "startups"],
        "Water": ["finance/investing", "healthcare", "real estate", "import/export", "luxury"],
        "Wood":  ["education", "media", "publishing", "agriculture", "consulting"],
        "Metal": ["finance", "law", "manufacturing", "engineering", "government"],
        "Earth": ["real estate", "food", "construction", "retail", "hospitality"],
    }

    if second_house_sign in sign_to_industry:
        industry_signals.extend(sign_to_industry[second_house_sign][:3])

    ug_element = useful_god.split()[0] if useful_god else ""
    if ug_element in useful_element_to_industry:
        industry_signals.extend(useful_element_to_industry[ug_element][:2])

    # Deduplicate while preserving order
    seen = set()
    industries = []
    for ind in industry_signals:
        if ind not in seen:
            seen.add(ind)
            industries.append(ind)

    return {
        "score": score,
        "tier": tier,
        "tier_desc": tier_desc,
        "dhana_yoga_count": len(dhana_yogas),
        "risk_flag": risk_flag,
        "eighth_planets": eighth_planets,
        "industries": industries[:5],
        "useful_god": useful_god,
        "almuten_dignity": almuten_dignity,
    }


def _format_wealth_score_block(ws: dict) -> str:
    """Format the wealth score into a report-ready block for injection into Material World."""
    score = ws["score"]
    tier  = ws["tier"]
    desc  = ws["tier_desc"]
    industries = ws["industries"]
    risk  = ws["risk_flag"]
    eighth = ws["eighth_planets"]
    yogas = ws["dhana_yoga_count"]

    ind_str = ", ".join(industries) if industries else "advisory and relationship-based work"

    risk_sentence = ""
    if risk and eighth:
        planets_str = ", ".join(eighth[:3])
        risk_sentence = (
            f"\n> ⚠️ **Joint-Venture Risk Flag:** {planets_str} in the shared-resources zone "
            f"of the chart. Mixing finances with partners or investing in speculative/uncontrolled "
            f"ventures carries above-average risk of sudden loss. Maintain sole asset control."
        )

    yoga_note = ""
    if yogas > 0:
        yoga_note = f" ({yogas} Vedic wealth combination{'s' if yogas > 1 else ''} confirmed)"

    block = (
        f"\n> **◈ WEALTH CAPACITY SCORE: {score}/10 — {tier}**{yoga_note}\n"
        f"> *{desc}.*\n"
        f"> **Primary wealth channels:** {ind_str}\n"
        f"> **Wealth profile:** slow-compounding, authority-based — peak wealth arrives in the "
        f"second half of life, driven by reputation and systems built over decades.\n"
        f"{risk_sentence}\n"
    )
    return block


# ─────────────────────────────────────────────────────────────────────────────
# Rule querier (optional Neo4j dependency)
# ─────────────────────────────────────────────────────────────────────────────
_rule_querier = None
try:
    from synthesis.rule_querier import RuleQuerier
    _rule_querier = RuleQuerier()
except Exception:
    pass


# ─────────────────────────────────────────────────────────────────────────────
# QuestionRouter — semantic question-to-data mapper
# ─────────────────────────────────────────────────────────────────────────────

class QuestionRouter:
    """
    Parses each user question for domain intent, then extracts and future-filters
    exactly the chart data needed to answer it.

    Output per question: a labelled evidence block the LLM can cite directly,
    containing only data AFTER today.
    """

    # ── Domain definitions ───────────────────────────────────────────────────
    DOMAINS = {
        "wealth": {
            "keywords": [
                "wealth", "wealthy", "rich", "money", "financial", "finance",
                "income", "earn", "afford", "net worth", "savings", "fortune",
            ],
            "houses": [2, 8, 11],
            "planets": ["Jupiter", "Venus", "Sun", "Moon"],
            "direction_cats": ["wealth", "finance", "general"],
        },
        "career": {
            "keywords": [
                "career", "work", "job", "doctor", "gp", "general practitioner",
                "practice", "profession", "qualify", "training", "start working",
                "nhs", "medicine", "medical", "hospital", "clinic",
            ],
            "houses": [1, 6, 10],
            "planets": ["Saturn", "Mars", "Sun"],
            "direction_cats": ["career", "general"],
        },
        "home": {
            "keywords": [
                "house", "home", "property", "buy", "own", "flat", "apartment",
                "mortgage", "rent", "real estate", "purchase",
            ],
            "houses": [4],
            "planets": ["Moon", "Saturn", "Venus"],
            "direction_cats": ["home", "general"],
        },
        "children": {
            "keywords": [
                "baby", "child", "children", "pregnant", "pregnancy",
                "family", "kid", "birth", "conceive", "offspring",
            ],
            "houses": [5],
            "planets": ["Jupiter", "Moon", "Venus"],
            "direction_cats": ["relationships", "general"],
        },
        "relationship": {
            "keywords": [
                "partner", "relationship", "marriage", "marry", "married",
                "boyfriend", "girlfriend", "spouse", "love", "soulmate",
            ],
            "houses": [7],
            "planets": ["Venus", "Mars", "Jupiter"],
            "direction_cats": ["relationships", "general"],
        },
        "business": {
            "keywords": [
                "passive income", "business", "side income", "invest", "online",
                "content", "stream", "create", "sell", "entrepreneur", "startup",
            ],
            "houses": [3, 5, 11],
            "planets": ["Mercury", "Jupiter", "Sun"],
            "direction_cats": ["wealth", "career", "general"],
        },
    }

    def __init__(self, today: datetime):
        self.today     = today
        self.today_jd  = self._dt_to_jd(today)
        self.today_str = today.strftime("%Y-%m-%d")

    @staticmethod
    def _dt_to_jd(dt: datetime) -> float:
        import swisseph as swe
        return swe.julday(dt.year, dt.month, dt.day,
                          dt.hour + dt.minute / 60.0 + dt.second / 3600.0)

    def _classify(self, question: str) -> list:
        """Return list of matching domain keys, ranked by keyword hits."""
        q_lower = question.lower()
        scores  = {}
        for domain, cfg in self.DOMAINS.items():
            hits = sum(1 for kw in cfg["keywords"] if kw in q_lower)
            if hits:
                scores[domain] = hits
        if not scores:
            return ["general"]
        return sorted(scores, key=lambda d: scores[d], reverse=True)

    def _future_storm_windows(self, temporal_clusters: list, max_windows: int = 6) -> list:
        """Return storm windows that start or end after today, sorted by start."""
        future = []
        for c in temporal_clusters:
            end_jd = c.get("end_jd", 0)
            if end_jd > self.today_jd:
                future.append(c)
        future.sort(key=lambda c: c.get("start_jd", 0))
        return future[:max_windows]

    def _future_transit_hits(self, outer_transit_data: dict,
                              relevant_planets: list = None) -> list:
        """Extract and future-filter outer transit hits."""
        # western.py exposes both "hits" and "all_hits" — prefer "hits", fall back to "all_hits"
        hits = outer_transit_data.get("hits") or outer_transit_data.get("all_hits", [])
        future = []
        for h in hits:
            # Prefer machine-readable ISO date; fall back to exact_jd comparison
            iso_date = h.get("exact_date_iso", "")
            exact_jd = h.get("exact_jd", 0)
            try:
                if iso_date:
                    y, mo, d = map(int, iso_date.split("-"))
                    hit_dt = datetime(y, mo, d, tzinfo=timezone.utc)
                    is_future = hit_dt > self.today
                else:
                    is_future = exact_jd > self.today_jd
                if is_future:
                    planet = h.get("transiting") or h.get("planet", "Unknown")
                    if relevant_planets is None or planet in relevant_planets:
                        future.append(h)
            except Exception:
                pass
        return sorted(future, key=lambda h: h.get("exact_jd", 0))

    def _profection_years_for_house(self, profections: list, houses: list) -> list:
        """Return profection entries where activated_house is in the given list."""
        return [p for p in profections if p.get("activated_house") in houses]

    def _relevant_directions(self, primary_directions: dict, cats: list) -> list:
        """Pull primary direction hits from relevant categories."""
        results = []
        for cat in cats:
            entries = primary_directions.get(cat, [])
            if isinstance(entries, list):
                results.extend(entries[:3])
        return results[:5]

    def build_evidence_block(self,
                              question: str,
                              chart_data: dict,
                              temporal_clusters: list,
                              ref: dict,
                              question_num: int) -> str:
        """
        Build a tailored, future-filtered evidence block for a single question.
        Returns a formatted string block to inject into the LLM prompt.
        """
        domains = self._classify(question)
        primary_domain = domains[0] if domains[0] != "general" else (domains[1] if len(domains) > 1 else "general")

        cfg = self.DOMAINS.get(primary_domain, {
            "houses": [1, 2, 10],
            "planets": ["Jupiter", "Saturn", "Venus"],
            "direction_cats": ["general"],
        })

        relevant_houses  = cfg["houses"]
        relevant_planets = cfg["planets"]
        direction_cats   = cfg["direction_cats"]

        w_pred = chart_data.get("western",  {}).get("predictive", {})
        v_pred = chart_data.get("vedic",    {}).get("predictive", {})
        b_pred = chart_data.get("bazi",     {}).get("predictive", {})
        w_nat  = chart_data.get("western",  {}).get("natal",      {})
        v_nat  = chart_data.get("vedic",    {}).get("natal",      {})

        profections     = w_pred.get("profections_timeline", [])
        outer_transits  = w_pred.get("outer_transit_aspects", {})
        primary_dirs    = w_pred.get("primary_directions",   {})
        progressions    = w_pred.get("progressions",         {})

        dasha = v_pred.get("vimshottari", {})
        da_yun = b_pred.get("da_yun", {}).get("pillars", [])

        lines = [f"═══ EVIDENCE BLOCK: Question {question_num} ═══"]
        lines.append(f"QUESTION: {question}")
        lines.append(f"DOMAIN DETECTED: {primary_domain.upper()} "
                     f"(relevant houses: {relevant_houses}, key planets: {relevant_planets})")
        lines.append("")

        # ── Active Time Lords ───────────────────────────────────────────────
        lines.append("── ACTIVE TIME LORDS (what period is the native in RIGHT NOW) ──")
        lines.append(f"Vimshottari Maha Dasha: {dasha.get('maha_lord','?')} "
                     f"({dasha.get('approx_remaining_years','?')} yrs remaining)")
        lines.append(f"Antardasha: {dasha.get('antar_lord','?')} "
                     f"({dasha.get('antar_remaining_years','?')} yrs remaining)")
        if ref.get("_current_da_yun"):
            cy = ref["_current_da_yun"]
            lines.append(f"Current Da Yun: {cy.get('stem','?')}{cy.get('branch','?')} "
                         f"(age {cy.get('start_age','?')}–{cy.get('end_age','?')})")

        # ── Profection years that activate the relevant houses ───────────────
        lines.append("")
        lines.append(f"── PROFECTION YEARS ACTIVATING HOUSE(S) {relevant_houses} ──")
        lines.append("(These are the years when this life domain is cosmically activated)")
        house_profs = self._profection_years_for_house(profections, relevant_houses)
        if house_profs:
            for p in house_profs:
                lines.append(f"  {p.get('year')}: Age {p.get('age')} — "
                             f"House {p.get('activated_house')} activates, "
                             f"sign {p.get('profected_sign')}, "
                             f"Time Lord = {p.get('time_lord')}")
        else:
            lines.append("  No profection years found for this domain in the 5-year window.")

        # ── Future storm windows ────────────────────────────────────────────
        lines.append("")
        lines.append("── FUTURE STORM WINDOWS (multi-system convergences, all after TODAY) ──")
        future_windows = self._future_storm_windows(temporal_clusters, max_windows=5)
        if future_windows:
            for i, c in enumerate(future_windows, 1):
                start = _jd_to_str(c.get("start_jd", 0))
                end   = _jd_to_str(c.get("end_jd",   0))
                label = c.get("confidence_label", "?")
                score = c.get("convergence_score", 0)
                n_sys = c.get("n_systems", c.get("intensity", 1))
                sys_list = ", ".join(c.get("systems_involved", ["?"]))
                techs = "; ".join(
                    f"{ev.get('technique','?')} ({ev.get('system','?')})"
                    for ev in c.get("events", [])[:3]
                )
                lines.append(f"  [{i}] {start}–{end} | {label} ({score:.2f}) | {n_sys} systems: {sys_list}")
                lines.append(f"       Techniques: {techs}")
        else:
            lines.append("  No future storm windows computed for this chart yet.")

        # ── Outer transit exact hits (future, relevant planets) ─────────────
        lines.append("")
        lines.append(f"── OUTER PLANET TRANSIT HITS TO NATAL CHART (future only, key planets: {relevant_planets}) ──")
        transit_hits = self._future_transit_hits(outer_transits, relevant_planets=None)
        # Filter to hits involving natal points connected to relevant houses
        domain_natal_points = self._get_relevant_natal_points(w_nat, v_nat, relevant_houses, relevant_planets)
        relevant_hits = [h for h in transit_hits
                         if h.get("natal_point") in domain_natal_points
                         or h.get("transiting") in relevant_planets][:12]
        if relevant_hits:
            for h in relevant_hits:
                planet   = h.get("transiting") or h.get("planet", "?")
                iso_date = h.get("exact_date_iso") or h.get("exact_date", "?")
                entry    = h.get("entry_date", "~45d before")
                exit_    = h.get("exit_date",  "~45d after")
                lines.append(f"  {iso_date}: {planet} {h['aspect']} "
                             f"natal {h['natal_point']}  "
                             f"[window: {entry}–{exit_}]  "
                             f"orb={h.get('orb_at_exact','?')}°")
        else:
            lines.append("  No specific transit hits found for this domain's planets/points.")

        # ── Primary Directions ──────────────────────────────────────────────
        lines.append("")
        lines.append("── PRIMARY DIRECTIONS (Regiomontanus, future arcs) ──")
        dirs = self._relevant_directions(primary_dirs, direction_cats)
        if dirs:
            for d in dirs:
                lines.append(f"  {json.dumps(d, default=str)}")
        else:
            lines.append("  None in this domain's categories.")

        # ── Progressions relevant to domain ─────────────────────────────────
        lines.append("")
        lines.append("── PROGRESSED POSITIONS (current, for additional context) ──")
        for pname in relevant_planets:
            pk = f"Progressed_{pname}"
            if pk in progressions:
                pd = progressions[pk]
                lines.append(f"  {pk}: {pd.get('degree',0):.1f}° {pd.get('sign','?')} "
                             f"{'(Rx)' if pd.get('retrograde') else ''}")
        if "Progressed_Ascendant" in progressions:
            pa = progressions["Progressed_Ascendant"]
            lines.append(f"  Progressed Ascendant: {pa.get('degree',0):.1f}° {pa.get('sign','?')}")
        if "Progressed_MC" in progressions:
            pm = progressions["Progressed_MC"]
            lines.append(f"  Progressed MC: {pm.get('degree',0):.1f}° {pm.get('sign','?')}")
        if "lunar_phase" in progressions:
            lp = progressions["lunar_phase"]
            lines.append(f"  Progressed Lunar Phase: {lp.get('phase','?')} "
                         f"(elongation {lp.get('elongation','?')}°)")
        if "prog_natal_aspects" in progressions:
            tight_aspects = [a for a in progressions["prog_natal_aspects"]
                            if any(pl in [a.get("progressed"), a.get("natal")]
                                   for pl in relevant_planets)][:4]
            for a in tight_aspects:
                lines.append(f"  Progressed {a['progressed']} {a['aspect']} natal {a['natal']} "
                             f"(orb {a['orb']}°) ← ACTIVE NOW")

        # ── Domain-specific natal factors ───────────────────────────────────
        lines.append("")
        lines.append("── KEY NATAL FACTORS FOR THIS QUESTION ──")
        self._append_natal_factors(lines, primary_domain, w_nat, v_nat, ref)

        lines.append("")
        lines.append(f"═══ END EVIDENCE: Question {question_num} ═══")
        return "\n".join(lines)

    def _get_relevant_natal_points(self, w_nat: dict, v_nat: dict,
                                    relevant_houses: list, relevant_planets: list) -> set:
        """Get natal point names that are lords of or in the relevant houses."""
        points = set(relevant_planets)
        # Add Ascendant and MC as always relevant
        points.update(["Ascendant", "Midheaven", "Sun", "Moon"])
        # Add house lords
        house_signs = {
            1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
            5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
            9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
        }
        return points

    def _append_natal_factors(self, lines: list, domain: str,
                               w_nat: dict, v_nat: dict, ref: dict):
        """Append domain-specific natal chart factors."""
        if domain == "wealth":
            houses = w_nat.get("houses", {})
            lines.append(f"  House 2 (income): {json.dumps(houses.get('House_2', {}), default=str)}")
            lines.append(f"  House 11 (gains): {json.dumps(houses.get('House_11', {}), default=str)}")
            lines.append(f"  Lot of Fortune: {ref.get('_lot_fortune_sign','?')} at {ref.get('_lot_fortune_deg','?')}")
            yogas = [y for y in v_nat.get("yogas", []) if "dhana" in str(y).lower() or "raja" in str(y).lower()]
            lines.append(f"  Dhana/Raja Yogas: {json.dumps(yogas, default=str)}")

        elif domain == "career":
            houses = w_nat.get("houses", {})
            lines.append(f"  House 10 (career): {json.dumps(houses.get('House_10', {}), default=str)}")
            lines.append(f"  House 6 (work/service): {json.dumps(houses.get('House_6', {}), default=str)}")
            lines.append(f"  MC sign: {ref.get('Midheaven', {}).get('sign','?')}")
            lines.append(f"  Amatyakaraka (career significator): {ref.get('_vedic_amatyakaraka','?')}")
            yogas = [y for y in v_nat.get("yogas", []) if "raja" in str(y).lower()]
            lines.append(f"  Raja Yogas: {json.dumps(yogas[:2], default=str)}")

        elif domain == "home":
            houses = w_nat.get("houses", {})
            lines.append(f"  House 4 (home/property): {json.dumps(houses.get('House_4', {}), default=str)}")
            lines.append(f"  Moon sign/placement: {ref.get('Moon', {}).get('sign','?')} "
                         f"at {ref.get('Moon', {}).get('degree', 0):.1f}°")
            lines.append(f"  Lot of Fortune (material base): {ref.get('_lot_fortune_sign','?')}")

        elif domain == "children":
            houses = w_nat.get("houses", {})
            lines.append(f"  House 5 (children/creativity): {json.dumps(houses.get('House_5', {}), default=str)}")
            lines.append(f"  Jupiter placement: {ref.get('Jupiter', {}).get('sign','?')} "
                         f"at {ref.get('Jupiter', {}).get('degree', 0):.1f}°")
            lines.append(f"  Moon Nakshatra: {ref.get('_moon_nakshatra','?')} (fertility indicator)")
            jup_dig = (w_nat.get("dignities", {}).get("planet_dignities", {}).get("Jupiter", {})
                       .get("total_score", "?"))
            lines.append(f"  Jupiter dignity score: {jup_dig}")

        elif domain == "relationship":
            houses = w_nat.get("houses", {})
            lines.append(f"  House 7 (partnership): {json.dumps(houses.get('House_7', {}), default=str)}")
            lines.append(f"  Darakaraka: {ref.get('_vedic_darakaraka','?')}")
            lines.append(f"  Venus placement: {ref.get('Venus', {}).get('sign','?')} "
                         f"at {ref.get('Venus', {}).get('degree', 0):.1f}°")

        elif domain == "business":
            houses = w_nat.get("houses", {})
            lines.append(f"  House 11 (gains/income streams): {json.dumps(houses.get('House_11', {}), default=str)}")
            lines.append(f"  House 3 (communication/content): {json.dumps(houses.get('House_3', {}), default=str)}")
            lines.append(f"  Mercury placement: {ref.get('Mercury', {}).get('sign','?')} "
                         f"at {ref.get('Mercury', {}).get('degree', 0):.1f}°")
            lines.append(f"  Atmakaraka: {ref.get('_vedic_ak','?')} (soul path — aligns with business type)")

        else:
            lines.append(f"  Maha Dasha: {ref.get('_maha_dasha','?')} "
                         f"({ref.get('_dasha_years_left','?')} yrs remaining)")
            lines.append(f"  Profection Time Lord: {ref.get('_time_lord','?')}")


# ─────────────────────────────────────────────────────────────────────────────
# Archon
# ─────────────────────────────────────────────────────────────────────────────

class Archon:
    """Master narrative architect for the 13-Section Celestial Dossier."""

    # ── Model selection per section type ─────────────────────────────────────
    # Override in config.py/settings if desired.
    MODEL_MAP = {
        "oracle":       getattr(settings, "archon_model",       "gpt-4o"),
        "natal":        getattr(settings, "archon_model",       "gpt-4o"),
        "current":      getattr(settings, "archon_model",       "gpt-4o"),
        "year_forecast":getattr(settings, "archon_model",       "gpt-4o"),
        "directive":    getattr(settings, "archon_model",       "gpt-4o"),
    }

    TEMP_MAP = {
        "oracle":        0.82,   # slightly warmer — hook writing
        "natal":         0.70,   # precise diagnosis
        "current":       0.60,   # factual briefing
        "year_forecast": 0.68,   # precise + vivid
        "directive":     0.55,   # crisp orders
    }

    # gemini-2.5-pro counts thinking tokens against max_output_tokens.
    # At reasoning_effort="low": ~300-500 thinking tokens consumed.
    # Budget = (prose_words × 1.5 tokens/word) + 800 thinking buffer.
    MAX_TOKENS_MAP = {
        "oracle":        1800,   # target ~220w prose + 800 thinking buffer (shorter cold read)
        "natal":         4500,   # target ~460w prose + 800 thinking buffer (mechanisms format)
        "current":       2000,   # target ~155w prose + 800 thinking buffer
        "year_forecast": 5500,   # target ~620w prose + 800 thinking buffer
        "directive":     3200,   # target ~310w prose + 800 thinking buffer
        "questions":     8000,   # 5 questions × ~400-550w each + evidence blocks + buffer
    }

    # Keep thinking minimal for creative writing — output tokens matter more than reasoning depth
    ARCHON_REASONING_EFFORT = "low"

    def generate_report(self,
                        arbiter_synthesis: dict,
                        chart_data: dict,
                        metadata: dict,
                        temporal_clusters: list = None,
                        user_questions: list = None,
                        query_context: dict = None) -> str:
        """
        Generate the Celestial Dossier.
        user_questions: list of up to 5 question strings.
        query_context: pre-built QueryContext dict from QueryEngine.
          If provided, steers every section toward the user's questions.
          If not provided but user_questions is, a simple Part IV is still generated.
        """
        ref           = self._extract_reference_positions(chart_data)
        cluster_block = _format_clusters(temporal_clusters or [])

        # Compute wealth score deterministically (no API call)
        wealth_score  = _compute_wealth_score(chart_data, ref)
        wealth_block  = _format_wealth_score_block(wealth_score)

        header   = self._generate_header(metadata, chart_data, ref)
        sections = []
        total    = len(SECTION_DEFS)

        clean_questions = [q.strip() for q in (user_questions or []) if q and q.strip()][:5]

        for sec_num in sorted(SECTION_DEFS.keys()):
            sd = SECTION_DEFS[sec_num]

            # Skip questions section if no questions provided
            if sd["id"] == "questions" and not clean_questions:
                continue

            print(f"   [Archon] Generating section {sec_num + 1}/{total}: {sd['title']}...")

            prompt = self._build_section_prompt(
                sec_num, sd, arbiter_synthesis, chart_data, ref,
                cluster_block, temporal_clusters_raw=temporal_clusters or [],
                user_questions=clean_questions if sd["id"] == "questions" else None,
                wealth_block=wealth_block if sd["id"] == "material_world" else None,
                wealth_score=wealth_score if sd["id"] in ("material_world", "directive", "questions") else None,
                query_context=query_context,
            )
            sys_prompt = self._get_system_prompt(sd)

            response = gateway.generate(
                system_prompt    = sys_prompt,
                user_prompt      = prompt,
                model            = self.MODEL_MAP.get(sd["type"], settings.archon_model),
                max_tokens       = self.MAX_TOKENS_MAP.get(sd["type"], 5000),
                temperature      = self.TEMP_MAP.get(sd["type"], 0.70),
                # Questions need careful date reasoning — use medium effort
                reasoning_effort = "medium" if sd.get("id") == "questions" else self.ARCHON_REASONING_EFFORT,
            )

            if response.get("success"):
                content = response["content"]
                content = self._enforce_section_header(content, sd)
                content = self._validate_degrees_internal(content, ref, sec_num)
                content = self._audit_banned_words(content, sec_num)
                content = self._audit_past_dates(content, sec_num)
                sections.append(content)
            else:
                err = response.get("error", "Unknown error")
                sections.append(
                    f"\n\n# {sd['header']}\n\n**[Generation Failed: {err}]**\n\n"
                )
                logger.error(f"Section {sec_num} ({sd['id']}) failed: {err}")

        # ── Assemble with part dividers ────────────────────────────────────
        full_report = header

        # Dashboard — immediately after header, before Part I
        # Skip when questions are submitted: the report focus shifts to Q&A depth,
        # not the year table. The storm windows are still used inside each answer.
        show_dashboard = temporal_clusters and not clean_questions
        if show_dashboard:
            full_report += _compute_year_dashboard(temporal_clusters)

        part_labels = {
            "I":   "\n\n---\n\n# PART I: THE NATIVITY\n\n---\n\n",
            "II":  "\n\n---\n\n# PART II: THE FIVE-YEAR ALMANAC\n\n---\n\n",
            "III": "\n\n---\n\n# PART III: THE DIRECTIVE\n\n---\n\n",
            "IV":  "\n\n---\n\n# PART IV: YOUR QUESTIONS\n\n---\n\n",
        }
        current_part = None
        # zip only the sections that were actually generated
        generated_sec_nums = [
            n for n in sorted(SECTION_DEFS.keys())
            if not (SECTION_DEFS[n]["id"] == "questions" and not clean_questions)
        ]
        for sec_num, sec_content in zip(generated_sec_nums, sections):
            sd   = SECTION_DEFS[sec_num]
            part = sd["part"]
            if part != current_part:
                full_report += part_labels[part]
                current_part = part
            full_report += sec_content + "\n\n"

        full_report += (
            "\n\n---\n\n"
            "*All planetary positions verified against Swiss Ephemeris. "
            "Primary Direction arcs calculated via Regiomontanus method. "
            "Parans computed using RAMC horizon-crossing method (Brady 1998).*"
        )

        return full_report

    # ─────────────────────────────────────────────────────────────────────────
    # System Prompt Selector
    # ─────────────────────────────────────────────────────────────────────────

    def _get_system_prompt(self, sd: dict) -> str:
        t = sd["type"]
        header = sd["header"]
        if t == "oracle":
            return ORACLE_PROMPT
        elif t == "natal":
            return NATAL_PROMPT.replace("{HEADER}", header)
        elif t == "current":
            return CURRENT_CONFIG_PROMPT
        elif t == "year_forecast":
            year = str(sd.get("target_year", ""))
            return YEAR_FORECAST_PROMPT.replace("{YEAR}", year).replace("{YEAR}", year)
        elif t == "questions":
            return QUESTIONS_PROMPT
        elif t == "directive":
            if sd["id"] == "warning":
                return WARNING_PROMPT
            return DIRECTIVE_PROMPT
        return NATAL_PROMPT.replace("{HEADER}", header)

    # ─────────────────────────────────────────────────────────────────────────
    # Section Prompt Builder
    # ─────────────────────────────────────────────────────────────────────────

    def _build_section_prompt(self, sec_num: int, sd: dict,
                               synthesis: dict, chart_data: dict,
                               ref: dict, cluster_block: str,
                               temporal_clusters_raw: list = None,
                               user_questions: list = None,
                               wealth_block: str = None,
                               wealth_score: dict = None,
                               query_context: dict = None) -> str:
        is_predictive = sd["type"] in ("year_forecast", "current", "directive")

        if is_predictive:
            data_block = self._build_predictive_block(ref, chart_data)
        else:
            data_block = self._build_natal_block(ref)

        # ── Query Architecture: inject header_block into data_block ──────────────
        if query_context:
            header = query_context.get("header_block", "")
            if header:
                data_block = header + data_block

        synth_str    = json.dumps(synthesis, default=str)
        synth_trunc  = synth_str[:1800] if len(synth_str) > 1800 else synth_str

        extra        = self._section_specific_data(sec_num, sd, chart_data, ref, synthesis)

        # Inject wealth score block into material_world section
        if wealth_block and sd.get("id") == "material_world":
            extra = (
                "=== WEALTH CAPACITY SCORE (pre-computed from chart data) ===\n"
                + wealth_block
                + "\nInclude this score verbatim as the very first element of the section, "
                  "before any mechanism header. It is a mathematical calculation — do not "
                  "soften, modify, or qualify it. Present it exactly as shown.\n"
                + "=== END SCORE BLOCK ===\n\n"
                + extra
            )

        # Inject hard financial rules context into directive sections
        if wealth_score and sd.get("id") in ("five_year_directive", "warning"):
            industries = ", ".join(wealth_score.get("industries", [])[:4])
            risk = wealth_score.get("risk_flag", False)
            eighth = wealth_score.get("eighth_planets", [])
            ws_score = wealth_score.get("score", 5.0)
            tier = wealth_score.get("tier", "")
            hard_rules_ctx = (
                "=== CHART FINANCIAL PROFILE (for Directive hard rules) ===\n"
                f"Wealth Capacity: {ws_score}/10 — {tier}\n"
                f"Primary wealth channels: {industries}\n"
            )
            if risk and eighth:
                hard_rules_ctx += (
                    f"RISK FLAG: {chr(39).join(eighth[:3])} in shared-resources zone. "
                    "This chart has a structural vulnerability to financial loss through partnerships.\n"
                    "REQUIRED: The Directive must include at least one HARD RULE about financial "
                    "independence — specific, non-negotiable, written in bold. Example format:\n"
                    "> **HARD RULE: Never sign a 50/50 equity split. Maintain 51%+ control of "
                    "any business you build.**\n"
                )
            hard_rules_ctx += "=== END FINANCIAL PROFILE ===\n"
            extra = hard_rules_ctx + extra

        # ── Query Architecture: inject per-section steering into extra ───────────
        if query_context:
            section_id = sd.get("id", "")
            steering_map = query_context.get("steering", {})
            steering_block = steering_map.get(section_id, "")
            if steering_block:
                extra = steering_block + "\n\n" + extra


        graph_section = ""
        if _rule_querier is not None:
            try:
                rules = _rule_querier.get_chapter_rules(sec_num, chart_data)
                if rules:
                    graph_section = f"\n{rules}\n"
            except Exception:
                pass

        cluster_section = ""
        if is_predictive and temporal_clusters_raw:
            if sd.get("type") == "year_forecast":
                # Inject only THIS year's windows — prevents cross-year data bleeding
                year = sd.get("target_year")
                year_block = _format_clusters_for_year(temporal_clusters_raw, year) if year else cluster_block
                cluster_section = f"\n{year_block}\n"
            else:
                cluster_section = f"\n{cluster_block}\n"

        min_w, max_w = sd.get("words", (500, 700))

        # Questions section — uses QuestionRouter for tailored per-question evidence
        if sd.get("id") == "questions" and user_questions:
            today = datetime.now(timezone.utc)
            today_str = today.strftime("%Y-%m-%d")
            router = QuestionRouter(today)

            # Build evidence block for each question individually
            evidence_blocks = []
            for i, q in enumerate(user_questions, 1):
                eb = router.build_evidence_block(
                    question=q,
                    chart_data=chart_data,
                    temporal_clusters=temporal_clusters_raw or [],
                    ref=ref,
                    question_num=i,
                )
                evidence_blocks.append(eb)

            all_evidence = "\n\n".join(evidence_blocks)

            parts = [
                f"TODAY: {today_str}  ← HARD DATE BOUNDARY. Every date you write MUST be after this.",
                "",
                data_block,
                "=== SYNTHESIS DATA (arbiter) ===",
                synth_trunc,
                "",
                "=== TAILORED EVIDENCE BLOCKS (one per question, pre-filtered to future dates) ===",
                "Each block below contains ONLY future-dated data relevant to that specific question.",
                "Use the data in these blocks as your primary source. Do not substitute dates from memory.",
                "",
                all_evidence,
                "",
                "=== WRITE THE ANSWERS ===",
                f"Start with: # {sd['header']}",
                f"Answer {len(user_questions)} question(s) in order. Separate with ---.",
                "For each answer: direct verdict first, then cite 2+ specific dates from the evidence block above.",
                f"TODAY IS {today_str}. Any date before this is FORBIDDEN.",
            ]
            return "\n\n".join(p for p in parts if p)

        parts = [
            data_block,
            "=== SECTION FOCUS ===",
            f"Section: {sd['title']}",
            f"Focus: {sd['focus']}",
            f"Key domains: {', '.join(sd['domains']) if sd['domains'] else 'See focus above'}",
            "=== SYNTHESIS DATA ===",
            synth_trunc,
            graph_section,
            cluster_section,
            "=== SECTION-SPECIFIC DATA ===",
            extra,
            f"Write: {sd['title']}",
            "Requirements:",
            f"- Start with exactly: # {sd['header']}",
            f"- Length: {min_w}-{max_w} words",
            f"- {'Use DMS positions from MANDATORY NATAL DATA' if not is_predictive else 'Use exact date windows from TEMPORAL STORM WINDOWS'}",
            "- State system conflicts explicitly",
            "- Every claim must reference specific planetary evidence",
        ]
        return "\n\n".join(p for p in parts if p)

    # ─────────────────────────────────────────────────────────────────────────
    # Section-specific data injections
    # ─────────────────────────────────────────────────────────────────────────

    def _section_specific_data(self, sec_num: int, sd: dict,
                                chart_data: dict, ref: dict,
                                synthesis: dict = None) -> str:
        w_natal = chart_data.get("western", {}).get("natal", {})
        v_natal = chart_data.get("vedic",   {}).get("natal", {})
        w_pred  = chart_data.get("western", {}).get("predictive", {})

        sid = sd["id"]

        # ── Oracle Opening ────────────────────────────────────────────────────
        if sid == "oracle_opening":
            tight = [a for a in w_natal.get("aspects", [])
                     if a.get("orb", 99) <= 2.0][:3]
            yogas = v_natal.get("yogas", [])[:2]
            return (
                f"Tightest aspects (≤2°): {json.dumps(tight, default=str)}\n"
                f"Key yogas: {json.dumps(yogas, default=str)}\n"
                f"Maha Dasha: {ref.get('_maha_dasha')} — Antardasha: {ref.get('_antar_dasha')}\n"
                f"Fixed Star parans: {json.dumps(ref.get('_parans', [])[:4], default=str)}\n"
                f"Chart pattern: {ref.get('_dominant_pattern', 'N/A')}\n"
                f"Almuten: {ref.get('_almuten')} | Hyleg: {ref.get('_hyleg')}\n"
                f"Saju Day Master: {ref.get('_dm_stem', 'N/A')} {ref.get('_dm_tier', 'N/A')} | "
                f"Useful God: {ref.get('_useful_god', 'N/A')}"
            )

        # ── Architecture of Self ──────────────────────────────────────────────
        elif sid == "architecture_of_self":
            tight = [a for a in w_natal.get("aspects", [])
                     if a.get("orb", 99) <= 3.0][:5]
            parans = ref.get("_parans", [])[:4]
            stars  = ref.get("_significant_stars", ref.get("_fixed_stars", []))[:4]
            return (
                f"Tightest aspects: {json.dumps(tight, default=str)}\n"
                f"Yogas: {json.dumps(v_natal.get('yogas', [])[:3], default=str)}\n"
                f"Chart pattern: {json.dumps(ref.get('_patterns_summary', {}), default=str)}\n"
                f"True Parans (RAMC method): {json.dumps(parans, default=str)}\n"
                f"Fixed Star contacts: {json.dumps(stars, default=str)}\n"
                f"Dodecatemoria dominant: {ref.get('_dodec_dominant_sign')} "
                f"(ruler {ref.get('_dodec_dominant_ruler')})\n"
                f"Pre-natal syzygy: {ref.get('_syzygy_type')} in {ref.get('_syzygy_sign')}, "
                f"{ref.get('_syzygy_days_before')} days before birth"
            )

        # ── Material World ────────────────────────────────────────────────────
        elif sid == "material_world":
            houses = w_natal.get("houses", {})
            lots   = w_natal.get("lots",   {})
            dirs   = chart_data.get("western", {}).get("predictive", {}).get(
                        "primary_directions", {}).get("career", [])[:3]
            return (
                f"House 2: {json.dumps(houses.get('House_2', {}), default=str)}\n"
                f"House 10: {json.dumps(houses.get('House_10', {}), default=str)}\n"
                f"Lots: {json.dumps(lots, default=str)}\n"
                f"MC: {json.dumps(w_natal.get('angles', {}).get('Midheaven', {}), default=str)}\n"
                f"Career Primary Directions: {json.dumps(dirs, default=str)}\n"
                f"Vedic 2nd/11th: {json.dumps(v_natal.get('houses', {}).get('Bhava_2', {}), default=str)}\n"
                f"D10 Sun: {v_natal.get('placements', {}).get('Sun', {}).get('d10', 'N/A')}\n"
                f"Amatyakaraka: {ref.get('_vedic_amatyakaraka')}"
            )

        # ── Inner World ───────────────────────────────────────────────────────
        elif sid == "inner_world":
            desc        = w_natal.get("angles", {}).get("Descendant", {})
            shadbala    = chart_data.get("vedic", {}).get("strength", {}).get("shadbala", {})
            interactions= chart_data.get("bazi", {}).get("natal", {}).get("interactions", {})
            venus_dig   = (w_natal.get("dignities", {})
                                  .get("planet_dignities", {}).get("Venus", {}))
            peach       = next((s for s in chart_data.get("bazi", {})
                                              .get("natal", {}).get("shensha", [])
                                if "Peach" in s.get("type", "")), None)
            return (
                f"Descendant: {json.dumps(desc, default=str)}\n"
                f"House 6: {json.dumps(w_natal.get('houses', {}).get('House_6', {}), default=str)}\n"
                f"House 7: {json.dumps(w_natal.get('houses', {}).get('House_7', {}), default=str)}\n"
                f"Venus dignities: {json.dumps(venus_dig, default=str)}\n"
                f"Darakaraka: {ref.get('_vedic_darakaraka')}\n"
                f"D9 Venus: {v_natal.get('placements', {}).get('Venus', {}).get('d9', 'N/A')}\n"
                f"Peach Blossom: {json.dumps(peach, default=str)}\n"
                f"Shadbala Moon/Mars: "
                f"{json.dumps({k: v for k, v in shadbala.get('planet_scores', {}).items() if k in ['Moon', 'Mars']}, default=str)}\n"
                f"Saju interactions: {json.dumps(interactions, default=str)}"
            )

        # ── Karmic Mandate ────────────────────────────────────────────────────
        elif sid == "karmic_mandate":
            north_node = w_natal.get("placements", {}).get("North Node", {})
            ketu_v     = v_natal.get("placements", {}).get("Ketu", {})
            zr         = chart_data.get("hellenistic", {}).get("zodiacal_releasing", {})
            dodec      = chart_data.get("hellenistic", {}).get("dodecatemoria", {})
            stars      = ref.get("_parans", [])[:4] or ref.get("_significant_stars", [])[:4]
            return (
                f"North Node: {json.dumps(north_node, default=str)}\n"
                f"Ketu (Vedic): {json.dumps(ketu_v, default=str)}\n"
                f"ZR brief: {json.dumps({'fortune_L1': zr.get('fortune', [])[:2], 'spirit_L1': zr.get('spirit', [])[:2]}, default=str)}\n"
                f"Syzygy: {json.dumps(chart_data.get('western', {}).get('natal', {}).get('syzygy', {}), default=str)}\n"
                f"Star fate signatures: {json.dumps(stars, default=str)}\n"
                f"Dodecatemoria Node: {json.dumps(dodec.get('placements', {}).get('North Node', {}), default=str)}"
            )

        # ── Current Configuration ─────────────────────────────────────────────
        elif sid == "current_configuration":
            dasha    = chart_data.get("vedic", {}).get("predictive", {}).get("vimshottari", {})
            outer_t  = w_pred.get("outer_transit_aspects", {}).get("summary_block", "")[:400]
            return (
                f"Maha Dasha: {ref.get('_maha_dasha')} "
                f"({ref.get('_dasha_years_left')} yrs remaining)\n"
                f"Antardasha: {ref.get('_antar_dasha')} "
                f"({ref.get('_antar_dasha_years')} yrs remaining)\n"
                f"Current Profection: {ref.get('_profection_sign')} "
                f"House {ref.get('_profection_house')}, Time Lord: {ref.get('_time_lord')}\n"
                f"Dominant transits today:\n{outer_t}"
            )

        # ── Year Forecast Sections (2026–2030) ───────────────────────────────
        elif sd["type"] == "year_forecast":
            year    = sd.get("target_year", 2026)
            profecs = w_pred.get("profections_timeline", [])
            prof_yr = next((p for p in profecs if p.get("year") == year), {})
            tajaka  = chart_data.get("vedic", {}).get("predictive", {}).get("tajaka", [])
            taj_yr  = next((t for t in tajaka  if t.get("year") == year), {})
            dasha   = chart_data.get("vedic", {}).get("predictive", {}).get("vimshottari", {})
            liu     = [l for l in chart_data.get("bazi", {}).get("predictive", {})
                                 .get("liu_nian_timeline", []) if l.get("year") == year]
            kakshya = chart_data.get("vedic", {}).get("predictive", {}).get(
                        "kakshya_transits", {}).get(str(year), {})
            outer   = w_pred.get("outer_transit_aspects", {}).get("by_year", {}).get(str(year), [])
            lr      = [l for l in w_pred.get("lunar_returns", [])
                       if str(l.get("year", "")) == str(year)][:2]
            return (
                f"YEAR: {year}\n"
                f"Profection {year}: {json.dumps(prof_yr, default=str)}\n"
                f"Tajaka {year}: {json.dumps(taj_yr, default=str)}\n"
                f"Liu Nian {year}: {json.dumps(liu, default=str)}\n"
                f"Vimshottari active: Maha {dasha.get('maha_lord','?')} / "
                f"Antar {dasha.get('antar_lord','?')} "
                f"({dasha.get('antar_remaining_years','?')} yrs left)\n"
                f"Kakshya {year}: {json.dumps(kakshya, default=str)}\n"
                f"Outer transit aspects {year}: {json.dumps(outer[:8], default=str)}\n"
                f"Lunar returns sample: {json.dumps(lr, default=str)}"
            )

        # ── Directive & Warning ───────────────────────────────────────────────
        elif sd["type"] == "directive":
            synth = synthesis or {}
            pd    = chart_data.get("western", {}).get("predictive", {}).get(
                        "primary_directions", {})
            all_dirs = []
            for cat in pd.values():
                if isinstance(cat, list):
                    all_dirs.extend(cat[:2])
            return (
                f"Consensus points: {json.dumps(synth.get('consensus_points', [])[:5], default=str)}\n"
                f"Unified narrative: {synth.get('unified_narrative', '')}\n"
                f"Key contradictions: {json.dumps(synth.get('contradictions', [])[:3], default=str)}\n"
                f"Primary Directions: {json.dumps(all_dirs[:4], default=str)}\n"
                f"Peak risk window: {json.dumps(synth.get('critical_periods', [{}])[0], default=str)}"
            )

        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Mandatory data blocks (preserved from v1 + parans upgrade)
    # ─────────────────────────────────────────────────────────────────────────

    def _build_natal_block(self, ref: dict) -> str:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines = [f"TODAY: {today_str}  ← All timing must be AFTER this date.",
                 "=== MANDATORY NATAL DATA — USE THESE EXACT VALUES ==="
        ]
        lines.append("FORMAT: DEGREES° ARCMINUTES' SIGN  (e.g., '19° 43' Cancer')")
        lines.append("")

        ZODIAC = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                  "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        planet_order = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                        "Uranus","Neptune","Pluto","North Node","South Node",
                        "Chiron","Ascendant","Midheaven","Descendant","IC"]

        lines.append("--- PLANETARY POSITIONS ---")
        for planet in planet_order:
            data = ref.get(planet)
            if data and isinstance(data, dict):
                lines.append(f"{planet}: {data['dms']} {data['sign']}  (lon: {data['longitude']:.4f}°)")

        lines.append("")
        lines.append("--- ESSENTIAL CHART FACTORS ---")
        lines.append(f"Chart sect: {'Day chart' if ref.get('_is_day_chart') else 'Night chart'}")
        lines.append(f"Hyleg: {ref.get('_hyleg', 'Unknown')}")
        lines.append(f"Almuten: {ref.get('_almuten', 'Unknown')}")
        lines.append(f"Most dignified planet: {ref.get('_most_dignified', 'Unknown')} (score {ref.get('_most_dignified_score', 'N/A')})")
        lines.append(f"Dominant chart pattern: {ref.get('_dominant_pattern', 'None')}")
        lines.append("")
        lines.append("--- HELLENISTIC LOTS ---")
        lines.append(f"Lot of Fortune: {ref.get('_lot_fortune_sign', '?')} {ref.get('_lot_fortune_deg', '?')}")
        lines.append(f"Lot of Spirit:  {ref.get('_lot_spirit_sign', '?')}")
        lines.append("")
        lines.append("--- VEDIC FACTORS ---")
        lines.append(f"Atmakaraka:    {ref.get('_vedic_ak', 'Unknown')}")
        lines.append(f"Amatyakaraka:  {ref.get('_vedic_amatyakaraka', 'Unknown')}")
        lines.append(f"Darakaraka:    {ref.get('_vedic_darakaraka', 'Unknown')}")
        lines.append(f"Moon Nakshatra: {ref.get('_moon_nakshatra', 'Unknown')} pada {ref.get('_moon_pada', '?')}")
        lines.append("")
        lines.append("--- SAJU (BAZI) ---")
        if ref.get("_saju_available"):
            for pillar in ["Year", "Month", "Day", "Hour"]:
                val = ref.get(f"_saju_{pillar}", "?")
                lines.append(f"{pillar} Pillar: {val}")
            lines.append(f"Day Master: {ref.get('_dm_stem')} {ref.get('_dm_element')} — {ref.get('_dm_tier')}")
            lines.append(f"Useful God: {ref.get('_useful_god', '?')}")
        else:
            lines.append("Saju: UNAVAILABLE")
        lines.append("")
        lines.append("--- TIMING CONTEXT ---")
        lines.append(f"Maha Dasha: {ref.get('_maha_dasha')} ({ref.get('_dasha_years_left')} yrs remaining)")
        lines.append(f"Antardasha: {ref.get('_antar_dasha')} ({ref.get('_antar_dasha_years')} yrs remaining)")
        lines.append(f"Current Profection: {ref.get('_profection_sign')} "
                     f"(House {ref.get('_profection_house')}, Time Lord: {ref.get('_time_lord')})")
        lines.append("")
        lines.append("--- TRUE PARANS (RAMC horizon method) ---")
        parans = ref.get("_parans", [])[:6]
        if parans:
            for p in parans:
                lines.append(f"  • {p.get('interpretation', json.dumps(p, default=str))}")
        else:
            stars = ref.get("_significant_stars", ref.get("_fixed_stars", []))[:4]
            if stars:
                for s in stars:
                    lines.append(f"  • {s.get('interpretation', json.dumps(s, default=str))}")
            else:
                lines.append("  No star contacts above threshold")
        lines.append("")
        lines.append("--- HELIACAL EVENTS ---")
        for ev in ref.get("_heliacal_events", [])[:3]:
            lines.append(f"  • {ev.get('interpretation', str(ev))}")

        return "\n".join(lines)

    def _build_predictive_block(self, ref: dict, chart_data: dict) -> str:
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")

        w_pred    = chart_data.get("western", {}).get("predictive", {})
        profecs   = w_pred.get("profections_timeline", [])
        transits  = w_pred.get("transits_timeline", [])
        sr        = w_pred.get("solar_returns", [])[:5]
        sr_brief  = [{"year": s.get("year"), "asc": s.get("ascendant"),
                      "dom_house": s.get("dominant_house")} for s in sr]
        tajaka    = chart_data.get("vedic", {}).get("predictive", {}).get("tajaka", [])[:5]
        liu_nian  = chart_data.get("bazi", {}).get("predictive", {}).get("liu_nian_timeline", [])
        da_yun    = chart_data.get("bazi", {}).get("predictive", {}).get("da_yun", {})
        zr        = chart_data.get("hellenistic", {}).get("zodiacal_releasing", {})
        outer     = w_pred.get("outer_transit_aspects", {})

        lines = [f"TODAY: {today_str}  ← THIS IS THE HARD DATE BOUNDARY. NO DATES BEFORE THIS.",
                 "=== PREDICTIVE DATA BLOCK (Almanac sections) ==="
        ]
        lines.append("Do not re-diagnose the natal chart. Use natal positions only as brief anchors.")
        lines.append("")
        lines.append("--- NATAL ANCHORS (reference only) ---")
        for p in ["Sun", "Moon", "Ascendant", "Midheaven", "Saturn"]:
            if p in ref:
                d = ref[p]
                lines.append(f"{p}: {d.get('dms','?')} {d.get('sign','?')}")
        lines.append("")
        lines.append("--- ACTIVE TIME LORDS ---")
        lines.append(f"Maha Dasha: {ref.get('_maha_dasha')} ({ref.get('_dasha_years_left')} yrs remaining)")
        lines.append(f"Antardasha: {ref.get('_antar_dasha')} ({ref.get('_antar_dasha_years')} yrs remaining)")
        lines.append(f"Current Profection: {ref.get('_profection_sign')} "
                     f"(House {ref.get('_profection_house')}, Time Lord: {ref.get('_time_lord')})")
        if ref.get("_saju_available") and ref.get("_current_da_yun"):
            cyun = ref["_current_da_yun"]
            lines.append(f"Current Da Yun: {cyun.get('stem','?')}{cyun.get('branch','?')} "
                         f"({cyun.get('stem_element','?')}/{cyun.get('branch_element','?')}, "
                         f"age {cyun.get('start_age','?')}–{cyun.get('end_age','?')})")
        lines.append("")
        lines.append("--- PROFECTIONS 2026-2030 ---")
        lines.append(json.dumps(profecs, default=str, indent=None))
        lines.append("")
        lines.append("--- OUTER PLANET TRANSIT ASPECT HITS (exact dates) ---")
        if outer.get("summary_block"):
            lines.append(outer["summary_block"])
        else:
            lines.append(json.dumps(transits, default=str, indent=None))
        lines.append("")
        lines.append("--- SOLAR RETURNS ---")
        lines.append(json.dumps(sr_brief, default=str))
        lines.append("")
        lines.append("--- TAJAKA (VEDIC ANNUAL) ---")
        lines.append(json.dumps(tajaka, default=str, indent=None))
        lines.append("")
        lines.append("--- LIU NIAN (SAJU ANNUAL) ---")
        lines.append(json.dumps(liu_nian[:5], default=str, indent=None))
        lines.append("")
        lines.append("--- DA YUN CURRENT ---")
        lines.append(json.dumps(ref.get("_liu_nian", []), default=str, indent=None))
        lines.append("")
        lines.append("--- KAKSHYA TRANSITS ---")
        kakshya = chart_data.get("vedic", {}).get("predictive", {}).get("kakshya_transits", {})
        lines.append(json.dumps(kakshya, default=str, indent=None)[:1500])
        lines.append("")
        lines.append("--- PRIMARY DIRECTIONS (Key) ---")
        pd = chart_data.get("western", {}).get("predictive", {}).get("primary_directions", {})
        all_dirs = []
        for cat in pd.values():
            if isinstance(cat, list):
                all_dirs.extend(cat[:2])
        lines.append(json.dumps(all_dirs[:6], default=str, indent=None))

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Reference Position Extractor (preserved from v1)
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_reference_positions(self, chart_data: dict) -> dict:
        ref = {}
        w   = chart_data.get("western", {}).get("natal", {})
        for planet, data in w.get("placements", {}).items():
            if isinstance(data, dict):
                sign = data.get("sign") or data.get("sign_name", "")
                deg  = data.get("degree") or data.get("deg_in_sign", 0) or 0
                lon  = data.get("longitude") or data.get("lon", 0) or 0
                if sign:
                    ref[planet] = {
                        "sign":      sign,
                        "degree":    round(float(deg), 4),
                        "longitude": round(float(lon), 4),
                        "dms":       _deg_to_dms(float(deg))
                    }
        for angle, data in w.get("angles", {}).items():
            if isinstance(data, dict):
                sign = data.get("sign", "")
                deg  = data.get("degree") or data.get("deg_in_sign", 0) or 0
                lon  = data.get("longitude") or data.get("lon", 0) or 0
                if sign:
                    ref[angle] = {
                        "sign":      sign,
                        "degree":    round(float(deg), 4),
                        "longitude": round(float(lon), 4),
                        "dms":       _deg_to_dms(float(deg))
                    }

        vedic = chart_data.get("vedic", {}).get("natal", {})
        ref["_vedic_ak"]           = vedic.get("chara_karakas", {}).get("Atmakaraka",   "Unknown")
        ref["_vedic_amatyakaraka"] = vedic.get("chara_karakas", {}).get("Amatyakaraka", "Unknown")
        ref["_vedic_darakaraka"]   = vedic.get("chara_karakas", {}).get("Darakaraka",   "Unknown")

        moon_v = vedic.get("placements", {}).get("Moon", {})
        ref["_moon_nakshatra"] = moon_v.get("nakshatra", "Unknown")
        ref["_moon_pada"]      = moon_v.get("pada",      "Unknown")

        dasha = chart_data.get("vedic", {}).get("predictive", {}).get("vimshottari", {})
        ref["_maha_dasha"]         = dasha.get("maha_lord",              "Unknown")
        ref["_dasha_years_left"]   = dasha.get("approx_remaining_years", "Unknown")
        ref["_antar_dasha"]        = dasha.get("antar_lord",             "Unknown")
        ref["_antar_dasha_years"]  = dasha.get("antar_remaining_years",  "Unknown")

        strength = chart_data.get("bazi", {}).get("strength", {})
        dm       = strength.get("day_master", {})
        dm_stem  = dm.get("stem",    "")
        dm_elem  = dm.get("element", "")
        if dm_stem and dm_elem and dm_elem not in ("", "Unknown"):
            ref["_saju_available"] = True
            ref["_dm_stem"]        = dm_stem
            ref["_dm_element"]     = dm_elem
            ref["_dm_tier"]        = strength.get("tier",       "Unknown")
            ref["_useful_god"]     = strength.get("useful_god", "Unknown")
        else:
            ref["_saju_available"] = False
            ref["_dm_stem"]        = "UNAVAILABLE"
            ref["_dm_element"]     = "UNAVAILABLE"
            ref["_dm_tier"]        = "UNAVAILABLE"
            ref["_useful_god"]     = "UNAVAILABLE"

        pillars = chart_data.get("bazi", {}).get("natal", {}).get("pillars", {})
        for pname, pdata in pillars.items():
            if isinstance(pdata, dict):
                stem   = pdata.get("stem",         "?")
                branch = pdata.get("branch",        "?")
                s_el   = pdata.get("stem_element",  "?")
                b_el   = pdata.get("branch_element","?")
                void   = " [VOID]" if pdata.get("is_void") else ""
                ref[f"_saju_{pname}"] = f"{stem}{branch} ({s_el}/{b_el}){void}"

        da_yun    = chart_data.get("bazi", {}).get("predictive", {}).get("da_yun", {})
        yun_pills = da_yun.get("pillars", [])
        if yun_pills:
            ref["_current_da_yun"] = yun_pills[0]
        liu_nian = chart_data.get("bazi", {}).get("predictive", {}).get("liu_nian_timeline", [])
        ref["_liu_nian"] = liu_nian[:5]

        hell    = chart_data.get("hellenistic", {})
        lots    = hell.get("lots", {})
        fortune = lots.get("fortune", {})
        spirit  = lots.get("spirit",  {})
        prof    = hell.get("annual_profections", {})

        ref["_lot_fortune_sign"] = fortune.get("sign", "Unknown")
        ref["_lot_fortune_deg"]  = (_deg_to_dms(fortune.get("longitude", 0) % 30)
                                    if fortune.get("longitude") else "Unknown")
        ref["_lot_spirit_sign"]  = spirit.get("sign", "Unknown")
        ref["_is_day_chart"]     = fortune.get("is_day_chart", True)
        ref["_profection_sign"]  = prof.get("profected_sign",  "Unknown")
        ref["_profection_house"] = prof.get("activated_house", "Unknown")
        ref["_time_lord"]        = prof.get("time_lord",        "Unknown")
        ref["_hyleg"]            = hell.get("hyleg", "Unknown")

        patterns = w.get("patterns", {})
        ref["_patterns_summary"]  = patterns.get("summary", {})
        ref["_dominant_pattern"]  = patterns.get("summary", {}).get("dominant_pattern", "None")

        # Paran data — prefer true RAMC parans, fall back to conjunctions
        paran_data = w.get("parans", {})
        if isinstance(paran_data, dict):
            true_parans = paran_data.get("natal_parans", [])
            conj_parans = paran_data.get("conjunctions", [])
            ref["_parans"]           = (true_parans or conj_parans)[:8]
            ref["_significant_stars"] = paran_data.get("significant_stars", [])[:6]
            ref["_heliacal_events"]  = paran_data.get("heliacal_events", [])[:4]
        else:
            ref["_parans"]           = []
            ref["_significant_stars"] = w.get("significant_stars", [])[:6]
            ref["_heliacal_events"]  = w.get("heliacal_events", [])[:4]

        pd       = chart_data.get("western", {}).get("predictive", {}).get("primary_directions", {})
        all_dirs = []
        for cat in pd.values():
            if isinstance(cat, list):
                all_dirs.extend(cat[:2])
        ref["_primary_directions"] = all_dirs[:4]

        syzygy = w.get("syzygy", {})
        ref["_syzygy_type"]       = syzygy.get("type",            "Unknown")
        ref["_syzygy_sign"]       = syzygy.get("sign",            "Unknown")
        ref["_syzygy_days_before"]= syzygy.get("days_before_birth","Unknown")

        dignities   = w.get("dignities", {})
        pd_dig      = dignities.get("planet_dignities", {})
        ref["_almuten"] = dignities.get("almuten", {}).get("almuten", "Unknown")
        best_p, best_s = None, -99
        for p, d in pd_dig.items():
            if isinstance(d, dict) and d.get("total_score", -99) > best_s:
                best_s = d.get("total_score", -99)
                best_p = p
        ref["_most_dignified"]       = best_p or "Unknown"
        ref["_most_dignified_score"] = best_s

        dodec     = hell.get("dodecatemoria", {})
        dodec_sum = dodec.get("summary", {})
        ref["_dodec_dominant_sign"]  = dodec_sum.get("dominant_dodecatemoria_sign",   "Unknown")
        ref["_dodec_dominant_ruler"] = dodec_sum.get("dominant_dodecatemoria_ruler",  "Unknown")
        ref["_dodec_own_planets"]    = dodec_sum.get("own_dodecatemoria_planets",     {})

        return ref

    # ─────────────────────────────────────────────────────────────────────────
    # Header
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_header(self, metadata: dict, chart_data: dict = None,
                         ref: dict = None) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        name      = metadata.get("name", "Unknown")
        loc       = metadata.get("location", "")
        bt        = metadata.get("birth_time", "")

        # Extract key chart signature for subtitle
        sun_sign  = ""
        moon_sign = ""
        asc_sign  = ""
        if ref:
            sun_sign  = ref.get("Sun",       {}).get("sign", "") if isinstance(ref.get("Sun"), dict) else ""
            moon_sign = ref.get("Moon",      {}).get("sign", "") if isinstance(ref.get("Moon"), dict) else ""
            asc_sign  = ref.get("Ascendant", {}).get("sign", "") if isinstance(ref.get("Ascendant"), dict) else ""
        sig = f"{sun_sign} Sun · {moon_sign} Moon · {asc_sign} Ascendant" if all([sun_sign, moon_sign, asc_sign]) else ""

        return f"""# THE CELESTIAL DOSSIER
## {name}

{f'*{sig}*' if sig else ''}

**Prepared:** {timestamp}  
**Birth:** {bt} · {loc}  
**Systems:** Western Tropical · Vedic Sidereal · Saju (Bazi) · Hellenistic  
**Methods:** Primary Directions (Regiomontanus) · Vimshottari Dasha · Annual Profections · Tajaka · Kakshya · True RAMC Parans

---

*This dossier synthesises four independent astrological traditions into a single coherent portrait.
Where systems agree, confidence is high. Where they diverge, both signals are named and weighted.*

---

"""

    # ─────────────────────────────────────────────────────────────────────────
    # Enforcement & Validation (preserved from v1)
    # ─────────────────────────────────────────────────────────────────────────

    def _enforce_section_header(self, content: str, sd: dict) -> str:
        expected = f"# {sd['header']}"
        if not content.strip().startswith(expected):
            content = f"{expected}\n\n" + content.lstrip()
        return content

    def _validate_degrees_internal(self, content: str, ref: dict, sec_num: int) -> str:
        """
        Find and FIX degree hallucinations in natal/oracle sections.
        Replaces wrong degree strings with the verified value from the ref dict.
        Returns corrected content.

        Strategy: if LLM writes "12° 33' Leo" but ref shows Sun at 27° 10' Leo,
        and no other planet is in Leo, we replace the wrong value with the correct one.
        Only corrects when match is unambiguous (exactly one planet in that sign).
        """
        sd = SECTION_DEFS.get(sec_num, {})
        if sd.get("type") not in ("natal", "oracle"):
            return content

        # Build sign → [(planet, degree, dms)] lookup
        sign_to_planets: dict = {}
        for planet, data in ref.items():
            if not isinstance(data, dict):
                continue
            sign = data.get("sign", "")
            if not sign:
                continue
            sign_to_planets.setdefault(sign, []).append({
                "planet":  planet,
                "degree":  data.get("degree", 0),
                "dms":     data.get("dms", _deg_to_dms(data.get("degree", 0))),
            })

        pattern = r'(\d{1,2})°\s*(\d{2})\'?\s*([A-Z][a-z]+)'
        corrections = 0

        def _replace_match(m: re.Match) -> str:
            nonlocal corrections
            claimed_d    = int(m.group(1))
            claimed_m    = int(m.group(2))
            claimed_sign = m.group(3)
            claimed_dec  = claimed_d + claimed_m / 60.0
            original     = m.group(0)

            planets_in_sign = sign_to_planets.get(claimed_sign, [])
            if not planets_in_sign:
                return original  # Unknown sign label — leave it

            if len(planets_in_sign) == 1:
                # Unambiguous: exactly one body in this sign
                truth = planets_in_sign[0]
                delta = abs(claimed_dec - truth["degree"])
                if delta > 1.0:
                    correct_str = f"{truth['dms']}' {claimed_sign}"
                    logger.info(
                        f"Sec{sec_num} DEGREE FIX: {original} → {correct_str} "
                        f"({truth['planet']}, delta {delta:.2f}°)"
                    )
                    corrections += 1
                    return correct_str
            else:
                # Multiple planets in same sign — find closest match
                best = min(planets_in_sign, key=lambda p: abs(p["degree"] - claimed_dec))
                delta = abs(claimed_dec - best["degree"])
                if delta > 2.0:  # Higher threshold when ambiguous
                    correct_str = f"{best['dms']}' {claimed_sign}"
                    logger.info(
                        f"Sec{sec_num} DEGREE FIX (ambiguous): {original} → {correct_str} "
                        f"(best match {best['planet']}, delta {delta:.2f}°)"
                    )
                    corrections += 1
                    return correct_str

            return original

        corrected = re.sub(pattern, _replace_match, content)
        if corrections:
            logger.info(f"Sec{sec_num}: corrected {corrections} hallucinated degree(s)")
        return corrected

    # ─────────────────────────────────────────────────────────────────────────
    # Post-generation banned-words audit
    # ─────────────────────────────────────────────────────────────────────────

    def _audit_banned_words(self, content: str, sec_num: int) -> str:
        """
        Scan generated text for banned words and log violations.
        Does NOT modify the text (that would corrupt prose) — only logs so
        you can track which prompts need tightening.

        Banned words are those that signal vague, padded, or un-grounded writing:
        the kind that made the original report feel "accurate but boring."
        """
        BANNED = {
            # Cosmic fluff
            "journey", "tapestry", "dance", "weave", "cosmic", "realm",
            "vibration", "manifest", "manifestation", "universe",
            # Weasel hedges
            "potential", "perhaps", "maybe", "might suggest",
            # Agency-free descriptors
            "deeply", "truly", "intricate", "multifaceted", "dynamic interplay",
            "embody", "explore",
            # Encouragement language (wrong tone for this report)
            "trust yourself", "remember that", "you deserve", "nurture",
        }
        # Tone-skew tracking (not banned, but flagged if overused together)
        TONE_SKEW = [
            "trap", "wound", "ceiling", "sabotage", "rupture",
            "collapse", "rubble", "dismantl", "isolat", "destabil",
        ]

        sd_id    = SECTION_DEFS.get(sec_num, {}).get("id", f"sec{sec_num}")
        lower    = content.lower()
        found    = []
        for word in BANNED:
            # Case-insensitive whole-word check
            pattern = r"\b" + re.escape(word) + r"\b"
            matches = re.findall(pattern, lower)
            if matches:
                found.append(f"'{word}' ×{len(matches)}")

        if found:
            logger.warning(
                f"Sec{sec_num} ({sd_id}) BANNED WORDS DETECTED: {', '.join(found)}"
            )
        else:
            logger.info(f"Sec{sec_num} ({sd_id}) banned-word audit: CLEAN")

        # Tone skew audit — warn if negative-coded words appear 4+ times together
        skew_hits = []
        for word in TONE_SKEW:
            import re as _re
            pat = r"\b" + _re.escape(word)
            hits = _re.findall(pat, lower)
            if hits:
                skew_hits.append(f"'{word}' ×{len(hits)}")
        if len(skew_hits) >= 4:
            logger.warning(
                f"Sec{sec_num} ({sd_id}) TONE SKEW — heavy negative framing: "
                f"{', '.join(skew_hits)}"
            )

        return content  # always return unchanged

    def _audit_past_dates(self, content: str, sec_num: int) -> str:
        """
        For the questions section only: scan for past-year citations and log them.
        Does NOT modify content — logs violations so you can see if the LLM ignored the date rule.
        """
        today = datetime.now(timezone.utc)
        current_year = today.year

        sd_id = SECTION_DEFS.get(sec_num, {}).get("id", f"sec{sec_num}")
        if sd_id != "questions":
            return content

        # Find all 4-digit year patterns in the text
        year_mentions = re.findall(r'\b(20\d{2})\b', content)
        past_years = [y for y in year_mentions if int(y) < current_year]

        if past_years:
            unique_past = sorted(set(past_years))
            logger.error(
                f"PAST DATE VIOLATION in questions section: "
                f"Past years cited: {unique_past}. "
                f"Today is {today.strftime('%Y-%m-%d')}. "
                f"These dates should not appear in answers."
            )
        else:
            logger.info(f"Questions date audit: CLEAN — no past years found.")

        return content
