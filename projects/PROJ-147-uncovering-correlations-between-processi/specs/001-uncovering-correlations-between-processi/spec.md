# Feature Specification: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

**Feature Branch**: `001-uncovering-correlations`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "How do rolling speed, temperature, and reduction ratio jointly influence the crystallographic texture of rolled metallic alloys, and can a data‑driven regression model accurately predict texture coefficients from these processing parameters across multiple alloy systems?"

**Research Question**: How do rolling speed, temperature, and reduction ratio jointly **predict** and **associate** with the crystallographic texture of rolled metallic alloys, and can a data‑driven regression model accurately predict texture coefficients from these processing parameters across multiple alloy systems?

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑End Data‑Driven Texture Prediction (Priority: P1)
**Anchored to**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-009, FR-010

A materials researcher wants to feed publicly available rolling‑process datasets into a reproducible pipeline, obtain a trained regression model, and receive quantitative predictions of texture coefficients for new processing conditions. If public data is unavailable, the system MUST generate a synthetic dataset to validate the pipeline logic.

**Why this priority**: This story delivers the core scientific value—demonstrating that processing parameters can be used to predict texture, directly answering the research question. It ensures the pipeline is functional even when real data is missing.

**Independent Test**: Execute the full pipeline on a curated subset of the Materials Project dataset (≥ 200 samples) IF available; OTHERWISE, execute on a synthetic dataset generated per FR-011 (≥ 200 samples, 3 alloy families). Verify that a model file and prediction CSV are produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** a directory containing raw CSV/JSON files with processing parameters and pole‑figure data OR a synthetic data generation trigger, **When** the pipeline is launched, **Then** it must (a) ingest all files or generate synthetic data, (b) preprocess them, (c) train a multi-output RandomForestRegressor for all texture coefficients jointly (See FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-009, FR-010), and (d) output a `predictions.csv` with one row per test sample and columns for each coefficient.
2. **Given** the trained model, **When** a new CSV of processing conditions (no texture data) is supplied, **Then** the pipeline must generate predicted texture coefficients and store them in `new_predictions.csv` within ≤ 30 seconds per 100 rows (See FR-005, FR-007).

---

### User Story 2 – Model Evaluation & Feature‑Importance Reporting (Priority: P2)
**Anchored to**: FR-003, FR-004, FR-005, FR-009, FR-010

A researcher needs to assess how well the model predicts texture and understand which processing variables drive the predictions.

**Why this priority**: Provides quantitative validation of the hypothesis and insight into the physics‑driven relationships, enabling further scientific interpretation.

**Independent Test**: Run the pipeline on a held-out test split (a standard train/test partition) of the dataset (real or synthetic) and verify that an `evaluation_report.json` contains R², MAE, and RMSE for each coefficient, and an `importance_plot.png` is generated. If synthetic data is used, the "ground truth" for evaluation is the known generator parameters (See FR-004, FR-005, FR-009, FR-010). **Note**: For synthetic data, "ground truth" refers to the generator's defined function, not scientific ground truth for real materials.

**Acceptance Scenarios**:

1. **Given** the trained model and test set, **When** the evaluation step is executed, **Then** the report must show a cross‑validated R² for every texture coefficient (threshold R² ≥ 0.50 for synthetic data, see FR-010 for sensitivity analysis).
2. **Given** the completed model, **When** the feature‑importance module runs, **Then** it must produce a ranked list where at least one processing variable has an importance score ≥ 0.10 per FR-010 sensitivity analysis (See FR-005, FR-009, FR-010).

---

### User Story 3 – Reproducible Containerized Execution (Priority: P3)
**Anchored to**: FR-006

A lab technician wants to run the entire analysis on a CI platform (GitHub Actions) without installing dependencies locally (See FR-006).

**Why this priority**: Guarantees reproducibility, lowers the barrier to adoption, and satisfies the "Reproducibility" clause in the methodology.

**Independent Test**: Trigger the provided GitHub Actions workflow on a fresh repository fork (if enabled); the job must complete within 6 hours, using ≤ 2 CPU cores and ≤ 6 GB RAM, and produce the same artifacts as the local run.

**Acceptance Scenarios**:

1. **Given** the repository with the Dockerfile and workflow YAML (if enabled), **When** the CI job starts, **Then** it must build the Docker image (Python, scikit-learn, pandas, pymtex) and run the full pipeline without manual steps, exiting with status 0.
2. **Given** a failure due to missing data files, **When** the CI job aborts, **Then** the logs must contain a clear error message indicating the missing resource and the job must be marked as failed (no silent crashes).

---

### Edge Cases

- **Boundary condition**: What happens when a processing parameter (e.g., temperature) falls outside the range observed in the training data?  
  *System must flag the out‑of‑range entry, log a warning, and still produce a prediction using the trained model.*
