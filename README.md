# PawPal+ Applied AI System

> **Base project:** PawPal+ from Module 2 (pet care scheduling app built with Streamlit and Python dataclasses)

**Demo walkthrough (Loom):** <video controls src="https://i.imgur.com/mWyoJp6.mp4" title="_[Add your Loom link here after recording]_"></video>

---
https://i.imgur.com/mWyoJp6.mp4
## What This Is

PawPal+ is a pet care scheduling assistant that uses AI to help owners plan their day. You put in your pets, add tasks like walks or medications, and it generates a prioritized schedule. On top of that, it has an AI advisor that actually reads your schedule and tells you if something looks wrong — like if your cat has asthma but the inhaler task is ranked low priority.

The original Module 2 version was just a Streamlit app with scheduling logic. This version adds:
- A Claude-powered AI advisor that analyzes your schedule and flags health concerns
- Input validation and logging throughout
- A standalone test harness that runs 6 scenarios and prints a pass/fail report

---

## Original Project

**PawPal+ (Module 2)** — the goal was to build a backend scheduling system with four classes (Owner, Pet, Task, Scheduler) and connect it to a Streamlit UI. It could sort tasks by priority and time, detect scheduling conflicts, and auto-queue recurring tasks. It had 25 unit tests covering all the core behaviors.

This final project extends that by adding a real AI layer on top of the scheduling engine.

---

## Architecture

The system has four main components. Here's how they connect:

```
User → Streamlit UI (app.py)
           ↓
     Logic Layer (pawpal_system.py)
           ↓
       Scheduler ──→ AI Advisor (ai_advisor.py) ──→ Claude API
           ↓
     Test Harness (test_harness.py) → Pass/Fail Report
```

Full diagram: [assets/system_architecture.md](assets/system_architecture.md)

- **Streamlit UI** (`app.py`) — handles all user interaction and session state. Validates inputs before passing them to the logic layer.
- **Logic Layer** (`pawpal_system.py`) — Task, Pet, Owner, Scheduler classes. Scheduler is the brain: sorts, filters, detects conflicts, manages recurring tasks. Has logging throughout.
- **AI Advisor** (`ai_advisor.py`) — the agentic component. It takes the current schedule + pet health info, sends it to Claude (haiku model), and gets back an explanation of the task ordering, any health concerns, a confidence score, and suggestions for missing tasks.
- **Test Harness** (`test_harness.py`) — runs 6 predefined scheduling scenarios and prints which ones pass or fail with confidence ratings.

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/applied-ai-system-project.git
cd applied-ai-system-project

# 2. Set up the environment
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Anthropic API key (needed for AI analysis feature)
export ANTHROPIC_API_KEY="your-key-here"
# Windows: set ANTHROPIC_API_KEY=your-key-here

# 5. Run the app
streamlit run app.py
```

The app works without an API key — you just won't be able to use the AI analysis button. Everything else (scheduling, conflict detection, recurring tasks) works fine without it.

```bash
# Run the unit tests
python3 -m pytest tests/ -v

# Run the test harness (standalone evaluation)
python3 test_harness.py

# Run the terminal demo
python3 main.py
```

---

## Sample Interactions

### Example 1: Priority scheduling with conflict detection

**Input:** Owner Jordan has a cat named Milo (asthma condition). Adds three tasks:
- Inhaler @ 8:00 AM, 5 min, priority 5, daily
- Feeding @ 8:03 AM, 10 min, priority 4, daily
- Grooming @ 11:00 AM, 45 min, priority 3, weekly

**Output (schedule view):**
```
⚠️ CONFLICT: 'Inhaler' (Milo) ends at 08:05 AM but 'Feeding' (Milo) starts at 08:03 AM

Priority order:
1. Inhaler for Milo — Due: 08:00 AM · 5 min · ★★★★★ · daily
2. Feeding for Milo — Due: 08:03 AM · 10 min · ★★★★☆ · daily
3. Grooming for Milo — Due: 11:00 AM · 45 min · ★★★☆☆ · weekly
```

The conflict warning fires immediately because the 5-minute inhaler task ends at 8:05 but feeding starts at 8:03.

---

### Example 2: Completing a recurring task

**Input:** Mark "Morning Walk" (daily) as complete.

**Output:**
```
Done! Next 'Morning Walk' auto-scheduled (id: a3f7c2b1)
```

The original task is marked done, and a fresh pending task for the next cycle is automatically added to the scheduler. The task count goes from 4 to 5.

---

### Example 3: AI advisor analysis

**Input:** Owner Alex has Luna (Golden Retriever, 12 days since groomed) and Milo (cat, asthma). Schedule has 5 tasks. Click "Get AI Analysis."

**AI output:**
```
Explanation: The schedule prioritizes Milo's inhaler and Luna's morning walk equally at priority 5,
placing them first. Evening activities are ranked lower, which is appropriate since medical tasks
should always precede grooming or enrichment.

