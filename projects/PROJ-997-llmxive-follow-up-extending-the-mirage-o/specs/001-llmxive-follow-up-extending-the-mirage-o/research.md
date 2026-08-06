# Research: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Problem Statement

The research aims to investigate the "policy gap"—the divergence between full-precision training signals and quantized inference outputs in Large Language Models (LLMs). Specifically, it seeks to determine if training-side features (**gradient norms** and **local curvature**) can predict the hardware-measured KL divergence between full-precision and quantized (INT4, INT8, FP8) outputs. This would enable a "Monotonic Inference Policy" (MIPU) loop that uses a fast analytical proxy instead of expensive synchronous hardware checks.

## Dataset Strategy

The project relies on verified, open-source datasets for prompts and reasoning labels. The following datasets have been verified for reachability and format compatibility:

| Dataset Name | Format | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **GSM8K** | Parquet | ` (via `datasets.load_dataset('gsm8k', 'main')`) | **Reasoning Subset**. Contains prompts and ground-truth answers. Used for the Static RL Simulation to calculate "Final Scores" (accuracy) and for the t-test on reasoning stability. |
| **HuggingFaceH4/ultrachat_200k** | Parquet | `https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k` (via `datasets.load_dataset('HuggingFaceH4/ultrachat_200k')`) | **General Prompts**. Contains diverse chit-chat prompts. Used to augment the dataset size for feature extraction and gap measurement where ground-truth answers are not required. |
| **CohereLabs/wikipedia-2023-11-embed-multilingual-v3-int8-binary** | Parquet | ` | **Reference**. Used to validate quantized activation formats if needed. |

**Decision/Rationale**:
- **Primary Strategy**: The plan uses a **hybrid dataset strategy**.
 1. **GSM8K** is used for the subset of samples involved in the **Static RL Simulation** (Phase 4) because it provides the necessary `ground_truth_answer` to calculate the "Final Score" (accuracy) required for the paired t-test in SC-003.
 2. **Ultrachat_200k** is used to augment the total sample size (n ≥ 300) for the feature extraction and gap measurement phases (Phase 2/3), ensuring statistical power for the regression model without requiring ground-truth answers for every sample.
- **Streaming**: All datasets are streamed (`streaming=True`) to respect the available RAM limit.

**Dataset Variable Fit Check**:
- **GSM8K**: Verified to contain `question` (prompt) and `answer` (ground truth). Suitable for the reasoning subset.
- **Ultrachat_200k**: Verified to contain `messages` (prompts). Suitable for general feature extraction.
- **Quantized Outputs**: The plan generates quantized outputs (INT4, INT8, FP8) and full-precision outputs (FP16) on-the-fly using `llama.cpp` and `transformers` on the runner to ensure ground-truth alignment. This satisfies the "Hardware-Grounded Validation" requirement with verified data sources.

## Methodology

### 1. Data Generation (Hardware-Grounded)
- **Prompt Selection**: Sample a subset of prompts from GSM8K (for reasoning) and Ultrachat_200k (for general diversity).
- **Full-Precision Inference**: Run Llama-8B (FP16) to get baseline logits and gradients.
- **Feature Extraction**:
 - **Gradient Norms**: Compute L2 norm of the gradients w.r.t. input embeddings.
 - **Local Curvature**: Compute via Hutchinson's estimator (random projection) to approximate the trace of the Hessian.
- **Quantized Inference**: Run `llama.cpp` (CPU) on the same prompts in INT4, INT8, and FP8 modes.
- **Ground Truth**: Calculate KL divergence between FP16 and each quantized output.
- **Ground Truth Answer**: Store `answer` from GSM8K for the reasoning subset.

### 2. Model Training
- **Algorithm**: Kernel Ridge Regression (KRR) with RBF kernel.
- **Input**: Gradient norms and local curvature.
- **Target**: KL divergence (ground truth).
- **Training**: Split data into a training set and a test set using a standard high-low proportion. Use fixed seed.
- **Hyperparameter Tuning**: Use a fixed, small grid for alpha and gamma (e.g., alpha=[0.1, 1.0, 10.0], gamma=[0.01, 0.1, 1.0]) to ensure reproducibility and avoid overfitting.
- **Validation**: Measure Pearson correlation (r) and MAE.

### 3. Statistical Validation
- **Correlation**: Check if r > 0.8 for at least one quantization level.
- **Bound Verification**: Check if |predicted - actual| < 0.1 for ≥95% of samples.
- **Multiplicity Correction**: Apply Bonferroni correction for multiple tests (INT4, INT8, FP8).
- **Collinearity**: Compute Variance Inflation Factor (VIF) for gradient norms and curvature.
- **Power Analysis**: Ensure n ≥ 300 for statistical power. If compute time exceeds a practical threshold, reduce n to a smaller sample size and note the power limitation.

### 4. Static RL Simulation
- **Environment**: The test set of prompts (specifically the GSM8K subset for scoring).
- **Baseline Policy**: A policy that accepts [deferred] of samples (or uses a fixed threshold). Calculate **Baseline Acceptance Rate**.
- **Proxy Policy**: Accept sample if `predicted_gap < threshold`. Calculate **Proxy Acceptance Rate**.
- **Metrics**: Calculate acceptance rate and **Final Score** (accuracy against `ground_truth_answer` from GSM8K) on accepted samples.
- **Comparison**: Paired t-test between Proxy Acceptance Rate and Baseline Acceptance Rate, and between Final Scores.

### 5. Assumptions & Limitations
- **Observational Nature**: The study is observational; findings are associational, not causal.
- **Hardware Constraints**: The plan assumes `llama.cpp` can run INT4/INT8/FP8 on the CPU runner within the time limit. If not, the sample size will be reduced.
- **Curvature Proxy**: Full Hessian trace is infeasible; Hutchinson's estimator is used. This is an approximation acknowledged in the study.
- **Data Availability**: The plan uses verified datasets (GSM8K, Ultrachat). It does not rely on unverified datasets.

## Ethical Considerations

- **Reproducibility**: All code and data generation scripts are open-source and reproducible.
- **Bias**: The verified datasets may have inherent biases. The study will acknowledge this limitation.
- **Resource Usage**: The plan is optimized for CPU usage to minimize energy consumption and maximize accessibility.

## Conclusion

This research will provide empirical evidence on the feasibility of using training-side features (gradient norms, curvature) to predict quantization-induced policy gaps. By grounding the validation in actual hardware inference (CPU-based `llama.cpp`) and using verified datasets (GSM8K for reasoning, Ultrachat for general), the study aims to establish a robust analytical bound that can replace expensive synchronous checks in MIPU loops.