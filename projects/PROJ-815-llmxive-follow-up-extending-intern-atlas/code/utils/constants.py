"""
Constants for the llmXive follow-up: extending Intern-Atlas project.

Defines date ranges, edge types, and retraction label mappings used
throughout the data extraction and analysis pipeline.
"""

# Date range configuration
START_YEAR = 2010
END_YEAR = 2018
DATE_RANGE = (START_YEAR, END_YEAR)

# Valid edge types (human-annotated only)
# Excludes LLM-inferred and retraction-outcome types to prevent semantic leakage
EDGE_TYPE_IMPROVES = "improves"
EDGE_TYPE_REPLACES = "replaces"
EDGE_TYPE_EXTENDS = "extends"

VALID_EDGE_TYPES = {
    EDGE_TYPE_IMPROVES,
    EDGE_TYPE_REPLACES,
    EDGE_TYPE_EXTENDS,
}

# Retraction label mappings
# 0 = Robust (no retraction, no fragile flags)
# 1 = Fragile (retraction with reason FR-004 or similar indicating fragility)
# 2 = Retraction-Only (retracted but not classified as fragile)
LABEL_ROBUST = 0
LABEL_FRAGILE = 1
LABEL_RETRACTION_ONLY = 2

RETRACTION_LABELS = {
    LABEL_ROBUST: "Robust",
    LABEL_FRAGILE: "Fragile",
    LABEL_RETRACTION_ONLY: "Retraction-Only",
}

# Reverse mapping for lookup
RETRACTION_LABEL_VALUES = {
    "Robust": LABEL_ROBUST,
    "Fragile": LABEL_FRAGILE,
    "Retraction-Only": LABEL_RETRACTION_ONLY,
}

# Feature engineering constants
MIN_OUTGOING_EDGES_FOR_ENTROPY = 1
LEVENSHTEIN_THRESHOLD = 0.85

# Model training constants
RANDOM_SEED = 42
TEST_SIZE = 0.2

# Robustness analysis constants
PERMUTATION_ITERATIONS = 100
VIF_THRESHOLD = 5.0
MI_THRESHOLD = 0.1
THRESHOLD_SWEEP_VALUES = [0.3, 0.5, 0.7]