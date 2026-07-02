# Implementation Plan: Quantifying the Influence of Topological Defects on 2D Material Properties

**Branch**: `001-quantify-defect-influence` | **Date**: 2024-01-15 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-quantify-defect-influence/spec.md`

## Summary

This plan implements a computational workflow to quantify the influence of topological defects (dislocations, grain boundaries) on the electronic conductivity, Young's modulus, and fracture strength of graphene and MoS₂. The approach prioritizes the **2022 Supplementary Defect Dataset** (real data) and the **Materials Project REST API** for pristine structures. A **synthetic fallback** (physics-based) is available ONLY if the primary real dataset is missing or invalid. 

**Critical Scope Limitation**: If the workflow falls back to synthetic data, the project goal shifts from "Quantifying Real-World Defect Influence" to "Validating the Analysis Pipeline and Detecting Programmed Correlations." All scientific claims in this mode are restricted to "Methodological Validation" and "Associational Claims within the Synthetic Domain." No causal or external validity claims are made if synthetic data is used.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `requests`, `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `mp-api`, `statsmodels`
- **Storage**: Local CSV/Parquet files in `data/`
- **Testing**: `pytest`
- **Target Platform**: Linux (GitHub Actions free‑tier runner)
- **Performance Goals**: Complete full workflow (data fetch, modeling, inference) within 6 hours on 2 CPU cores, ≤7 GB RAM.
- **Constraints**: No GPU, no large‑scale deep learning, all libraries CPU‑compatible.

## Workflow Steps (ordered)

