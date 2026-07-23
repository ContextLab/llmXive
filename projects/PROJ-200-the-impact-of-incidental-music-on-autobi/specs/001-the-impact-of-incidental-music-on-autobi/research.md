# Research: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Literature Review & Theoretical Basis

The "reminiscence bump" describes the tendency for older adults to recall disproportionately more memories from adolescence and early adulthood (ages -30). This study investigates a specific mechanism: **incidental music exposure**. We hypothesize that tracks listened to frequently during the developmental window of adolescence (ages 0-15, per FR-001) become more strongly encoded in autobiographical memory, leading to higher vividness and valence ratings when these tracks are used as cues later in life.

Key theoretical frameworks:
- **Encoding Specificity Principle**: Memory retrieval is most effective when cues match the context of encoding. Incidental exposure during adolescence may create strong, context-rich associations.
- **Developmental Critical Periods**: Adolescence is a period of heightened neuroplasticity and emotional intensity, potentially strengthening music-memory associations.

## 2. Dataset Strategy

We require two primary data sources:
1.  **Music Exposure Data**: Track metadata (release date, popularity) and listen history (timestamps, user IDs).
2.  **Autobiographical Memory Data**: User-generated free-text cues (linked to tracks), vividness ratings, and valence ratings.

### Verified Datasets

Per the project constraints, we utilize the following verified sources:

| Dataset | Description | Verified URL | Relevance |
|---------|-------------|--------------|-----------|
| **Million Song Dataset (MSD)** | Track metadata, popularity, and listen counts. | *No verified URL provided in the input block.* |
| **Autobiographical Memory Test (AMT)** | Free-text cues and memory ratings. | *No verified URL provided in the input block.* |

**Feasibility Assessment & Gap Resolution**:
The specification requires the **Million Song Dataset (MSD)** and **Autobiographical Memory Test (AMT)**. However, the "Verified datasets" block provided in the input **does not contain** the actual MSD or AMT datasets.

**Decision**: 
- **Prototype Run**: The pipeline will use **simulated data** generated to match the schema of the required datasets. This allows for validation of the pipeline logic, statistical methods, and power calculations against a known ground truth.
- **Path to Real Data**: A specific section (Section 5) details the steps required to obtain and integrate the real MSD and AMT datasets once available.

### Mock Data Generation Protocol

To ensure the prototype run is scientifically valid for code testing, the mock data will be generated with the following properties:
- **Effect Size**: A predefined correlation (r=0.20, beta=0.15) between `adolescent_exposure_ratio` and `mean_vividness` will be embedded to test power calculations.
- **Temporal Structure**: Listen timestamps will be generated to reflect realistic listening patterns across the lifespan, ensuring the `adolescent_exposure_ratio` calculation is non-trivial.
- **Psychometric Properties**: Vividness and valence ratings will be generated with realistic distributions and correlations (e.g., positive correlation between vividness and valence) to mimic the AMT.
- **Selection Bias**: A non-random selection process will be simulated where tracks with higher exposure are more likely to be recalled as cues, allowing us to test the Heckman correction.

**Data Strategy Table**:

| Component | Source Strategy | Verification Status |
|-----------|-----------------|---------------------|
| **Track Metadata** | Simulated based on MSD schema (release date, popularity). | ⚠️ **Simulated**: Used for prototype validation. |
| **Listen History** | Simulated with realistic temporal structure. | ⚠️ **Simulated**: Used for prototype validation. |
| **Memory Cues/Ratings** | Simulated based on AMT schema with embedded effect size. | ⚠️ **Simulated**: Used for prototype validation. |

**Dataset Variable Fit**:
- **Required Variables**: `user_id`, `track_id`, `listen_timestamp`, `birth_year`, `cue_text`, `vividness`, `valence`, `track_release_date`, `popularity`.
- **Fit**: The simulated data will strictly adhere to the schema defined in `data-model.md`, ensuring all required variables are present and correctly typed.

## 3. Statistical Methodology

### Primary Model (FR-005)
- **Type**: Linear Mixed-Effects Model (LMM).
- **Formula**: `mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)`
- **Rationale**: Accounts for the hierarchical structure of data (multiple tracks per user) and individual baseline differences in vividness ratings.
- **Software**: `statsmodels` (Python) or `lme4` (R via `rpy2` if needed, but `statsmodels` is preferred for Python-only stack). `statsmodels` supports `MixedLM`.

### Sensitivity Analysis (FR-006)
- **Method**: Re-run aggregation and modeling with Levenshtein distance thresholds across a range of low values.
- **Metric**: Stability of the `adolescent_exposure_ratio` coefficient and p-value across thresholds.
- **Note**: Aggregation is **re-run** for each threshold to ensure the data structure changes with the matching stringency.

