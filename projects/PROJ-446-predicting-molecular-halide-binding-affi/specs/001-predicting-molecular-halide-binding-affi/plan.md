# Implementation Plan: Predicting Molecular Halide Binding Affinities

**Branch**: `001-predicting-halide-binding-affinities` | **Date**: 2024-01-15 | **Spec**: `specs/001-predicting-molecular-halide-binding-affinities/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-halide-binding-affinities/spec.md`

## Summary

This project implements a machine learning pipeline to predict molecular halide binding affinities (F⁻, Cl⁻, Br⁻, I⁻) for host molecules. The primary technical approach involves ingesting experimental data from NIST/PubChem (or generating physics-constrained simulated data if real data is insufficient), computing RDKit molecular descriptors, training Random Forest and Gradient Boosting models with host-molecule-stratified cross-validation, and performing statistical comparisons of model performance across halide ions using bootstrap confidence intervals.

**Critical Fallback Logic**: Per **FR-011**, if the dataset contains fewer than 50 hosts with ≥3 halides each, the system **MUST** switch to **Single-Halide Prediction Mode**. In this mode:
1.  The system generates a simulated dataset for the **most abundant halide only**.
2.  **Comparative Analysis (US-4) is ABORTED** because there is no variance in `halide_identity` to compare.
3.  All outputs are flagged as "Simulated Data Mode" and explicitly state that the primary research question (comparative selectivity) is unanswerable.
4.  The pipeline continues to validate the ML code path (training, feature importance) but does not claim to predict real-world halide selectivity.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `scikit-learn>=1.4.0`, `rdkit`, `pandas`, `numpy`, `requests`, `beautifulsoup4`, `pyyaml`, `seaborn`, `matplotlib`
**Storage**: Local CSV/JSON/Parquet files (no external database)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free-tier: 2 vCPU, 7 GB RAM)
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: Complete full pipeline (data ingestion to report) within ≤6 hours; peak RAM ≤7 GB.
**Constraints**: No GPU acceleration for model training (CPU-first); must handle data scarcity via simulated fallback; strict host-molecule split to prevent leakage.
**Scale/Scope**: Target ≥50 host molecules with ≥3 halide measurements each; if <50, switch to simulated single-halide mode.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; external data fetched from canonical sources. | `code/` scripts will set `RANDOM_SEED=42` globally. Data ingestion will target verified HuggingFace URLs for NIST/PubChem proxies or direct scraping with retry logic. |
| **II. Verified Accuracy** | Citations verified against primary sources. | `research.md` will cite only URLs from the "Verified datasets" block. **Simulated Data**: No external source; validity is satisfied by internal reproducibility (seeded RNG) and explicit "Simulated" flagging. |
| **III. Data Hygiene** | Checksums recorded; no in-place modification. | `state.yaml` will store SHA-256 hashes for all `data/raw/` and `data/processed/` files. Derivations create new files (e.g., `raw.csv` → `processed.csv`). |
| **IV. Single Source of Truth** | Figures/stats trace to one row in `data/` and one block in `code/`. | The analysis scripts will read strictly from `data/processed/halide_binding_data.csv` and write results to `data/processed/model_runs.json` and `data/processed/feature_analysis.json`. |
| **V. Versioning Discipline** | Artifact hashes updated on change. | The Advancement-Evaluator Agent will append content hashes to `state.yaml` upon every file write in `code/` or `data/`. |
| **VI. Halide-Specific Evaluation** | Per-halide R²/RMSE reported. | **Real Data**: Split test sets by `halide_identity` and compute metrics separately. **Simulated (Single-Halide) Mode**: Principle VI is **SUSPENDED**. Comparative metrics are reported as `N/A` and `comparative_analysis_aborted: true`. |
| **VII. Molecular Split Validation** | Split by host ID, not measurement. | The `GroupKFold` splitter from `scikit-learn` will be used, grouping by `host_id`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-halide-binding-affinities/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-446-predicting-molecular-halide-binding-affi/
├── code/
│   ├── 01_data_ingestion.py       # Scraping, filtering, simulation (FR-001, FR-011)
│   ├── 02_feature_engineering.py  # RDKit descriptors, fingerprints (FR-002)
│   ├── 03_model_training.py       # RF/GB, GroupKFold, CV (FR-004, FR-005)
│   ├── 04_feature_analysis.py     # Stability, PDP, Physical Plausibility (FR-006, FR-013)
│   ├── 05_statistical_reporting.py# Bootstrap CI, Associational disclaimer (FR-009, FR-012)
│   └── utils.py                   # Shared constants, logging, schema validation
├── data/
│   ├── raw/                       # Downloaded raw files (if any)
│   └── processed/
│       ├── halide_binding_data.csv
│       ├── model_runs.json
│       └── feature_analysis.json
├── tests/
│   ├── test_data_ingestion.py
│   ├── test_model_split.py
│   └── test_statistical_reporting.py
├── state.yaml                     # Artifact hashes, versioning
└── requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead. All logic resides in `code/` with data flowing through `data/processed/`. This aligns with the CLI nature of the pipeline and the constraints of the GitHub Actions runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Simulated Data Fallback (FR-011)** | Real halide binding data is sparse and often access-gated; a fallback ensures the pipeline runs and produces *some* result (even if flagged) rather than failing silently. | Removing the fallback would cause the pipeline to abort if <50 hosts are found, violating the requirement to produce a report even under data scarcity. |
| **Host-Molecule Stratified Split** | Standard random splitting would leak data (same host in train and test), inflating R². | A simple random split would violate Constitution Principle VII and produce scientifically invalid metrics. |
| **Bootstrap CI over Wilcoxon** | N=5 folds is insufficient for Wilcoxon signed-rank; bootstrap allows robust CI estimation on small sample sizes. | Using Wilcoxon on N=5 would be statistically invalid and rejected by the Reference-Validator. |
| **Single-Halide Abortion** | FR-011 mandates single-halide mode if data is insufficient. Comparative analysis is impossible in this mode. | Attempting to compare a single halide against itself is mathematically invalid. The plan explicitly aborts the comparison. |

