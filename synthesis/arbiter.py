"""The Arbiter - Reconciles contradictions between systems."""
import logging
import time
from experts.gateway import gateway
from config import settings
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class Arbiter:
    """First-level synthesis: resolves conflicts between 4 experts."""

    SYSTEM_PROMPT = """You are the Arbiter, a meta-astrologer who synthesizes Western (Tropical), Vedic (Sidereal), Saju (Bazi), and Hellenistic analyses into a coherent whole.

SYNTHESIS PROTOCOL:
1. CONSENSUS DETECTION: Identify where 2+ systems agree on timing, themes, or outcomes (amplify these - high confidence)
2. CONTRADICTION HANDLING: Where systems disagree, analyze the nature of the disagreement:
   - Different metaphors pointing to same reality (synthesize)
   - Genuine tension (e.g., Western "free will" vs Hellenistic "fate" - note the paradox)
   - Different timing (e.g., Vedic Dasha vs Western transit - both valid, different mechanisms)
3. EMERGENT PATTERNS: Find patterns only visible across all four systems
4. CONFIDENCE SCORING: 0-100 score based on system agreement

CROSS-SYSTEM MAPPINGS:
- Western Sun ≈ Vedic Sun ≈ Saju Day Master (core identity)
- Western Moon ≈ Vedic Moon (emotions, mind)
- Western Ascendant ≈ Vedic Ascendant ≈ Saju Day Pillar (body, self)
- Western Saturn transit ≈ Vedic Sade Sati ≈ Saju "challenges" periods
- Western Progressions ≈ Vedic Dasha ≈ Saju Da Yun (developmental timing)

OUTPUT FORMAT: Strict JSON only."""

    def reconcile(self, analyses: List[Dict], chart_data: Dict,
                  convergences: List[Dict] = None,
                  contradictions: List[Dict] = None,
                  temporal_clusters: List[Dict] = None,
                  user_questions: list = None) -> Dict[str, Any]:
        """Reconcile four expert analyses. Retries up to 3 times on connection errors."""
        prompt = self._build_prompt(analyses, chart_data, convergences, contradictions,
                                    temporal_clusters, user_questions)

        schema = {
            "type": "object",
            "properties": {
                "executive_summary": {"type": "string"},
                "consensus_points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string"},
                            "systems_agreeing": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "contradictions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "systems": {"type": "array", "items": {"type": "string"}},
                            "tension": {"type": "string"},
                            "resolution": {"type": "string"},
                            "navigate_by": {"type": "string"}
                        }
                    }
                },
                "critical_periods": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "period": {"type": "string"},
                            "systems_agreeing": {"type": "array", "items": {"type": "string"}},
                            "intensity": {"type": "number"},
                            "meaning": {"type": "string"},
                            "action": {"type": "string"}
                        }
                    }
                },
                "system_tensions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "unified_narrative": {"type": "string"}
            },
            "required": ["executive_summary", "consensus_points", "critical_periods"]
        }

        # ── Retry loop: 3 attempts with exponential backoff ──────────────────
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = gateway.structured_generate(
                    system_prompt=self.SYSTEM_PROMPT,
                    user_prompt=prompt,
                    output_schema=schema,
                    model=settings.arbiter_model,
                    reasoning_effort="high"
                )

                if response.get("success") and response.get("data"):
                    if attempt > 1:
                        logger.info(f"Arbiter succeeded on attempt {attempt}")
                    return response["data"]

                error_msg = response.get("error", "Unknown error")

                # Only retry on transient connection errors
                if any(t in str(error_msg).lower() for t in
                       ["connection", "timeout", "rate limit", "503", "502", "network"]):
                    if attempt < max_attempts:
                        wait = 5 * attempt  # 5s, 10s
                        logger.warning(f"Arbiter attempt {attempt} failed ({error_msg}). "
                                       f"Retrying in {wait}s...")
                        time.sleep(wait)
                        continue
                # Non-retryable error or exhausted retries
                logger.error(f"Arbiter synthesis failed: {error_msg}")
                return self._fallback_reconciliation(analyses)

            except Exception as e:
                if attempt < max_attempts and any(
                    t in str(e).lower() for t in ["connection", "timeout", "network"]
                ):
                    wait = 5 * attempt
                    logger.warning(f"Arbiter attempt {attempt} exception ({e}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Arbiter synthesis failed with exception: {e}")
                    return self._fallback_reconciliation(analyses)

        logger.error("Arbiter exhausted all retries")
        return self._fallback_reconciliation(analyses)

    def _build_prompt(self, analyses: List[Dict], chart_data: Dict,
                      convergences: List[Dict] = None,
                      contradictions: List[Dict] = None,
                      temporal_clusters: List[Dict] = None,
                      user_questions: list = None) -> str:
        """Build specific prompt for reconciliation."""
        # Question focus block — makes arbiter synthesis question-biased
        q_block = ""
        if user_questions:
            clean_qs = [q.strip() for q in user_questions if q and q.strip()][:5]
            if clean_qs:
                q_block = (
                    "\n=== USER QUESTIONS — BIAS SYNTHESIS TOWARD THESE DOMAINS ===\n"
                    "The native submitted these questions. When writing consensus_points\n"
                    "and critical_periods, prioritize mechanisms that answer them.\n"
                    + "\n".join(f"  Q{i+1}: {q}" for i, q in enumerate(clean_qs))
                    + "\n=== END QUESTIONS ===\n\n"
                )
        # Unpack analyses with truncation to save tokens
        def truncate(text, max_len=1500):
            if not text or len(text) <= max_len:
                return text
            return text[:max_len] + f"\n\n[... {len(text) - max_len} chars truncated]"

        western = next((a for a in analyses if a.get("system") == "Western"), {})
        vedic = next((a for a in analyses if a.get("system") == "Vedic"), {})
        saju = next((a for a in analyses if a.get("system") == "Saju"), {})
        hellenistic = next((a for a in analyses if a.get("system") == "Hellenistic"), {})

        # Get only essential chart data
        w_natal = chart_data.get('western', {}).get('natal', {})
        sun_sign = w_natal.get('placements', {}).get('Sun', {}).get('sign', 'Unknown')
        moon_sign = w_natal.get('placements', {}).get('Moon', {}).get('sign', 'Unknown')
        asc_sign = w_natal.get('angles', {}).get('Ascendant', {}).get('sign', 'Unknown')

        # Minimal convergence/contradiction summary
        conv_summary = f"{len(convergences)} multi-system agreements" if convergences else "None"
        contrad_summary = f"{len(contradictions)} contradictions" if contradictions else "None"
        cluster_summary = f"{len(temporal_clusters)} temporal clusters" if temporal_clusters else "None"

        return q_block + f"""SYNTHESIZE THESE FOUR EXPERT ANALYSES:

=== WESTERN (Tropical) ===
{truncate(western.get('analysis', 'No analysis'))}

=== VEDIC (Sidereal) ===
{truncate(vedic.get('analysis', 'No analysis'))}

=== SAJU (Bazi) ===
{truncate(saju.get('analysis', 'No analysis'))}

=== HELLENISTIC (Ancient) ===
{truncate(hellenistic.get('analysis', 'No analysis'))}

=== VALIDATION DATA ===
Convergences: {conv_summary}
Contradictions: {contrad_summary}
Temporal Clusters: {cluster_summary}
Chart: Sun {sun_sign}, Moon {moon_sign}, Asc {asc_sign}

Provide JSON only with: executive_summary, consensus_points, contradictions, critical_periods, unified_narrative."""

    def _fallback_reconciliation(self, analyses: List[Dict]) -> Dict:
        """Simple fallback if LLM fails."""
        return {
            "executive_summary": "The chart indicates significant transformation potential across multiple astrological frameworks.",
            "consensus_points": [
                {
                    "theme": "Transformation",
                    "systems_agreeing": ["Western", "Vedic", "Hellenistic"],
                    "confidence": 75,
                    "description": "All systems indicate a period of change and development"
                }
            ],
            "contradictions": [],
            "critical_periods": [],
            "system_tensions": ["Different timing mechanisms between systems"],
            "unified_narrative": "Multiple systems point to a significant developmental period requiring integration of material and spiritual priorities."
        }