### Parametric Bootstrap (Replaces FR-007)
- **Method**: Parametric bootstrap to generate a null distribution for the fixed effect coefficient (`adolescent_exposure_ratio`).
- **Procedure**:
  1. Fit the LMM to the observed data.
  2. Extract the residuals.
  3. Resample residuals with replacement.
  4. Generate new outcome values (`mean_vividness`) using the fixed effects and random intercepts from the original model plus the resampled residuals.
  5. Refit the model to the new outcome data.
  6. Repeat the procedure iteratively to build a null distribution of the coefficient.
- **Null Hypothesis**: The coefficient for `adolescent_exposure_ratio` is zero.
- **P-value**: Proportion of bootstrap coefficients with an absolute value greater than or equal to the observed coefficient.
- **Rationale**: This method preserves the random intercept structure and correctly tests the fixed effect null hypothesis, unlike the block-permutation test which was invalid for this design.

### Selection Bias Correction (New Section 3.5)
- **Method**: Two-Stage Heckman Correction (or Inverse Probability Weighting).
- **Rationale**: Addresses the circularity where tracks are selected as cues based on salience (which is driven by exposure).
- **Procedure**:
  1. **Selection Model**: Model the probability of a track being recalled as a cue (binary outcome) based on exposure and other covariates.
  2. **Inverse Mills Ratio**: Calculate the inverse Mills ratio from the selection model.
  3. **Outcome Model**: Include the inverse Mills ratio as a control variable in the primary LMM.
- **Outcome**: This breaks the circular dependency and provides an unbiased estimate of the exposure effect.

### Multiple Comparison Correction
- **Context**: Sensitivity analysis involves multiple models.
- **Correction**: Apply Bonferroni or Benjamini-Hochberg correction to the p-values from the sensitivity analysis if interpreting them as a family of tests. However, the primary inference comes from the main model (threshold=3 or optimal).

### Power & Sample Size
- **Limitation**: The mock dataset size is known and controlled.
- **Acknowledgement**: The plan explicitly states that power calculations are validated against the known effect size in the mock data. Results from the prototype run are for **pipeline validation**, not statistical inference on real data.

### Measurement Validity
- **AMT**: The Autobiographical Memory Test is a validated instrument. The mock data mimics its psychometric properties for the purpose of testing the pipeline logic.

### Collinearity Check (EC-003)
- **Method**: Calculate Variance Inflation Factor (VIF) for `adolescent_exposure_ratio` and `popularity`.
- **Threshold**: VIF > 5 triggers a warning.

### Fallback Mechanism (FR-008)
- **Trigger**: If >50% of users have missing birth years.
- **Action**: **Exclude** these users from the primary LMM analysis.
- **Descriptive Analysis**: Calculate the "Global Exposure" metric (mean adolescent exposure for the user's birth decade) for the excluded subset and report it descriptively. Do **not** use it as a predictor in the primary model to avoid ecological fallacy.

## 4. Compute Feasibility

- **CPU-First**: The LMM and parametric bootstrap on a mock dataset (≤ 100k rows) will run comfortably on the GitHub Actions free-tier (2 CPU, 7GB RAM).
- **Streaming**: If the real MSD were used, `datasets.load_dataset(..., streaming=True)` would be used to avoid memory overflow.
- **No GPU Required**: The statistical methods (LMM, bootstrap) are CPU-tractable. No deep learning models are involved.

## 5. Data Availability & Risks

- **Risk**: The primary datasets (MSD, AMT) are **not** in the verified URL list.
- **Mitigation**: The pipeline is designed to run with **simulated data** that strictly adheres to the schema defined in `data-model.md`. This ensures the code logic is correct. The `research.md` explicitly states that the **results are not generalizable** until the real datasets are obtained and integrated.
- **Execution**: The CI runner will execute the pipeline with the simulated data to generate the required artifacts (`data/processed/*.parquet`, `data/final/*.csv`) for validation.
- **Path to Real Data**:
  1.  **MSD**: Obtain access to the full Million Song Dataset via the official HuggingFace repository (`brian/MSD`) or the original source (UCI/MSD team) once credentials are secured.
  2.  **AMT**: Obtain access to the Autobiographical Memory Test dataset via the official repository or a validated public source.
  3.  **Pipeline Adaptation**: Replace the mock data generation step (`01_download_data.py`) with the real data fetcher. Update `requirements.txt` if new dependencies are needed.
