# Implementation Plan: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

**Branch**: `001-impact-of-visual-attention-patterns` | **Date**: 2026-07-08 | **Spec**: `specs/001-impact-of-visual-attention-patterns/spec.md`
**Input**: Feature specification from `/specs/001-impact-of-visual-attention-patterns/spec.md`

## Summary

This project implements a computational analysis pipeline to investigate how visual attention patterns (fixation duration on source attribution) interact with headline emotional valence and cognitive reflection scores to influence belief susceptibility. 

**Critical Distinction**: The current phase focuses on **Pipeline Validation** using synthetic data to verify the code's ability to ingest, process, and model eye-tracking data. The **Scientific Inquiry** phase (testing the WYSIATI hypothesis) is deferred until a real-world dataset containing the full triad (Eye-tracking + Headline Text + Belief Rating) is acquired. Synthetic data is used *only* to validate the computational pipeline (ingestion, I-VT, regression logic) and to test the system's ability to handle null results. It does not validate the scientific hypothesis.

The system ingests raw eye-tracking data (or synthetic equivalents), applies I-VT fixation detection, calculates emotional valence using NRC/VADER lexicons, and executes a mixed-effects regression model. It includes robustness checks for fixation thresholds and sensitivity analyses for multiple comparisons, strictly adhering to CPU-only execution constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `datasets` (HuggingFace - for verified ROI/VADER structural validation only), `nltk`, `seaborn`.  
**Storage**: Local file system (`data/` for raw and processed CSV/Parquet, `output/` for results).  
**Testing**: `pytest` with synthetic data mocks for regression logic.  
**Target Platform**: Linux (Ubuntu-latest GitHub Actions runner).  
**Project Type**: Data Analysis Pipeline / Research Script.  
**Performance Goals**: Complete full pipeline (ingestion → regression → robustness) within 300 minutes on 2 CPU cores, 7GB RAM.  
**Constraints**: No GPU usage; no heavy deep learning models; data sampled to fit RAM; random seeds pinned for reproducibility.  
**Scale/Scope**: Single dataset processing; ~10k-50k trials (synthetic) to test *computational scalability* and *memory constraints* (SC-005), not statistical power for the WYSIATI hypothesis.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility**: Random seeds will be pinned in `code/`. External datasets will be fetched via `datasets.load_dataset` from verified HuggingFace URLs (for structural validation only).
2.  **Verified Accuracy**: All dataset citations in `research.md` are restricted to the "# Verified datasets" block provided in the prompt. No new URLs invented.
3.  **Data Hygiene**: Raw data will be checksummed upon download. All transformations (fixation detection, valence calculation) will write to new files in `data/processed/`. PII checks will be run via `Repository-Hygiene Agent` (simulated in plan).
4.  **Single Source of Truth**: All figures and stats in the final report will trace back to `output/regression_results.csv` and `output/robustness_summary.csv`.
5.  **Versioning Discipline**: Artifact hashes will be recorded in `state/` upon successful run.
6.  **Multi-Modal Data Integrity**: Eye-tracking data (fixations) and self-reported belief ratings will be processed in **separate, linked streams** (Gaze stream: `01_preprocessing.py`; Belief/CRT stream: synthetic generation) until the merge step (`03_data_merge.py`), ensuring no circular computation.
7.  **Outcome-Neutral Validation**: The analysis protocol includes a **Null Result Protocol**. If the regression p-value for the interaction term is >= 0.05, the system MUST generate a 'Null Result Report' and treat this as a primary finding, not a failure.

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-visual-attention-patterns/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_preprocessing.py          # Ingest raw data, I-VT detection, ROI mapping, data loss filtering
├── 02_valence_calculation.py    # NRC/VADER application, headline text processing (runs AFTER merge)
├── 03_data_merge.py             # Merge gaze, valence, CRT, and belief ratings
├── 04_regression_analysis.py    # Mixed-effects model (three-way interaction), Holm-Bonferroni correction (FR-007)
├── 05_robustness_analysis.py    # Sensitivity sweeps (multiple thresholds) -> generates output/robustness_summary.csv
├── 06_visualization.py          # Generate plots for paper, measure runtime (SC-005)
├── 09_null_result_report.py     # Generate Null Result Report if p >= 0.05 (Outcome-Neutral Validation)
└── requirements.txt             # Pinned dependencies
tests/
├── unit/
│   ├── test_preprocessing.py
│   └── test_valence.py
└── integration/
    └── test_full_pipeline.py