- **Error scenario**: How does the system handle completely missing texture data for a sample?  
  *System must skip the sample during training, record the omission in a preprocessing log, and continue without terminating the pipeline.*
- **Data quality**: What if > 20 % of samples contain NaN values for a given parameter?  
  *System must abort training and emit a "Data quality insufficient" error, prompting the user to acquire more complete data. This threshold is based on the community standard that >20% missing data typically compromises statistical power for regression models with N < 500.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST attempt to ingest processing‑parameter and texture‑measurement files from the Materials Project, Open Materials Database (OMDB), and NIST Materials Data Repository (CSV/JSON formats). If no paired samples (processing parameters + texture measurements) are found in these sources, the system MUST immediately trigger the synthetic data generator defined in FR-011. The system MUST validate ≥50 paired samples exist per alloy family before training; if real data is insufficient, the synthetic generator MUST produce the required samples. Abort if the total sample count (real + synthetic) is < 50 per family (See FR-011). **(Anchored to US-1)**
- **FR-002**: System MUST preprocess ingested data by (a) standardizing units (°C, m s⁻¹, % reduction), (b) median‑imputing missing numeric values, (c) removing outliers beyond a statistically significant threshold, (d) deriving physics‑based features (e.g., strain rate, Zener‑Hollomon parameter), (e) explicitly including alloy composition and prior processing history as input features to control for confounding variables, and (f) performing a Variance Inflation Factor (VIF) check on all derived features; any feature with VIF ≥ 5 MUST be removed or regularized to prevent multicollinearity artifacts in feature importance rankings. **(Anchored to US-1)**
- **FR-003**: System MUST compute quantitative texture descriptors (maximum ODF values for {100}, {110}, {111} crystallographic planes) from raw pole‑figure or ODF data using `pymtex` or an equivalent spherical‑harmonic approximation. If the input is synthetic (generated per FR-011), the system MUST use the synthetic pole-figure/ODF files produced by the generator. Equivalence criterion: alternative tool must produce ODF intensities within ±5% MRD of pymtex on a standard reference dataset. The texture coefficient is defined as the peak ODF intensity (in multiples of random distribution, MRD) for each specified crystallographic plane, following community‑standard practice in rolled metal texture analysis. **Verification**: For synthetic data, the system MUST verify that the computed descriptors match the generator's intended values within ±5% MRD. **(Anchored to US-1)**
- **FR-004**: System MUST train a multi‑output RandomForestRegressor for all texture coefficients jointly (not separate models), performing hyper‑parameter tuning (n_estimators, max_depth) via a k‑fold cross‑validation grid that completes in ≤ 30 minutes of wall‑clock time on ≤ 2 CPU cores. **(Anchored to US-1)**
- **FR-005**: System MUST output (a) prediction CSVs for test and new samples, (b) an evaluation report containing R², MAE, and RMSE for each coefficient, and (c) a permutation‑importance ranking visualisation (≤ 5 MB PNG). **(Anchored to US-1, US-2)**
- **FR-006**: System SHOULD (optional, reproducibility enhancement) containerize the entire workflow in a lightweight Docker image based on `python:3.11-slim` (Python 3.11, scikit-learn, pandas, pymtex) and provide a GitHub Actions workflow that respects the resource limits (≤ 6 h runtime, ≤ 2 CPU cores, ≤ 6 GB RAM) IF the containerization feature is enabled. The `python:3.11-slim` base image is selected for minimal footprint while maintaining full Python 3.11 compatibility. **(Anchored to US-3)**
- **FR-007**: System MUST log all processing steps, including data‑quality warnings, hyper‑parameter choices, and any out‑of‑range predictions, to a human‑readable `pipeline.log`. **(Anchored to US-1, US-2)**
- **FR-009**: System MUST validate results across at least 3 distinct alloy families (e.g., Al, Cu, steel) with separate performance metrics reported per family. **Mechanism**: The evaluation report MUST include a `per_family_metrics` JSON object where keys are alloy family names and values contain R², MAE, and RMSE for each texture coefficient. **(Anchored to US-2)**
- **FR-010**: System MUST perform sensitivity analysis on performance thresholds: sweep R² thresholds over a range of values to assess their impact on results. For synthetic data, the system MUST report the stability of R² and feature importance scores across multiple random seeds (≥ 5 seeds) using variance as the stability metric. **Sweep Range**: R² thresholds must be swept across a moderate range in incremental steps.. **Note**: FPR/FNR calculation is not required for real data as no ground truth exists; stability analysis across seeds replaces this for synthetic validation. **(Anchored to US-2)**
- **FR-011**: System MUST include a synthetic data generator that creates paired processing parameters and texture coefficients for at least 3 alloy families. The generator MUST simulate physical relationships: (a) rolling speed, temperature, and reduction ratio as inputs; (b) texture coefficients as outputs with added Gaussian noise (σ=0.05 MRD); (c) alloy composition and prior history as confounding variables; (d) generation of synthetic pole-figure/ODF files compatible with `pymtex`. The generator MUST produce ≥50 samples per alloy family on demand. **Constraint**: The synthetic data MUST include raw diffraction/ODF files to satisfy Constitution Principle VI and FR-003. **Validation Scope**: Results on synthetic data are strictly for pipeline verification (code logic, data flow) and cannot support the scientific hypothesis of 'uncovering correlations' in real materials. **Power Analysis**: The generator MUST include a power analysis module to calculate the minimum detectable effect size for N=50 per family; if the effect size is > 0.3 (|r|), a warning MUST be logged. **(Anchored to US-1)**

