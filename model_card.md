# Model Card: PawPal+ AI Schedule Advisor

---

## Model Overview

**Model used:** `claude-haiku-4-5-20251001` (Anthropic)
**Task:** Agentic schedule analysis for pet care planning
**Input:** A pet owner's daily task list + pet health info (conditions, allergies, grooming status)
**Output:** Natural language explanation of the schedule ordering, health flags, a confidence score (1–5), and suggestions for missing tasks

The AI advisor is the "agentic" component of PawPal+. It doesn't just generate text — it reasons about the schedule, checks for health concerns given the specific pet's conditions, rates how complete the plan looks, and suggests what might be missing. It's not fine-tuned; it uses Claude's general knowledge combined with structured pet-specific context I pass in the prompt.

---

## How It Works

When the user clicks "Get AI Analysis," `ai_advisor.py` builds a prompt that includes:
- The owner's name and notification preference
- Each pet's name, species, breed, age, conditions, and allergies
- The full daily plan in priority order (task name, pet, due time, duration, frequency)
- Any active conflict warnings

Claude haiku receives this and returns a structured response with four labeled sections: EXPLANATION, HEALTH FLAGS, CONFIDENCE, SUGGESTIONS. The code then parses that response into a Python dict and displays it in the Streamlit UI.

I used haiku instead of sonnet/opus because the prompt is short and the task is straightforward — it doesn't need a ton of reasoning depth. Haiku is faster and cheaper for this use case.

---

## Evaluation

I tested the AI advisor manually on 5 different schedules:

| Test case | Expected behavior | Result |
|---|---|---|
| Pet with asthma, no inhaler on schedule | Flag missing medication | Flagged ✓ |
| Two pets, tasks out of priority order | Explain the ordering | Explained correctly ✓ |
| Overdue grooming (14 days) | Flag as concern | Flagged ✓ |
| Empty schedule (no tasks) | Say the plan is incomplete | Confidence 1-2, suggested adding tasks ✓ |
| Clean schedule, no health issues | Return "None" for flags | Returned "None" ✓ |

**5/5 manual scenarios behaved as expected.**

The confidence scores made sense across tests — a well-structured schedule with no health issues got 4–5, a sparse one with missing tasks got 2–3.

---

## Limitations

- **Not veterinary advice.** Claude's pet health knowledge comes from general training data, not veterinary literature. If someone has a pet with a rare or complex condition, the advice might be generic or even wrong. This app should never be used as a substitute for an actual vet.
- **Consecutive-pair conflict detection only.** The scheduler checks consecutive pairs in the sorted task list, so it can miss non-adjacent overlaps. The AI advisor doesn't have visibility into this limitation — it just sees the plan as given.
- **No date awareness.** The scheduler uses `time` objects, not `datetime`. So recurring tasks don't actually know what day they're scheduled for — the AI advisor can't flag "you're scheduling a grooming session for Sunday when you said you're unavailable." That would need a date system added.
- **English only.** The prompt and response are in English. No internationalization.
- **Hallucination risk.** Like any LLM, Claude can occasionally produce plausible-sounding but incorrect health advice. The structured prompt format reduces this, but doesn't eliminate it.

---

## Ethical Considerations

**Misuse potential:** The health flag output could be mistaken for actual medical guidance. A responsible version of this product would add a clear disclaimer ("This is not veterinary advice") and possibly rate-limit how often users can run AI analysis to avoid over-reliance.

**Data privacy:** Currently the app doesn't store anything — all data lives in Streamlit session state and is gone when the tab closes. If this were a real product, pet health data (conditions, allergies) would be sensitive and would need proper storage, encryption, and consent handling.

**Bias in training data:** Claude's knowledge of pet care reflects what's common in English-language internet content. It might give better, more specific advice for common breeds and common conditions than for rare ones. A Persian cat owner might get less useful advice than a golden retriever owner just because there's more golden retriever content in the training data.

---

## AI Collaboration in This Project

I used Claude Code (the CLI tool, not the API) to build most of this project — generating class skeletons, writing tests, reviewing design decisions, writing documentation.

**One helpful suggestion:** When I asked the AI to review the class structure, it caught that I had a `pets` list on both the `Owner` and the `Scheduler`. That's two sources of truth for the same data — if you add a pet to the owner, the scheduler wouldn't see it. The fix was to make `Scheduler` hold a reference to `Owner` instead of its own list. That was genuinely useful, I wouldn't have caught it immediately.

**One flawed suggestion:** Early on, the AI put a `tasks` list directly on the `Pet` class. The reasoning was "each pet has its own tasks." That sounds logical but it's wrong in practice — pets don't manage their own care schedules, their owners do. Centralizing tasks in the `Scheduler` is cleaner because it means one place to add, remove, filter, sort, and check for conflicts. I rejected that suggestion and kept the design owner-centric.

---

## Ideas for Improvement

- Upgrade `due_time` from `time` to `datetime` so recurring tasks actually schedule for tomorrow
- Add a "missing critical tasks" flag — if a pet has a condition but no relevant task is scheduled, the advisor should always flag it
- Store data between sessions (SQLite or a simple JSON file)
- Add a disclaimer banner in the UI clarifying this isn't veterinary advice
- Let users rate the AI advice (thumbs up/down) to collect feedback for future improvement
