---
task_type: MiniGrid
description: >
 Semantic alignment specification for MiniGrid navigation tasks.
 This contract defines how generated token sequences are evaluated for
 validity against the canonical ground‑truth paths for MiniGrid episodes.
validity_criteria: >
 A token sequence is considered valid if it matches **any** of the
 known shortest paths from the start state to the goal state for the
 given MiniGrid instance. Tokens that deviate from all known paths are
 marked invalid.
ground_truth_source: data/canonical_ground_truth.jsonl
---

# MiniGrid Semantic Alignment

This document describes the alignment logic used to label generated
MiniGrid token sequences. The `ground_truth_source` points to a JSONL
file containing, for each prompt, the set of valid navigation paths.

The alignment process:

1. Load the ground‑truth record for the prompt (`prompt_id`).
2. Extract the `valid_paths` field – a list of token‑ID sequences that
 constitute correct solutions.
3. Compare the generated token sequence token‑by‑token against each
 candidate path.
4. If **any** path matches the generated sequence at a given position,
 the token is labeled `valid`; otherwise it is labeled `invalid`.

This contract is used by the generation and labeling pipeline to
produce `*_labels.jsonl` files for downstream entropy‑validity analysis.
