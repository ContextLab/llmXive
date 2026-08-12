# Research: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Problem Statement

The core research question is whether the discriminative signal captured by DelTA Coefficients (derived from dynamic gradient backpropagation) is encoded in the *static semantics* of the input prompt, or if it is an *emergent* property of the model's internal state processing. Specifically, we test if **input-level syntax and semantics** (represented by a distinct external model's embeddings) are predictive of **internal gradient signals** (represented by the Oracle model). If static features (n-grams, POS, semantic similarity from a *distinct* model) can predict DelTA Coefficients with significant accuracy, the signal is partially pre-determined by input structure. If not, the signal is emergent (or non-linearly dependent on the input in a way the static features cannot capture).

## Dataset Strategy

### Verified Datasets
The study relies exclusively on the **GSM8K** dataset, a collection of grade school math word problems.
*   **Source**: HuggingFace `openai/gsm8k`.
*   **Verified URLs**:
    *   `https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet`
    *   (Alternative mirrors: `whynlp/gsm8k-aug`, `issai/GSM8k_Kazakh_Russian` - primary is `openai/gsm8k`).
*   **Selection Rationale**: GSM8K provides structured reasoning traces with verified correctness, essential for the DelTA algorithm which requires a known ground truth to compute gradients.
*   **Access Method**: Programmatic download via `datasets.load_dataset("openai/gsm8k", "main")`. This avoids interactive portals and ensures CI reproducibility.
*   **Data Filtering**: Only examples with `correct=True` (or equivalent verified label) are retained. The pipeline asserts a minimum of 500 examples to ensure statistical power for the regression.

### Data Constraints
*   **Size**: The full GSM8K test set is small (<1MB), but the processing (tokenization + feature extraction) is the bottleneck.
*   **Feasibility**: The dataset fits easily within the available RAM and disk limits. The primary constraint is the compute time for the Oracle step.

## Methodological Approach

### 1. Oracle Generation (Ground Truth)
*   **Algorithm**: DelTA (Discriminative Token Credit Assignment).
*   **Model**: Llama-3-8B (Primary) -> Llama-3-1B (Fallback).
*   **Mechanism**: Forward pass followed by backpropagation to compute the gradient of the loss with respect to each token's contribution.
*   **Constraint**: The output is a scalar coefficient per token.
*   **Validation**: Variance of coefficients must be > 1e-9. If not, the data is discarded (indicates a failure to capture signal).
*   **Compute Path**:
    *   Attempt 8B with 4-bit quantization on Kaggle GPU.
    *   If OOM/Timeout, switch to 1B model (full precision or 8-bit) to ensure real gradients are computed.
    *   Quantization strategy is fixed; any impact on gradient magnitudes will be reported as a limitation.

### 2. Static Feature Extraction (Predictors)
*   **Principle**: Strict Independence. No hidden states from the Llama-3 Oracle are used.
*   **Feature Independence Protocol**:
    *   **FR-003 (Amended)**: While the original spec mentioned "Llama-3-8B last-layer embedding space", using the *same* model for features and oracle creates a tautological correlation (Circular Validation). To satisfy the **Static-Input Independence** principle (Constitution Principle VI), we use a **distinct, frozen external model** to approximate semantic similarity. This tests if the *input semantics* (as seen by a general model) predict the *internal gradients* (as seen by the specific Oracle).
    *   **External Model**: `sentence-transformers/all-MiniLM-L6-v2`.
    *   **Citation**: `https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2`.
*   **Features**:
    *   **N-grams**: Frequency of local token sequences (1-gram to 3-gram) using a **sliding window of size 3 centered on the target token**, normalized by window size.
    *   **POS**: Part-of-speech tags derived from a standard NLP tool (e.g., SpaCy or NLTK) on the raw text, assigned per token.
    *   **Semantic Similarity**: Cosine similarity between the token's context and a reference set of GSM8K solution patterns. This reference set is embedded using the **external MiniLM model** to avoid circularity with the Llama-3-8B weights.
*   **Handling OOV**: Tokens not in the reference vocabulary are assigned a zero vector or a default "unknown" embedding.

