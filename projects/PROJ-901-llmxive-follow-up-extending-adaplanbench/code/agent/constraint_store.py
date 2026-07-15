"""
Deterministic key-value store for active constraints.

This module implements the constraint store component of the dual-track architecture.
It maintains a persistent, queryable record of constraints revealed during task execution.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid

from agent.base import ViolationType


@dataclass
class Constraint:
    """Represents a single constraint with its metadata."""
    id: str
    text: str
    revealed_at: datetime
    is_active: bool = True
    source: str = "explicit"  # explicit, inferred, implicit
    verified: bool = False
    violation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraint to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "revealed_at": self.revealed_at.isoformat(),
            "is_active": self.is_active,
            "source": self.source,
            "verified": self.verified,
            "violation_count": self.violation_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Constraint":
        """Reconstruct constraint from dictionary."""
        return cls(
            id=data["id"],
            text=data["text"],
            revealed_at=datetime.fromisoformat(data["revealed_at"]),
            is_active=data.get("is_active", True),
            source=data.get("source", "explicit"),
            verified=data.get("verified", False),
            violation_count=data.get("violation_count", 0)
        )


@dataclass
class ConstraintStore:
    """
    Deterministic key-value store for active constraints.

    This store maintains the set of constraints revealed during task execution,
    tracks their activation state, and provides methods for querying and updating.
    """
    task_id: str
    constraints: Dict[str, Constraint] = field(default_factory=dict)
    constraint_order: List[str] = field(default_factory=list)  # preserves reveal order
    total_violations: int = 0
    last_updated: Optional[datetime] = None

    def add_constraint(self, text: str, source: str = "explicit") -> Constraint:
        """
        Add a new constraint to the store.

        Args:
            text: The constraint text.
            source: The source of the constraint (explicit, inferred, implicit).

        Returns:
            The newly created Constraint object.
        """
        constraint_id = str(uuid.uuid4())
        constraint = Constraint(
            id=constraint_id,
            text=text,
            revealed_at=datetime.now(),
            source=source,
            is_active=True,
            verified=False,
            violation_count=0
        )
        self.constraints[constraint_id] = constraint
        self.constraint_order.append(constraint_id)
        self.last_updated = datetime.now()
        return constraint

    def get_constraint(self, constraint_id: str) -> Optional[Constraint]:
        """Retrieve a constraint by its ID."""
        return self.constraints.get(constraint_id)

    def get_active_constraints(self) -> List[Constraint]:
        """Return all currently active constraints."""
        return [c for c in self.constraints.values() if c.is_active]

    def get_all_constraints(self) -> List[Constraint]:
        """Return all constraints in reveal order."""
        return [self.constraints[cid] for cid in self.constraint_order]

    def deactivate_constraint(self, constraint_id: str) -> bool:
        """
        Deactivate a constraint (e.g., when it's no longer relevant).

        Args:
            constraint_id: The ID of the constraint to deactivate.

        Returns:
            True if the constraint was found and deactivated, False otherwise.
        """
        constraint = self.constraints.get(constraint_id)
        if constraint:
            constraint.is_active = False
            self.last_updated = datetime.now()
            return True
        return False

    def mark_verified(self, constraint_id: str) -> bool:
        """
        Mark a constraint as verified.

        Args:
            constraint_id: The ID of the constraint to verify.

        Returns:
            True if the constraint was found and marked, False otherwise.
        """
        constraint = self.constraints.get(constraint_id)
        if constraint:
            constraint.verified = True
            self.last_updated = datetime.now()
            return True
        return False

    def record_violation(self, constraint_id: str, violation_type: ViolationType) -> bool:
        """
        Record a violation for a specific constraint.

        Args:
            constraint_id: The ID of the constraint that was violated.
            violation_type: The type of violation that occurred.

        Returns:
            True if the violation was recorded, False if constraint not found.
        """
        constraint = self.constraints.get(constraint_id)
        if constraint:
            constraint.violation_count += 1
            self.total_violations += 1
            self.last_updated = datetime.now()
            return True
        return False

    def get_violation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of violations across all constraints.

        Returns:
            Dictionary containing violation statistics.
        """
        active_constraints = self.get_active_constraints()
        violated_constraints = [c for c in active_constraints if c.violation_count > 0]

        return {
            "task_id": self.task_id,
            "total_constraints": len(self.constraints),
            "active_constraints": len(active_constraints),
            "violated_constraints": len(violated_constraints),
            "total_violations": self.total_violations,
            "violation_rate": self.total_violations / len(active_constraints) if active_constraints else 0.0,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire store to a dictionary."""
        return {
            "task_id": self.task_id,
            "constraints": [c.to_dict() for c in self.get_all_constraints()],
            "total_violations": self.total_violations,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintStore":
        """Deserialize a store from a dictionary."""
        store = cls(
            task_id=data["task_id"],
            total_violations=data.get("total_violations", 0)
        )
        if "last_updated" in data and data["last_updated"]:
            store.last_updated = datetime.fromisoformat(data["last_updated"])

        for c_data in data.get("constraints", []):
            constraint = Constraint.from_dict(c_data)
            store.constraints[constraint.id] = constraint
            store.constraint_order.append(constraint.id)

        return store

    def save_to_file(self, filepath: str) -> None:
        """Save the store to a JSON file."""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ConstraintStore":
        """Load a store from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)