"""
Oracle Policy Engine
--------------------

This module provides a pure‑Python ``OraclePolicyEngine`` that evaluates a
workflow against a set of deterministic policy rules and returns a list of
violations.  The implementation is deliberately lightweight and **does not**
import any symbols from compression or execution modules, satisfying the
Constitution VI independence requirement.

The engine currently implements a minimal subset of policies required for
the unit tests and for downstream components:

* **Budget cap** – a workflow specifies ``budget_cap`` (the maximum allowed
  budget) and ``requested_budget`` (the budget the workflow attempts to use).
  If ``requested_budget`` exceeds ``budget_cap`` a violation of type
  ``\"budget_exceeded\"`` is recorded.
* **Data sovereignty** – a placeholder rule that could be expanded later.

The engine can be extended with additional deterministic checks without
affecting its independence.
"""

from __future__ import annotations

from typing import Any, Dict, List


class OraclePolicyEngine:
    """
    Pure‑Python policy engine that deterministically evaluates a workflow.
    
    The engine is intentionally simple: it inspects known keys in the
    workflow dictionary and produces a list of violation dictionaries.
    
    Each violation dictionary contains at least a ``type`` field describing
    the nature of the violation and an optional ``details`` field with
    additional context.
    """

    def __init__(self) -> None:
        """Create a new OraclePolicyEngine instance."""
        # No state is required for the deterministic checks.
        pass

    def evaluate(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate ``workflow`` against all supported policy rules.
        
        Parameters
        ----------
        workflow: Dict[str, Any]
            A dictionary representing a synthetic workflow.  Expected keys
            include (but are not limited to):
            - ``budget_cap`` (numeric, optional)
            - ``requested_budget`` (numeric, optional)
            - ``data_sovereignty`` (bool, optional)
        
        Returns
        -------
        List[Dict[str, Any]]
            A list of violation dictionaries.  The list is empty if the
            workflow complies with all evaluated rules.
        """
        violations: List[Dict[str, Any]] = []

        # ---- Budget cap rule -------------------------------------------------
        if "budget_cap" in workflow and "requested_budget" in workflow:
            try:
                cap = float(workflow["budget_cap"])
                requested = float(workflow["requested_budget"])
                if requested > cap:
                    violations.append({
                        "type": "budget_exceeded",
                        "details": {
                            "budget_cap": cap,
                            "requested_budget": requested,
                        },
                    })
            except (TypeError, ValueError):
                # If values are not numeric, treat as a violation for safety.
                violations.append({
                    "type": "budget_invalid",
                    "details": {
                        "budget_cap": workflow.get("budget_cap"),
                        "requested_budget": workflow.get("requested_budget"),
                    },
                })

        # ---- Data sovereignty placeholder rule -------------------------------
        # This rule exists to illustrate how additional deterministic checks
        # could be added without breaking independence.
        if workflow.get("data_sovereignty") is False:
            violations.append({
                "type": "data_sovereignty_violation",
                "details": {"allowed": True, "found": False},
            })

        # Additional policy checks can be added here following the same
        # pattern, ensuring they remain pure functions of the workflow dict.

        return violations
