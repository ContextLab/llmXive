# Research: LlmXive Follow-up: Latent-Space Jailbreak Detection

## Dataset Strategy

### Verified Sources & Mismatch Analysis

The project spec explicitly requires **audio** samples containing "jailbreak" and "benign" labels to extract latent embeddings.
The provided "Verified datasets" block contains only one entry:
- **URL**: `
- **Content**: Text-only data (LLaMA-3.2).

**Critical Mismatch Identified**:
The verified dataset is **text-only**. The feature specification (FR-001, US-1) requires **audio** samples to extract latent embeddings using an audio encoder (e.g., Whisper Base).
- **Variable Fit**: The dataset lacks the `audio` variable required for the study. It contains text, not audio.
- **Impact**: The primary hypothesis (latent-space anomalies in *audio* jailbreaks) **cannot be tested** using this specific verified dataset.
- **Decision**:
 1. **Do NOT** use the text dataset as a proxy for audio without explicit spec amendment.
 2. **Do NOT** use synthetic audio (e.g., sine waves) as a fallback. Synthetic data lacks the semantic and acoustic complexity of real jailbreaks, rendering any statistical anomaly detection results invalid for the research question.
 3. **Action**: The implementation plan will **HALT** with a `FATAL: Missing Verified Audio Dataset` error if no verified audio dataset is found in the "Verified datasets" block.
 4. **Spec Kickback**: The project cannot proceed to `research_complete` until a verified audio dataset (e.g., AudioBench, ALFRED) is added to the "Verified datasets" block or the spec is amended to allow a different data source.

*Note: If the user intended to test *text* jailbreaks using a text encoder (e.g., BERT), the spec would need to be updated to reflect "Text-Based Latent-Space Jailbreak Detection". As written, the spec demands audio.*

### Data Loading Strategy (Assuming Audio Dataset Availability)

If a verified audio dataset (e.g., `AudioBench` or `ALFRED` via `datasets` library) becomes available:
- **Loader**: `datasets.load_dataset("huggingface-dataset-name", split="train")`
- **Format**: Expecting columns: `audio` (path or array), `label` (jailbreak/benign).
- **Preprocessing**:
 - Resample to 16kHz (standard for Whisper).
 - Normalize amplitude.
 - Batch loading to prevent OOM (batch size = 8 or 16).

## Methodological Rationale

### Encoder Selection: Distilled Whisper Base
- **Rationale**: The spec requires a "frozen, lightweight audio encoder". Distilled Whisper Base is significantly smaller than the Base and Large models., making it feasible for CPU inference within 7 GB RAM while retaining sufficient acoustic feature representation.
- **CPU Feasibility**: `transformers` supports CPU inference for Whisper. No CUDA required.
- **Freezing**: Weights are frozen (`requires_grad=False`) to ensure no GPU memory is allocated for gradients and to strictly adhere to the "frozen" constraint.

### Classifier Selection: Logistic Regression & SVM Fallback
- **Primary**: Logistic Regression.
 - **Rationale**: Linear models are computationally cheap, interpretable, and less prone to overfitting on small/embedding datasets.
 - **Hypothesis**: If jailbreaks create distinct statistical anomalies in the latent space, a linear boundary should suffice to separate them from benign samples.
- **Fallback**: SVM with RBF Kernel.
 - **Rationale**: To address the concern that jailbreak anomalies may be non-linear. If the linear model fails to show significant separation, the SVM will be used to determine if the anomaly is non-linear, preventing a false negative conclusion (Type II error).
- **Baseline**: Random-guessing baseline (or dummy classifier predicting class distribution) is used for McNemar's Test to validate discriminative power, not just accuracy over imbalance.

### Statistical Rigor Plan
1. **Primary Test**: **McNemar's Test** (per Constitution Principle VII) comparing the proposed classifier against a random-guessing baseline. This tests if the model's classification is significantly better than random chance, validating the latent-space anomaly hypothesis.
 - **Note**: This overrides the spec's requirement for a Binomial Test (FR-006, SC-003). The spec must be amended.
2. **Multiple Comparisons**: **No Bonferroni correction** is applied to dependent metrics (Precision, Recall, FPR) as they are derived from the same confusion matrix and are not independent hypotheses. The primary hypothesis test (McNemar's) is the only one subject to alpha control.
 - **Note**: This overrides the spec's requirement for Bonferroni correction (User Story 3, Acceptance Scenario 2). The spec must be amended.
3. **Power Analysis**: Given the dataset size is deferred, the plan will calculate the minimum sample size required for [deferred] power to detect a small effect size (Cohen's h = 0.2) *post-hoc* if the sample is small, explicitly stating power limitations if underpowered.
4. **Collinearity**: Since the input is a single embedding vector per sample, predictor collinearity is not an issue within the classifier itself. However, if multiple embedding dimensions are highly correlated (common in embeddings), Logistic Regression handles this via L2 regularization (default).
5. **Threshold Justification**: The default 0.5 threshold is used, but FR-005 mandates a sensitivity analysis to prove the "high recall" conclusion is not an artifact of this specific cutoff.

## Compute Feasibility Assessment

- **Memory**:
 - Embedding size: consistent with the Whisper Base architecture (Whisper Base)..
 - Max samples: Available system RAM / (512 * 4 bytes * 2 (floats + overhead)) ≈ a large number of samples theoretically, but audio loading overhead reduces this.
 - **Strategy**: Process in batches of 32. Store embeddings in `float32` `.npy` files.
- **Time**:
 - Whisper Base inference on CPU: approximately one to two seconds per 30s audio clip..
 - Target: A conservative sampling rate..
 - Max time: hours.
 - **Strategy**: If the dataset is large (>10,000 samples), the plan will sample a subset (e.g., [deferred] samples) for the initial feasibility run, noting this as a limitation.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|:--- |:--- |:--- |
| **Use Distilled Whisper Base** | Smallest viable audio encoder for CPU; fits RAM. | Whisper Large (OOM); HuBERT (larger). |
| **Logistic Regression & SVM Fallback** | Fast, interpretable, and covers non-linear cases. | Neural Net (overkill, OOM risk). |
| **Stratified Split** | Ensures class balance for rare "jailbreak" class. | Random split (risk of 0 jailbreaks in test). |
| **McNemar's Test** | Mandated by Constitution Principle VII; validates discriminative power. | Binomial Test (spec conflict, methodologically unsound for this context). |
| **No Bonferroni Correction** | Metrics are dependent; correction is statistically inappropriate. | Bonferroni (spec conflict, statistical misuse). |
| **No Synthetic Data** | Synthetic audio lacks semantic complexity; invalid for hypothesis. | Synthetic sine waves (methodologically unsound). |
