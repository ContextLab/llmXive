# Implementation Plan: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Branch**: `001-predict-elastic-modulus` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-elastic-modulus/spec.md`

## Summary

This project implements a computational pipeline to predict the **Residual Bulk Modulus** ($B_{observed} - B_{Miedema}$) of High-Entropy Alloys (HEAs). The approach retrieves compositional and elastic constant data from the Materials Project and OQMD APIs, computes compositional descriptors (mixing enthalpy, atomic radius variance, etc.), and applies an **Isometric Log-Ratio (ILR)** transformation to break the compositional closure constraint. Three regression models (Random Forest, Gradient Boosting, ElasticNet) are trained on CPU-only infrastructure. The study prioritizes statistical rigor (grouped bootstrapping, FDR correction, sensitivity analysis) and explicitly frames results as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `requests`, `pyyaml`, `shap`, `matplotlib`, `seaborn`, `joblib`  
**Storage**: Local CSV/Parquet files in `data/` (checksummed); `data/source_metadata.yaml` for API provenance.  
**Testing**: `pytest` (unit tests for feature engineering; integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner: A minimal computing environment consisting of a single CPU and modest memory resources.).  
**Project Type**: Computational Research Pipeline / CLI Tool.  
**Performance Goals**: Complete full pipeline (fetch, engineer, train, evaluate) within 6 hours on CPU.  
**Constraints**: No GPU; no deep learning; strict memory limits (constrained RAM capacity); dataset must be filtered to HEAs with a high number of constituent elements; Miedema-derived features excluded when predicting Residual Bulk Modulus (FR-008).  
**Scale/Scope**: Target a substantial number of valid HEA samples. If APIs yield $< 500$, the pipeline attempts to merge with verified HEA elastic datasets from literature (e.g., specific HEA elastic constants databases). If the merged count is still $< 500$, the pipeline halts with a "Dataset Insufficient" error (SC-001).

> **Dataset Feasibility Note**: Public HEA datasets with *elastic constants* (C11, C12, C44) are sparse. The plan targets a specific subset ($\ge 5$ elements + elastic constants) as described in FR-001. While OQMD contains millions of entries, the elastic subset is smaller. The pipeline implements a fallback merge strategy with literature-verified HEA elastic datasets to meet the 500-sample threshold, citing [Reference: HEA Elastic Constants Database] for feasibility justification.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Requirement | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; external datasets fetched from canonical sources. | All scripts will set `random_state=42` globally. API fetch parameters recorded in `source_metadata.yaml`. |
| **II. Verified Accuracy** | Citations verified against primary sources. | All citations in `research.md` will be checked against the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | Checksums recorded; no in-place modification. | `data/` files will be checksummed (SHA256) upon download; derived files will have new names (e.g., `raw_hea.csv` -> `processed_hea_ilr.parquet`). |
| **IV. Single Source of Truth** | Figures/stats trace to `data/` and `code/`. | All metrics output to `results/metrics.yaml` and consumed by the report generator. No hand-typed values. |
| **V. Versioning Discipline** | Content hashes for artifacts. | The `Advancement-Evaluator Agent` invalidates stale review records when the `state/...yaml` `artifact_hashes` map changes. The pipeline script will update this map with new checksums after each run, triggering the evaluator's invalidation logic as described in Principle V. |
| **VI. Materials Database Provenance** | API versions/params recorded in `source_metadata.yaml`. | The data ingestion script will explicitly log API version, query params, and timestamps to `data/source_metadata.yaml`. |
| **VII. Model Evaluation Transparency** | R², RMSE, MAE, confidence interval via bootstrap, t-test against null. | Evaluation module will output these exact metrics to `results/metrics.yaml` and enforce a bootstrap procedure with a sufficient number of iterations. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-elastic-modulus/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── hea_sample.schema.yaml
│   ├── compositional_descriptor.schema.yaml
│   ├── model_performance.schema.yaml
│   └── model_performance_record.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

**Note on Schemas**: `model_performance_record.schema.yaml` is the canonical schema for the 'Model Performance Record' entity. `model_performance.schema.yaml` is provided as an alternative view for specific metric logging but the record schema is the primary standard.

### Source Code (repository root)

```text
projects/PROJ-443-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── fetch_hea.py          # API fetch + OQMD CSV fallback + Literature merge
│   │   ├── preprocess.py         # ILR, descriptor calc, normalization
│   │   └── utils.py
│   ├── models/
│   │   ├── train.py              # RF, GB, ElasticNet training
│   │   ├── evaluate.py           # Bootstrap, FDR, sensitivity analysis
│   │   └── interpret.py          # SHAP, partial dependence
│   └── main.py                   # Pipeline orchestration
├── data/
│   ├── raw/                      # Raw API responses/CSVs
│   ├── processed/                # ILR-transformed datasets
│   └── source_metadata.yaml      # API provenance
├── results/
│   ├── metrics.yaml              # Performance stats
│   └── figures/                  # Parity plots, SHAP
├── tests/
│   ├── test_preprocess.py
│   └── test_evaluate.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`code/` subdirectory) selected to maintain a linear pipeline flow suitable for a research script. This aligns with the "Computational Research Pipeline" type and simplifies dependency management for CPU-only execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **ILR Transformation** | Required to break compositional singularity (FR-003). | Standard log-ratio or raw percentages cause singular matrices in regression, violating statistical assumptions. |
| **Grouped Bootstrap** | Required to prevent data leakage (FR-005). | Standard bootstrap would resample individual samples from the same alloy system, inflating confidence and violating independence assumptions. |
| **Residual Target** | Required to isolate alloying effects (FR-004). | Predicting raw Bulk Modulus would conflate rule-of-mixtures baseline with alloying effects, reducing interpretability of "alloying effect". |
| **Sensitivity Analysis** | Required for robustness (FR-006). | A single threshold (0.3) is fragile; sweeping thresholds and reporting Type I error rates validates the claim's robustness. |
| **Literature Merge Fallback** | Required to meet sample size (SC-001). | Relying solely on API data risks < 500 samples; merging with verified literature datasets ensures statistical power. |