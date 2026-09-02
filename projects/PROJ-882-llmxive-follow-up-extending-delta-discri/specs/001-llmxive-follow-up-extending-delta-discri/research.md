# Research: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Executive Summary

This research investigates whether the discriminative signal captured by the DelTA algorithm (dynamic token credit assignment) is encoded in the static input semantics of math word problems (GSM8K). The hypothesis is that if the signal is purely emergent from the model's internal dynamics, a static predictor (MLP) using only n-grams, POS tags, and semantic similarity (via MiniLM) will fail to predict the DelTA coefficients. Conversely, if static features show significant correlation, the signal may be partially predictable from input structure.

**Critical Note on Dataset**: The original spec referenced "MathQA" for semantic similarity. However, MathQA is a multiple-choice dataset and lacks verified, direct URLs for the specific "solution trace" format required for this study. Furthermore, its domain (QA) differs from GSM8K (step-by-step reasoning). **This plan replaces MathQA with OpenMathInstruct-1**, a verified HuggingFace dataset containing step-by-step reasoning traces. This change is necessary to satisfy the "Static-Input Independence" principle and ensure domain relevance. **Action Required**: The spec must be amended to reflect this change.

## Dataset Strategy

We utilize the **GSM8K** dataset for the primary analysis and the **OpenMathInstruct-1** dataset as a reference for semantic similarity patterns.

### Verified Datasets

| Dataset | Purpose | Verified Source URL | Access Method |
|:--- |:--- |:--- |:--- |
| **GSM8K** | Primary benchmark for DelTA coefficient generation. Filtered for verified correct solutions. | ` (and train split via `datasets.load_dataset('openai/gsm8k')`) | `datasets.load_dataset("openai/gsm8k", "main")` |
| **OpenMathInstruct-1** | Reference set for "known reasoning patterns" to compute semantic similarity via MiniLM. | `https://huggingface.co/datasets/TIGER-Lab/OpenMathInstruct-1` | `datasets.load_dataset("TIGER-Lab/OpenMathInstruct-1")` |

*Note: The plan explicitly rejects using GSM8K as a self-referential fallback for semantic similarity to avoid circularity and violate Constitution Principle VI.*

### Data Filtering & Sampling
- **Source**: GSM8K (`train` split preferred for training, `test` for evaluation if available, or stratified split of `train`).
- **Filter**: `correctness == True` (or equivalent label indicating a verified solution).
- **Sample Size**: Target a substantial corpus of examples. If < 10 valid examples found, abort with `ERR_INSUFFICIENT_DATA`.
- **Stratification**: Stratified by solution length (character count or token count) to ensure diversity in problem complexity.
- **Seed**: `42` for all sampling operations.

## Methodology

### Phase 1: Oracle Ground-Truth Generation (DelTA Coefficients)
1. **Model**: `meta-llama/Llama-3-8B` (or `meta-llama/Meta-Llama-3-8B-Instruct`).
2. **Task**: Compute **Discriminative** DelTA Coefficient:
 - Forward pass on correct solution to get $Loss_{correct}$.
 - Perturb target token (mask/replace) and re-compute loss to get $Loss_{perturbed}$.
 - $DelTA = \nabla_{token} (Loss_{correct} - Loss_{perturbed})$.
3. **Compute Strategy**:
 - **CPU**: Attempt first. If memory/time limits exceeded, detect CUDA requirement and trigger Kaggle offload.
 - **GPU (Kaggle)**: Load model with `device="cuda"` and apply quantization if necessary to fit in 16GB VRAM.
4. **Validation**:
 - Check variance of output coefficients. If `variance <= 1e-9`, abort with `ERR_TRIVIAL_TARGET`.
 - Ensure no NaNs or Infs.

### Phase 2: Static Feature Extraction
1. **Features**:
 - **N-gram Statistics**: Count of unigrams, bigrams, trigrams in the prompt.
 - **POS Tags**: Part-of-speech tags (e.g., noun, verb, number) mapped to token positions using a sliding window (±2).
 - **Semantic Similarity**: Cosine similarity between the prompt (or token context) and a reference set of **OpenMathInstruct-1** solution traces using `sentence-transformers/all-MiniLM-L6-v2`.