data/
├── raw/                         # Downloaded parquet files (checksummed)
├── processed/                   # Cleaned CSVs/Parquets
└── synthetic/                   # Synthetic test data for unit tests (no hypothesis-driven correlations)
output/
├── regression_results.csv
├── robustness_summary.csv
├── runtime.log                  # Total runtime log for SC-005
├── null_result_report.md        # Generated if p >= 0.05
└── figures/
```

**Structure Decision**: Single-project structure chosen for simplicity and direct data flow. All scripts are linear and sequential, minimizing dependency complexity. The separation of preprocessing, valence, and analysis ensures modularity while maintaining a clear data lineage.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified. The plan strictly adheres to the spec and constitution. | N/A |

## FR/SC Mapping

- **FR-001 (I-VT Detection)**: Addressed by `01_preprocessing.py`.
- **FR-002 (>20% Data Loss Filter)**: Addressed by `01_preprocessing.py`.
- **FR-003 (NRC/VADER Fallback)**: Addressed by `02_valence_calculation.py`.
- **FR-004 (Mixed-Effects Model)**: Addressed by `04_regression_analysis.py`.
- **FR-005 (Sensitivity Analysis {50, 100, 150}ms)**: Addressed by `05_robustness_analysis.py`.
- **FR-006 (Causal Framing)**: Addressed by `04_regression_analysis.py` (populates `causal_framing_statement` in output; disclaimer for synthetic data).
- **FR-007 (Multiple-Comparison Correction)**: Addressed by `04_regression_analysis.py` (Holm-Bonferroni).
- **SC-001 (Data Loss Proportion)**: Measured in `01_preprocessing.py` and logged.
- **SC-002 (Interaction P-Value)**: Output in `regression_results.csv`.
- **SC-003 (Robustness Variation)**: Measured in `05_robustness_analysis.py` and output in `robustness_summary.csv`.
- **SC-004 (Family-Wise Error Rate)**: Measured and reported in `robustness_summary.csv` (columns: `family_wise_error_rate`, `alpha_level_used`).
- **SC-005 (Runtime Limit)**: Measured and reported in `output/runtime.log` (logged by `06_visualization.py`).

## Data Flow

1.  **Ingestion**: Raw Parquet files (from verified ROI dataset) or synthetic data are loaded into `Participant` and `GazeEvent` tables.
2.  **Filtering**: Participants with `data_loss_ratio` > 0.20 are excluded.
3.  **Merge**: `GazeEvent` is joined with `Stimulus` and `Participant` on IDs in `03_data_merge.py`. **Headline text is available at this step.**
4.  **Valence Calculation**: `Stimulus` table is populated by applying NRC/VADER to `headline_text` in `02_valence_calculation.py` (runs AFTER merge).
5.  **Outlier Capping**: CRT scores are capped at 1st/99th percentiles in `02_valence_calculation.py` or `03_data_merge.py` (T023) **before** any correlation analysis (T037).
6.  **Regression**: The aggregated dataset is fed into the Mixed-Effects Model in `04_regression_analysis.py`.
7.  **Robustness**: `05_robustness_analysis.py` re-runs the regression with 50/100/150ms thresholds and generates `output/robustness_summary.csv`.
8.  **Null Result Protocol**: `09_null_result_report.py` is triggered if p >= 0.05 to generate a formal report.
9.  **Output**: `AnalysisResult` is written to `output/regression_results.csv` and `output/robustness_summary.csv`. Runtime is logged to `output/runtime.log`.