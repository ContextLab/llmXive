# Research: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## 1. Dataset Strategy

### 1.1 Verified Datasets
The following datasets have been verified as accessible and relevant for this study. **No other dataset URLs are cited.**

| Dataset Name | Source Type | Verified URL / ID | Status |
| :--- | :--- | :--- | :--- |
| LST Wear Data Aggregation | Literature Supplements (Local) | `data/raw/lst_supplement_1.csv`, `data/raw/lst_supplement_2.csv` | **Verified (Local)**: These files are provided as fixed inputs with checksums. Dynamic search logic is disabled. |
| Tribology Open Data | OpenML | `openml_id: 104` (Example) | **Pending Validation**: The pipeline will attempt to load `openml_id: 104` (or specific ID from verified list). If the ID is not found or does not match the schema, the pipeline fails immediately with a "Missing Specific Dataset ID" error. No dynamic search is performed. |
| HuggingFace Materials | HuggingFace Datasets | `huggingface_id: materials/tribology-wear` (Example) | **Pending Validation**: The pipeline will attempt to load `huggingface_id: materials/tribology-wear`. If not found, the pipeline fails immediately. |

*Note: As per the "Verified datasets" block in the input, if no specific programmatic source is found, the plan relies on the 'literature supplements' as fixed local files. The ingestion script will **not** attempt to search OpenML or HuggingFace dynamically. It will only attempt to load the specific IDs listed above or local files. If these fail, the pipeline triggers `data_insufficiency_error`.*

### 1.2 Data Acquisition & Processing Plan
1.  **Ingestion**:
    *   **OpenML**: Use `openml.datasets.get_dataset(id=104)` (or specific ID). **No search**. If ID not found, raise error.
    *   **HuggingFace**: Use `datasets.load_dataset("materials/tribology-wear")`. **No search**. If ID not found, raise error.
    *   **Literature**: Load fixed CSVs from `data/raw/`.
2.  **Standardization**:
    *   Map all incoming columns to the canonical schema: `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, `wear_rate`, `contact_load`, `sliding_speed`, `material_class`.
    *   Apply `schema_map.json` for alias resolution (e.g., "laser_power" -> "power").
3.  **Missing Value Handling**:
    *   **Predictors**: Drop rows with missing `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`.
    *   **Test Parameters**: Retain rows with missing `contact_load` or `sliding_speed` but set `normalization_method='raw'`.
4.  **Normalization**:
    *   Calculate specific wear coefficient $K$ using Archard's law: $K = \frac{V}{L \cdot S}$.
    *   **Constraint**: If `contact_load` or `sliding_speed` are missing, retain raw `wear_rate` and flag. **Critical**: When predicting `K`, the features `contact_load` and `sliding_speed` are **excluded** from the predictor set to prevent circular validation (Target Leakage).

### 1.3 Dataset Fit Assessment & Minimum Viable Dataset
*   **Required Variables**: `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, `wear_rate`, `material_class`.
*   **Potential Mismatch**: Many tribology datasets report "wear rate" (mm³/Nm) directly without providing raw `contact_load` or `sliding_speed`.
    *   **Mitigation**: The plan explicitly handles this by flagging `normalization_method='raw'` (FR-009) and including these in the sensitivity analysis (FR-011).
    *   **Minimum Viable Dataset Contingency**: If the aggregated `normalized_count` (records with valid Archard normalization) is < 100, the primary predictive modeling (FR-003, FR-004) is **halted**. The research question shifts to a **descriptive meta-analysis** of the available 'raw' data, and the pipeline proceeds only to FR-011 (Sensitivity Analysis) and descriptive statistics.
*   **Sample Size**: Target N=300. If the aggregated data falls short, the plan triggers `data_insufficiency_error` (SC-006) and proceeds only to sensitivity analysis.

## 2. Methodological Rationale

### 2.1 Model Selection
*   **Linear Regression**: Baseline for SC-001 comparison.
*   **Random Forest**: Captures non-linearities and interactions without overfitting on small datasets (N~300).
*   **Gradient Boosting**: High predictive power, robust to outliers.
*   **Rationale**: These are CPU-tractable, well-supported by `scikit-learn`, and sufficient for tabular data. No deep learning is required (FR-003).

### 2.2 Validation Strategy
*   **5-Fold CV**: Standard for hyperparameter tuning (FR-004).
*   **Leave-One-Material-Class-Out (LOMO)**: Critical for SC-003. Tests if the model learns a universal physical relationship or just material-specific patterns.
    *   *Small Sample Handling*: If a material class has < 15 records, the LOMO test for that class is skipped and marked as 'insufficient_samples'.
    *   *Fallback*: If <3 material classes exist, switch to 5-Fold CV and log a warning (FR-006).
*   **Conditional Permutation Testing**: Used for feature significance (FR-008) to avoid assumptions of normality and correct for multiple comparisons in a non-parametric way. **Crucially**, standard permutation is invalid for correlated features. The plan uses **conditional permutation** (permuting residuals) or **orthogonalization** (PCA) on correlated features before testing to ensure valid p-values.

### 2.3 Statistical Rigor
*   **Multiple Comparisons**: Addressed via Permutation Testing (sufficient iterations for robust inference) rather than Bonferroni, as features are correlated (FR-008).
*   **Collinearity**: VIF diagnostics (FR-010) will identify and remove redundant features. For significance testing, conditional permutation is used to handle remaining correlations.
*   **Causal Framing**: All results framed as associational (FR-007) due to observational data nature.
*   **Circular Validation Prevention**: When the target is the normalized wear coefficient `K` (derived from `contact_load` and `sliding_speed`), these two variables are **excluded** from the feature set. This prevents the model from simply learning the normalization formula.

### 2.4 Compute Feasibility
*   **CPU-First**: All models (`scikit-learn`) run efficiently on 2 CPU cores.
*   **Memory**: Dataset size is negligible for RAM.
*   **Time**: GridSearch (10+ params) + 2,000 permutations + SHAP on 300 rows will complete well within 6 hours.

## 3. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only Execution** | FR-003 mandates CPU-only. The dataset size and model complexity (RF/GB) are fully tractable on CPU. No GPU escape hatch is needed. |
| **Conditional Permutation over Standard** | Features (e.g., power, speed, energy) are highly correlated. Standard permutation assumes independence and yields invalid p-values. Conditional permutation preserves the correlation structure while breaking the specific feature-target link (FR-008). |
| **LOMO CV with Small Sample Check** | The research goal is "virtual prototyping" across materials. Standard K-Fold would leak material-specific patterns. LOMO is the only valid test for generalizability (FR-006, SC-003), but requires a minimum sample size (n>=15) per class for statistical validity. |
| **Archard Normalization with Feature Exclusion** | Wear rates are not comparable across studies without normalizing for load and speed. This is the standard in tribology (FR-009). However, to avoid circular validation, `contact_load` and `sliding_speed` are excluded from predictors when predicting `K`. |
| **Minimum Viable Dataset Contingency** | If `normalized_count` < 100, the primary analysis is statistically underpowered. The plan degrades gracefully to descriptive analysis of the 'raw' subset rather than producing invalid results. |
