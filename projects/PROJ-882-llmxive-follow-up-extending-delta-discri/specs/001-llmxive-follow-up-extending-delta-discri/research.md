# Research: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Research Question
Can static input features (n-grams, POS tags, semantic similarity) recover the discriminative token credit assignment (DelTA) signal?
-   **Hypothesis**: If the signal is "emergent" (intrinsic to the model's dynamic internal state), static features will fail to predict it, even if the signal is theoretically predictable from better features (hidden states).
-   **Null Hypothesis**: If the signal is predictable from static features, the static model will achieve significant correlation.
-   **Control**: An "Upper Bound Oracle" model using hidden states will determine the theoretical ceiling of predictability, distinguishing between "emergent signal" (Static Low, Upper Bound High) and "poor proxies" (Static Low, Upper Bound Low).

## Dataset Strategy

| Dataset | Source / URL | Usage | Access Method |
| :--- | :--- | :--- | :--- |
| **GSM8K** | `https://huggingface.co/datasets/openai/gsm8k` | Primary data source for prompts and verified solutions. Used for Oracle generation and feature extraction. | `datasets.load_dataset("openai/gsm8k", "main", split="train")` |
| **MiniLM Embeddings** | `https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2` | Pre-trained model for computing semantic similarity of tokens to reference reasoning patterns. | `sentence-transformers` library (CPU) |

**Data Verification**:
- The GSM8K dataset is verified to contain [deferred] training examples with `question` and `answer` fields.
-   Filtering logic: Only examples with verified correct solutions (based on the provided answer string matching the model's generation or ground truth) will be used.
-   Stratification: Subsets will be stratified by solution length to ensure representation of short and long reasoning chains.

**Data Availability & Feasibility**:
-   **GSM8K**: Publicly available via HuggingFace. No credentials required. Downloadable via `datasets` library.
-   **MiniLM**: Publicly available via HuggingFace. No credentials required.
-   **Feasibility**: The dataset size (~k examples) fits easily within the available disk and RAM limits. The subset for the Oracle step is small enough for gradient computation on a Kaggle GPU.

## Methodological Rigor

### 1. Oracle Generation (Ground Truth)
-   **Method**: Execute the DelTA algorithm on Llama-3-1B.
-   **Constraint**: Must run on GPU if CPU fails (auto-offload to Kaggle).
-   **Validation**: Compute variance of coefficients. If `variance <= 1e-9`, abort with `ERR_TRIVIAL_TARGET`.
-   **Sample Size**: Stratified sample of 500 examples (seed=42). If < 10 valid examples remain after filtering, fail.

### 2. Feature Extraction (Static Input)
-   **Features**:
    -   **N-grams**: Local n-gram statistics (n=1 to 3) mapped to token positions via sliding window (±2).
    -   **POS Tags**: Part-of-speech tags from `spacy`.
    -   **Semantic Similarity**: Cosine similarity between token embeddings (via MiniLM) and a reference set of GSM8K solution patterns.
-   **Independence**: **Strictly forbidden** to use hidden states from the Llama-3-1B oracle for the *Static Model*. Only external, static features allowed.
-   **Handling Missing Data**: Tokens with OOV in MiniLM will be assigned a zero vector or default embedding.

### 3. Upper Bound Oracle (Control)
-   **Method**: Train a regression model using the **hidden states** of the Llama-3-1B oracle model as input features.
-   **Purpose**: To establish the theoretical maximum predictability of the DelTA signal. If the Upper Bound model also fails, the signal is not recoverable from *any* linear combination of features (or is noise). If it succeeds, the signal is recoverable but not from static features.
-   **Constraint**: This step uses the oracle's internal states, so it is not a "static" approximation, but a necessary control to interpret the Static Model's results.

### 4. Model Training
-   **Architecture**: Multi-layer perceptron (MLP) with ReLU activation and a hidden layer of moderate capacity. (identical for Static and Upper Bound models).
-   **Optimizer**: Adam (default).
-   **Loss**: Mean Squared Error (MSE) between predicted and true DelTA coefficients.
-   **Hardware**: CPU-only (scikit-learn / PyTorch CPU).
-   **Regularization**: L2 regularization to prevent overfitting on small subsets.

### 5. Evaluation & Significance
-   **Metrics**:
    -   **Spearman Rank Correlation**: Primary metric.
    -   **Kendall's Tau**: Secondary metric (robust to ties/skew and sign issues in gradient attribution).
    -   **95% Confidence Intervals**: Calculated via Bootstrap (iterations) to account for sample size limitations.
-   **Baselines**:
    -   Random Baseline: $N(0,1)$ weights (seed=42).
    -   Uniform Baseline: All weights = 1.
-   **Permutation Test**: Shuffle **entire GSM8K examples** (not individual tokens) 1000 times. Compute p-value.
-   **Classification Logic**:
    -   **Emergent Signal**: Static Model (Low Correlation, p > 0.05) AND Upper Bound Model (High Correlation, p < 0.05).
    -   **Poor Proxies**: Static Model (Low Correlation) AND Upper Bound Model (Low Correlation).
    -   **Significant**: Static Model (High Correlation).
-   **Causal Framing**: All results must be reported as **associational**. The study design does not support causal claims.

### 6. Statistical Considerations
-   **Multiple Comparisons**: Not applicable (single primary hypothesis: correlation > 0).
-   **Power Analysis**: Acknowledged limitation: Sample size (500) may limit power to detect weak correlations. The use of 95% CIs mitigates this by showing the range of plausible values.
-   **Collinearity**: N-gram and POS features may be correlated. The MLP will handle this, but feature importance analysis will be interpreted with caution.
-   **Domain Mismatch**: The plan explicitly acknowledges that DelTA is a property of the Llama-3 latent space, while MiniLM is a frozen semantic space. The Upper Bound Oracle controls for this by testing predictability within the correct latent space.

## Compute Feasibility Decision

-   **Oracle Step**: **GPU Required**. Gradient backpropagation through 1B parameters for 500 examples is too heavy for 2-core CPU within 6 hours.
    -   *Plan*: Use `device="cuda"` with `load_in_8bit` if available, or standard FP16 on Kaggle GPU. Auto-offload logic handles CPU failure.
-   **Upper Bound Oracle**: **CPU Feasible**. Inference (no backprop) is fast on CPU.
-   **Feature Extraction**: **CPU Feasible**. MiniLM inference is fast on CPU.
-   **Training**: **CPU Feasible**. 2-layer MLP on 500 examples is trivial for CPU.
-   **Evaluation**: **CPU Feasible**. Permutation test and Bootstrap are computationally light.

**Decision**: The pipeline will attempt CPU first. If the Oracle step fails or times out, the runner will automatically offload to Kaggle GPU. All other steps remain CPU-bound.

## Constitution Alignment

-   **Principle VI (Static-Input Independence)**: Explicitly enforced by separating the Oracle model (Llama-3-1B) from the Feature Extractor (MiniLM) for the *Static Model*. The *Upper Bound Oracle* is a separate control experiment that uses hidden states but is not part of the "static approximation" claim.
-   **Principle VII (Oracle Ground-Truth)**: Enforced by variance check and real-time backpropagation.
-   **Principle I (Reproducibility)**: All seeds pinned to a fixed count. Dataset version pinned to `main` split.