2. **Independence**: **Strictly NO** use of Llama-3-8B hidden states or embeddings. Only external, static features.
3. **Handling Missing Data**: Tokens with OOV (out-of-vocabulary) in the feature extractor are assigned default vectors (zeros) or filtered.

### Phase 3: Model Training & Evaluation
1. **Model**: 2-layer MLP (Input -> 128 -> 128 -> 1) with ReLU activation.
2. **Training**: CPU-only. Optimizer: Adam. Loss: MSE or MAE.
3. **Evaluation**:
 - **Primary Metric**: Spearman rank correlation between predicted and true coefficients. **Aggregation**: Correlation computed at the example level (average of token correlations per example) to account for clustering.
 - **Baselines**: Random baseline (N(0,1)), Uniform baseline.
 - **Significance**: **Example-level Permutation Test**: Shuffle entire example IDs (preserving token structure within examples) to generate null distribution. P-value calculation.
 - **Feature Importance**: Permutation Importance to distinguish "signal is emergent" vs "features are poor proxies".

## Statistical Rigor & Assumptions

### Multiple Comparisons
- Only one primary hypothesis test (Spearman correlation) is performed per run. No family-wise error correction is strictly required for a single metric, but the permutation test inherently controls for chance.

### Sample Size & Power
- **Limitation**: With ~500 examples and token-level clustering, the effective sample size is lower. The example-level permutation test accounts for non-i.i.d. structure. Power is acknowledged as limited; a null result may be due to low power or true lack of signal.
- **Justification**: A feasible subset size is selected to fit the compute budget (4h limit) while providing a reasonable distribution of problem types.

### Causal Inference
- **Observational Design**: The study is observational. We correlate static input features with dynamic output coefficients. We **cannot** claim that static features *cause* the DelTA signal. Claims are framed as "associational" or "predictive".
- **Collinearity**: N-gram counts and semantic similarity may be correlated. The MLP will learn the combined effect, but feature importance analysis will highlight which features drive the prediction.

### Measurement Validity
- **DelTA Coefficient**: Validated by the algorithm's definition (gradient-based credit assignment).
- **Semantic Similarity**: Validated by the use of `all-MiniLM-L6-v2`, a standard model for semantic textual similarity.
- **Static Features**: N-gram and POS are standard, validated linguistic features.
- **Domain Mismatch Control**: If correlation is low, the system checks if feature importance is uniformly low. If not, it flags 'domain mismatch' (MiniLM vs Math reasoning) rather than 'emergent signal'.

## Compute Feasibility & Escape Hatch

- **CPU Path**:
 - **Feature Extraction**: Fast (NLP libraries).
 - **MLP Training**: Fast (small model, <10k tokens).
 - **Oracle Step**: **Bottleneck**. Running Llama-8B for gradient backprop on 500 examples on CPU is infeasible (estimated days).
- **GPU Escape Hatch**:
 - If the CPU run fails or times out on the Oracle step, the execution engine will detect the CUDA requirement (or explicit `device="cuda"` in code) and re-run on a Kaggle GPU.
 - **Kaggle Strategy**: Use low-bit quantization (`bitsandbytes`) if full precision exceeds 16GB VRAM. Limit the example set to a manageable size to fit within the Extended kernel limit.
 - **No Fabrication**: We do not simulate the gradient step. We run the real step on the scaled-down dataset.

## Decision Rationale

- **Dataset Choice**: GSM8K is the standard for math reasoning and has a verified HuggingFace source. **OpenMathInstruct-1** is used for semantic reference because it contains step-by-step reasoning traces (matching GSM8K's format) and is verified. MathQA is rejected due to domain mismatch (multiple-choice) and lack of verified "solution trace" format.
- **Model Choice**: 2-layer MLP is sufficient for a non-linear mapping of static features and ensures CPU feasibility.
- **Evaluation**: Spearman correlation is robust to non-linear scaling of coefficients. **Example-level** permutation testing is essential to account for the non-i.i.d. nature of tokens within a single example.
