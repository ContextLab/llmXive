# Implementation Plan: Influence of Microstructural Features on Fatigue Life in Aluminum Alloys

**Branch**: `001-fatigue-microstructure-analysis` | **Date**: 2025-01-15 | **Spec**: `specs/001-fatigue-microstructure-analysis/spec.md`
**Input**: Feature specification from `/specs/001-fatigue-microstructure-analysis/spec.md`

## Summary

This project investigates the quantitative influence of microstructural features (grain size, secondary phase distribution, dislocation density) on the fatigue life of aluminum alloys using machine learning. **Due to the lack of verified domain-specific datasets in the provided source list, the primary goal of this iteration is 'Pipeline Validation and Methodological Demonstration' rather than empirical discovery of physical laws.** The approach involves generating a synthetic dataset that mimics the statistical properties of aluminum fatigue data, preprocessing tabular and image data, extracting features (using texture analysis as a proxy for dislocation density), training regression models (Random Forest, Gradient Boosting, ElasticNet) under strict CPU constraints, and performing rigorous statistical analysis (ANOVA, bootstrapping, multiple-comparison correction) to **validate the pipeline's ability to recover known generator parameters and handle data constraints**. All findings derived from this synthetic data are explicitly framed as methodological validations, not empirical insights into real-world fatigue mechanisms.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `opencv-python`, `scikit-image`, `matplotlib`, `seaborn`, `requests`, `huggingface_hub`  
**Storage**: Local filesystem (`data/`, `results/`), JSON/CSV artifacts  
**Testing**: `pytest` (unit/contract), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM, no GPU)  
**Project Type**: Data Science / Computational Materials Science Pipeline (Synthetic Validation)  
**Performance Goals**: Complete pipeline in ≤6 hours; RAM ≤7GB; R² > 0.7 (target for parameter recovery)  
**Constraints**: No GPU usage; no large model training; strict adherence to 7GB RAM; all findings framed as associational; dislocation density treated as a proxy; **results are synthetic-only**.  
**Scale/Scope**: Target N ≥ 150 specimens (synthetic); 512×512 image crops; regression models; A sufficient number of bootstrap resamples.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value. **Note: Current data source is synthetic due to verified URL mismatches.**

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All scripts will pin random seeds (`np.random.seed`, `random.seed`, `sklearn` `random_state`). External data sources will be fetched via canonical URLs (or generated synthetically with fixed seeds). `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **Pass (with Caveats)** | Citations in `research.md` are limited to the verified URLs provided. The Reference-Validator will check these. **Critical Note**: The verified URLs provided were mismatched (medical/LLM data), necessitating the synthetic fallback. This deviation is documented in `research.md`. |
| **III. Data Hygiene** | **Pass** | Raw data (synthetic) will be stored in `data/raw/` with checksums. Derived data (cleaned CSVs, feature matrices) will be in `data/processed/`. No in-place modifications. |
| **IV. Single Source of Truth** | **Pass** | All figures and statistics in `paper/` will be generated directly from `results/` artifacts via scripts. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Content hashes for artifacts will be tracked in `state/`. Code changes will update the `updated_at` timestamp. |
| **VI. Computational Resource Compliance** | **Pass** | Models limited to ≤100 trees/estimators. No GPU/CUDA. RAM usage monitored; data subset if necessary to fit 7GB. |
| **VII. Image Processing Determinism** | **Pass** | OpenCV/scikit-image pipelines will use fixed seeds and explicit parameters (no global defaults). 512×512 crops enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-fatigue-microstructure-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── 01_data_acquisition.py       # Synthetic data generation & validation (FR-001 Fallback, FR-002 Logic Test)
├── 02_feature_extraction.py     # Image processing & tabular feature extraction (FR-004, FR-005)
├── 03_model_training.py         # ML training & CV (FR-006, FR-007)
├── 04_statistical_analysis.py   # ANOVA, bootstrapping, sensitivity (FR-008, FR-009, FR-014)
├── 05_visualization.py          # Plot generation (FR-010)
├── utils/
│   ├── config.py                # Paths, seeds, hyperparameters
│   └── logging.py               # Exclusion logging, fallback logging
└── requirements.txt             # Pinned dependencies

data/
├── raw/                         # Generated synthetic datasets (checksummed)
└── processed/                   # Cleaned CSVs, feature matrices

results/
├── metrics.json                 # Model performance (FR-007)
├── anova_summary.csv            # Statistical significance (FR-008)
├── plots/                       # PNGs ≤500KB (FR-010)
└── exclusion_report.log         # Data cleaning log (FR-002 Logic Test)
```

