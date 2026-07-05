# Implementation Plan: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

**Branch**: `001-visual-distraction-cognitive-control` | **Date**: 2024-01-15 | **Spec**: `specs/001-visual-distraction-cognitive-control/spec.md`
**Input**: Feature specification from `specs/001-visual-distraction-cognitive-control/spec.md`

## Summary

This project investigates the association between visual complexity in home work environments and cognitive control performance. The technical approach involves acquiring or synthesizing paired datasets (cognitive task metrics + workspace images), computing three visual complexity metrics (edge density, color entropy, object count) via CPU-tractable OpenCV and pre-trained detectors, and performing rigorous statistical analysis (Pearson correlation, linear regression, bootstrap resampling) while strictly adhering to associational framing and collinearity diagnostics.

**Critical Note on Data Strategy**: Given the lack of a verified public dataset linking participant-level cognitive scores with specific workspace images, this project utilizes a **Synthetic Data Pipeline** primarily to validate the *methodological pipeline* (metric extraction, statistical robustness, schema compliance) rather than to make empirical claims about human behavior. The synthetic data generator creates independent distributions for predictors and outcomes to ensure the analysis is a genuine hypothesis test, not a tautological verification.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `opencv-python-headless`, `ultralytics` (YOLOv5n/tiny CPU-optimized), `matplotlib`, `seaborn`, `Pillow`  
**Storage**: Local filesystem (`data/` for raw/processed, `results/` for artifacts)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for metric extraction)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Total runtime ≤ 6 hours; memory usage ≤ 6 GB during peak processing; synthetic data generation < 5 minutes.  
**Constraints**: No GPU usage; no large language model inference; all data must be reproducible via pinned random seeds; strict associational language in all outputs.  
**Scale/Scope**: N ≥ 100 participants (real or synthetic); 3 visual metrics × 2 cognitive outcomes = 6 primary hypothesis tests.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds in `code/` and canonical dataset sources. `requirements.txt` will pin versions. Synthetic image generation logic is included in `01_data_acquisition.py` using `Pillow`. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset references to verified URLs (HuggingFace/OpenML) or explicit synthetic generation. No hallucinated URLs. |
| **III. Data Hygiene** | **PASS** | Plan requires checksumming of raw data in `data/` and immutable derivation steps. |
| **IV. Single Source of Truth** | **PASS** | Analysis scripts will output JSON/CSV results that feed directly into the paper generation; no hand-typed stats. PCA components stored in `pca_component_1` field. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be hashed; plan structure supports content-addressable storage logic. |
| **VI. Psychological Measurement Validity** | **PASS** | Plan uses standardized Stroop/Flanker metrics and validated CV methods (OpenCV, standard entropy). |
| **VII. Ecological Sampling Integrity** | **PASS** | Synthetic data generation logic includes diverse parameter ranges for `lighting_condition`, `room_type`, and `demographic_group` to simulate typical home office conditions as required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-distraction-cognitive-control/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_data_acquisition.py       # Downloads or generates synthetic data (including Pillow-based image compositing)
├── 02_visual_metrics.py         # Computes edge density, entropy, object count
├── 03_analysis.py               # Correlation, regression, bootstrap, VIF, PCA
├── 04_visualization.py          # Generates scatter plots
├── utils.py                     # Logging, checksumming, seed management
└── requirements.txt             # Pinned dependencies

data/
├── raw/                         # Downloaded datasets or generated synthetic CSVs/Images
├── processed/                   # Merged analysis-ready dataframes
└── checksums.json               # Artifact hashes

results/
├── statistics.json              # Correlation coefficients, p-values, betas
├── plots/                       # Generated scatter plots
└── sensitivity/                 # Bootstrap and binning results

tests/
├── contract/                    # Validates output against contracts/*.yaml
├── unit/                        # Tests for metric extraction logic
└── integration/                 # End-to-end pipeline test
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `results/`) chosen to minimize overhead for a research pipeline. No separate backend/frontend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Bootstrap Resampling (≥1000)** | Required by FR-009/SC-005 for robust CI estimation. | Standard parametric CIs are insufficient for non-normal distributions of visual complexity metrics. |
| **PCA for Collinearity** | Required by FR-012/SC-007 if VIF ≥ 5. | Standard multiple regression fails if predictors are definitionally related; PCA preserves variance while removing multicollinearity. The resulting component is stored as `pca_component_1` to ensure Single Source of Truth. |
| **Synthetic Data Fallback** | Required by FR-001/US-1 due to lack of linked public datasets. | Real-world linked datasets (cognitive + workspace image) are non-existent. Synthetic simulation is the only viable path to N≥100 for pipeline validation, explicitly decoupled from outcome generation to avoid tautology. |
| **Pillow Image Generation** | Required by Constitution Principle I (Reproducibility) to ensure images exist for CV pipeline on fresh runners. | External image datasets cannot be guaranteed to be available or linked to IDs. `Pillow` compositing is CPU-tractable and fully reproducible. |