### 3. Prediction Model
*   **Architecture**: 2-layer Multi-Layer Perceptron (MLP) with ReLU activation.
*   **Input**: Concatenation of n-gram counts, POS one-hot encodings, and semantic similarity scores.
*   **Output**: Scalar prediction of the DelTA Coefficient.
*   **Training**: Standard MSE loss. Optimizer: Adam.
*   **Hardware**: CPU-only (PyTorch CPU).

### 4. Evaluation & Statistics
*   **Metric**: Spearman Rank Correlation ($\rho$). This is chosen because the absolute scale of DelTA coefficients may vary, but the *relative* ranking of token importance is the signal of interest.
*   **Baselines**:
    *   **Random**: Correlation with noise $N(0,1)$.
    *   **Uniform**: Correlation with a constant vector.
*   **Significance**: **Cluster-Robust Permutation Test** (1000 shuffles of entire *examples*, not individual tokens) to generate a null distribution. $p < 0.05$ indicates significance. This accounts for the high correlation between tokens within a single example and prevents inflation of the effective sample size.
*   **Interpretation**:
    *   If $\rho > 0.1$ and significant: **"Signal is Predictable"** (Static features encode discriminative signal).
    *   If $\rho \approx 0$ and feature importance is low: **"Features are poor proxies"**.
    *   If $\rho \approx 0$ but feature importance is high: **"Signal is emergent (or non-linear)"** (Static features have relevance but cannot predict the linear relationship, suggesting the signal is emergent in a complex way).
*   **Feature Importance**: **Permutation Importance** is chosen over SHAP due to CPU constraints and the need for a lightweight, interpretable metric sufficient to distinguish between 'signal is emergent' and 'features are poor proxies'.

## Statistical Rigor & Assumptions

*   **Multiple Comparisons**: Not applicable (single primary hypothesis: correlation > 0).
*   **Power Analysis**: A sample of examples with ~20 tokens each yields a substantial volume of data points. However, due to intra-example correlation, the effective sample size is lower. The cluster-robust permutation test corrects for this.
*   **Causal Claims**: The study design is **observational**. We cannot claim that static features *cause* the DelTA signal. We can only claim they are *predictive* of it. All findings are framed as associational (FR-007).
*   **Collinearity**: N-gram counts and semantic similarity may be correlated. The MLP will handle this via regularization (L2), but feature importance analysis (Permutation Importance) will be used to disentangle contributions.
*   **Measurement Validity**: The DelTA algorithm is the ground truth by definition of the study. The static features are standard NLP metrics with established validity, computed via a distinct model to ensure independence.

## Compute Feasibility Decision

*   **Oracle Step**: Running Llama backprop on CPU is likely to exceed the 6-hour limit or 7GB RAM.
    *   *Plan*: Attempt on CPU first. If it fails (OOM or Timeout), the execution stage will auto-offload to a Kaggle GPU (16GB VRAM).
    *   *Critical Constraint*: Limited VRAM capacity is insufficient for 8B backprop. If the 8B run fails on Kaggle, the pipeline **MUST** switch to **Llama-3-1B** to ensure real gradients are computed. This is a necessary compromise to avoid fabricating results.
*   **Feature Extraction & Training**: These are explicitly designed for CPU. The MLP is tiny (<1MB). Feature extraction is $O(N \times L)$ and fits in memory.
*   **Conclusion**: The plan is feasible. The "Model Fallback" ensures the Oracle step completes with real data, even if the model size is reduced.

## Limitations

*   **Model Size**: If 8B fails, results are reported for 1B. The hypothesis is tested on "small-to-medium LLMs" rather than strictly 8B.
*   **Feature Set**: The static features are limited to n-grams, POS, and simple semantic similarity. More complex syntactic parsers or external knowledge graphs were excluded to maintain the "static" constraint and CPU feasibility.
*   **Dataset Bias**: GSM8K is a specific domain (math word problems). Results may not generalize to open-ended generation.
*   **External Model**: Using MiniLM for features means the semantic space is approximated, not identical to the oracle's, which is a deliberate choice to ensure independence.
*   **Quantization**: If the 8B run requires quantization, the gradient magnitudes may differ from full precision. This limitation will be reported.
