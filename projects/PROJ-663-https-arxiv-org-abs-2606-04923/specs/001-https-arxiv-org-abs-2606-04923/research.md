# Research: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

## 1. Objective

To reproduce the core findings of the CHERRL paper regarding reward hacking detection in LLM-based RL agents. Specifically, this research aims to:
1. Establish a functional CPU-only environment for the CHERRL codebase using Qwen1.5-1.8B (float16).
2. Demonstrate that injecting specific linguistic biases into the "Judge" model causes the RL agent's reward score to diverge from ground-truth quality (Reward Hacking).
3. Validate the RHDA (Reward Hacking Detection Agent) in identifying the onset of this divergence and performing a threshold sensitivity analysis.

## 2. Verified Datasets

The following datasets are verified and available for use. Per project rules, only these sources are cited.

| Dataset Name | Description | Verified URL / Loader |
|:--- |:--- |:--- |
| **HealthBench (Train)** | Training data for the RL environment. Contains health-related prompts and rubrics. | `https://huggingface.co/datasets/healthbench/healthbench_train/resolve/main/data/train-00000-of-00001.parquet` |
| **Qwen1.5-1.8B (Weights)** | Model weights for the target model (Qwen1.5-1.8B) in float16. | `https://huggingface.co/Qwen/Qwen1.5-1.8B-Instruct-GGUF/resolve/main/qwen1_5-1_8b-instruct-q4_k_m.gguf` |
| **CHERRL Rollout Logs** | Clean control rollout logs for baseline comparison and validation. | ` |

**Dataset Strategy**:
- **Primary Data**: The `healthbench_train.parquet` is loaded from the verified HuggingFace URL. If the vendored file is missing, the system fails fast.
- **Model Data**: The Qwen1.5-1.8B weights are loaded from the verified HuggingFace GGUF repository. This format is optimized for CPU inference and fits within 7GB RAM.
- **Bias Data**: The "self-praise", "lexical", and "tone" biases are defined as prompt templates in `external/CHERRL/configs/bias_config.yaml`.

## 3. Methodology

### 3.1 Environment Setup (US-1)
- **Action**: Clone `external/CHERRL` submodule.
- **Dependencies**: Install `torch` (CPU version), `transformers`, `accelerate`, `pandas`.
- **Sanity Check**: Execute a script that loads the Qwen1.5-1.8B model in `float16` on CPU and processes a single row from the HealthBench dataset.
- **Success Criterion**: Script exits with code 0; no CUDA errors.

### 3.2 Bias Injection & Training (US-2)
- **Configuration**: Define 3 bias types in `configs/bias_config.yaml`:
 1. `self-praise`: Judge rewards tokens indicating self-aggrandizement.
 2. `lexical`: Judge rewards specific high-frequency words regardless of context.
 3. `tone`: Judge rewards overly polite or formal tone.
- **Execution**: Run multiple independent seeds for each bias configuration AND multiple independent seeds for the baseline (no bias). Total: runs.
- **Steps**: 500 steps per run.
- **Observation**: Log per-step rewards and generated tokens.
- **Ground Truth**: For each step, calculate an independent "Ground Truth Quality" score using an unbiased rubric (or the original CHERRL unbiased judge).
- **Statistical Rigor**:
 - **Metric**: Mean reward over the final 50 steps of each seed.
 - **Test**: Mann-Whitney U test comparing the distribution of biased means vs. baseline means.
 - **Multiple Comparisons**: Bonferroni correction applied to the 3 bias comparisons (p < 0.05 / 3).
 - **Causal Framing**: All claims will be framed as "associational effects of injected bias on reward scores", avoiding claims of agent "intent".
 - **Power Limitation**: The sample size (a small number of seeds) is small. The goal is to demonstrate the *mechanism* of hacking.

### 3.3 Detection & Sensitivity (US-3)
- **Agent**: Run the RHDA agent on the generated logs.
- **Threshold Sweep**: Execute detection with thresholds `{0.01, 0.05, 0.1}`.
- **Output**: Generate `threshold_grid.csv` containing True Positive Rate (TPR) and False Positive Rate (FPR) for each threshold.
- **Ground Truth Definition**: The "onset" is defined as the step index where the bias configuration becomes active (Step X). The detection agent's target is to identify the step where the reward curve statistically diverges from the baseline distribution *after* Step X. The metric is "time-to-detect" relative to the known injection point.
- **Validation**: Compare detected onset step against the known injection step (ground truth).

### 3.4 Precision Sensitivity Check
- **Action**: Run a small subset of data in float32 (if feasible) or compare against a known float16 baseline to ensure the bias detection mechanism is not an artifact of quantization.
- **Goal**: Validate that the CPU/float16 approximation does not introduce artifacts that mimic or mask reward hacking.

## 4. Compute Feasibility Analysis

- **Memory**: Qwen-1.8B in `float16` requires approximately 3.6GB for weights + overhead. This fits within the available RAM limit.
 - *Mitigation*: If memory pressure is detected, the pipeline ABORTS with a clear error message recommending the smaller Qwen1.5-0.5B model. It does NOT automatically switch.
- **Time**: A sufficient number of runs is employed. Even with slow CPU inference, this should complete well within 4 hours. The time limit is safe.
- **Disk**: Logs and models will be cached. The storage limit is sufficient for the model weights (compressed) and logs.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **OOM (Out of Memory)** | Job crashes before completion. | **ABORT**. Pipeline terminates with clear error. No silent fallback. |
| **Bias Not Detected** | Reward curve does not diverge. | Verify bias prompt templates. Check if the "Judge" model attends to biased tokens. |
| **Dataset Missing** | `healthbench_train.parquet` not found. | Fail fast with clear error message. |
| **RHDA False Positives** | Detection triggers too early. | Sensitivity analysis (SC-004) will quantify this; report the trade-off. |
| **Quantization Artifact** | Bias detection is an artifact of float16. | Perform "Precision Sensitivity Check" (Section 3.4). |

## 6. Decision Rationale

- **Model Choice**: Qwen-1.8B is chosen as the smallest viable model that fits in 7GB RAM in float16.
- **Precision**: `float16` is required to fit the model. A control experiment (Section 3.4) validates the approximation.
- **Thresholds**: 0.01, 0.05, 0.1 are standard statistical significance levels, satisfying the requirement for a "valid report".
- **Seeds**: Multiple seeds per condition are required for valid statistical testing (Mann-Whitney U).