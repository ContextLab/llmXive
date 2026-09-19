# Research: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## 1. Problem Statement & Hypothesis

**Problem**: Laser Surface Texturing (LST) parameters (pulse duration, power, scanning speed, pattern geometry) significantly influence wear resistance, but the functional relationship is often non-linear and material-specific. Current studies are fragmented across materials, hindering "virtual prototyping."

**Hypothesis**: A non-linear regression model (e.g., Gradient Boosting) trained on aggregated open data can predict wear rate with higher accuracy (R²) than linear baselines, and feature importance analysis (SHAP) will reveal that `scanning_speed` and `pattern_geometry` dominate wear resistance, interacting non-linearly with material hardness.

**Scope**: The study is strictly **associational**. Causal claims are prohibited (FR-007) as the data is aggregated from observational studies without random assignment.

**Data Sufficiency & Scope Degradation**:
- **Full Study**: Requires N >= 300 and >= 3 material classes.
- **Pilot Study**: If 100 <= N < 300, the study proceeds with a "pilot" scope, explicitly stating that cross-material generalizability is untestable.
- **Halt**: If N < 100 or schema mismatch, the pipeline halts with `data_insufficiency_error`.
- **Single Source Limitation**: If only one source is found, the "virtual prototyping" claim is explicitly flagged as untestable, and the research question is reframed to "Single-Source Exploratory Analysis."

## 2. Dataset Strategy

### 2.1 Data Sources (Verified)

The plan utilizes the following verified, directly-downloadable datasets. No access-gated data is used.

| Dataset Name | Verified URL | Content Fit |
|:--- |:--- |:--- |
| **LST Wear Data** | ` | Primary source for LST parameters (`pulse_duration`, `power`, `scanning_speed`) and wear outcomes. **Note**: Schema validation is strict. If this dataset lacks LST columns, the pipeline halts. |
| **Auxiliary Sources** | *None* | The provided verified list contains only one candidate. The plan does NOT fabricate additional sources. |

**Data Availability Assessment**:
- **Primary Source**: The HuggingFace dataset `hieuhocnlp/lstm-deep-usc-test` is the only verified candidate.
- **Risk**: The dataset name suggests a time-series/NLP context, not tribological wear data.
- **Mitigation**: The ingestion pipeline (`code/ingest.py`) MUST validate the schema. If the dataset lacks `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, or `wear_rate`, the system MUST halt with `data_schema_mismatch` (FR-001).
- **Source Count**: The spec requires ≥3 distinct sources. The current verified list contains only **one** candidate dataset.
 - **Action**: The pipeline will proceed with the single verified source but will trigger `data_source_limitation` warning (FR-012). If the single source yields < 300 records, the study is explicitly framed as "pilot" or "exploratory," and the "virtual prototyping" claim is marked as untestable.

### 2.2 Data Ingestion & Preprocessing

1. **Loading**: Use `pandas.read_parquet` for the HuggingFace source.
2. **Schema Mapping**: Map source columns to canonical schema:
 - `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry` (LST params)
 - `hardness`, `elastic_modulus` (Material props)
 - `wear_rate` (Target)
 - `contact_load`, `sliding_speed`, `density` (Optional for Archard)
