 Explicitly name your original project (from Modules 1-3) and provide a 2-3 sentence summary of its original goals and capabilities.
Title and Summary: What your project does and why it matters.
Architecture Overview: A short explanation of your system diagram.
Setup Instructions: Step-by-step directions to run your code.
Sample Interactions: Include at least 2-3 examples of inputs and the resulting AI outputs to demonstrate the system is functional.
Design Decisions: Why you built it this way, and what trade-offs you made.
Testing Summary: What worked, what didn't, and what you learned.
Reflection: What this project taught you about AI and problem-solving.
     What are the limitations or biases in your system?
    Could your AI be misused, and how would you prevent that?
    What surprised you while testing your AI's reliability?
    describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.





 Runs correctly and reproducibly: If someone follows your instructions, it should work.
Includes logging or guardrails: Your code should track what it does and handle errors safely.

recording:
✅ End-to-end system run (2–3 inputs)
✅ AI feature behavior (RAG, agent, etc.)
✅ Reliability/guardrail or evaluation behavior
✅ Clear outputs for each case

build off of :
# PawPal+ (Module 2 Project)
**PawPal+** is a Streamlit app that helps a pet owner plan care tasks for their pets using smart scheduling logic.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## Features

- **Owner & pet management** — Create an owner profile, add multiple pets, and manage them across sessions using Streamlit's session state
- **Task tracking** — Add tasks with duration, priority (1–5), frequency (daily/weekly/once), and due time
- **Sorting by time** — View tasks in chronological order regardless of the order they were entered
- **Filtering** — Filter the task list by pet name and/or completion status
- **Priority scheduling** — `generate_daily_plan()` sorts pending tasks by priority descending, then by due time
- **Conflict detection** — `get_conflicts()` returns human-readable warnings when two tasks have overlapping time windows
- **Recurring tasks** — Completing a daily or weekly task automatically queues the next occurrence; one-off tasks do not recur

## Project Structure

```
pawpal_system.py   — Logic layer: Task, Pet, Owner, Scheduler classes
app.py             — Streamlit UI connected to logic layer
main.py            — Terminal demo script
tests/
  test_pawpal.py   — Automated test suite (25 tests)
class_diagram.md   — Final UML class diagram (Mermaid.js)
reflection.md      — Design and AI collaboration reflection
```

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

# Run the terminal demo
python3 main.py
```

## Testing PawPal+

```bash
python3 -m pytest
# or for verbose output:
python3 -m pytest tests/ -v
```

### What the tests cover

| Category | Tests |
|---|---|
| Task completion | `mark_complete()` flips status; idempotent |
| Task CRUD | add/remove changes count correctly |
| Sorting | chronological order; no-time tasks sort last |
| Filtering | by pet name, by status, combined |
| Recurring tasks | daily/weekly spawn next occurrence; once does not |
| Conflict detection | returns warning strings; empty list when clear |
| Daily plan | excludes completed; priority then time order |
| Session wiring | owner is single source of truth for pets |

**Confidence level: ★★★★☆** — Core behaviors and main edge cases are covered. See `reflection.md` section 4b for edge cases to address next.

## Smarter Scheduling

The scheduler uses three algorithms working together:

1. **`sort_by_time()`** — Uses Python's `sorted()` with a lambda key: `lambda t: t.due_time or time(23, 59)`. Tasks with no due time fall to the end.
2. **`filter_tasks(pet_name, completed)`** — Resolves the pet name to a set of IDs first, then filters in a single pass — O(n) with no nested loops.
3. **`get_conflicts()`** — Sorts timed tasks, then checks consecutive pairs. If task A's end time (due + duration in minutes) exceeds task B's start time, a conflict string is generated. Returns a list so the UI can display all conflicts at once rather than stopping at the first.
4. **`complete_task()`** — When a daily or weekly task is completed, a new `Task` is created with a fresh UUID and added to the scheduler, preserving the same time and priority for the next cycle.