### Key Entities

- **ProcessingRecord**: Represents a single rolling experiment; attributes include `alloy_id`, `rolling_speed` (m s⁻¹), `temperature` (°C), `reduction_ratio` (%), `composition_vector`, `prior_history`, and optional `raw_diffraction_file`. **Relationship**: Links to `TextureDescriptor` via `alloy_id` and `sample_id`.
- **AlloyFamily**: Classification of alloys by composition range and crystal structure (e.g., FCC Al, FCC Cu, BCC steel); used to group samples for cross‑family validation.
- **TextureDescriptor**: Quantitative representation of crystallographic texture; attributes include `odf_100`, `odf_110`, `odf_111` (in MRD units). **Relationship**: Linked to `ProcessingRecord` via `alloy_id` and `sample_id`.
- **TrainedModel**: Serialized multi‑output RandomForest model for all texture coefficients; includes hyper‑parameter metadata.
- **SyntheticDataConfig**: Configuration for the synthetic generator; includes `num_samples`, `alloy_families`, `noise_level`, and `seed`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Cross‑validated R² measured on the held‑out test set for each of the three texture coefficients across all alloy families (reference: baseline of a mean predictor trained on the training set; threshold R² ≥ 0.50 for synthetic data, p < 0.05 via t-test against random for real data). **Note**: For synthetic data, the R² ≥ 0.50 threshold is a pipeline sanity check (verifying the model can learn the generator's function), not a scientific hypothesis test. **(Anchored to US-1, FR-004)**
- **SC-002**: At least one processing variable attains a permutation‑importance score ≥ 0.10 for every AlloyFamily (reference: uniform importance of 1/N where N is number of features for real data; reference: known generator weights for synthetic data). **(Anchored to US-2, FR-005)**
- **SC-003**: End‑to‑end pipeline execution completes within 6 hours, using ≤ 2 CPU cores and ≤ 6 GB RAM on the GitHub Actions runner (reference: CI resource quota; optional per FR-006). **(Anchored to US-3, FR-006)**

## Assumptions

- Public datasets from Materials Project, Open Materials Database (OMDB), and NIST MAY lack the required fields (rolling speed, temperature, reduction ratio, pole‑figure/ODF data) or paired data; the system relies on the synthetic data generator (FR-011) as the primary fallback to ensure pipeline execution.
- All processing parameters are reported in SI‑compatible units; any required conversion factors are known and unambiguous.
- Median imputation and 3 σ outlier removal are sufficient to handle missing / noisy data for the scope of this study.
- RandomForest regression is an appropriate baseline model for capturing non‑linear relationships in this domain; physics‑informed features are derived per FR-002.
- Users have Docker installed locally and have permission to run GitHub Actions workflows in a repository they control (optional; FR-006 is marked SHOULD not MUST).
- The computational budget of ≤ 30 minutes for hyper‑parameter search is adequate to find a model meeting SC‑001 (threshold R² ≥ 0.50).
- Containerization and CI workflows (FR-006) are optional reproducibility enhancements not required for core research validity.
- Synthetic data generated per FR-011 is valid for pipeline testing and code validation but CANNOT be used to validate the physical hypothesis of real material correlations; this is a known scientific limitation. **Decoupling**: Pipeline validation (code works) is distinct from scientific validation (hypothesis supported); synthetic data only supports the former.

## Limitations

- **Data Availability**: No verified public source currently exists for paired rolling-process and texture data. The system relies on synthetic data (FR-011) for validation, which validates the pipeline logic but not the physical hypothesis.
- **Scientific Validity**: Results derived from synthetic data are circular for physics validation (ground truth is defined by the generator). The model's ability to predict real-world texture is unproven until real data is obtained.
- **Confounding Variables**: While FR-002 includes composition and history, unmodeled microstructural factors (e.g., grain size, precipitate distribution) may still influence texture in real materials, potentially limiting generalizability.
- **Statistical Power**: The minimum sample size of 50 per alloy family may be insufficient to detect small effect sizes (e.g., |r| < 0.3) with high power (≥ 0.80). A formal power analysis is required (see FR-011) to define the minimum detectable effect size; if the effect size is > 0.3, the study may be underpowered to detect real correlations.