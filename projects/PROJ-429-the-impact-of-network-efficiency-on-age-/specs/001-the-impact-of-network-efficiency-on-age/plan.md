# Implementation Plan: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Branch**: `001-network-efficiency-aging` | **Date**: 2026-07-07 | **Spec**: `specs/001-network-efficiency-aging/spec.md`

## Summary

This project implements a computational pipeline to quantify the topological organization of brain networks from resting-state EEG data, compute graph-theoretical metrics (path length, clustering, efficiency, modularity) using an Area Under the Curve (AUC) approach for robustness, and statistically analyze their association with age and cognitive performance (MMSE/MoCA). The approach involves downloading the Temple University Hospital (TUH) EEG Corpus (accession ID: `tuh_eeg`), applying MNE-Python for artifact removal and epoching (using fixed-duration epochs for connectivity), constructing functional connectivity matrices via coherence, deriving graph metrics (AUC across densities), and performing Spearman correlations and multiple regression (Cognition ~ Efficiency + Covariates) with multiple-comparison correction. The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners.

**Critical Constraint**: The study relies on a single dataset (TUH) containing both EEG and cognitive metadata. If cognitive scores are missing for participants in the TUH corpus, the analysis for cognitive prediction will be restricted to age correlation only, acknowledging the limitation. No cross-dataset matching is attempted.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: MNE-Python, NetworkX, NumPy, SciPy, Pandas, Scikit-learn, Statsmodels, PyYAML, PyWavelets  
**Storage**: Local file system (CSV/Parquet for intermediate data); no external database  
**Testing**: pytest (unit tests for metric computation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Computational research pipeline / CLI tool  
**Performance Goals**: Process a representative subset of EEG data within 6 hours; memory usage < 7 GB  
**Constraints**: No GPU; no deep learning training; data subset to fit RAM; multiple-comparison correction mandatory  
**Scale/Scope**: A sample of participants (subset of TUH/PhysioNet); A core set of metrics; Primary outcomes (age, cognition)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Plan mandates pinned seeds, isolated virtualenv, and canonical data sources (TUH). |
| II. Verified Accuracy | PASS | Plan requires citation of validated instruments and verified dataset URLs only. |
| III. Data Hygiene | PASS | Plan mandates checksums, immutable raw data, and derived file naming conventions. |
| IV. Single Source of Truth | PASS | Plan enforces traceability via `trace_id` (SHA-256 of source file + code block hash) injected into output CSVs. |
| V. Versioning Discipline | PASS | Plan mandates that `download.py` and `preprocess.py` generate SHA-256 hashes stored in `state/version_map.yaml`, triggering `updated_at` timestamp updates upon artifact changes. |
| VI. Electrophysiological Signal Integrity | PASS | Plan specifies MNE-Python pipeline with bandpass filtering (low-frequency to a specific upper bound defined by the study's methodological constraints.) and ICA to preserve temporal structure while removing artifacts. |
| VII. Non-Circular Predictor-Outcome Separation | PASS | Predictors (EEG networks) and outcomes (age/cognition) are from independent sources; no circular construction. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-efficiency-aging/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── participant.schema.yaml
│   ├── network_metric.schema.yaml
│   ├── correlation_result.schema.yaml
│   └── regression_result.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-429-the-impact-of-network-efficiency-on-age-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── main.py                 # Entry point for pipeline
│   ├── config.py               # Configuration and paths
│   ├── data/
│   │   ├── download.py         # Data fetching, checksumming, hash injection
│   │   └── preprocess.py       # MNE-Python preprocessing (s epochs for connectivity)
│   ├── network/
│   │   ├── connectivity.py     # Coherence calculation (Welch/epochs of appropriate duration)
│   │   └── metrics.py          # Graph-theoretical metrics (AUC approach)
│   ├── stats/
│   │   ├── correlation.py      # Spearman correlation
│   │   ├── regression.py       # Multiple regression (Cognition ~ Efficiency)
│   │   └── correction.py       # FDR/Bonferroni
│   └── viz/
│       └── plots.py            # Age-stratified visualizations
├── data/
│   ├── raw/                    # Downloaded raw/parquet files
│   ├── processed/              # Preprocessed epochs, connectivity matrices
│   └── results/                # Metrics CSVs, regression tables
├── state/
│   └── version_map.yaml        # Artifact hashes and timestamps (Constitution V)
├── tests/
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── ...
```

**Structure Decision**: Single project structure selected to maintain simplicity for a research pipeline. Modules are separated by domain (data, network, stats, viz) to ensure modularity and testability while avoiding unnecessary complexity.

## Test Coverage Matrix

| Test File | Covered User Stories | Covered Functional Requirements |
|-----------|---------------------|---------------------------------|
| `tests/unit/test_metrics.py` | US-1 | FR-003, FR-008 |
| `tests/unit/test_stats.py` | US-2 | FR-004, FR-006, FR-007 |
| `tests/integration/test_pipeline.py` | US-1, US-2, US-3 | FR-001, FR-002, FR-005, SC-001, SC-003 |

**Test Decision**: Explicit mapping ensures every requirement is validated. The `test_pipeline.py` specifically verifies the end-to-end flow including data download, preprocessing, and statistical output generation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple-comparison correction module | Required by FR-006 and SC-004 to control FWER | Ignoring correction would inflate Type I error rates, violating statistical rigor. |
| Sensitivity analysis on threshold | Required by FR-008 and SC-003 to ensure robustness | Single threshold analysis risks findings being artifacts of arbitrary parameter choice. |
| VIF check in regression | Required by Assumption about collinearity | Omitting VIF check risks invalid coefficient estimates due to multicollinearity. |
| AUC for Network Metrics | Required by Methodology Review (concern 7db2650b) | Single fixed threshold (0.1) is arbitrary and sensitive to density; AUC is robust. |
| 10s Epochs for Coherence | Required by Scientific Soundness Review (concern b12f8fb7) | Short epochs yield noisy coherence estimates.; A sufficiently high sampling rate provides sufficient frequency resolution.. |

## Versioning & Hashing Mechanism

To satisfy Constitution Principle V (Versioning Discipline) and IV (Single Source of Truth):
1. **Hash Generation**: `download.py` and `preprocess.py` compute SHA-256 hashes of input files and the specific code block version (via git commit hash or file hash).
2. **Trace ID**: These hashes are combined and injected as a `trace_id` column in all output CSVs (Participant, NetworkMetric, etc.).
3. **State Management**: All hashes and `updated_at` timestamps are written to `state/version_map.yaml`.
4. **Trigger**: Any change to a source file or data artifact updates the corresponding entry in `version_map.yaml` and triggers a timestamp update.

## Traceability Mechanism

To satisfy Constitution Principle IV (Single Source of Truth):
1. **Trace ID Injection**: Every row in output CSVs (Participant, NetworkMetric, CorrelationResult, RegressionResult) includes a `trace_id` field.
2. **Composition**: `trace_id` = SHA-256(raw_source_file + code_block_hash).
3. **Paper Linkage**: Every statistic in the final paper is linked to a specific `trace_id`, which can be traced back to exactly one row in `data/` and one block in `code/`.
4. **Verification**: The `state/version_map.yaml` serves as the index for these trace IDs.
