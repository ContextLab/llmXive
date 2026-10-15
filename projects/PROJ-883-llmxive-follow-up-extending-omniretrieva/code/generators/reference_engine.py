"""Reference Engine.

Provides a deterministic, rule‑based greedy plan generator used as the
ground‑truth plan for synthetic queries. For the skeleton stage we keep
the implementation simple: the plan is a string that encodes the source
type and the requested complexity level.
"""

from typing import Dict, Any

class ReferenceEngine:
    """Deterministic greedy reference engine."""

    def generate_plan(self, query: Dict[str, Any]) -> str:
        """
        Generate a deterministic ground‑truth plan for a query.

        Parameters
        ----------
        query: Dict[str, Any]
            The query dictionary. Expected keys:
            - ``source_type`` (str): one of ``"text"``, ``"relational"``,
              ``"graph"``.
            - ``complexity_level`` (int): integer depth of the logical plan.

        Returns
        -------
        str
            A deterministic plan identifier.
        """
        source = query.get("source_type", "unknown")
        level = query.get("complexity_level", 0)
        # Simple deterministic representation.
        return f"{source}_plan_depth_{level}"