## Implementation Tasks

### T001: Data Ingestion & Validation
- **Input**: Raw HTML/JSON from NIST/PubChem (or empty).
- **Logic**:
  1. Attempt scraping per FR-001.
  2. Filter for solvents (acetonitrile, chloroform, DCM).
  3. Validate SMILES.
  4. Count hosts with ≥3 halides.
  5. **If count < 50**: Trigger FR-011. Log warning. Generate simulated data for **most abundant halide only**.
  6. **If count ≥ 50**: Proceed with real data.
- **Output**: `data/processed/halide_binding_data.csv` (validated against `dataset.schema.yaml`).

### T002: Feature Engineering
- **Logic**: Compute RDKit descriptors (ECFP4, Gasteiger charge sum, molecular volume).
- **Output**: Updated CSV with descriptor columns.

### T003: Data Power Check (FR-012)
- **Logic**: Count hosts per halide. If any halide has N < 10, set `underpowered` flag.
- **Output**: Metadata flag for reporting.

### T004: Model Training (Real Data Mode)
- **Logic**: Train RF/GB with GroupKFold on real data.
- **Output**: `data/processed/model_runs.json` with per-halide metrics.

### T016: Single-Halide Model Training (FR-011 Fallback)
- **Logic**:
  1. Detect `data_mode == 'Simulated'` and `halide_count == 1`.
  2. Train RF/GB on the single available halide (no grouping by halide needed, but GroupKFold by host still applies).
  3. Compute R²/RMSE for the single halide.
  4. **Do NOT compute pairwise differences**.
- **Output**: `data/processed/model_runs.json` with `comparative_analysis_aborted: true`.

### T012: Per-Halide Power Check (FR-012)
- **Logic**: Verify N >= 10 per halide. If not, set `underpowered` flag.
- **Output**: Flag passed to T017.

### T015: Feature Analysis & Physical Plausibility
- **Logic**:
  1. Compute feature stability (CV) via bootstrap.
  2. **Physical Plausibility Check**: If top feature is `charge_density`, verify coefficient sign is positive (attractive). If negative, flag as "Physically Implausible".
- **Output**: `data/processed/feature_analysis.json`.

### T017: Statistical Reporting
- **Logic**:
  1. If `data_mode == 'Real'` AND `halide_count >= 2`: Compute Bootstrap CI for pairwise differences.
  2. If `data_mode == 'Simulated'` OR `halide_count < 2`: Set `comparative_analysis_aborted: true`. Report "Comparative analysis not applicable due to single-halide data."
  3. Include "Associational" disclaimer.
- **Output**: Final report `data/processed/report.md`.