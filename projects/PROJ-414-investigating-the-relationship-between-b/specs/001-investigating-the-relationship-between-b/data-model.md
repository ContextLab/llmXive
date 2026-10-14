# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview

Schemas for every derived artifact. Contract tests in `tests/contract/` validate outputs against the files in `contracts/`. All behavioral/covariate fields are optional because their presence in the real data is determined at runtime; mandatory fields are only those the pipeline itself derives.

## Entities

- **Subject**: `subject_id`, optional real metadata (age, fd, task condition, skill proxy, instrument, genre, practice intensity, education, years of training), exclusion flag + reason, QC metrics.
- **QCRecord** (`qc_<subject>.json`): per-subject QC summary — fraction of bad volumes, exclusion flag, exclusion reason, motion-proxy description (FD column if present, else amplitude-based scrubbing, documented).
- **ColumnInventory** (`data/raw/column_inventory.json`): the real parquet column names, plus which expected behavioral/covariate fields (skill proxies, covariates, task labels) were found — this drives the conditional association stage.
- **ROITimeseries**: per-subject `(timepoints × 100)` matrix, long-format rows keyed by `subject_id`, `timepoint`, `roi_id` (vertex-block id).
- **NetworkMetric** (vertex-block connectivity descriptor): `subject_id`, `window_id`, `metric_name`, `value` (wide form in files: one row per subject/window).
- **PCAScores**: per-subject scores on retained principal components.
- **RegressionResult**: per-PC coefficient, permutation p (Freedman–Lane), FDR p, significance flag, null-result flag.
- **ManifestRow**: one row per subject in `results/manifest.csv` — the Single Source of Truth (FR-012).

## File Layout

```text
data/
├── raw/test-00000-of-00016.parquet   # untouched verified download
├── raw/column_inventory.json         # real column inventory from download step
├── checksums.json                    # SHA-256 of raw file
└── derived/
    ├── roi_timeseries_<subject>.csv
    ├── qc_<subject>.json
    ├── metrics_<subject>.csv
    └── pca_scores.csv
results/
├── manifest.csv
├── regression_results.csv            # only if association stage ran
├── sensitivity_summary.csv
├── power_analysis.json
└── fig_network_topology.png
```

## Schema Notes

- `roi_id` ranges over `roi_1` … `roi_100` (deterministic contiguous fsLR vertex blocks; **not neuroanatomical regions**).
- `window_id` starts at 0; only windows with ≥30 timepoints are emitted.
- `skill_proxy_used` records which real column (if any) served as the dependent variable; `"none"` triggers the documented halt path (expected outcome).
- Excluded subjects appear in the manifest with `excluded=true` and an `exclusion_reason` and may have null metric values, satisfying the edge-case requirement and SC-006 (every processed subject has a row).
- The manifest carries all available covariate columns and dynamic PC scores; see `contracts/manifest.schema.yaml`.