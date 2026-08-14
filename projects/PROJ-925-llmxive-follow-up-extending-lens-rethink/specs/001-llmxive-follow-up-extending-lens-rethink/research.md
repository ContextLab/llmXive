# Research: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Research Question

Which linguistic features (uncertainty, complexity, density) predict the deviation between CLIP scores and human preference ratings in text-to-image generation, and can this relationship be modeled efficiently on CPU resources?

## Dataset Strategy

The primary dataset is **pick-a-pic**. The specification (FR-003) explicitly requires this dataset and forbids synthetic fallbacks.

**Verified Source Status**:
The provided "# Verified datasets" block **does not** contain a verified URL for 'pick-a-pic'.
- **Action**: The implementation **MUST** attempt to load the dataset via the Hugging Face `datasets` library using the canonical name `pick-a-pic`.
- **Fallback**: If `datasets.load_dataset("pick-a-pic")` fails (e.g., 404, private, or removed), the system **MUST** raise a `DataSchemaError` with the message "Missing required dataset or column: pick-a-pic" and halt execution. **No alternative URL will be fabricated.**
- **Rationale**: The spec (FR-003) states: "If the 'pick-a-pic' dataset is unavailable... the system MUST raise a DataSchemaError... No synthetic or fallback data sources are permitted."

**Dataset Variables & Fit**:
- **Required Variables**: `caption` (text), `clip_score` (float), `human_rating` (float).
- **Fit Check**: The raw `pick-a-pic` dataset typically contains image-text pairs and binary preferences (chosen/rejected), NOT pre-computed `clip_score` or scalar `human_rating`.
- **Mitigation**: A distinct **Phase 0 (Data Preprocessing & Score Generation)** will be executed to:
  1. Generate `clip_score` by running a pre-trained CLIP model (batched, CPU) on the image-text pairs.
  2. Derive `human_rating` from the binary preference (chosen=1.0, rejected=0.0) or use the `score` column if the specific HF subset includes it.
  3. If neither scalar rating nor preference pairs are available, the system halts with `DataSchemaError`.

**Data Volume & Sampling Strategy**:
- **Risk**: The full dataset may exceed memory or the predefined CPU budget.
- **Mitigation**: A **Stratified Sampling** strategy is mandated to ensure statistical power for detecting small effect sizes (r >= 0.1).
  - **Strata**: Caption length (quartiles) and syntactic depth (quartiles).
  - **Minimum Sample Size**: N=10,000 rows, ensuring at least 250 samples per stratum.
  - **Logic**: If the full dataset can be processed within 6 hours, use the full dataset. Otherwise, perform stratified sampling to preserve the distribution of the 'alignment gap'.
  - **Power**: This sample size is sufficient to detect r=0.1 with >80% power at α=0.05.
  - **Rationale**: Random sampling risks under-representing the 'alignment gap' if it correlates with complexity; stratification ensures the distribution of the target variable is preserved.

**Data Access Plan**:
1. Attempt `datasets.load_dataset("pick-a-pic", streaming=True)`.
2. If successful, execute **Phase 0** to generate missing scores.
3. If the dataset is inaccessible, raise `DataSchemaError` immediately.
4. No other datasets (COCO, CLIP, BERT) are used for the *primary* target variable calculation, though BERT models are used for feature extraction.

## Methodology

### Phase 0: Data Preprocessing & Score Generation (New)
- **Objective**: Generate `clip_score` and `human_rating` if missing.
- **CLIP Score**: Run `clip-score` model (batched, CPU) on image-text pairs.
- **Human Rating**: Derive from binary preference (chosen=1.0, rejected=0.0) or use existing `score` column. If the dataset only provides rankings, map to a scalar (e.g., 0.0 to 1.0) based on the proportion of times an image was chosen. If no scalar mapping is possible, halt with `DataSchemaError`.
- **Validation**: Ensure `human_rating` is a scalar float. If binary, proceed with caution (see Phase 2).

### Phase 1: Linguistic Feature Extraction (US-1, FR-001, FR-002, FR-007)
- **Uncertainty Proxy**: Compute perplexity using a pre-trained BERT model (e.g., `bert-base-uncased`). Proxy = `ln(perplexity)`.
  - *Constraint*: Must complete < 5s/caption on CPU.
  - **Validation (FR-009)**: Compute correlation with a **Semantic Entropy Baseline**.
    - **Baseline Definition**: The Shannon entropy of the BERT next-token prediction distribution (computed via `transformers` logits) over the same caption. This provides a text-only, computable baseline for "semantic uncertainty".
    - **Threshold**: If correlation < 0.3, **HALT** execution with `CODE_INVALID_PROXY`. Do not proceed with a known invalid proxy.
  - **Contingency**: If the baseline cannot be computed, the study halts.
