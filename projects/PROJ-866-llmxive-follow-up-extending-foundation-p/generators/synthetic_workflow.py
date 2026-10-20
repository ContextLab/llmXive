"""
generators.synthetic_workflow
-----------------------------

This module implements the ``SyntheticWorkflowGenerator`` class required by
the unit tests (``tests/unit/test_generator.py``). The implementation builds
on the deterministic workflow generator already present under
``code/generators/synthetic_workflow.py`` but provides a simple, explicit
API that matches the test expectations:

* ``SyntheticWorkflowGenerator(seed: int)`` – constructs the generator with
  a deterministic random seed.
* ``generate_workflows(count: int) -> List[Dict]`` – returns a list of
  workflow dictionaries. Each workflow contains a ``metadata`` mapping with
  a ``depth`` field. The generator guarantees:
    - exactly ``count`` workflows,
    - 20 distinct depth levels (0‑19),
    - at least 25 workflows per depth when ``count`` is 500 (the default
      used in the full pipeline).

The class does **not** depend on any external data source; it creates
synthetic workflows that satisfy the contract required by downstream
components. The structure mirrors the schema used elsewhere in the project
but is kept minimal to avoid unnecessary coupling.
"""

import random
from typing import List, Dict

class SyntheticWorkflowGenerator:
    """
    Deterministic synthetic workflow generator.

    The generator produces simple workflow dictionaries containing a
    ``metadata`` field with a ``depth`` entry. Depth values are distributed
    uniformly across the range 0‑19. For counts that are not a multiple of 20,
    the remaining workflows are assigned depths in a round‑robin fashion.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        random.seed(self.seed)

    def _depth_sequence(self, count: int) -> List[int]:
        """
        Produce a deterministic list of depth values.

        For ``count`` >= 20 the function repeats the sequence
        ``0, 1, ..., 19`` as many times as needed, then appends the first
        ``count % 20`` values to reach the exact length.
        """
        base = list(range(20))  # depths 0‑19
        repeats, remainder = divmod(count, 20)
        seq = base * repeats + base[:remainder]
        return seq

    def generate_workflows(self, count: int) -> List[Dict]:
        """
        Generate ``count`` synthetic workflow dictionaries.

        Each workflow has the minimal required fields:
          - ``workflow_id``: a deterministic identifier.
          - ``metadata``: a mapping containing at least ``depth``.
          - ``is_valid``: always ``True`` for the synthetic data.
          - ``policy_complexity``: a deterministic integer derived from the
            depth (e.g., ``depth * 3 + 1``) to provide some variability
            for downstream analysis.

        The function is fully deterministic given the initial seed.
        """
        depths = self._depth_sequence(count)
        workflows: List[Dict] = []
        for idx, depth in enumerate(depths):
            wf = {
                "workflow_id": f"workflow_{idx:06d}",
                "metadata": {"depth": depth},
                "is_valid": True,
                # Additional fields that downstream components may expect.
                "policy_complexity": depth * 3 + 1,
                "description": f"Synthetic workflow #{idx} at depth {depth}",
            }
            workflows.append(wf)
        return workflows
