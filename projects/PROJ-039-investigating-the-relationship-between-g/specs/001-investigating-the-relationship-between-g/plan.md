# Implementation Plan: Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power (Virtual Cohort & Distributional Analysis)

**Branch**: `001-gut-microbiome-eeg-alpha` | **Date**: 2024-01-15 | **Spec**: `specs/001-gut-microbiome-eeg-alpha/spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-eeg-alpha/spec.md`

## Summary

This project implements a **Virtual Cohort Matching** and **Distributional Comparison** pipeline to investigate the relationship between gut microbiome composition and resting-state EEG alpha power. 

**Critical Methodological Shift**: The original "Ecological Correlation" approach (aggregating independent datasets into demographic strata and correlating means) has been **abandoned** due to critically low statistical power (N=5-20) and the tautological nature of correlating demographic bin means.

**New Two-Path Strategy**:
1.  **Path A (Virtual Cohort Matching)**: Attempt to match individual subjects from the American Gut Project (AGP) and OpenNeuro ds000246 based on demographic similarity (Age, Sex, BMI). If ≥10 valid matched pairs are found, perform Spearman correlation on individual-level data (CLR-transformed taxa vs. alpha power).
2.  **Path B (Distributional Comparison)**: If <10 matched pairs are found, the pipeline automatically switches to comparing the full distributions of alpha power between groups defined by microbiome abundance levels (e.g., High vs. Low abundance of specific taxa) using non-parametric tests (Mann-Whitney U / Kolmogorov-Smirnov).

