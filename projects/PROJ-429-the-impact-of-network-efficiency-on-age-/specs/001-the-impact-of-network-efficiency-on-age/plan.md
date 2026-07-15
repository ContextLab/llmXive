# Implementation Plan: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Branch**: `001-network-efficiency-aging` | **Date**: 2026-07-07 | **Spec**: `spec.md`

## Summary

This project quantifies the relationship between resting-state brain network efficiency (derived from graph-theoretical metrics on EEG) and age/cognitive performance in older adults. The technical approach involves downloading preprocessed EEG data from the **Temple University Hospital (TUH) EEG Corpus** (as mandated by FR-001), constructing functional connectivity matrices using **Imaginary Coherence** (to address volume conduction), computing graph metrics (path length, efficiency, modularity), and performing Spearman correlations and multiple regressions with strict multiple-comparison correction.

**Critical Data Note**: The current "Verified datasets" block does not contain a source linking EEG signals with clinical cognitive scores (MMSE/MoCA). Consequently, the **Cognitive Correlation Analysis (US-2/US-3) is BLOCKED** until a valid, linked dataset is added to the verified list. The pipeline will proceed with **EEG-only analysis** (calculating metrics and correlating with Age if available) and will flag the missing cognitive data. Synthetic data is **NOT** used for the final scientific analysis; it is reserved strictly for pipeline unit testing (US-2).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `numpy`, `pandas`, `scikit-learn`, `networkx`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `requests`  
**Storage**: Local CSV/JSON/Parquet files in `data/` and `results/`  
**Testing**: `pytest` (unit tests for graph metrics, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline  
**Performance Goals**: Process full available corpus in batches (20 subjects/batch) within 6 hours; memory usage < 6GB.  
**Constraints**: No GPU; no large-LLM inference; strict adherence to verified dataset URLs; no circular predictor-outcome construction.  
**Scale/Scope**: Single study. Sample size (N) is determined dynamically by the number of participants in the verified TUH EEG Corpus with valid metadata and linked IDs. If N < 85, the study is flagged as underpowered.

## Constitution Check

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PARTIAL** | `requirements.txt` pinned; random seeds set. *Note: Scientific reproducibility blocked by missing cognitive data; Pipeline reproducibility PASS.* |
| **II. Verified Accuracy** | **BLOCKED** | Cognitive data source missing from verified list. Pipeline runs on EEG-only. |
| **III. Data Hygiene** | **PASS** | Checksums recorded in `state/`; raw data immutable. |
| **IV. Single Source of Truth** | **PARTIAL** | Results trace to `data/` CSVs, but cognitive results are missing. |
| **V. Versioning Discipline** | **PASS** | Content hashes used for artifact invalidation. |
| **VI. Electrophysiological Signal Integrity** | **PASS** | Pipeline uses MNE-Python with bandpass (low-frequency to high-frequency cutoff), ICA, and **Imaginary Coherence**. |
| **VII. Non-Circular Predictor-Outcome** | **BLOCKED** | Outcome (Cognition) data missing; independence cannot be verified for final analysis. *Note: Pipeline architecture is valid, but data availability blocks final analysis.* |

## Project Structure

### Documentation (this feature)
```text
specs/001-network-efficiency-aging/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── dataset.schema.yaml
    ├── metrics.schema.yaml
    ├── output.schema.yaml
    └── results.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-429-the-impact-of-network-efficiency-on-age-/
├── code/
│   ├── __init__.py
│   ├── config.yaml          # Pipeline parameters (thresholds, bands)
│   ├── requirements.txt
│   ├── 01_download_data.py
│   ├── 02_preprocess_eeeg.py
│   ├── 03_compute_graph_metrics.py
│   ├── 04_correlation_analysis.py
│   ├── 05_regression_analysis.py
│   ├── 06_visualization.py
│   └── utils/
│       ├── cognitive_registry.py
│       └── stats_helpers.py
├── data/
│   ├── raw/
│   └── processed/
├── results/
│   ├── metrics.csv
│   ├── correlations.json
│   ├── power_analysis.json
│   ├── fwer_check.json
│   └── regression_summary.json
└── tests/
    ├── test_graph_metrics.py
    └── test_pipeline.py
```

**Structure Decision**: Single Python package structure (`code/`) to ensure modularity and testability. All data flows from `data/raw` → `data/processed` → `results/`. Parameters are loaded from `code/config.yaml`. Intermediate data is converted to Parquet for efficient batch processing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multiple Comparison Correction** | FR-006 requires FWER control for >1 test. | Simple p-values inflate Type I error; Bonferroni/FDR is standard for neuroimaging. |
| **Sensitivity Analysis (Threshold)** | FR-008 requires stability check. | Single threshold risks artifact; sweeping a range of values ensures robustness. |
| **Cognitive Registry** | FR-007 requires validation of tools. | Hardcoded check prevents invalid self-reported scores from skewing results. |
| **Volume Conduction Correction** | Methodology requires robust connectivity. | Coherence is sensitive to field spread; Imaginary Coherence is required for valid graph metrics. |
| **Power Analysis** | SC-002 requires simulation-based power check. | Static N assumptions are unreliable; simulation ensures study validity. |
| **Batch Processing** | RAM constraints (7GB). | Processing full corpus at once exceeds memory; batch processing (20 subjects) ensures feasibility. |