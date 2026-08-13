"""
Configuration module for the llmXive geometry extension project.

This module defines seed lists used throughout the pipeline and related
constants that describe the expected number of seeds.  The values are
deliberately small to keep test execution fast while still exercising the
disjoint‑seed logic required by the specification.

The seed lists are:
* ``MASK_DERIVATION_SEEDS`` – seeds used for deriving masks.
* ``EVAL_SEEDS`` – seeds used for evaluation runs.

The constants ``N_MASK_SEEDS`` and ``N_EVAL_SEEDS`` define the expected
lengths of the corresponding lists, and ``START_SEED`` is the first seed
for the evaluation set.
"""

# Number of mask‑derivation seeds
N_MASK_SEEDS: int = 5

# Seed range for mask derivation (0 .. N_MASK_SEEDS‑1)
MASK_DERIVATION_SEEDS = list(range(N_MASK_SEEDS))

# Evaluation seed configuration
START_SEED: int = 100
N_EVAL_SEEDS: int = 10

# Evaluation seeds: START_SEED .. START_SEED + N_EVAL_SEEDS‑1
EVAL_SEEDS = list(range(START_SEED, START_SEED + N_EVAL_SEEDS))