- **Syntactic Complexity**: Max depth of dependency parse tree using `spaCy`.
- **Noun-Phrase Density**: Count of distinct noun phrases / total tokens.
- **Covariates**: Token count, distinct noun phrase count (text-only).
- **Confounding Control**: Compute correlation between each linguistic feature and `Z_clip`. If correlation > 0.7, flag the feature as potentially trivially predicting the CLIP component.
- **Handling Edge Cases**:
  - Short captions (depth < 2): Exclude, log ID (FR-011).
  - Perplexity failure: Catch exception, log ID, exclude row (FR-012).

### Phase 2: Target Variable Calculation (US-2, FR-003, FR-010)
- **Standardization**: Z-score normalize `clip_score` and `human_rating` **strictly within the training fold** (fit on train, transform on test) to prevent data leakage.
- **Deviation**: $| \text{Z\_clip} - \text{Z\_human} |$.
- **Binary Target Acknowledgement**: If `human_rating` is binary (0/1), the target will be discrete. The plan acknowledges this and prioritizes **Spearman's rho** for evaluation.
- **Zero Variance Check**: Before training, check variance of deviation. If 0, halt with "Target not learnable" (FR-010).
- **Missing Data**: Exclude samples with missing `human_rating` (FR-003).
- **Statistical Handling**: The target variable is non-negative, bounded, and likely skewed. The analysis will **not** rely on Gaussian assumptions.

### Phase 3: Model Training & Evaluation (US-3, FR-004, FR-005)
- **Model**: XGBoost (CPU-only).
- **Configuration**: `tree_method='hist'` or default CPU. `torch.set_num_threads(1)` enforced.
- **Multicollinearity Handling**:
  - **VIF Check**: Calculate Variance Inflation Factor (VIF) for all predictors.
  - **Fallback**: If VIF > 5 for any feature, switch to **Ridge Regression** (L2 regularization) to stabilize coefficients while retaining both features as required by FR-007. Interpretation will be limited to 'joint contribution'.
- **Validation**: 5-fold cross-validation.
- **Metrics**:
  - **Pearson's r** (linear association).
  - **Spearman's rho** (monotonic association, robust to discrete targets).
  - **R²** (non-linear fit).
  - **Success Criteria**: If Spearman's rho > Pearson's r, prioritize R² as the primary success metric. Target: R² > 0.01 (explaining small but non-trivial variance).
  - **Distribution Awareness**: Use non-parametric bootstrapping for confidence intervals on metrics to account for the bounded, skewed nature of the target.

### Phase 4: Statistical Rigor (FR-006, FR-008, SC-004, SC-005)
- **Permutation Test**: **Conditional Permutation** (Block Permutation).
  - **Method**: Shuffle features within strata defined by token count bins or syntactic complexity quartiles to preserve the correlation structure among collinear features.
  - **N_permutations**: 1,000.
- **FDR Correction**: Apply Benjamini-Hochberg to p-values (FDR $\le$ 0.05).
- **Sensitivity Analysis**:
  - **Threshold Sweep**: Iterate over significance thresholds.
  - **Noise Injection**: Inject Gaussian noise into `human_rating` with σ = {0.01, 0.05, 0.1, 0.2} times the standard deviation of the human ratings in the training set (FR-008).
  - **Aggregation**: For each sweep, record the rank of each feature. Compute **mean rank** and **std dev of rank** across iterations.
  - **Output**: `stability_metrics.json` with fields `mean_rank` and `std_dev_rank` as defined in `significance_results.schema.yaml`.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Addressed via Benjamini-Hochberg procedure (FR-006).
- **Sample Size/Power**: N=10,000 (stratified) ensures power > 80% for r=0.1.
- **Causal Inference**: Observational study. Claims are strictly **associational**. No randomization.
- **Measurement Validity**: BERT perplexity is an *operational proxy* for uncertainty. Validity is checked (FR-009) against the BERT next-token entropy baseline. If invalid, study halts.
- **Collinearity**: Addressed via VIF check and Ridge Regression. Independent effects are not claimed for definitionally related features; joint contribution is reported.
- **Target Distribution**: The target is bounded and non-Gaussian. Non-parametric metrics (Spearman's rho, bootstrapping) are used to ensure validity.

## Compute Feasibility

- **CPU-First**: All steps designed for vCPU, sufficient RAM.
  - Feature extraction: Streaming BERT inference (batch size tuned for memory).
  - Training: XGBoost on CPU (efficient for tabular data).
  - CLIP Inference (Phase 0): Batched on CPU (may take time, but feasible for N=10k).
- **GPU Escape Hatch**: Not required. The methodology (XGBoost, BERT inference) is CPU-tractable.

## Data Availability & Risks

- **Risk**: 'pick-a-pic' dataset unavailability (404).
- **Mitigation**: The code will fail loudly with `DataSchemaError` as per FR-003. No synthetic data will be generated.
- **Risk**: Dataset size > 7GB.
- **Mitigation**: Use `streaming=True` and stratified sampling (N=10,000) to ensure power and fit within budget.