1. **Data Acquisition & Source Verification**
   - `01_data_acquisition.py`:
     - **Step 1.1**: Query Materials Project REST API for ≥ 50 pristine graphene and MoS₂ structures; cache locally under `data/raw/`.
     - **Step 1.2**: Attempt to download the **2022 Supplementary Defect Dataset** (CSV/JSON) identified in the project idea (Accession ID: `defect_dataset_2022_supplementary`). 
       - **Verification**: Check for existence, valid columns (defect type, density, conductivity, elastic tensor, fracture energy), and non-null values.
       - **Fallback**: If the 2022 dataset is missing, invalid, or incomplete:
         - Invoke the **Physics-Based Synthetic Generator** (seed = 42, versioned via git hash).
         - **Generator Logic**: 
           - **Primary Mode (Training Set)**: Uses **Analytical Continuum Mechanics** (Griffith criterion, Rule of Mixtures, Matthiessen's rule) to generate properties.
           - **Hold-Out Mode (Distinct Physics Engine)**: Uses a **Gaussian Process Surrogate** trained on a separate public DFT dataset (if available) or distinct analytical parameters to emulate a "Distinct Physics Engine" (Analytical vs. Statistical/DFT-based).
         - Generate ≥ 100 entries with defect density ∈ [0.001, 0.1] and property bounds (conductivity > 0, Young's modulus > 0, fracture energy > 0).
     - **Step 1.3**: Implement exponential backoff (max 3 retries) for API calls; on total failure load cached pristine structures or abort with `[ERROR: API access unavailable and no cache present]`.

2. **Data Integrity & Hygiene**
   - Verify checksum of each raw file; record in `state/projects/PROJ-209-...yaml`.
   - **Consistency Check**: Ensure the synthetic generator uses the *exact same* pristine reference values ($P_0$) fetched in Step 1.1 for normalization to avoid trivial linear relationships.
   - Flag entries with missing required fields; attempt mock DFTB+ computation (≤ 300 s) for missing fracture energy; on timeout mark `[MISSING: timeout]` and exclude.
   - Filter out entries with defect density ≤ 0 or NaN; log count.

3. **Normalization & Feature Engineering**
   - `02_data_processing.py`:
     - Fetch material‑level pristine reference values (`σ₀`, `E₀`, `σ_f₀`) once per material from the cached pristine structures.
     - Compute normalized targets Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀.
     - One‑hot encode `defect_type`; retain geometric descriptors (`defect_density`, `tilt_angle`); include `synthesis_method` and `grain_size` as covariates when present.
     - Save `features.csv` and `targets.csv` under `data/processed/` and record their SHA‑256 checksums in the state file via `scripts/update_state_hashes.py`.

4. **Collinearity Handling (FR‑008)**
   - Compute Variance Inflation Factor (VIF) for all predictors.
   - **Primary Strategy**: Apply **Ridge Regression** (L2 regularization) to handle collinearity in geometric descriptors (e.g., tilt angle vs. density).
   - **Fallback**: If Ridge fails or if a feature is deemed physically redundant (VIF > 5 AND low importance), exclude the lower‑importance feature and re‑train.
   - Log the collinearity handling method used.

5. **Model Training & Validation (FR‑004, FR‑012)**
   - `03_modeling.py`:
     - Train three separate Random Forest regressors (targets: conductivity, Young's modulus, fracture strength) using a train/test split (80/20, `seed=42`).
     - Perform 5‑fold cross‑validation (k = 5); compute mean R², MAPE, and **standard deviation of R²** (`cv_std`) (reported for SC‑003). Values > 0.1 are flagged as high variance.
     - Baseline null model: predict mean of training targets; compare R² improvement.
     - **Hold‑out Strategy (FR-012)**:
       - **Real Data**: Use a distinct random‑seed split (different from the main train/test split) for the hold-out set.
       - **Synthetic Data**: Use the **Hold-Out Mode** generated in Step 1.2 (Distinct Physics Engine: Analytical vs. Surrogate) to ensure statistical independence from the training data's generative assumptions.

6. **Statistical Inference**
   - `04_inference.py`:
     - Permutation importance for each feature; compute p‑values.
     - Apply Benjamini-Hochberg FDR correction (q ≤ 0.05) across the three target‑specific tests (FR‑005, SC‑004).
     - **Scope Note**: If synthetic data is used, p-values are reported as measures of "Internal Consistency" only.
     - Record adjusted p‑values in model output.
     - Perform sensitivity analysis: sweep any decision cutoff (e.g., defect density thresholds at deciles) and report FPR/FNR per sweep (FR‑007, SC‑005).

7. **Confounding Control (FR‑013)**
   - If `synthesis_method` or `grain_size` columns exist:
     - Stratify CV folds by these variables.
   - If absent:
     - Proceed without stratification.
     - Include any available confounders as covariates.
     - Log the omission as a limitation.
     - **Do NOT** create synthetic strata.

8. **External Validation & Reporting (FR‑009, SC‑007)**
   - Attempt to locate an external validation dataset (experimental or distinct DFT).
   - **Logic**:
     - If **Synthetic Data** was used as the primary source: Generate `Validation_Report.json` with `status: "SYNTHETIC_FALLBACK"`.
     - If **Real Data** was used but no external validation exists: Generate `Validation_Report.json` with `status: "NO_EXTERNAL_DATA"`.
   - If an external set is found: Evaluate model on the external set and record metrics.

9. **Reproducibility & Versioning**
   - All scripts pinned in `code/requirements.txt`.
   - Random seeds (`seed=42`) and synthetic generator version (git commit hash) recorded in `model_config.yaml`.
   - Feature matrix checksum saved in state file (Principle III & VII) via `scripts/update_state_hashes.py`.
   - CI step `scripts/update_state_hashes.py` runs after each major artifact creation.

## Constitution Check

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| I. Reproducibility | **PASS** | Seeds pinned; deterministic synthetic generator (versioned); CI recomputes checksums. |
| II. Verified Accuracy | **PASS** | All external citations (physics‑based scaling laws) are real; synthetic generator logic is version-controlled and documented as a "Verified Artifact". |
| III. Data Hygiene | **PASS** | Checksums recorded; raw → processed → derived files never modified in place. |
| IV. Single Source of Truth | **PASS** | Figures and statistics trace to `data/processed/` and `code/` scripts; values (e.g., seed=42 [FR-004], 6 hours [SC-006]) trace to Spec. |
| V. Versioning Discipline | **PASS** | `scripts/update_state_hashes.py` updates artifact hashes; synthetic generator version logged. |
| VI. Defect Dataset Integrity | **PASS (Real Data) / Conditional (Synthetic)** | Primary attempt to download the 2022 dataset. If synthetic fallback is triggered, status is "Method Validation Mode" (not a violation, but a scope shift). |
| VII. Modeling Reproducibility | **PASS** | `model_config.yaml` stores split ratios, hyper‑parameters, seeds; feature matrix checksum recorded in state file. |

## Project Structure

```
specs/001-quantify-defect-influence/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── defect_entry.schema.yaml
    ├── model_output.schema.yaml
    ├── output.schema.yaml
    └── processed_data.schema.yaml
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Data Fallback | Required by FR‑010/FR-002 when primary dataset missing. | Hard‑failing would block CI. |
| Mock DFTB+ | Required for missing fracture energy without heavy compute. | Real DFTB+ exceeds CPU limits. |
| Collinearity Handling (Ridge) | FR‑008 mandates handling; Ridge is preferred over arbitrary exclusion. | Simple exclusion may discard physically relevant coupled variables. |
| Distinct Physics Engine Hold‑out | FR‑012 requires either distinct split or distinct physics engine. | Using only a split would miss the "engine" clause when synthetic data are used. |
| Dataset Integrity | Constitution VI restricts sources; primary attempt to fetch 2022 dataset respects this. | Ignoring primary source would breach principle. |
| Validation Report Logic | FR-009/SC-007 requires specific status values. | Ambiguity in status (NO_EXTERNAL_DATA vs SYNTHETIC_FALLBACK) must be resolved. |