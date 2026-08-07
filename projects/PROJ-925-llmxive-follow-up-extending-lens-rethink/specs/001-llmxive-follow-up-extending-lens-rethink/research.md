# Research: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Research Question
Can linguistic features (uncertainty, syntactic complexity, visual token density) extracted from text captions predict the "alignment deviation" (discrepancy between CLIP scores and human preferences) in text-to-image generation?

## Methodological Rigor & Statistical Plan

### 1. Dataset Strategy
**Target Dataset**: The specification requires the 'pick-a-pic' dataset, which contains paired CLIP scores and human preference ratings.
**Constraint Check**: The provided "Verified datasets" block for this project contains URLs for CLIP (jsonl), COCO, and BERT tokenized data, but **NO verified source for 'pick-a-pic'**.
**Resolution**:
- **Primary Plan**: Attempt to load a dataset with **pre-computed CLIP scores** (e.g., a derived subset of LAION or similar HuggingFace dataset) to avoid the infeasibility of downloading and processing 100k+ images on a 2-CPU runner.
- **Strict Fallback Policy**: If no verified dataset containing both `clip_score` and `human_rating` is available, the pipeline **MUST halt immediately** with a `DataSchemaError`. 
- **NO Synthetic Data**: The proposal to use 'COCO captions with synthetic human ratings' is **REJECTED**. Synthetic ratings cannot validate the 'alignment gap' between CLIP and *actual* human preference, rendering the research question unanswerable. This violates Principle II (Verified Accuracy) and Principle III (Data Hygiene).
- **Data Processing**:
  - **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to process the dataset in chunks.
  - **Filtering**: Exclude samples where `human_rating` is missing (NaN) as per FR-003.
  - **Normalization**: Normalize `clip_score` and `human_rating` to [0, 1] before calculating deviation.

### 2. Feature Extraction (Predictors)
- **Linguistic Uncertainty Proxy**: Calculated as `ln(perplexity)` using a pre-trained BERT model (e.g., `bert-base-uncased`).
  - *Constraint*: Must complete within 5s/caption on CPU. If a batch takes longer, the batch size is reduced.
  - **Construct Validity**: We acknowledge that BERT perplexity measures token prediction probability, not direct semantic entropy. However, in the context of LLM-generated captions, higher perplexity is operationally defined as a proxy for "linguistic uncertainty" or "ambiguity" that correlates with model instability. This is a computable indicator, not a direct measure of the theoretical construct, but is sufficient for the correlational study design.
- **Syntactic Complexity**: Maximum depth of the dependency parse tree using `spaCy`.
- **Noun-Phrase Density**: Ratio of noun phrases to total tokens.
- **Visual Token Density (FR-007 Proxy)**: Ratio of noun phrases to total tokens. This serves as a text-derived proxy for "image complexity" (more complex descriptions often imply more complex images) without violating Principle VI (Text-Only).
- **Controls**: Caption length (token count).

### 3. Target Variable (Outcome)
- **Deviation Score**: $| \text{Normalized}(\text{CLIP\_Score}) - \text{Normalized}(\text{Human\_Rating}) |$.
- **Handling Missing Data**: Samples with missing `human_rating` are dropped, not imputed (FR-003).
- **Zero Variance Check**: If the target column has zero variance, the pipeline halts with `ValueError("Target not learnable")`.
- **Circularity Resolution**: The target variable is a function of the text (via CLIP). The study reframes the hypothesis: we are not predicting "error" in an absolute sense, but "text-driven metric instability". The analysis identifies which linguistic properties cause the CLIP metric to deviate from human consensus. A **Text Permutation Null Model** is included to validate that the observed importance is due to specific text content, not just length/structure.

### 4. Modeling & Statistical Tests
- **Model**: XGBoost Regressor (CPU-only).
- **Hypothesis**: Linguistic complexity positively correlates with alignment deviation.
- **Significance Testing (FR-006)**:
  - **Feature Permutation Importance**: To assess the significance of specific features, we perform a **permutation test on the feature columns (X)**, not the target (Y). For each feature $X_j$, we shuffle its values $N=1000$ times while keeping the target $Y$ fixed. We calculate the drop in model performance (e.g., MSE) for each shuffle to generate a null distribution for that feature's importance. This directly tests if $X_j$ contributes to prediction, satisfying FR-006.
  - **Target Permutation (Global Model Check)**: Permuting the target $Y$ is performed separately to verify that the model is not predicting random noise (global significance), but this is distinct from feature-level testing.
  - **Text Permutation Null**: Permute text captions relative to image/human rating pairs to break the text-image dependency.
  - **FDR Control**: Benjamini-Hochberg procedure applied to p-values at $\alpha = 0.05$.
  - **Reproducibility**: Random seed pinned (e.g., 42) and logged.
- **Sensitivity Analysis (FR-008)**:
  - **Noise Injection**: Inject Gaussian noise ($\sigma \in \{0.01, 0.05, 0.1\}$) into human ratings.
  - **Re-training**: Re-fit the XGBoost model for each noise level.
  - **Aggregation**: Compute the **Spearman rank correlation** of the feature importance vectors across the noise levels to assess stability.
- **Multiple Comparison Correction**: Applied via Benjamini-Hochberg as part of the feature permutation test.

### 5. Compute Feasibility & Profiling
- **CPU-First**: All tasks run on CPU.
  - `transformers` (BERT): Use `device="cpu"`, `torch.set_num_threads(1)`.
  - `xgboost`: Native CPU support.
- **Memory Management**:
  - Stream dataset to avoid loading full 100k+ rows into RAM.
  - Process features in batches (e.g., 500 captions/batch).
- **Profiling Tools (SC-002, SC-003)**:
  - **Memory**: Use Python's `tracemalloc` module in `main.py` to log peak RSS to `results/memory_profile.json`.
  - **Time**: Use Python's `time` module in `main.py` to log wall-clock duration to `results/timing_profile.json`.
- **GPU Escape Hatch**: Not applicable. The methodology is fully CPU-tractable.

### 6. Limitations & Assumptions
- **Observational Nature**: Claims are associational, not causal.
- **Measurement Validity**: BERT perplexity is used as a proxy for semantic uncertainty, acknowledging it differs from strict semantic entropy.
- **Target Noise**: Human ratings are treated as ground truth despite known noise; robustness is assessed via sensitivity analysis.
- **Data Constraints**: If pre-computed dataset is unavailable, the study **halts** rather than using unverified data.

## Decision/Rationale
- **Why XGBoost?**: It is the most efficient tree-based model for tabular data on CPU, offering high performance with low memory overhead compared to deep learning models for this specific regression task.
- **Why Streaming?**: The dataset may exceed the RAM limit of the CI runner. Streaming ensures the full dataset can be processed or a representative sample drawn without OOM errors.
- **Why Feature Permutation?**: Standard p-values from XGBoost are not directly available; permuting features (X) provides a robust, non-parametric method to assess feature significance and control for false discoveries, distinguishing it from target permutation (Y) which tests global model significance.
- **Why Visual Token Density?**: It satisfies FR-007 (control for image complexity) using only text-derived features, maintaining compliance with Principle VI (Linguistic Feature Isolation).