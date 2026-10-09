---
task_type: MiniGrid
description: |
 Defines the semantic alignment for MiniGrid navigation tasks. The alignment
 specifies how generated token sequences are compared against ground‑truth
 navigation paths to determine token‑level validity.
validity_criteria: |
 A token is considered valid if it matches the corresponding token in
 any known shortest path from the start state to the goal state for the
 MiniGrid episode. Tokens that do not appear at the same position in any
 valid path are marked invalid.
ground_truth_source: data/canonical_ground_truth_minigrid.jsonl
---

# Semantic Alignment for MiniGrid

This contract describes the rules for aligning generated MiniGrid token
sequences with the canonical ground‑truth navigation paths. It is used by
the generation and labeling pipelines to produce per‑token validity flags.
