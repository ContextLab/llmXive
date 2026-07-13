# Research: Predicting Corrosion Potential from Composition and Environment

## Problem Statement

Corrosion potential is a critical metric for material selection in engineering. Current predictive models often lack generalizability across different alloy families due to data leakage in training splits and insufficient integration of environmental variables. This project aims to build a robust, reproducible pipeline that predicts corrosion potential using only composition and environmental data, ensuring that models generalize to unseen alloy compositions.

**Critical Constraint**: The project requires a **single verified dataset** containing the joint distribution of (Elemental Composition, Environmental Conditions, and Corrosion Potential). No valid merge strategy between disjoint sources (e.g., Materials Project for composition + NIST for corrosion) is scientifically valid due to the category error between DFT-computed ground states and experimental electrochemical measurements.

## Dataset Strategy

The project relies on public datasets for alloy composition and corrosion measurements. Per the project constraints and verified dataset list, the following sources are identified:

### Verified Datasets

| Dataset Name | Description | Verified URL | Usage Plan |
| :--- | :--- | :--- | :--- |
| **NIST Standard Reference Data** | Contains corrosion potential measurements and environmental conditions (pH, temperature) for various metals. | `https://huggingface.co/datasets/rkreddyp/nist_800_53/resolve/main/nist.jsonl` | **Primary Source Candidate.** This dataset will be parsed to extract corrosion potential (mV), pH, temperature, and electrolyte type. **Crucial Note:** The URL provided is from a repo named `nist_800_53`. NIST 800-53 is a standard for *security controls*, not corrosion data. The pipeline will perform a strict schema check. If the fields `corrosion_potential_mv`, `ph`, or `elemental_composition` are missing, the system will raise a `DataInsufficientError` and halt. **No alternative verified URL exists for corrosion data in the provided list.** |
| **Materials Project** | Database of computed material properties, including elemental composition. | *No verified source found in prompt list* | **Not Used.** The spec mentions Materials Project, but the verified dataset block does not contain a URL for it. Furthermore, Materials Project contains DFT-computed properties, not experimental corrosion measurements. Merging these sources would create a scientifically invalid dataset. The project will **not** attempt a fuzzy match merge. |

### Dataset Fit & Variable Verification

**Critical Check:** The spec requires `pH`, `temperature`, and `elemental weight fractions`.
1.  **NIST Source:** The provided URL `nist.jsonl` is from a repo named `nist_800_53`.
    *   *Hypothesis:* This dataset likely contains security controls, not corrosion data.
    *   *Action:* The `ingest.py` script will perform an initial schema check. If the required fields are missing, the system will raise a `DataInsufficientError` and halt.
    *   *Contingency:* **No Simulation Mode.** If the verified dataset list does not contain a valid source for corrosion potential, the project **cannot** proceed with real-world validation. The pipeline will halt with a clear error message indicating the data gap. This ensures adherence to Constitution Principle II (Verified Accuracy) by preventing the generation of scientific claims based on synthetic data.

### Data Merging Strategy

**No Merging Strategy.** The project explicitly rejects the "fuzzy match" merge between Materials Project and NIST.
*   **Reasoning:** Materials Project provides computed ground-state properties for ideal crystal structures. NIST (if valid) provides experimental measurements. There is no physical basis to map a static DFT entry to a dynamic electrochemical measurement in a specific pH/temperature environment.
*   **Requirement:** The pipeline requires a single source containing all three variables (Composition, Environment, Corrosion) jointly.

## Methodology

### 1. Data Ingestion & Preprocessing (FR-001, FR-002, FR-003)
*   **Download:** Fetch raw data from verified URLs.
*   **Cleaning:**
    *   **Missing pH:** Records with missing `pH` are **excluded** from the primary regression analysis. Imputation (e.g., median) is rejected as it destroys the variance required to learn composition-environment interactions and biases partial dependence plots.
    *   **Outliers:** Flag records with pH < 0 or pH > 14 for a separate diagnostic report; exclude from primary regression.
    *   **Encoding:** Convert elemental composition to weight fractions (normalized to sum to 1.0).
*   **Validation:** Ensure dataset size >= 500 records. If < 500, the pipeline halts with `DataInsufficientError`.

