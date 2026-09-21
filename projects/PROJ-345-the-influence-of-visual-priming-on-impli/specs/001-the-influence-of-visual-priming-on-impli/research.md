# Research: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Research Question & Hypotheses

**Primary Question**: Does visual priming with emotionally valenced stimuli influence implicit attitudes (measured by IAT response times) towards ambiguous social stimuli, and is this effect moderated by stimulus ambiguity?

**Hypotheses**:
1. **H1 (Main Effect)**: Trials primed with negative valence stimuli will exhibit slower response times (indicating stronger implicit bias) compared to trials primed with positive valence stimuli.
2. **H2 (Interaction)**: The effect of prime valence on response times will be moderated by the ambiguity of the target stimulus; the effect will be stronger for high-ambiguity targets.
3. **H3 (Observational)**: All observed associations are correlational and do not imply causation due to the secondary nature of the data and lack of randomization in the original dataset.

## 2. Dataset Strategy

The project relies on publicly available, programmatic datasets. Per the verified sources, the following datasets are selected:

| Dataset Name | Purpose | Verified URL | Load Method | Notes |
|:--- |:--- |:--- |:---:--- |
| **IAT Embeddings** | Primary IAT response times, participant IDs, and stimulus metadata | ` | `datasets.load_dataset(..., data_files=URL)` | **Schema Verified**: Contains `response_time`, `participant_id`, `stimulus_id`. **Demographics**: Columns `age`, `gender`, `education` are explicitly mapped if present. If missing, model term omitted. |

**Data Availability Assessment**:
- The primary dataset (`davanstrien/ia_test_embeddings`) is directly downloadable via HTTP/Parquet.
- No access-gated data (e.g., ADNI, UK Biobank) is used.
- **Demographics Extraction**:
 - **Target Columns**: `age`, `gender`, `education`.
 - **Logic**: The pipeline checks for the existence of these columns.
 - If present: Included as fixed effects in the LME model.
 - If missing: The corresponding term is **omitted** from the model equation. A flag `Demographics Missing: <column_name>` is written to `state/demographics_status.json`. No random slopes for demographics are computed.
 - **No Fallback**: No alternative dataset is used for demographics to avoid cross-dataset confounding.
- **Ambiguity/Valence**: If human-rated scores are missing, the pipeline derives them using independent methods (see Section 3.4).
- **Streaming**: For large datasets, `streaming=True` will be used to process data in chunks to stay within 7GB RAM limits.
- **Fallback**: If the primary dataset schema is invalid, the pipeline halts with 'Data Gap: Schema Mismatch'. No unverified fallbacks (e.g., 'IATI Cloud') are used.

## 3. Statistical Methodology

### 3.1. Model Specification

The analysis utilizes a Linear Mixed-Effects (LME) model. The model specification is **conditional** based on data availability:

**Case A: Demographics Available**
$$ RT_{ij} = \beta_0 + \beta_1(Valence_i) + \beta_2(Ambiguity_i) + \beta_3(Valence_i \times Ambiguity_i) + \beta_{cov}(Covariates_i) + u_j + \epsilon_{ij} $$

**Case B: Demographics Missing**
$$ RT_{ij} = \beta_0 + \beta_1(Valence_i) + \beta_2(Ambiguity_i) + \beta_3(Valence_i \times Ambiguity_i) + u_j + \epsilon_{ij} $$
*(The term $\beta_{cov}(Covariates_i)$ is explicitly omitted.)*

Where:
- $RT_{ij}$: Response time for trial $i$ by participant $j$.
- $Valence_i$: Derived prime valence (continuous or categorical).
- $Ambiguity_i$: Stimulus ambiguity score (human-rated or derived).
- $Covariates_i$: Demographic covariates (Age, Gender, Education) **only if present** in the dataset.
- $u_j$: Random intercept for participant $j$.
- $\epsilon_{ij}$: Residual error.
- **Robust Standard Errors**: If $Ambiguity_i$ or $Valence_i$ are derived (not human-rated), the model MUST use Robust Standard Errors (Huber-White) to account for measurement error.

### 3.2. Rigor & Corrections
- **Multiple Comparisons**: False Discovery Rate (FDR) correction (Benjamini-Hochberg) applied to all hypothesis tests involving >1 outcome (FR-004).
- **Collinearity**: Variance Inflation Factor (VIF) calculated for fixed effects. If VIF > 5.0, the system flags the result and refrains from claiming independent effects (FR-005).
- **Correlation Check**: Pre-modeling correlation check between Valence and Ambiguity. If correlation > 0.7, the interaction term is dropped and the model is re-run with main effects only, with a report warning.
- **Causal Framing**: All results explicitly stated as associational (FR-003).
- **Sensitivity Analysis**: Significance thresholds ($\alpha$) swept across [0.01, 0.05, 0.10] to assess robustness (FR-006). Results are saved to `sensitivity_analysis.csv` and embedded in the final PDF.

### 3.3. Power & Sample Size
- **Power Justification**: A priori power analysis will be conducted using G*Power logic for LME interaction effects.
 - **Effect Size**: Assumed small-to-medium (f=0.15).
 - **Power**: 0.80.
 - **Alpha**: 0.05.
 - **Minimum N**: The pipeline calculates the minimum number of trials required ($N_{min}$). If the available dataset falls below $N_{min}$, the study proceeds with a 'Power Limitation' flag in the report, explicitly stating the study is underpowered to detect the interaction effect.
- **Sample Size**: Determined by the available rows in the verified dataset after filtering for missing linkage.

### 3.4. Derivation Strategy (Independent Measurement)
- **Valence**: Derived using an emotion classifier (e.g., `transformers` pipeline for text/images).
- **Ambiguity**: Derived using a **Lexical Ambiguity Index** (for text) or **Face Texture Variance** (for images). These methods are distinct from Valence derivation to prevent circular validation.
- **Selection Bias Correction**: If the analysis is scoped to human-rated ambiguity (due to missing data), a sensitivity analysis compares the 'human-rated' subset to the 'derived' subset. If significant bias is found, the interaction hypothesis is reported with a 'Selection Bias' warning.

## 4. Compute Feasibility & GPU Strategy

- **CPU-First**: All data ingestion, preprocessing, and LME fitting (via `statsmodels` or `lme4` equivalent in Python) will run on CPU.
- **GPU Fallback**: Optional for heavy inference (e.g., large transformer inference). If the valence derivation step requires a large transformer model that exceeds CPU time limits:
 - The pipeline will attempt a scaled-down inference (e.g., 8-bit quantization, smaller batch size) on a free Kaggle GPU.
 - The execution agent will auto-detect CUDA requirements and offload the specific inference task.
 - **No Fabrication**: If the model cannot run on either CPU (scaled) or GPU (scaled), the pipeline halts; no synthetic data is generated.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Conditional Model Equation** | Explicitly handles missing demographic data by omitting the term rather than imputing, preserving validity. |
| **CPU-First LME** | `statsmodels` is lightweight and runs efficiently on 2 CPU cores. No GPU needed for regression. |
| **FDR over Bonferroni** | Preserves statistical power for exploratory subgroup analysis while controlling error rate. |
| **Halt on Missing Data** | Ensures data integrity and prevents biased results from imputation of critical stimulus metadata. |
| **Derivation Allowed** | Per FR-001, derivation is the mandated fallback if human data is missing. |
| **Robust SE** | Required to handle measurement error in derived predictors. |
| **Independent Derivation** | Prevents circular validation of Valence and Ambiguity. |