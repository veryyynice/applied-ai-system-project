import logging
import uuid
from dataclasses import dataclass, field
from datetime import time
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a single pet care activity."""

    id: str
    pet_id: str
    name: str
    description: str
    duration_mins: int
    frequency: str        # "once", "daily", "weekly"
    priority: int         # 1 (low) to 5 (high)
    due_time: Optional[time] = None
    is_completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True
        logger.info("Task marked complete: %s (id=%s)", self.name, self.id)

    def __str__(self) -> str:
        due = self.due_time.strftime("%I:%M %p") if self.due_time else "No time set"
        status = "Done" if self.is_completed else "Pending"
        return (
            f"[{status}] {self.name} @ {due} "
            f"({self.duration_mins} min) — Priority {self.priority}"
        )


@dataclass
class Pet:
    """Stores pet profile details."""

    id: str
    name: str
    species: str
    breed: str
    age_years: int
    weight_kg: float
    allergies: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    days_since_groomed: int = 0

    def __str__(self) -> str:
        return f"{self.name} ({self.breed}, {self.age_years}yr)"


@dataclass
class Owner:
    """Manages a collection of pets."""

    name: str
    contact_info: str
    available_hours: list[tuple[time, time]] = field(default_factory=list)
    notification_preference: str = "app"  # "app", "email", "sms"
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's roster."""
        self.pets.append(pet)
        logger.info("Pet added: %s (id=%s)", pet.name, pet.id)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by ID from this owner's roster."""
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.id != pet_id]
        if len(self.pets) < before:
            logger.info("Pet removed: id=%s", pet_id)

    def get_all_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Initialize with an owner; pets are sourced from owner only."""
        self.owner = owner
        self.tasks: list[Task] = []
        logger.info("Scheduler initialized for owner: %s", owner.name)

    def add_task(self, task: Task) -> None:
        """Add a task; raises ValueError on invalid input."""
        if not task.name or not task.name.strip():
            logger.warning("Rejected task with empty name (id=%s)", task.id)
            raise ValueError("Task name cannot be empty.")
        if not 1 <= task.priority <= 5:
            logger.warning("Rejected task with invalid priority %d (id=%s)", task.priority, task.id)
            raise ValueError("Priority must be between 1 and 5.")
        if task.duration_mins <= 0:
            logger.warning("Rejected task with invalid duration %d (id=%s)", task.duration_mins, task.id)
            raise ValueError("Duration must be greater than 0.")
        self.tasks.append(task)
        logger.info("Task added: %s (id=%s, priority=%d)", task.name, task.id, task.priority)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by ID."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if len(self.tasks) < before:
            logger.info("Task removed: id=%s", task_id)

    def get_tasks_for_pet(self, pet: Pet) -> list[Task]:
        """Return all tasks belonging to a specific pet."""
        return [t for t in self.tasks if t.pet_id == pet.id]

    def get_incomplete_tasks(self, pet: Pet) -> list[Task]:
        """Return tasks for a pet that are not yet completed."""
        return [t for t in self.get_tasks_for_pet(pet) if not t.is_completed]

    # ── Sorting ───────────────────────────────────────────────────────────────

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted by due_time ascending; tasks with no time go last."""
        source = tasks if tasks is not None else self.tasks
        return sorted(source, key=lambda t: t.due_time or time(23, 59))

    # ── Filtering ─────────────────────────────────────────────────────────────

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        Args:
            pet_name:  If given, only tasks for the pet with this name.
            completed: True = done only, False = pending only, None = all.
        """
        pet_ids: Optional[set[str]] = None
        if pet_name is not None:
            pet_ids = {p.id for p in self.owner.pets if p.name.lower() == pet_name.lower()}

        result = []
        for t in self.tasks:
            if pet_ids is not None and t.pet_id not in pet_ids:
                continue
            if completed is not None and t.is_completed != completed:
                continue
            result.append(t)
        return result

    # ── Recurring tasks ───────────────────────────────────────────────────────

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task complete and, if recurring, queue its next occurrence.

        Returns the next-occurrence Task for daily/weekly tasks, or None.
        """
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task is None:
            logger.warning("complete_task called with unknown id: %s", task_id)
            return None

        task.mark_complete()

        if task.frequency in ("daily", "weekly"):
            next_task = Task(
                id=str(uuid.uuid4())[:8],
                pet_id=task.pet_id,
                name=task.name,
                description=task.description,
                duration_mins=task.duration_mins,
                frequency=task.frequency,
                priority=task.priority,
                due_time=task.due_time,
                is_completed=False,
            )
            self.tasks.append(next_task)
            logger.info(
                "Recurring task queued: %s (id=%s, frequency=%s)",
                next_task.name, next_task.id, next_task.frequency,
            )
            return next_task

        return None

    # ── Conflict detection ────────────────────────────────────────────────────

    def get_conflicts(self) -> list[str]:
        """Return human-readable conflict warnings for overlapping tasks.

        Checks consecutive pairs of sorted pending timed tasks.
        """
        timed = sorted(
            [t for t in self.tasks if t.due_time and not t.is_completed],
            key=lambda t: t.due_time,
        )

        def end_minutes(t: Task) -> int:
            return t.due_time.hour * 60 + t.due_time.minute + t.duration_mins

        def start_minutes(t: Task) -> int:
            return t.due_time.hour * 60 + t.due_time.minute

        warnings = []
        for i in range(len(timed) - 1):
            a, b = timed[i], timed[i + 1]
            if end_minutes(a) > start_minutes(b):
                pet_a = next((p.name for p in self.owner.pets if p.id == a.pet_id), "?")
                pet_b = next((p.name for p in self.owner.pets if p.id == b.pet_id), "?")
                a_end = time((end_minutes(a) // 60) % 24, end_minutes(a) % 60)
                msg = (
                    f"CONFLICT: '{a.name}' ({pet_a}) ends at "
                    f"{a_end.strftime('%I:%M %p')} but "
                    f"'{b.name}' ({pet_b}) starts at "
                    f"{b.due_time.strftime('%I:%M %p')}"
                )
                warnings.append(msg)
                logger.warning(msg)

        return warnings

    def check_conflicts(self) -> bool:
        """Return True if any pending tasks have overlapping time windows."""
        return len(self.get_conflicts()) > 0

    # ── Planning ──────────────────────────────────────────────────────────────

    def generate_daily_plan(self) -> list[Task]:
        """Return today's pending tasks sorted by priority (high first), then due time."""
        pending = [t for t in self.tasks if not t.is_completed]
        plan = sorted(
            pending,
            key=lambda t: (-t.priority, t.due_time or time(23, 59)),
        )
        logger.info("Daily plan generated: %d tasks", len(plan))
        return plan

    def send_reminder(self, task: Task) -> None:
        """Print a reminder for a task (placeholder for real notification logic)."""
        pet_name = next(
            (p.name for p in self.owner.pets if p.id == task.pet_id), "Unknown pet"
        )
        due = task.due_time.strftime("%I:%M %p") if task.due_time else "soon"
        msg = (
            f"REMINDER [{self.owner.notification_preference.upper()}]: "
            f"'{task.name}' for {pet_name} is due at {due}."
        )
        print(msg)
        logger.info(msg)
