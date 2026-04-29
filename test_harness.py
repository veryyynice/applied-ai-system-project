"""
PawPal+ Test Harness — automated evaluation script (stretch feature)

Runs 6 predefined scenarios against the scheduler and prints a pass/fail
summary with confidence ratings. Each scenario tests a real user situation.

Usage:
    python3 test_harness.py
"""

from datetime import time

from pawpal_system import Owner, Pet, Task, Scheduler


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_owner(name="TestOwner"):
    return Owner(name=name, contact_info="test@test.com")


def make_pet(id="p1", name="Buddy", conditions=None):
    return Pet(
        id=id, name=name, species="dog", breed="Mutt",
        age_years=3, weight_kg=10,
        conditions=conditions or [],
    )


def make_task(id, pet_id, name, priority, due_time=None, duration_mins=15,
              frequency="daily", completed=False):
    t = Task(
        id=id, pet_id=pet_id, name=name, description="",
        duration_mins=duration_mins, frequency=frequency,
        priority=priority, due_time=due_time, is_completed=completed,
    )
    return t


def run_scenario(name, fn):
    """Run a single scenario function, catch exceptions, return result dict."""
    try:
        passed, details, confidence = fn()
        return {"name": name, "passed": passed, "details": details, "confidence": confidence}
    except Exception as exc:
        return {"name": name, "passed": False, "details": f"EXCEPTION: {exc}", "confidence": 0}


# ── Scenarios ─────────────────────────────────────────────────────────────────

def scenario_priority_ordering():
    """High-priority tasks should appear first in the daily plan."""
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    scheduler.add_task(make_task("t1", pet.id, "Bath", priority=1, due_time=time(8, 0)))
    scheduler.add_task(make_task("t2", pet.id, "Medication", priority=5, due_time=time(9, 0)))
    scheduler.add_task(make_task("t3", pet.id, "Walk", priority=3, due_time=time(10, 0)))

    plan = scheduler.generate_daily_plan()
    priorities = [t.priority for t in plan]
    passed = priorities == sorted(priorities, reverse=True)
    confidence = 5 if passed else 1
    details = f"Order: {priorities} — expected [5, 3, 1]"
    return passed, details, confidence


def scenario_conflict_detection():
    """Overlapping tasks should be detected and reported."""
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    # Task at 8:00 lasting 60 min, another at 8:30 — should conflict
    scheduler.add_task(make_task("t1", pet.id, "Grooming", priority=3,
                                 due_time=time(8, 0), duration_mins=60))
    scheduler.add_task(make_task("t2", pet.id, "Walk", priority=4,
                                 due_time=time(8, 30), duration_mins=15))

    conflicts = scheduler.get_conflicts()
    passed = len(conflicts) > 0 and "CONFLICT" in conflicts[0]
    confidence = 5 if passed else 2
    details = f"Got {len(conflicts)} conflict(s): {conflicts[0] if conflicts else 'none'}"
    return passed, details, confidence


def scenario_no_false_conflicts():
    """Non-overlapping tasks should NOT trigger conflict warnings."""
    owner = make_owner()
    scheduler = Scheduler(owner)

    scheduler.add_task(make_task("t1", "p1", "Morning walk", priority=4,
                                 due_time=time(7, 0), duration_mins=30))
    scheduler.add_task(make_task("t2", "p1", "Feeding", priority=3,
                                 due_time=time(8, 0), duration_mins=10))

    conflicts = scheduler.get_conflicts()
    passed = len(conflicts) == 0
    confidence = 5 if passed else 1
    details = f"Conflicts detected: {conflicts} — expected none"
    return passed, details, confidence


