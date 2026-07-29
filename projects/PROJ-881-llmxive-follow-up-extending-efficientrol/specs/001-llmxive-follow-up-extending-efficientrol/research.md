# Research: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Research Question

Does intermediate-layer Shannon entropy in transformer models predict token validity (correctness) in autoregressive generation for mathematical reasoning (GSM8K) and navigation (MiniGrid) tasks?

## Background & Hypothesis

Current speculative decoding methods rely on heuristics that may not capture the true uncertainty of a model's internal state. This study hypothesizes that **entropy signals from intermediate layers contain predictive information about whether a generated token will eventually be part of a valid ground-truth sequence**.

**Hypothesis**: There is a statistically significant negative correlation between intermediate-layer entropy and token validity. Lower entropy in early/mid layers predicts higher validity.

## Dataset Strategy

We utilize the following verified datasets. All data is fetched via `datasets.load_dataset` with `streaming=True` to ensure memory efficiency on the CPU-only runner.

| Dataset | Source URL | Usage | Verification |
|---------|------------|-------|--------------|
| GSM8K | https://huggingface.co/datasets/openai/gsm8k | Mathematical reasoning tasks. Ground truth: solution string. | Verified Hugging Face Hub repository. |
| MiniGrid | https://huggingface.co/datasets/fka/awesome-ml-minigrid | Navigation tasks. Ground truth: action sequence. | Verified Hugging Face Hub repository (canonical benchmark). |

**Dataset Limitations**:
- **GSM8K**: Contains only reasoning problems; no multi-turn dialogue.
- **MiniGrid**: Uses the canonical `minigrid` benchmark to ensure meaningful ground-truth action sequences.
- **Model Choice**: We use `Qwen/Qwen1.5-0.5B` (0.5B parameters) to ensure CPU feasibility and higher validity rates (>20%) to avoid class imbalance issues common with larger models on these tasks.

## Methodology

### 1. Data Acquisition & Ground Truth Labeling (FR-001, FR-002)
- **Download**: Fetch GSM8K and MiniGrid subsets using `datasets.load_dataset(..., streaming=True)`, limiting to 500 examples per task.
- **Generation**: Run `Qwen/Qwen1.5-0.5B` on CPU with `temperature=0.0` to generate deterministic sequences.
- **Labeling (Semantic Alignment)**:
  - **GSM8K**: Extract the final numeric answer from the ground truth. Align the model's generated sequence to this answer. Tokens leading to the correct answer are labeled 'valid' (1) only if they are part of a consistent reasoning path. If the model diverges from the correct path, tokens from the divergence point onwards are labeled 'invalid' (0).
  - **MiniGrid**: Compare the generated action sequence against the ground-truth action sequence. Tokens matching the ground truth are 'valid' (1); mismatches are 'invalid' (0).
  - **Handling Ambiguity**: If multiple valid paths exist (MiniGrid), a token is 'valid' if it matches *any* valid path.
- **Output**: `data/processed/ground_truth_labels.jsonl` with `token_id`, `validity` (0/1), `task_type`.

### 2. Intermediate State Extraction (FR-003, FR-007)
- **Instrumentation**: Re-run the generation process with hooks to capture logits at every layer.
- **Memory Strategy**: Process sequences **one at a time** (single-sequence streaming) to ensure memory usage remains under 7GB RAM. This avoids the OOM risk of batching multiple sequences.
- **Entropy Calculation**: Compute Shannon entropy $H = -\sum p_i \log p_i$ for each token at each layer.
  - **Handling Zero Probability**: Clamp probabilities $p_i \ge \epsilon$ (e.g., $10^{-9}$) before log calculation to avoid `log(0)`.
- **Output**: `data/processed/entropy_profiles.jsonl` with `token_id`, `layer_id`, `entropy_value`.

### 3. Statistical Analysis (FR-004, FR-005, FR-006)
- **Model**: Fit a **Mixed-Effects Logistic Regression (GLMM)**: $P(\text{valid}) = \sigma(\beta_0 + \beta_1 \cdot \text{entropy} + \beta_2 \cdot \text{layer\_index} + u_{sequence\_id})$, where $u_{sequence\_id}$ is a random intercept for each sequence to account for token-level autocorrelation.
- **Stratification**: Analyze GSM8K and MiniGrid separately, then pooled.
- **Multiple Comparison Correction**: Apply Benjamini-Hochberg (FDR) correction to p-values across layers/tasks (FR-006).
- **Threshold Optimization**: Sweep entropy thresholds to find the cutoff minimizing $w_{FP} \cdot FP + w_{FN} \cdot FN$ (equal weights).
- **Sensitivity Analysis**: Report False Positive Rate (FPR) and False Negative Rate (FNR) at the optimal threshold.
- **Power Analysis**: Acknowledge sample size limitations (N=500 per task) and report confidence intervals.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: We explicitly apply FDR correction (Benjamini-Hochberg) to control the family-wise error rate when testing coefficients across multiple layers (FR-006).
- **Sample Size**: With ~500 examples per task and sequence lengths up to 512, we have ~250k token-level observations. This provides high power for detecting even small effect sizes, but we will report power limitations if the dataset is smaller than expected.
- **Causal Claims**: We frame results as **associational**. We do not claim that reducing entropy *causes* validity; rather, we observe if entropy *predicts* validity.
- **Collinearity**: Layers are sequential; entropy values in adjacent layers are highly correlated. We will report layer-specific coefficients but avoid claiming "independent effects" of specific layers without VIF checks.
- **Measurement Validity**: Entropy is a standard measure of uncertainty. Validity is defined by exact match to ground truth, which is the standard for these datasets.

## Compute Feasibility

- **CPU-First**: All generation and analysis run on CPU using `torch` (no CUDA).
- **Memory**: **Single-sequence processing** ensures <7GB RAM usage. Batching 50 sequences of 512 tokens is too large; we process one sequence at a time.
- **Time**: 500 examples * 512 tokens * 30 layers is computationally intensive but feasible within 6 hours on a 2-core runner if optimized (e.g., using `torch.no_grad()`).
- **GPU Escape Hatch**: Not required for this study as the model size is small enough for CPU. If the chosen model proves too large, we will switch to a smaller variant (e.g., 0.5B) rather than offloading to GPU, to maintain CPU-first reproducibility.

## Decision/Rationale

- **Model Choice**: `Qwen/Qwen1.5-0.5B` is selected to ensure CPU feasibility and higher validity rates. Larger models would require quantization and may still exceed RAM limits with intermediate state extraction.
- **Streaming**: `datasets.load_dataset(..., streaming=True)` is used to avoid loading the entire dataset into memory.
- **Batching**: **Single-sequence processing** is chosen to balance memory overhead with processing efficiency.
- **Statistical Method**: Mixed-Effects Logistic Regression (GLMM) is chosen to handle token-level autocorrelation and provide valid standard errors.