Health flags:
• Milo has asthma — confirm inhaler is administered before any strenuous activity for Luna
  that might create noise or stress.
• Luna is overdue for grooming (12 days) — consider moving the grooming task to a higher priority.

Confidence: 4/5 — Good

Suggestions: Consider adding a post-grooming check for Luna given the overdue status.
```

---

## Design Decisions

**Why Claude haiku for the AI advisor?** It's fast and cheap. The advisor prompt is short (under 300 tokens) so haiku handles it in under a second. Using opus or sonnet would be overkill for what's basically a short analysis task.

**Why agentic workflow instead of RAG?** The data the AI needs (pet health info, task list) is already in memory — there's no external knowledge base to retrieve from. An agentic approach made more sense: the AI receives state, reasons about it, and returns a structured verdict. It "acts" by generating health flags and confidence scores, and "checks its own work" by rating how complete the plan is.

**Why consecutive-pair conflict detection instead of O(n²)?** For a personal pet care app with maybe 5-10 tasks a day, checking every pair would be overkill. The consecutive-pair approach (sort by time, check neighbors) catches the most common case — two back-to-back tasks booked too close — and is much easier to read and reason about.

**Why not persist data to a file/database?** Keeping everything in `st.session_state` kept the scope tight. Adding a database would've doubled the complexity with minimal benefit for a single-user demo app. The tradeoff is that data resets on page refresh.

**Input validation:** Added `ValueError` guardrails in `Scheduler.add_task()` that reject empty task names, invalid priorities (outside 1-5), and zero/negative durations. The UI catches these and shows a user-friendly error instead of crashing.

---

## Testing Summary

**Unit tests (pytest):** 25 tests, all passing. Cover task completion, CRUD, filtering, sorting, recurring tasks, conflict detection, and session wiring.

**Test harness (6 scenarios):**

| Scenario | Result | Confidence |
|---|---|---|
| Priority Ordering | ✓ PASS | 5/5 |
| Conflict Detection | ✓ PASS | 5/5 |
| No False Conflicts | ✓ PASS | 5/5 |
| Recurring Task Auto-Queue | ✓ PASS | 5/5 |
| Filter by Pet Name | ✓ PASS | 5/5 |
| Completed Tasks Excluded | ✓ PASS | 5/5 |

**Result: 6/6 passed. Avg confidence: 5.0/5.**

What didn't get tested: tasks spanning midnight (e.g., 11:45 PM + 30 min), and the AI advisor with an invalid API key (though the error handling for that was manually verified — it shows an error message instead of crashing).

---

## Reflection and Ethics

**Limitations and biases:**
The AI advisor uses Claude out of the box with no fine-tuning, so its suggestions are based on general pet care knowledge from training data — not veterinary advice. If someone's pet has a rare condition, the model might give generic flags instead of actually useful ones. The conflict detection also only checks consecutive pairs, so a task that overlaps with a non-adjacent task in the sorted list won't be caught.

**Could it be misused?**
Someone could misread the AI's health flag suggestions as actual medical guidance. The app doesn't claim to be a vet, but the output looks authoritative. A real version of this would need a prominent disclaimer: "This is not veterinary advice."

**What surprised me while testing:**
The AI advisor was more reliable than I expected at picking up on health context. When I tested it with a pet that had asthma and no inhaler on the schedule, it flagged the missing medication unprompted — I didn't tell it to look for that specifically, it just noticed from the conditions list. That was kind of impressive.

**AI collaboration:**
I used Claude Code (the CLI) throughout this project to write code, generate tests, review design decisions, and write documentation. One really helpful moment was when I asked it to review the class skeleton and it caught that I had a `pets` list on both the `Owner` and the `Scheduler` — two sources of truth for the same data, which would've caused bugs. Removing that and making `Scheduler` reference `Owner` directly was a clean fix.

One moment where the suggestion was wrong: early on it put task ownership on the `Pet` class (like `Pet.tasks`). That doesn't make sense — pets don't manage their own schedules, people do. I rejected that and kept tasks centralized in the `Scheduler`.

---

## File Structure

```
applied-ai-system-project/
├── app.py                    # Streamlit UI
├── pawpal_system.py          # Core logic (Task, Pet, Owner, Scheduler)
├── ai_advisor.py             # AI analysis layer (Claude API)
├── test_harness.py           # Automated evaluation script
├── main.py                   # Terminal demo
├── requirements.txt
├── model_card.md             # Model documentation and reflection
├── reflection.md             # Module 2 design reflection (original)
├── class_diagram.md          # UML class diagram (Mermaid)
├── assets/
│   └── system_architecture.md  # System architecture diagram
└── tests/
    ├── __init__.py
    └── test_pawpal.py        # 25 unit tests
```