3. **Missing Value Handling (FR-002)**:
 - **Predictors**: Drop records where `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, or `elastic_modulus` are missing.
 - **Archard Inputs**: If `contact_load` or `sliding_speed` are missing, **retain** the record, set `normalization_method='raw'`, and use raw `wear_rate`.
 - **Target**: Drop records where `wear_rate` is missing.
4. **Archard Normalization (FR-009, FR-018)**:
 - **Unit Conversion**: Detect units of `wear_rate` (mm, mg, mm³). Convert to Volume (V) using density and geometry (e.g., `V = mass / density` or `V = area * depth`).
 - **Calculation**: Calculate Wear Coefficient $K = \frac{V \cdot H}{L \cdot S}$ (where $H$=Hardness, $L$=Load, $S$=Sliding Distance).
 - **Fallback**: If $L$ or $S$ missing, flag as `raw`.
 - **Missing Contact Area**: If `contact_area` is missing, derive from `Load / Hardness` (plastic assumption) or flag as 'estimated'.
 - **Missing Sliding Distance**: If `sliding_distance` is missing, derive from `sliding_speed * time` (if time available) or flag as 'raw'.
5. **Target Definition & Tautology Prevention**:
 - To avoid circular validation (predicting K using H), the primary target is defined as **Raw Wear Rate** (or Volume Loss) where possible.
 - If K is used as the target, **Hardness** is excluded from the predictor set to prevent the model from simply learning $K \propto 1/H$.
6. **Encoding**: One-hot encode `pattern_geometry`.

### 2.3 Statistical Rigor & Methodology

- **Multiple Comparisons**: When running permutation tests (2000 permutations) for feature significance (FR-008), apply Benjamini-Hochberg correction to control False Discovery Rate (FDR).
- **Power Analysis (FR-014)**: Perform a priori power analysis (using `statsmodels.stats.power`) **before** model training on the **normalized subset**. If power < 0.8 for expected effect size, switch to Linear Regression or flag `power_insufficiency`.
- **Causal Framing (FR-007)**: All results framed as "associational." A post-processing **Causal Language Filter** scans the generated report to replace causal terms with "associates with" or "predicts."
- **Collinearity (FR-010, FR-015)**:
 - **Deterministic Resolution Strategy**: Iteratively remove the feature with the highest VIF > 5. If ties, remove the feature with the lowest mean absolute SHAP value (least important). Repeat until all VIFs <= 5.
 - **Hypothesis Preservation**: If a hypothesis-critical feature (e.g., `scanning_speed`) is removed due to collinearity, the report explicitly states: "Feature X dropped due to collinearity with Y; hypothesis regarding X untestable in isolation."
- **Model Selection**:
 - Models: Linear Regression, Random Forest, Gradient Boosting (FR-003).
 - Hyperparameter Tuning: GridSearchCV with ≥10 combinations (FR-004).
 - Validation: 5-Fold CV for tuning; Leave-One-Material-Class-Out (LOMO) for final generalizability (FR-006).
 - **Fallback**: If < 3 material classes, switch to 5-Fold CV and flag `fallback_active`. The research question shifts to "within-material prediction."
- **Sensitivity Analysis (FR-011)**:
 - Train model on 'normalized-only' subset.
 - Train model on 'full' (normalized + raw) subset.
 - **Statistical Validity Check (FR-017)**: Run Shapiro-Wilk (normality) and Levene's (homogeneity) on the 'raw' subset. If p < 0.05, exclude 'raw' from sensitivity analysis and report `raw_subset_invalid`.
 - Report the difference in R² and MAE between the two models.

### 2.4 Compute Feasibility

- **CPU-First**: All models (Linear, RF, GB) are CPU-tractable on standard computing resources.

The research question is: [Research Question Placeholder]. The method is: [Method Placeholder]. References: [Citation Placeholder]. No GPU required (FR-003).
- **Memory**: Streaming data loading and batch processing of SHAP values ensure memory usage stays < 7GB.
- **Runtime**: Grid search limited to 10 combinations; SHAP computed on a sample (if N > 1000) to stay within 6h limit.

### 2.5 Pipeline Architecture for Leakage Prevention

- **Scikit-Learn Pipelines**: All preprocessing (scaling, VIF reduction, encoding) is encapsulated in a `Pipeline` object.
- **Fitting**: The pipeline is fitted **only** on the training fold during cross-validation.
- **Transformation**: The same pipeline is applied to the test fold, ensuring no data leakage.

## 3. Decision Rationale

- **Why CPU?** The spec explicitly forbids GPU (FR-003). Standard regression models (RF, GB) are efficient on CPU for N < 1000.
- **Why Single Source?** Only one verified URL exists in the provided block. The plan strictly adheres to verified sources and handles the "single source" constraint by triggering warnings and scope degradation rather than fabricating data.
- **Why Dual-Track?** Required by FR-002/FR-009 to preserve data with missing load/speed without violating physics.
- **Why Pipeline?** Required by Constitution Principle VI to prevent data leakage in scaling and interaction terms.