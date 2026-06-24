# Feature Specification: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

**Feature Branch**: `001-uncovering-correlations`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “How do rolling speed, temperature, and reduction ratio jointly influence the crystallographic texture of rolled metallic alloys, and can a data‑driven regression model accurately predict texture coefficients from these processing parameters across multiple alloy systems?”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑End Data‑Driven Texture Prediction (Priority: P1)

A materials researcher wants to feed publicly available rolling‑process datasets into a reproducible pipeline, obtain a trained regression model, and receive quantitative predictions of texture coefficients for new processing conditions.

**Why this priority**: This story delivers the core scientific value—demonstrating that processing parameters can be used to predict texture, directly answering the research question.

**Independent Test**: Execute the full pipeline on a curated subset of the Materials Project dataset (≥ 200 samples) and verify that a model file and prediction CSV are produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** a directory containing raw CSV/JSON files with processing parameters and pole‑figure data, **When** the pipeline is launched, **Then** it must (a) ingest all files, (b) preprocess them, (c) train a Random‑Forest regressor for each texture coefficient, and (d) output a `predictions.csv` with one row per test sample and columns for each coefficient.
2. **Given** the trained model, **When** a new CSV of processing conditions (no texture data) is supplied, **Then** the pipeline must generate predicted texture coefficients and store them in `new_predictions.csv` within ≤ 30 seconds per 100 rows.

---

### User Story 2 – Model Evaluation & Feature‑Importance Reporting (Priority: P2)

A researcher needs to assess how well the model predicts texture and understand which processing variables drive the predictions.

**Why this priority**: Provides quantitative validation of the hypothesis and insight into the physics‑driven relationships, enabling further scientific interpretation.

**Independent Test**: Run the pipeline on the held‑out test split (e.g., a typical proportion of the data) and verify that an `evaluation_report.json` contains R², MAE, and RMSE for each coefficient, and an `importance_plot.png` is generated.

**Acceptance Scenarios**:

1. **Given** the trained model and test set, **When** the evaluation step is executed, **Then** the report must show a cross‑validated R² ≥ 0.70 for every texture coefficient (or explicitly flag failure).
2. **Given** the completed model, **When** the feature‑importance module runs, **Then** it must produce a ranked list where at least one processing variable has an importance score ≥ 0.15 for each alloy family.

---

### User Story 3 – Reproducible Containerized Execution (Priority: P3)

A lab technician wants to run the entire analysis on a CI platform (GitHub Actions) without installing dependencies locally.

**Why this priority**: Guarantees reproducibility, lowers the barrier to adoption, and satisfies the “Reproducibility” clause in the methodology.

**Independent Test**: Trigger the provided GitHub Actions workflow on a fresh repository fork; the job must complete within 6 hours, using ≤ 2 CPU cores and ≤ 6 GB RAM, and produce the same artifacts as the local run.

**Acceptance Scenarios**:

1. **Given** the repository with the Dockerfile and workflow YAML, **When** the CI job starts, **Then** it must build the Docker image (Python 3.11, scikit‑learn, pandas, pymtex) and run the full pipeline without manual steps, exiting with status 0.
2. **Given** a failure due to missing data files, **When** the CI job aborts, **Then** the logs must contain a clear error message indicating the missing resource and the job must be marked as failed (no silent crashes).

---

### Edge Cases

- **Boundary condition**: What happens when a processing parameter (e.g., temperature) falls outside the range observed in the training data?  
  *System must flag the out‑of‑range entry, log a warning, and still produce a prediction using the trained model.*
- **Error scenario**: How does the system handle completely missing texture data for a sample?  
  *System must skip the sample during training, record the omission in a preprocessing log, and continue without terminating the pipeline.*
- **Data quality**: What if > 20 % of samples contain NaN values for a given parameter?  
  *System must abort training and emit a “Data quality insufficient” error, prompting the user to acquire more complete data.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest processing‑parameter and texture‑measurement files from the Materials Project, Open Materials Database, and NIST Materials Data Repository (CSV/JSON formats).  
- **FR-002**: System MUST preprocess ingested data by (a) standardizing units (°C, m s⁻¹, % reduction), (b) median‑imputing missing numeric values, and (c) removing outliers beyond 3 σ.  
- **FR-003**: System MUST compute quantitative texture descriptors (maximum ODF values for {100}, {110}, {111}) from raw pole‑figure or ODF data using `pymtex` or an equivalent spherical‑harmonic approximation.  
- **FR-004**: System MUST train a separate `RandomForestRegressor` for each texture coefficient, performing hyper‑parameter tuning (n_estimators, max_depth) via a 5‑fold cross‑validation grid that completes in ≤ 30 minutes of wall‑clock time on ≤ 2 CPU cores.  
- **FR-005**: System MUST output (a) prediction CSVs for test and new samples, (b) an evaluation report containing R², MAE, and RMSE for each coefficient, and (c) a permutation‑importance ranking visualisation (≤ 5 MB PNG).  
- **FR-006**: System MUST containerize the entire workflow in a lightweight Docker image (Python 3.11, scikit‑learn, pandas, pymtex) and provide a GitHub Actions workflow that respects the resource limits (≤ 6 h runtime, ≤ 2 CPU cores, ≤ 6 GB RAM).  
- **FR-007**: System MUST log all processing steps, including data‑quality warnings, hyper‑parameter choices, and any out‑of‑range predictions, to a human‑readable `pipeline.log`.  

*Clarification markers*:

- **FR-003**: [NEEDS CLARIFICATION: precise mathematical definition of “texture coefficient” – is it the maximum ODF value, the volume fraction of a specific orientation, or a derived pole‑figure intensity?]  
- **FR-006**: [NEEDS CLARIFICATION: target Docker base image (e.g., `python:3.11-slim` vs. `ubuntu:22.04`)?]  

### Key Entities

- **ProcessingRecord**: Represents a single rolling experiment; attributes include `alloy_id`, `rolling_speed` (m s⁻¹), `temperature` (°C), `reduction_ratio` (%), and optional composition vector.  
- **TextureDescriptor**: Quantitative representation of crystallographic texture; attributes include `odf_100`, `odf_110`, `odf_111` (or the clarified coefficient).  
- **TrainedModel**: Serialized RandomForest model per texture coefficient; includes hyper‑parameter metadata.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cross‑validated R² ≥ 0.70 on the held‑out test set for each of the three texture coefficients (reference: baseline of random prediction which yields R² ≈ 0).  
- **SC-002**: At least one processing variable attains a permutation‑importance score ≥ 0.15 for every alloy family (reference: uniform importance of 1/ N where N is number of features).  
- **SC-003**: End‑to‑end pipeline execution completes within 6 hours, using ≤ 2 CPU cores and ≤ 6 GB RAM on the GitHub Actions runner (reference: CI resource quota).  

## Assumptions

- Public datasets from Materials Project, OMDB, and NIST contain the required fields (rolling speed, temperature, reduction ratio, pole‑figure/ODF data) and are freely downloadable without authentication.  
- All processing parameters are reported in SI‑compatible units; any required conversion factors are known and unambiguous.  
- Median imputation and 3 σ outlier removal are sufficient to handle missing / noisy data for the scope of this study.  
- RandomForest regression is an appropriate baseline model for capturing non‑linear relationships in this domain.  
- Users have Docker installed locally and have permission to run GitHub Actions workflows in a repository they control.  
- The computational budget of ≤ 30 minutes for hyper‑parameter search is adequate to find a model meeting SC‑001.  

---
