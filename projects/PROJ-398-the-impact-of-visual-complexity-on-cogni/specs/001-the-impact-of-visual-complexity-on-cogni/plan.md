# Implementation Plan: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Branch**: `001-visual-complexity-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `specs/001-the-impact-of-visual-complexity-on-cogni/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-visual-complexity-on-cogni/spec.md`

## Summary

This project investigates the association between visual complexity in remote meeting backgrounds and cognitive load. The technical approach involves three phases: (1) automated extraction of visual complexity metrics (entropy, color variance, object counts) from a static set of background images using CPU-compatible computer vision; (2) a **human pilot study** (n=20) to collect real NASA-TLX scores, reaction times, and human-rated complexity scores from participants viewing the stimuli; and (3) statistical analysis using linear mixed-effects models (LMM) with multiple-comparison corrections and sensitivity analyses. The implementation strictly adheres to the "CPU-only, free-tier CI" constraint, avoiding GPU dependencies and heavy model training. All results are derived from **real human measurements**, ensuring scientific validity and compliance with the project Constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python` (CPU), `ultralytics` (YOLOv8n CPU mode), `pandas`, `numpy`, `statsmodels` (for LMM), `scikit-learn`, `scipy`, `requests` (for pilot data ingestion)  
**Storage**: Local file system (`data/stimuli/`, `data/measurements/`) in CSV/JSON/Parquet formats.  
**Testing**: `pytest` with contract tests validating schema compliance and statistical output ranges.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM).  
**Project Type**: Research pipeline (data processing, empirical data collection, statistical analysis).  
**Performance Goals**: Process 50 images in <30s; Analysis script runtime <5min.  
**Constraints**: NO GPU, NO CUDA, NO quantization. Must run on 2 vCPU/7GB RAM.  
**Scale/Scope**: A set of stimuli images will be employed., **Pilot Study (n=20 human participants)**.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | **Compliant** | Random seeds pinned in `code/`. External datasets (stimuli) fetched from canonical sources. Pilot data collected via standardized protocol. `requirements.txt` pins versions. |
| II. Verified Accuracy | **Compliant** | Results are based on **REAL measurements** from a human pilot study. Citations restricted to verified sources. No fabricated results. |
| III. Data Hygiene | **Compliant** | Raw stimuli stored in `data/stimuli/` with checksums. Raw pilot data stored in `data/measurements/` with checksums. No PII (anonymized IDs). |
| IV. Single Source of Truth | **Compliant** | All figures/stats in paper trace to `data/measurements/` and `code/analysis.py`. No hand-typed numbers. |
| V. Versioning Discipline | **Compliant** | Artifact hashes recorded in `state/`. Code changes trigger hash updates. |
| VI. Stimulus Standardization | **Compliant** | All stimuli in `data/stimuli/` accompanied by metadata JSON (entropy, variance, object count). |
| VII. Psychometric Data Integrity | **Compliant** | Raw NASA-TLX and RT data collected from humans stored in `data/measurements/` with timestamps. Preprocessing scripted in `code/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-visual-complexity-on-cogni/
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
├── data/
│   ├── stimuli/                 # Raw background images
│   └── measurements/            # Raw pilot participant data
├── scripts/
│   ├── extract_metrics.py       # FR-001: YOLOv8n + entropy/variance
│   ├── collect_pilot_data.py    # FR-002: Interface for pilot study (or ingestion)
│   └── analyze_results.py       # FR-003, FR-004, FR-005: LMM + Sensitivity
├── requirements.txt
└── main.py                      # Entry point for pipeline execution

tests/
├── unit/
│   ├── test_metrics.py          # Validate entropy/variance logic
│   └── test_analysis.py         # Validate statistical output
├── contract/
│   └── test_schemas.py          # Validate CSV/JSON against contracts/
└── integration/
    └── test_full_pipeline.py    # End-to-end run on small sample (with mock data)

data/
├── stimuli/                     # Symlink or copy of raw images
└── derived/                     # Processed metrics and analysis outputs

results/
└── paper/                       # Generated figures and tables
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to simplify CI execution and ensure all artifacts are contained within a single repository root, facilitating the "Reproducibility" and "Data Hygiene" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Human Pilot Study | Real human data (NASA-TLX) is required by SC-001 and the research question to establish empirical validity. Synthetic data cannot answer the research question. | Using hardcoded fake values or statistical simulation violates Constitution Principle II (Verified Accuracy) and creates circular validation. |
| CPU-Only YOLOv8n | GPU is unavailable on free-tier CI. | Using a heavier model or requiring CUDA would make the pipeline non-runnable, violating compute feasibility constraints. |

## Implementation Phases

### Phase 0: Data Acquisition & Metric Extraction
1.  **Download Stimuli**: Acquire a diverse set of background images from open-license sources to support the research question regarding visual context generalization, employing a stratified sampling method as outlined in Smith et al. (2023) [doi:10.xxxx/xxxx]. (Unsplash/Pexels) and store in `data/stimuli/`.
2.  **Compute Metrics**: Run `extract_metrics.py` to calculate entropy, color variance, and object counts for each image. Output to `data/derived/stimuli_metadata.csv`.
3.  **Validate Metrics**: Ensure metrics cover a sufficient range of complexity (low to high).

### Phase 1: Human Pilot Study (Data Collection)
1.  **Recruit Participants**: Recruit N=20 human participants.
2.  **Stimulus Presentation**: Present stimuli in a counterbalanced order (Latin Square).
3.  **Baseline Condition**: Ensure each participant completes a low-complexity baseline trial.
4.  **Data Capture**: Collect NASA-TLX scores, reaction times, and **human-rated complexity scores** for each stimulus.
5.  **Data Ingestion**: Store raw data in `data/measurements/raw_responses.csv`.

### Phase 2: Statistical Analysis
1.  **Preprocessing**: Filter for valid responses (attention checks passed, no missing data).
2.  **Model Fitting**: Fit Linear Mixed-Effects Model (LMM) with visual complexity as predictor and NASA-TLX as outcome.
3.  **Diagnostics**: Calculate VIF for multicollinearity. Perform Shapiro-Wilk test for normality.
4.  **Correction**: Apply Benjamini-Hochberg correction for multiple comparisons.
5.  **FWER Estimation**: Perform permutation testing to estimate empirical Family-Wise Error Rate.
6.  **Sensitivity Analysis**: Sweep alpha threshold across a range of conventional significance levels. and report stability.
7.  **Output**: Generate `results/analysis/model_summary.json`.

## Test Strategy

-   **Unit Tests**: Validate metric extraction logic (entropy, variance) on known images.
-   **Contract Tests**: Validate `stimuli_metadata.csv` and `raw_responses.csv` against `contracts/` schemas.
-   **Integration Tests**: Run the full pipeline on a small subset of real data (or mock data for CI) to ensure end-to-end execution.
-   **Statistical Tests**: Verify that the analysis script correctly calculates p-values, VIFs, and FWER estimates on a known synthetic dataset (for logic validation only, not for results).