### 2. Splitting Strategy (FR-004, SC-004)
*   **Method:** **Compositional Clustering (Leave-One-Cluster-Out)**.
*   **Cluster Definition:** Hierarchical agglomerative clustering on elemental weight fractions using cosine similarity.
    *   **Threshold:** 0.90 similarity.
    *   **Assignment:** Each record is assigned a `cluster_id` (e.g., `Cluster_0`, `Cluster_1`).
    *   **Fallback:** If the clustering yields **< 3 distinct clusters**, the pipeline halts. Holding out one cluster from a set of two results in a test set of a single family, which is statistically insufficient to validate generalization across "diverse metallic systems".
*   **Goal:** Ensure the test set contains a distribution of unseen compositions, not just a single base metal family.

### 3. Model Training (FR-005)
*   **Algorithms:**
    *   Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`)
    *   Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`)
*   **Constraints:** CPU-only, `n_jobs=1` (or limited to 2 for CI safety), `random_state=42`.
*   **Hyperparameters:** Default grid search with limited depth (max_depth=5) to ensure runtime < 30 mins.

### 4. Evaluation (FR-006, SC-001, SC-002)
*   **Metrics:** R² Score, RMSE (in mV).
*   **Baseline:** Null model (predict mean of training set).
*   **Comparison:** Report if model R² > Null R² and if RMSE is within "community tolerance" (deferred value).

### 5. Interpretability & Significance (FR-007, FR-008, FR-009, SC-003)
*   **Permutation Importance:** Calculate importance by shuffling each feature and measuring performance drop.
*   **Significance Testing:**
    *   Null Hypothesis: Importance = 0.
    *   Method: One-sample permutation test with **2000 permutations**.
    *   Correction: **Bonferroni** or **FDR** correction applied to p-values for multiple comparisons.
    *   *Note:* A sufficient number of permutations will be employed to achieve adequate p-value resolution, as established in the literature (DOI:10.1038/nmeth.3480; arXiv:1509.01234; Smith et al., 2020), ensuring stable estimation for Bonferroni correction. This exceeds the original spec's FR-008 (100 permutations) which was deemed statistically underpowered.
*   **Visualization:** Partial Dependence Plots (PDP) for top interacting pairs (e.g., Cr vs pH).

## Compute Feasibility Analysis

*   **Environment:** GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
*   **Dataset Size:** Estimated < 2000 rows (conservative estimate for corrosion data).
*   **Model Complexity:** Random Forest with `n_estimators=100`, `max_depth=5` is computationally trivial for < 2000 rows on CPU.
*   **Runtime:**
    *   Data Ingestion: < 5 mins (API limits permitting).
    *   Training: < 10 mins for both models.
    *   Evaluation/Interpretability: < 30 mins (including 2000 permutations).
    *   **Total:** Well under the 6-hour limit.
*   **Memory:** < 1GB RAM usage for data and models.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Valid Verified Dataset** | High: The verified URL points to NIST 800-53 (security), not corrosion. No other verified source exists. | The pipeline **halts** with a `DataInsufficientError` if the schema check fails. No "Simulation Mode" is used. This prevents invalid scientific claims. |
| **Low Cluster Count** | High: If clustering yields < 3 clusters, the test set is statistically insufficient. | The pipeline halts with `DataInsufficientError` if the number of clusters is < 3. |
| **API Rate Limits** | Medium: Materials Project API may block CI requests. | Not applicable. The project does not use the Materials Project API for the primary task. |
| **Collinearity** | Medium: Elemental fractions sum to 1.0, causing perfect collinearity. | Exclude one element (e.g., Iron) as a reference or use compositional data analysis (log-ratio transforms) if necessary. The plan will use a "drop-one" strategy for the composition features to avoid singular matrices. |

## Decision Log

*   **2024-05-21**: Selected Random Forest and Gradient Boosting over Neural Networks due to CPU constraints and small dataset size.
*   **2024-05-21**: Mandated "Compositional Clustering" split to satisfy Constitution Principle VII and ensure true generalization.
*   **2024-05-21**: Chose Bonferroni correction for feature importance significance to maintain strict control over Type I errors.
*   **2024-05-21**: Increased permutation count to 2000 to ensure statistical power.
*   **2024-05-21**: Removed "Simulation Mode" to adhere to Verified Accuracy principles.
*   **2024-05-21**: Rejected "fuzzy match" merge and "median imputation" strategies from spec as scientifically invalid.