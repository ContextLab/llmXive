# Research: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Research Question

Which linguistic features of text captions (BERT Perplexity, syntactic complexity, noun-phrase density) are statistically significant predictors of the "human-model disagreement" between CLIP scores and human preference ratings in text-to-image generation?

## Dataset Strategy

The project relies on open, programmatically accessible datasets verified for direct download on CI runners.

### Verified Datasets

| Dataset Name | Verified URL | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **Pick-a-Pic** | `https://huggingface.co/datasets/pick-a-pic/pick-a-pic` | Source of raw captions, image IDs, and human preference scores (`preference_score`). | Primary source for human ratings. Must verify presence of `preference_score` column. |
| **COCO Validation** | `https://huggingface.co/datasets/vikhyatk/coco-val/resolve/main/data/validation-00000-of-00001.parquet` | Hold-out test set for final evaluation (if Pick-a-Pic lacks sufficient test data). | Used to ensure no data leakage. |

**Critical Data Availability Note**: The study requires a "Human Rating" to compute the disagreement score. The verified dataset **Pick-a-Pic** is the primary candidate and contains the `preference_score` column. If this column is absent, the project **cannot** proceed with the current spec. The `loader.py` script will raise a `ValueError` ("Dataset missing required 'preference_score' column"), preventing fabrication.

### Data Processing Strategy

1. **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to iterate over shards without loading the full dataset into RAM.
2. **Sampling**: A stratified random sample of **[deferred] rows** will be drawn to ensure the feature extraction phase completes within the 6-hour CI limit. The random seed for sampling will be logged.
3. **Target Calculation**: The target variable is the **raw absolute difference** $Y = | \text{CLIP\_Score} - \text{Human\_Rating} |$. No normalization is applied to preserve the magnitude of the deviation.

## Methodological Rigor

### Statistical Approach

1. **Target Variable**: $Y = | \text{CLIP\_Score} - \text{Human\_Rating} |$.
   - **Raw Difference**: The absolute difference is calculated on the raw scale. This avoids the mathematical invalidity of subtracting two independently normalized distributions.
   - **Handling Missing Data**: Samples with `NaN` in `human_rating` are **excluded** (not imputed) to prevent bias.
   - **Zero Variance Check**: If the calculated $Y$ has zero variance (all deviations are 0), the training script halts with `ValueError("Target not learnable")`.
   - **Framing**: The model predicts "human-model disagreement" (a composite of model error and human noise), not pure "alignment gap", acknowledging the limitation.

2. **Predictors ($X$)**:
   - **BERT Perplexity**: $\ln(\text{Perplexity})$ from a pre-trained DistilBERT model (CPU inference). *Note: This is a proxy for linguistic complexity/uncertainty, distinct from the strict semantic entropy definition (Farquhar et al., 2024).*
   - **Syntactic Complexity**: Max depth of the dependency parse tree (spaCy).
   - **Noun-Phrase Density**: Count of noun phrases / total tokens.
   - **Token Diversity**: Type-Token Ratio.
   - **Confounders**: Caption length and image complexity (if available) are included as covariates to isolate linguistic effects.

3. **Model**: XGBoost Regressor (CPU-only, `tree_method='hist'`).
   - **Confounding Control**: Caption length and image complexity (if available) will be included as covariates in the model to isolate the effect of linguistic features.
   - **Multiple Comparison Correction**: Benjamini-Hochberg procedure applied to p-values from permutation importance tests (FR-006).
   - **Significance Threshold**: FDR < 0.05.
   - **Permutation Iterations**: **1,000 iterations** explicitly mandated for the null distribution.

4. **Stability Loop (SC-005)**:
   - The model will be trained and evaluated over **5 distinct random seeds**: `0, 42, 123, 2024, 9999`.
   - For each seed:
     1. Re-sample the data (stratified random sample).
     2. Retrain the model.
     3. Calculate feature importance rankings.
   - Aggregate results: Compute mean rank and standard deviation of ranks across the 5 seeds.
   - Output: `results/stability_metrics.json`.

### Causal Inference & Assumptions

- **Observational Nature**: This study is purely observational. Claims will be framed as "associational" (e.g., "Higher syntactic complexity is associated with higher disagreement") rather than causal.
- **Measurement Validity**: BERT Perplexity is operationalized as $\ln(\text{Perplexity})$. This is an approximation of the strict "semantic entropy" definition but is the only computable proxy available within the CPU constraints.
- **Collinearity**: Predictors like "Token Diversity" and "Noun-Phrase Density" may be correlated. The plan acknowledges this and uses permutation importance (which accounts for correlation) rather than raw coefficient magnitude.
- **Human Noise**: The target variable $Y$ conflates CLIP model error and human rating noise. The research question is reframed to "predicting human-model disagreement" rather than "alignment gap" to acknowledge this limitation.

## Compute Feasibility

### CPU-First Strategy

- **Feature Extraction**: DistilBERT inference on CPU is fast. Estimated time: [deferred] for 50k samples, but limited to 10k samples to ensure < 6h runtime.
- **Model Training**: XGBoost on 2 cores is fast (< 10 minutes for 10k rows).
- **Memory**: Streaming ensures peak RAM usage < 4 GB.
- **GPU Escape Hatch**: Not required. The entire pipeline is designed to run on CPU.

### Decision/Rationale

The choice of XGBoost and DistilBERT (CPU) is driven by the **CPU-Tractability Constraint** (Constitution Principle VII). No GPU is needed for this specific research question (predicting deviation from text features). Using a GPU would violate the "democratize access" goal and is unnecessary for the method.

## Risk Mitigation

| Risk | Mitigation |
| :--- | :--- |
| **Dataset lacks Human Ratings** | `loader.py` checks for the `preference_score` column immediately. If missing, the pipeline exits with a clear error message. No synthetic data is generated. |
| **DistilBERT Inference too slow** | Limit sample size to 10k to ensure < 6h runtime. |
| **Zero Variance in Target** | `preprocess.py` checks variance before training. If zero, raises `ValueError`. |
| **Feature Extraction Fails** | `features.py` wraps extraction in `try/except`. Failed rows are logged and excluded, not imputed. |
| **Confounding Variables** | Include caption length and image complexity as covariates in the XGBoost model to isolate linguistic effects. |