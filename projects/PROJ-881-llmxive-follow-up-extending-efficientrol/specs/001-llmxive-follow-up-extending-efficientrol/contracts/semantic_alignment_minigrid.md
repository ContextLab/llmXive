---
task_type: MiniGrid
description: "Semantic alignment for MiniGrid reinforcement learning navigation tasks."
validity_criteria: "A token is considered valid if it matches any token in a known optimal path for the given MiniGrid episode."
ground_truth_source: "data/canonical_ground_truth.jsonl"
---

# Semantic Alignment for MiniGrid

This contract defines the alignment criteria between generated token sequences and the ground‑truth
solutions for MiniGrid navigation tasks. The `ground_truth_source` points to a JSONL file containing
canonical solutions (paths) for each MiniGrid prompt. Validity is assessed token‑wise: a token is
valid when it appears at the same position in any of the known optimal paths for the episode.

The contract is used by the generation and labeling pipelines to produce binary validity flags
for each token in a sequence.
