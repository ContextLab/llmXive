---
task_type: MiniGrid
description: Alignment of MiniGrid prompts with ground‑truth validity criteria.
validity_criteria: Token matches any valid path in the MiniGrid environment.
ground_truth_source: data/minigrid_ground_truth.jsonl
---

# Semantic Alignment for MiniGrid

This contract defines how MiniGrid prompts are aligned with their ground‑truth solutions.

- **Task Type**: MiniGrid navigation tasks.
- **Description**: For each MiniGrid prompt we provide a set of valid token sequences (paths) that solve the navigation problem. The alignment process checks generated tokens against any of these valid paths.
- **Validity Criteria**: A generated token at position *i* is considered valid if it matches the token at the same position in *any* of the known ground‑truth paths. Tokens that do not match any path are flagged as invalid and a warning is logged.
- **Ground‑Truth Source**: See the file referenced by `ground_truth_source` above, which contains the canonical MiniGrid ground‑truth data in JSONL format.