All results are framed as associational only. No causal inference is made.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `mne`, `qiime2` (CPU-light mode), `matplotlib`, `seaborn`, `pyyaml`, `skbio`  
**Storage**: Local CSV/Parquet files (data/, artifacts/)  
**Testing**: `pytest` (contract tests against schema validation, unit tests for statistical functions)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU)  
**Project Type**: computational-research-pipeline  
**Performance Goals**: Complete end-to-end analysis within 6 hours; memory usage < 7 GB; disk usage < 14 GB  
**Constraints**: No GPU acceleration; no deep learning; data subset to fit memory; CPU-only statistical methods  
**Scale/Scope**: Target: ≥10 matched individual pairs (Path A) OR ≥50 independent samples for distributional tests (Path B).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|---|---|
| **I. Reproducibility** | ✅ PASS | Plan mandates pinned versions in `requirements.txt`, random seeds in code, and canonical dataset sources. QIIME2 and MNE-Python versions will be pinned. |
| **II. Verified Accuracy** | ⚠️ PENDING | Primary datasets (AGP, OpenNeuro ds000246) lack verified URLs in the provided list. Plan mandates 'Manual Download + Checksum' protocol. Reproducibility is contingent on successful execution of this fallback. |
| **III. Data Hygiene** | ✅ PASS | Plan requires checksums for all data files, immutable raw data, and PII scanning. Derived files will have new names with provenance. |
| **IV. Single Source of Truth** | ✅ PASS | All figures/statistics will trace back to specific rows in `data/` and code blocks. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | ✅ PASS | Content hashes will be recorded for all artifacts. State file will be updated on any change. |
| **VI. Microbiome Data Reproducibility** | ⚠️ PENDING | AGP data will be fetched via manual download (v2.0 release) with recorded hash. QIIME2 pipeline will use pinned version. Reproducibility contingent on hash verification. |
| **VII. EEG Signal Processing Consistency** | ⚠️ PENDING | OpenNeuro ds000246 data will be processed with pinned MNE-Python version. Preprocessing parameters (0.5–45 Hz filter, ICA, 2-min epochs, Welch's method) will be documented in `preprocess.yaml`. Reproducibility contingent on data availability. |

**Gates Determined**: Principles II, VI, and VII are marked 'PENDING' due to the lack of verified URLs. The plan proceeds only if the 'Manual Download + Checksum' fallback is successfully executed and documented.

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-eeg-alpha/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── correlation.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-039-investigating-the-relationship-between-g/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── preprocess_microbiome.py
│   ├── preprocess_eeg.py
│   ├── match_cohorts.py        # NEW: Virtual matching logic
│   ├── correlation_analysis.py # UPDATED: Individual or Distributional
│   ├── visualization.py
│   └── main.py
├── data/
│   ├── raw/
│   │   ├── agp_microbiome/
│   │   └── openneuro_eeg/
│   ├── processed/
│   │   ├── microbiome_features.csv
│   │   ├── eeg_features.csv
│   │   ├── matched_pairs.csv   # NEW: Matched individual data
│   │   └── distribution_groups.csv # NEW: Grouped for dist. tests
│   └── metadata.json
├── artifacts/
│   ├── checksums.txt
│   ├── preprocess.yaml
│   └── analysis_results.json
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── docs/
    └── [feature-specific docs]
```

**Structure Decision**: Single project structure selected to maintain simplicity for a computational research pipeline. All code, data, and artifacts are organized under a unified project directory with clear separation of raw data, processed data, and analysis code. Tests are organized by type (contract, integration, unit) to ensure comprehensive validation.

## Complexity Tracking

> **No violations detected in Constitution Check; complexity tracking table omitted.**

## Implementation Phases

### Phase 0: Research & Dataset Validation
- **FR-001, FR-002**: Validate dataset availability and compatibility
  - Verify AGP data contains genus-level abundances and demographic metadata (age, sex, BMI).
  - Verify OpenNeuro ds000246 contains resting-state EEG with sufficient artifact-free recordings.
  - **Critical**: Confirm that OpenNeuro ds000246 lacks 'diet' variable. Plan will use (Age, Sex, BMI) for matching only.
  - **Fallback**: If no verified URL exists, execute 'Manual Download + Checksum' protocol. Record hash in `data/metadata.json`.
  - Document any mismatches or limitations (e.g., missing BMI in AGP, limited diet categories in OpenNeuro).

### Phase 1: Data Preprocessing & Matching
- **FR-001**: Microbiome preprocessing
  - Download AGP 16S rRNA data (Manual or Verified).
  - Process with QIIME2 (pinned version, CPU-light mode) to genus-level abundances.
  - Apply pseudocount (0.5) for zero handling.
  - Output: `data/processed/microbiome_features.csv` with ≥100 rows.
- **FR-002**: EEG preprocessing
  - Download OpenNeuro ds000246 data (Manual or Verified).
  - Preprocess with MNE-Python (pinned version):
    - Bandpass filter (0.5–45 Hz)
    - ICA artifact removal
    - Epoch into 2-minute segments
    - Compute alpha power (8–12 Hz) using Welch's method
  - Filter subjects with <80% valid epochs.
  - Output: `data/processed/eeg_features.csv` with ≥50 subjects.
- **NEW**: Virtual Cohort Matching
  - Match AGP and OpenNeuro subjects based on (Age, Sex, BMI) using nearest-neighbor or propensity scoring.
  - If ≥10 valid pairs found: Proceed to **Individual Correlation** (Path A).
  - If <10 pairs found: Proceed to **Distributional Comparison** (Path B) (group full datasets by AGP abundance levels).
  - Output: `data/processed/matched_pairs.csv` OR `data/processed/distribution_groups.csv`.

### Phase 2: Statistical Analysis
- **FR-004, FR-005**: CLR transformation and alpha power computation
  - Apply CLR transformation to microbiome data (pseudocount=0.5).
  - Compute alpha power per subject (already done in Phase 1).
- **FR-006**: Correlation Testing (Conditional)
  - **Path A (Matched Pairs)**: Spearman correlation between CLR-transformed taxa abundances (or PCoA axes) and alpha power for matched individuals. Apply Benjamini-Hochberg FDR correction (q<0.1).
  - **Path B (Distributional)**: Mann-Whitney U or KS test comparing alpha power distributions between high/low abundance groups (defined by AGP median split).
  - **Collinearity**: Use PCoA/PCA of CLR data (top few axes) to avoid testing 20 collinear taxa.
- **FR-007**: Permutation Testing
  - **Path A**: Permute subject labels in matched pairs (sufficient iterations).
  - **Path B**: Permute group labels in distributional test (sufficient iterations).
  - Output: `perm_test_passed` boolean flag.
- **FR-009**: Collinearity diagnostics
  - Report collinearity among taxa (VIF) and PCoA variance explained.
  - Acknowledge compositional constraints.

### Phase 3: Visualization & Reporting
- **FR-008**: Generate publication-ready visualizations
  - **Path A**: Scatter plots of matched pairs (alpha power vs. PC1/PC2 or top taxon).
  - **Path B**: Boxplots/VIolin plots of alpha power by abundance group.
  - Correlation heatmap (if Path A).
- **FR-010**: Include associational disclaimer
  - Ensure all outputs contain: "Note: This analysis is associational only; no causal inference is made."
- **SC-001 to SC-005**: Validate success criteria
  - Count matched pairs (≥10 required for Path A) OR group sizes (≥25 per group for Path B).
  - Count significant associations (q<0.1 or p<0.05).
  - Verify permutation test results.
  - Validate visualization completeness.

## Computational Feasibility

All methods are CPU-tractable and fit within GitHub Actions free-tier constraints:
- **No GPU/CUDA**: Statistical methods (Spearman, Mann-Whitney, Permutation) use `scipy` and `numpy` on CPU.
- **Memory**: Data subset to ~7 GB RAM; individual-level data is lightweight.
- **Disk**: ~14 GB limit; raw data stored in compressed formats, processed data in CSV/Parquet.
- **Runtime**: ≤6 hours; matching and correlation analysis are computationally lightweight.
- **Libraries**: Pinned versions in `requirements.txt` ensure CPU-only installation.

## Risk Mitigation

- **Dataset Mismatch**: If AGP or OpenNeuro ds000246 lack required variables, explicitly document the gap and adjust analysis scope (e.g., exclude BMI if unavailable).
- **Insufficient Matches**: If <10 valid pairs exist, the pipeline automatically switches to Distributional Comparison (Path B). No error exit.
- **Sparse Data**: Pseudocount (0.5) applied before CLR transformation to handle zeros.
- **Collinearity**: Use PCoA/PCA to reduce predictor dimensionality.
- **Causal Inference**: All outputs include the associational disclaimer (FR-010).

## Next Steps

1. Execute Phase 0: Research & Dataset Validation (Confirm dataset IDs and fallback strategy).
2. Proceed to Phase 1: Data Preprocessing & Virtual Matching.
3. Implement Phase 2: Statistical Analysis (Conditional on Match Count).
4. Complete Phase 3: Visualization & Reporting.
5. Validate all success criteria (SC-001 to SC-005).