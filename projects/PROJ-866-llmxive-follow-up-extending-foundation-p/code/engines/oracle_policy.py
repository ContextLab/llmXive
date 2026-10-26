"""
code.engines.oracle_policy
--------------------------

Independent Oracle Policy Engine used to evaluate synthetic workflows
against a set of deterministic policy rules.  The engine is deliberately
simple – it checks only a small number of concrete constraints that are
present in the synthetic workflow metadata.  This implementation satisfies
the unit‑test for a budget‑cap violation (T002) and provides the
``evaluate`` method required by the full‑ and compressed‑context execution
engines.

The engine is deliberately stateless; all information needed for a
evaluation is carried by the ``workflow`` dictionary supplied by the
generator.
"""

from typing import Any, Dict, List, Tuple

class OraclePolicyEngine:
    """
    Simple deterministic policy evaluator.

    The evaluator looks for known keys in ``workflow['metadata']`` and
    returns a list of violations (as dictionaries) together with a list of
    detailed violation records.  Only the rules required by the test suite
    are implemented:

    * ``budget_exceeded`` – triggered when ``budget_used`` > ``budget_cap``.
    * ``data_sovereignty`` – triggered when a workflow is marked as
      ``requires_sovereignty`` but the ``sovereignty_provided`` flag is
      ``False``.
    * Additional rules can be added without breaking the existing API.

    The method signature matches the expectations of the execution engines:

    ``evaluate(workflow) -> (violations: List[Dict], details: List[Dict])``
    """

    def __init__(self) -> None:
        # No mutable state; the engine is pure.
        pass

    def evaluate(self, workflow: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Evaluate a workflow against the defined policy rules.

        Parameters
        ----------
        workflow: dict
            The workflow dictionary produced by the synthetic generator.
            Expected structure (relevant parts)::

                {
                    "id": "workflow_0001",
                    "metadata": {
                        "budget_cap": 100,
                        "budget_used": 120,
                        "requires_sovereignty": true,
                        "sovereignty_provided": false,
                        ...
                    },
                    ...
                }

        Returns
        -------
        violations: list of dict
            Each dict contains at least a ``rule_id`` key identifying the
            violated rule.
        details: list of dict
            Human‑readable details for each violation (e.g. node identifier,
            explanatory message).
        """
        violations: List[Dict[str, Any]] = []
        details: List[Dict[str, Any]] = []

        metadata = workflow.get("metadata", {})

        # ---- Budget cap rule ------------------------------------------------
        budget_cap = metadata.get("budget_cap")
        budget_used = metadata.get("budget_used")
        if budget_cap is not None and budget_used is not None:
            if budget_used > budget_cap:
                violations.append({"rule_id": "budget_exceeded", "node_id": "budget_node"})
                details.append({
                    "node_id": "budget_node",
                    "rule_id": "budget_exceeded",
                    "message": f"Budget used ({budget_used}) exceeds cap ({budget_cap})."
                })

        # ---- Data sovereignty rule -----------------------------------------
        requires_sovereignty = metadata.get("requires_sovereignty")
        sovereignty_provided = metadata.get("sovereignty_provided")
        if requires_sovereignty:
            if not sovereignty_provided:
                violations.append({"rule_id": "data_sovereignty_missing", "node_id": "sovereignty_node"})
                details.append({
                    "node_id": "sovereignty_node",
                    "rule_id": "data_sovereignty_missing",
                    "message": "Workflow requires data sovereignty but no provision is present."
                })

        # Additional deterministic checks can be added here without
        # affecting existing behaviour.

        return violations, details