def scenario_recurring_task_spawns_next():
    """Completing a daily task should auto-queue the next occurrence."""
    owner = make_owner()
    scheduler = Scheduler(owner)

    scheduler.add_task(make_task("t1", "p1", "Inhaler", priority=5,
                                 due_time=time(8, 0), frequency="daily"))
    initial_count = len(scheduler.tasks)

    next_task = scheduler.complete_task("t1")

    passed = (
        next_task is not None
        and not next_task.is_completed
        and len(scheduler.tasks) == initial_count + 1
        and next_task.frequency == "daily"
    )
    confidence = 5 if passed else 2
    details = (
        f"Tasks: {initial_count} → {len(scheduler.tasks)}, "
        f"next_task: {next_task.name if next_task else None}, "
        f"completed: {next_task.is_completed if next_task else '?'}"
    )
    return passed, details, confidence


def scenario_filter_by_pet():
    """Filtering by pet name should return only that pet's tasks."""
    owner = make_owner()
    luna = make_pet(id="p1", name="Luna")
    milo = make_pet(id="p2", name="Milo")
    owner.add_pet(luna)
    owner.add_pet(milo)
    scheduler = Scheduler(owner)

    scheduler.add_task(make_task("t1", luna.id, "Walk", priority=4))
    scheduler.add_task(make_task("t2", luna.id, "Feed", priority=3))
    scheduler.add_task(make_task("t3", milo.id, "Litter box", priority=2))

    result = scheduler.filter_tasks(pet_name="Luna")
    passed = len(result) == 2 and all(t.pet_id == luna.id for t in result)
    confidence = 5 if passed else 1
    details = f"Got {len(result)} tasks for Luna (expected 2), ids: {[t.pet_id for t in result]}"
    return passed, details, confidence


def scenario_completed_excluded_from_plan():
    """Completed tasks must not appear in the daily plan."""
    owner = make_owner()
    scheduler = Scheduler(owner)

    scheduler.add_task(make_task("t1", "p1", "Walk", priority=4, completed=True))
    scheduler.add_task(make_task("t2", "p1", "Feed", priority=3, completed=False))
    scheduler.add_task(make_task("t3", "p1", "Medication", priority=5, completed=True))

    plan = scheduler.generate_daily_plan()
    passed = len(plan) == 1 and plan[0].id == "t2"
    confidence = 5 if passed else 1
    details = f"Plan has {len(plan)} task(s) (expected 1): {[t.id for t in plan]}"
    return passed, details, confidence


# ── Main ──────────────────────────────────────────────────────────────────────

SCENARIOS = [
    ("Priority Ordering",           scenario_priority_ordering),
    ("Conflict Detection",          scenario_conflict_detection),
    ("No False Conflicts",          scenario_no_false_conflicts),
    ("Recurring Task Auto-Queue",   scenario_recurring_task_spawns_next),
    ("Filter by Pet Name",          scenario_filter_by_pet),
    ("Completed Tasks Excluded",    scenario_completed_excluded_from_plan),
]


def run_all():
    print("=" * 60)
    print("  PAWPAL+ TEST HARNESS — Automated Evaluation".center(60))
    print("=" * 60)

    results = [run_scenario(name, fn) for name, fn in SCENARIOS]

    passed_count = sum(1 for r in results if r["passed"])
    avg_confidence = (
        sum(r["confidence"] for r in results if r["passed"]) / passed_count
        if passed_count > 0
        else 0
    )

    for r in results:
        status = "✓ PASS" if r["passed"] else "✗ FAIL"
        conf = f"(confidence {r['confidence']}/5)" if r["passed"] else ""
        print(f"\n  {status}  {r['name']} {conf}")
        print(f"         {r['details']}")

    print("\n" + "-" * 60)
    print(f"  Result: {passed_count}/{len(results)} passed")
    print(f"  Avg confidence (passing tests): {avg_confidence:.1f}/5")
    if passed_count == len(results):
        print("  All scenarios passed — scheduler is reliable.")
    else:
        failed = [r["name"] for r in results if not r["passed"]]
        print(f"  Failed: {', '.join(failed)}")
    print("=" * 60)

    return passed_count, len(results)


if __name__ == "__main__":
    run_all()
