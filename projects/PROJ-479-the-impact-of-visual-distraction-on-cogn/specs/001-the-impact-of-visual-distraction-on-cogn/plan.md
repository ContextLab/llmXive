# Implementation Plan: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

**Branch**: `001-visual-distraction-cognitive-control` | **Date**: 2026-06-25 | **Spec**: `specs/001-visual-distraction-cognitive-control/spec.md`
**Input**: Feature specification from `/specs/001-visual-distraction-cognitive-control/spec.md`

## Summary

This project investigates the **empirical association** between visual complexity in home work environments and cognitive control performance (measured via Stroop/Flanker tasks). 

**Critical Strategy Shift**: The previous plan's reliance on synthetic data with hard-coded correlations was rejected for violating construct validity (creating a tautological study). This revised plan adopts a **Real Data, Proxy Linkage** strategy:
1.  **Acquire Real Data**: Download real cognitive task data from OpenML (Stroop/Flanker) and real workspace images from Unsplash.
2.  **Proxy Linkage**: Link the two datasets via **environmental metadata** (e.g., "Home Office", "Open Plan") rather than direct participant IDs, as no single public dataset links them directly.
3.  **Compute Metrics**: Run CPU-tractable computer vision (OpenCV, YOLOv8n) on the real Unsplash images to derive edge density, color entropy, and object count.
4.  **Empirical Analysis**: Perform statistical analysis (Pearson, Regression, VIF, Holm-Bonferroni) to test the null hypothesis that visual complexity is associated with cognitive performance.
5.  **Report**: Generate visualizations and reports framing all findings as associational, with explicit justification for the p<0.05 threshold.

This approach ensures the correlation is an **empirical observation** from real data, not a code artifact, satisfying the research question's requirement for ecological validity (within the limits of proxy linkage). Synthetic data is only used as a fallback if real data linkage fails to meet the N≥100 threshold.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `scipy`, `opencv-python-headless`, `ultralytics` (for CPU-tractable YOLOv8n object detection), `matplotlib`, `seaborn`, `requests` (for Unsplash API), `openml`, `pillow`
**Storage**: Local file system (`data/raw/`, `data/processed/`, `results/`)
**Testing**: `pytest` (unit tests for metrics, integration tests for pipeline)
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple vCPUs, ~7GB RAM)
**Project Type**: Data Analysis Pipeline / Research Script
**Performance Goals**: Total runtime ≤ 6 hours; Memory usage ≤ 6GB; No GPU dependency (CPU-first).
**Constraints**: 
- Must handle missing data gracefully (log and exclude).
- Must frame all results as associational (no causal claims).
- Must apply family-wise error correction (Holm-Bonferroni) for >3 tests.
- Must compute VIF and fallback to PCA if collinearity (VIF ≥ 5) is detected.
- All random seeds must be pinned for reproducibility.
- No PII in data; checksums recorded for all artifacts.
- **Pre-registered**: VIF threshold (≥5) and PCA fallback are pre-registered decisions.
- **Output Artifacts**: Must generate `results/statistics/multiplicity_table.csv`, `results/statistics/binning_sensitivity_table.csv`, and `results/statistics/justification.md`.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned random seeds in `code/` (specifically for the proxy matching algorithm) and checksums for all data artifacts in `data/`. External datasets (OpenML, Unsplash) will be fetched from canonical sources.
2.  **II. Verified Accuracy**: All citations for visual complexity methods (OpenCV, YOLO) and cognitive tasks (Stroop) will be validated against primary sources. The `Reference-Validator` will run on all generated docs.
3.  **III. Data Hygiene**: Raw data (OpenML, Unsplash downloads) will be preserved. Derivations (merged data, metrics) will be new files with documented hashes. No in-place modification. **PII Sanitization**: Image paths will be renamed to `img_<hash>.jpg` and EXIF data stripped to remove PII immediately upon download.
4.  **IV. Single Source of Truth**: All statistics in the final report will trace back to `results/statistics/statistics.json` and `results/statistics/multiplicity_table.csv`. No hand-typed numbers.
5.  **V. Versioning**: All artifacts will carry content hashes. The `state` file will be updated on any change.
6.  **VI. Psychological Measurement Validity**: The plan uses standardized Stroop/Flanker metrics (reaction time, accuracy) and pre-registered analysis pipelines (VIF/PCA threshold) to avoid post-hoc flexibility.
7.  **VII. Ecological Sampling Integrity**: Metadata (lighting, layout) will be extracted from the Unsplash API response and stored in `data/processed/image_metadata.json`. This metadata drives the proxy linkage, ensuring the images reflect diverse remote work conditions. For synthetic fallback, metadata will be sampled from the real Unsplash distribution.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-distraction-cognitive-control/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/
├── code/
│   ├── 01_data_acquisition.py       # Download OpenML cognitive data + Unsplash images
│   ├── 02_visual_metrics.py         # OpenCV/YOLO metric extraction on real images
│   ├── 03_analysis.py               # Stats, VIF, PCA, Holm-Bonferroni, Binning Sensitivity
│   ├── 04_sensitivity.py            # Bootstrap & binning sensitivity (generates tables)
│   ├── 05_reporting.py              # Plot generation, JSON export, p-threshold justification
│   └── utils.py                     # PII sanitization, proxy matching logic
├── data/
│   ├── raw/                         # Raw datasets (OpenML, Unsplash)
│   └── processed/                   # Merged data, metrics, image metadata
├── results/
│   ├── statistics/                  # JSON/CSV outputs, justification.md, multiplicity_table.csv
│   └── figures/                     # Scatter plots
├── tests/
│   └── unit/                        # Unit tests for metrics & edge cases
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular scripts (`01_` to `05_`) to ensure a clear, linear pipeline that respects data dependencies (download -> metrics -> analysis -> reporting). This aligns with the "Single Source of Truth" and reproducibility principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Proxy Linkage | No public dataset links participant-level cognitive data to specific workspace images. | Using a generic dataset without linkage would fail FR-005. Synthetic data creates a tautological study. |
| PCA Fallback Logic | Visual complexity metrics (edge, entropy, object count) are likely highly correlated (collinearity). | Simple multiple regression would yield unstable coefficients if VIF ≥ 5. PCA ensures robust predictors. |
| Holm-Bonferroni Correction | Multiple hypothesis tests (3 metrics × 2 outcomes = 6 tests) inflate Type I error. | Uncorrected p-values would violate SC-003 and standard statistical rigor. |
| p<0.05 Justification | SC-005 requires explicit justification for the significance threshold. | Assuming the threshold is standard without documentation violates the specification. |
| Binning Sensitivity Table | FR-010 requires a specific table output for sensitivity analysis. | Ignoring this output would fail FR-010. |

## Pre-registered Analysis Plan

To satisfy Constitution Principle VI (Psychological Measurement Validity), the following analytical decisions are pre-registered:
- **VIF Threshold**: A Variance Inflation Factor (VIF) ≥ 5 will trigger the PCA fallback.
- **PCA Fallback**: If VIF ≥ 5, the first principal component will be used as the primary predictor.
- **Significance Threshold**: p < 0.05 will be used, justified as a community standard (ASA Statement on p-values).
- **Multiplicity Correction**: Holm-Bonferroni correction will be applied to all hypothesis tests.
- **Binning Strategy**: Quantile-based binning (quartiles, deciles) will be used to verify robustness, with results tabulated.

These decisions are fixed before data analysis to prevent post-hoc flexibility.