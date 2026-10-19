"""Pinned configuration for the brain-network-dynamics / improvisation pipeline.

All random seeds, sliding-window parameters, QC thresholds, and analysis
constants are pinned here (Constitution Principle I: reproducibility).
Nothing in this file is data-dependent; every value is a fixed,
documented parameter of the analysis.

NOTE ON LABELING: the 100 "blocks" are a deterministic contiguous-vertex
grouping of the fsLR-64k surface, NOT a neuroanatomical parcellation.
All downstream outputs derived from them are "vertex-block connectivity
descriptors", never brain-network properties.
"""
from pathlib import Path

# ------------------------------------------------------------------
# Verified data source (sole input; see code/download_openneuro.py)
# ------------------------------------------------------------------
HF_REPO_ID = "clane9/openneuro-fslr64k"
HF_REPO_TYPE = "dataset"
HF_SPLIT = "test"
SHARD_BASENAME = "test-00000-of-00016.parquet"

# ------------------------------------------------------------------
# Reproducibility: pinned seeds
# ------------------------------------------------------------------
DEFAULT_SEED = 42
SENSITIVITY_SEED = 123  # documented re-run seed (quickstart section 6)
LOUVAIN_SEED = 42       # seeded Louvain modularity (FR-003)

# ------------------------------------------------------------------
# Timing / sliding-window parameters (FR-003, FR-006)
# ------------------------------------------------------------------
TR_SECONDS = 1.0          # repetition time used to convert seconds -> frames
DEFAULT_WINDOW_SECONDS = 45.0
DEFAULT_STEP_SECONDS = 10.0
SENSITIVITY_WINDOW_SECONDS = [30.0, 45.0, 60.0]
SENSITIVITY_STEP_SECONDS = [5.0, 10.0]
MIN_TIMEPOINTS_PER_WINDOW = 30  # windows below this are skipped and logged

# ------------------------------------------------------------------
# Preprocessing (FR-002, Python adaptation per plan amendment)
# ------------------------------------------------------------------
BANDPASS_LOW_HZ = 0.01
BANDPASS_HIGH_HZ = 0.1
N_VERTEX_BLOCKS = 100    # deterministic contiguous-vertex scheme

# ------------------------------------------------------------------
# QC bad-volume rule (spec edge case; fully specified in T003)
# ------------------------------------------------------------------
FD_THRESHOLD_MM = 0.5            # volume is bad when FD > 0.5 mm (if FD column exists)
DVARS_MAD_MULTIPLIER = 3.0       # no-FD fallback: DVARS-like statistic >
MAD_TO_SD_CONSTANT = 1.4826      # run_median + 3 * (1.4826 * MAD)
MAX_BAD_VOLUME_FRACTION = 0.20   # subject excluded when >20% of volumes are bad

# ------------------------------------------------------------------
# Statistical analysis (FR-005, FR-010 as amended; SC-001, SC-005)
# ------------------------------------------------------------------
N_PERMUTATIONS = 1000            # Freedman-Lane residual permutations (pinned)
FDR_ALPHA = 0.05                 # Benjamini-Hochberg FDR level
TARGET_POWER = 0.80              # FR-010 "[deferred]" value, pinned here
COHENS_D = 0.5                   # medium effect size (FR-010)
ALPHA = 0.05                     # two-tailed test level
PCA_VARIANCE_THRESHOLD = 0.80    # retain components explaining >=80% cumulative variance
N_MIN_SUBJECTS_FLOOR = 20        # Constitution VII N>=20 presupposition floor

# ------------------------------------------------------------------
# Derived paths (relative to the project root, resolved via llmxive_toolkit)
# ------------------------------------------------------------------
RAW_SHARD_RELATIVE = Path("raw") / SHARD_BASENAME
DERIVED_DIR_NAME = "raw"          # data/raw for the shard; derived files under data/derived
CHECKSUMS_FILENAME = "checksums.json"
COLUMN_INVENTORY_RELATIVE = Path("raw") / "column_inventory.json"

# Stage order for the CLI orchestrator (code/run_all.py)
STAGE_ORDER = [
    "download",
    "extract",
    "fix_exclusion_log",
    "metrics",
    "pca",
    "analysis",
    "sensitivity",
    "visualization",
    "manifest",
]
