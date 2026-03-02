"""
Fates Engine API + interactive CLI.

Two ways to use:
  1. FastAPI (POST /generate) — pass user_questions in JSON body
  2. CLI (python main.py) — interactively prompts for birth data + up to 5 questions
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from orchestrator import orchestrator


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Fates Engine API",
    description="Multi-system astrological report generation with query architecture",
    version="2.1.0"
)


class ChartRequest(BaseModel):
    birth_datetime: str            # "1993-07-19 20:44"
    location: str                  # "Singapore, Singapore"
    gender: Optional[str] = "unspecified"
    name: Optional[str] = "Unknown"
    output_dir: Optional[str] = "./reports"
    user_questions: Optional[List[str]] = None
    # Up to 5 questions that reshape the entire report.
    # Example:
    # [
    #   "Will I become wealthy, and if so when?",
    #   "Should I start my own business or stay employed?",
    #   "When will I meet my life partner?",
    #   "Is 2027 a good year to relocate abroad?",
    #   "What is my greatest natural strength?"
    # ]
    # Leave blank or omit for a standard (non-query-driven) report.


class ChartResponse(BaseModel):
    report_path: str
    summary: str
    systems_analyzed: list
    themes_detected: list
    status: str


@app.post("/generate", response_model=ChartResponse)
async def generate_report(request: ChartRequest):
    """
    Generate a full astrological dossier.

    If user_questions is provided, the QueryEngine extracts themes and steers
    every section of the report toward the user's specific questions, then
    appends Part IV (direct Q&A verdicts) at the end.
    """
    try:
        themes_detected = []
        if request.user_questions:
            from query_engine import QueryEngine, THEMES
            ctx = QueryEngine().process(request.user_questions)
            if ctx:
                themes_detected = [
                    THEMES[t]["label"]
                    for t in ctx.get("themes", [])
                    if t in THEMES
                ]

        path = orchestrator.generate_report(
            birth_datetime=request.birth_datetime,
            location=request.location,
            gender=request.gender,
            name=request.name,
            output_dir=request.output_dir,
            user_questions=request.user_questions,
        )

        qs = request.user_questions or []
        summary = (
            f"Query-driven report — {len(qs)} questions answered throughout"
            if qs else
            "Standard multi-system analysis complete"
        )

        return {
            "report_path": path,
            "summary": summary,
            "systems_analyzed": ["Western", "Vedic", "Saju", "Hellenistic"],
            "themes_detected": themes_detected,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "engine": "Fates Core v2.1 — Query Architecture",
        "models": ["gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-2.5-pro"],
        "query_architecture": "enabled",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Interactive CLI
# ─────────────────────────────────────────────────────────────────────────────

def _prompt_questions() -> list:
    """Interactively collect up to 5 questions from the user."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║            BEFORE WE BEGIN — YOUR QUESTIONS                 ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  You can ask up to 5 questions. The entire report will be   ║")
    print("║  shaped around your answers — every section will prioritize ║")
    print("║  the mechanisms most relevant to what you asked.            ║")
    print("║                                                              ║")
    print("║  Example questions:                                          ║")
    print("║  • Will I become wealthy, and if so when?                   ║")
    print("║  • Should I start my own business?                          ║")
    print("║  • When will I meet my life partner?                        ║")
    print("║  • Is 2027 a good year to relocate?                         ║")
    print("║  • What is my greatest natural strength?                    ║")
    print("║                                                              ║")
    print("║  Press Enter to skip any question.                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    questions = []
    for i in range(1, 6):
        try:
            q = input(f"  Q{i}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q:
            questions.append(q)

    if questions:
        print()
        print(f"  ✓ {len(questions)} question{'s' if len(questions) > 1 else ''} received.")
        from query_engine import QueryEngine, THEMES
        ctx = QueryEngine().process(questions)
        if ctx and ctx.get("themes"):
            labels = [
                f"{THEMES[t]['color']} {THEMES[t]['label']}"
                for t in ctx["themes"] if t in THEMES
            ]
            print(f"  Themes detected: {', '.join(labels)}")
        print("  Every section of the report will be shaped around these questions.")
        print("  Part IV will give you direct verdicts on each one.")
    else:
        print("  No questions — generating standard report.")

    print()
    return questions


def _collect_birth_data() -> dict:
    """Interactively collect birth data."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         FATES ENGINE v2.1 — Query Architecture              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    try:
        name           = input("  Name: ").strip() or "Unknown"
        birth_datetime = input("  Birth datetime (YYYY-MM-DD HH:MM): ").strip()
        location       = input("  Birth location (City, Country): ").strip()
        gender         = input("  Gender (optional, press Enter to skip): ").strip() or "unspecified"
        output_dir     = input("  Output directory [./reports]: ").strip() or "./reports"
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        raise SystemExit(0)
    return {
        "name": name,
        "birth_datetime": birth_datetime,
        "location": location,
        "gender": gender,
        "output_dir": output_dir,
    }


def run_cli():
    """Interactive CLI entry point."""
    birth_data = _collect_birth_data()
    questions  = _prompt_questions()

    print("🔮 Starting generation...\n")

    path = orchestrator.generate_report(
        birth_datetime=birth_data["birth_datetime"],
        location=birth_data["location"],
        gender=birth_data["gender"],
        name=birth_data["name"],
        output_dir=birth_data["output_dir"],
        user_questions=questions if questions else None,
    )

    print(f"\n✨ Done. Report: {path}")
    if questions:
        print(f"   Your {len(questions)} question(s) shaped every section.")
        print(f"   See Part IV for direct verdicts.")


if __name__ == "__main__":
    import sys
    if "--api" in sys.argv:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        run_cli()
