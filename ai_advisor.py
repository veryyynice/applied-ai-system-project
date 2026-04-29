"""
AI Schedule Advisor — agentic reasoning layer for PawPal+

Sends the current schedule + pet health context to Claude, which:
  1. Explains why tasks are ordered the way they are
  2. Flags any health concerns based on pet conditions / allergies
  3. Returns a confidence score (1-5) rating how complete the plan looks
  4. Suggests anything that might be missing

This is the "agentic" component: the AI receives state, reasons about it,
checks its own output for health flags, and returns a structured verdict.
"""

import logging
import os

import anthropic

logger = logging.getLogger(__name__)


def analyze_schedule(plan, owner, scheduler) -> dict:
    """Run the AI advisor on the current daily plan.

    Args:
        plan:      Ordered list of Task objects from generate_daily_plan()
        owner:     The Owner object (used for notification preference)
        scheduler: The Scheduler (used to pull all pet health info)

    Returns:
        dict with keys:
            explanation  (str)  — natural language breakdown of the schedule
            health_flags (list) — any health concerns spotted
            confidence   (int)  — 1–5 score on how solid the plan looks
            suggestions  (str)  — anything the AI thinks is missing
            error        (str)  — only set if the API call failed
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — AI advisor skipped")
        return {
            "explanation": "AI advisor unavailable (no API key set).",
            "health_flags": [],
            "confidence": 0,
            "suggestions": "",
            "error": "ANTHROPIC_API_KEY environment variable not set.",
        }

    # Build context strings
    pet_info_lines = []
    for pet in owner.pets:
        health = []
        if pet.conditions:
            health.append(f"conditions: {', '.join(pet.conditions)}")
        if pet.allergies:
            health.append(f"allergies: {', '.join(pet.allergies)}")
        if pet.days_since_groomed > 7:
            health.append(f"overdue for grooming ({pet.days_since_groomed} days)")
        pet_info_lines.append(
            f"- {pet.name} ({pet.breed} {pet.species}, {pet.age_years}yr)"
            + (f" — {'; '.join(health)}" if health else "")
        )

    task_lines = []
    for i, task in enumerate(plan, 1):
        pet = next((p for p in owner.pets if p.id == task.pet_id), None)
        due = task.due_time.strftime("%I:%M %p") if task.due_time else "no time set"
        task_lines.append(
            f"{i}. {task.name} for {pet.name if pet else '?'} "
            f"@ {due} | {task.duration_mins} min | priority {task.priority}/5 | {task.frequency}"
        )

    conflicts = scheduler.get_conflicts()
    conflict_section = (
        "CONFLICTS DETECTED:\n" + "\n".join(f"- {c}" for c in conflicts)
        if conflicts
        else "No scheduling conflicts."
    )

    prompt = f"""You are a practical pet care advisor. Review this owner's daily pet care schedule and give a quick, honest assessment.

OWNER: {owner.name} (notifications via {owner.notification_preference})

PETS:
{chr(10).join(pet_info_lines) if pet_info_lines else "No pets registered."}

TODAY'S PLAN ({len(plan)} tasks, sorted by priority then time):
{chr(10).join(task_lines) if task_lines else "No tasks scheduled."}

{conflict_section}

Respond in this exact format (keep each section brief — 1-3 sentences max):

EXPLANATION: [Why is this order reasonable? What's driving the priority ordering?]

HEALTH FLAGS: [Any concerns given the pets' conditions/allergies? Write "None" if clear.]

CONFIDENCE: [A number from 1-5. 5 = solid plan, 1 = missing critical tasks or major issues.]

SUGGESTIONS: [Anything obviously missing or that should be added? Write "None" if the plan looks complete.]"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        logger.info("AI advisor response received (%d chars)", len(raw))
        return _parse_response(raw)

    except anthropic.AuthenticationError:
        logger.error("Invalid Anthropic API key")
        return {
            "explanation": "",
            "health_flags": [],
            "confidence": 0,
            "suggestions": "",
            "error": "Invalid API key. Check your ANTHROPIC_API_KEY.",
        }
    except Exception as exc:
        logger.error("AI advisor failed: %s", exc)
        return {
            "explanation": "",
            "health_flags": [],
            "confidence": 0,
            "suggestions": "",
            "error": f"AI advisor error: {exc}",
        }


def _parse_response(raw: str) -> dict:
    """Parse the structured text response from Claude into a dict."""
    sections = {"EXPLANATION": "", "HEALTH FLAGS": "", "CONFIDENCE": "0", "SUGGESTIONS": ""}

    for key in sections:
        marker = f"{key}:"
        if marker in raw:
            after = raw.split(marker, 1)[1]
            # Take text until the next section header or end of string
            next_marker = None
            for other_key in sections:
                if other_key != key and f"{other_key}:" in after:
                    idx = after.index(f"{other_key}:")
                    if next_marker is None or idx < next_marker:
                        next_marker = idx
            value = after[:next_marker].strip() if next_marker else after.strip()
            sections[key] = value

    # Parse confidence as int
    try:
        confidence = int("".join(c for c in sections["CONFIDENCE"] if c.isdigit())[:1])
    except (ValueError, IndexError):
        confidence = 0

    # Parse health flags into a list
    flags_raw = sections["HEALTH FLAGS"]
    if flags_raw.lower() in ("none", "none.", ""):
        flags = []
    else:
        flags = [f.strip("- •").strip() for f in flags_raw.split("\n") if f.strip()]

    return {
        "explanation": sections["EXPLANATION"],
        "health_flags": flags,
        "confidence": confidence,
        "suggestions": sections["SUGGESTIONS"],
        "error": None,
    }