**Structure Decision**: Single project structure selected to align with the linear data science pipeline (Acquisition → Extraction → Training → Analysis). This minimizes overhead and ensures data flows sequentially through scripts, satisfying the "data before model" constraint.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Image Processing Fallback** | Microscopy images may be missing in public datasets. | A simple tabular-only pipeline would fail if images are present but not processed, or vice versa. The dual-path logic (FR-004b) ensures robustness without manual intervention. |
| **Proxy Feature Handling** | Dislocation density is rarely in public datasets. | Treating it as a measured value would violate scientific integrity. The explicit proxy logic (FR-013) and sensitivity analysis (FR-014) are required for validity. **Synthetic Proxy Limitation**: The proxy is generated via non-linear interaction to avoid simple collinearity, but its validity is untestable without real TEM/XRD data. |
| **Multiple Comparison Correction** | Testing multiple features risks false positives. | Uncorrected p-values would violate FR-012 and statistical rigor standards for observational studies. |
| **Tautology Avoidance** | Synthetic data is generated by known functions. | To avoid circular validation, the analysis focuses on "parameter recovery" (can the model find the generator's coefficients?) rather than "discovery of physical laws". |
| **Collinearity Limitation** | Synthetic predictors may be correlated. | The generator uses non-linear interactions to mimic real complexity, but perfect independence cannot be guaranteed. VIF diagnostics will be reported. |

## Scope Deviations & Data Acquisition Fallback

### Data Acquisition Fallback (FR-001)
**Status**: **Skipped (Verified URL Mismatch)**
- **Original Requirement (FR-001)**: Download aluminum alloy fatigue datasets from HuggingFace/NIST.
- **Issue**: The verified dataset URLs provided in the spec context were medical and LLM evaluation data, not materials science data.
- **Decision**: The pipeline will use a **Synthetic Data Generator** to create N=150 records mimicking the statistical properties of aluminum fatigue data.
- **Validation**: This allows verification of the *pipeline logic* (FR-002 through FR-014) but does not validate the *physical relationships*. A "Real Data Acquisition Path" is documented in `research.md` for future implementation when verified domain data is available.

### Image Processing Fallback (FR-004)
**Status**: **Synthetic Image Generation**
- **Original Requirement (FR-004)**: Load 512×512 microscopy image crops.
- **Issue**: No real microscopy images available in the verified dataset list.
- **Decision**: The pipeline will generate synthetic 512×512 grayscale "images" using Voronoi tessellation to simulate grain boundaries.
- **Validation**: This tests the image processing logic (OpenCV thresholding, contour detection) but cannot validate the correlation between texture metrics and real dislocation density.

### Metric Adaptation (SC-001)
**Status**: **Adapted**
- **Original Requirement (SC-001)**: Measure completeness against N ≥ 100 specimens from public repositories.
- **Adaptation**: Measure completeness against the **Synthetic Generator Output** (N ≥ 150) to ensure pipeline stability and memory constraints are met.

### Goal Reframing
**Status**: **Reframed**
- **Original Goal**: "Derive associational findings" regarding the influence of microstructural features on fatigue life.
- **Reframed Goal**: "Validate pipeline functionality and methodological rigor" by demonstrating the ability to recover known generator parameters and handle data constraints under strict CPU limits.
- **Rationale**: Synthetic data cannot answer the research question about *real* aluminum alloys. The study is now a software demo and methodological validation.