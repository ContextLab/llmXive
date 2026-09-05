# Research: llmXive Follow-up: Extending Asynchronous RL Staleness Bounds for Low-Capacity Models

## Research Question

Does the critical staleness threshold (the maximum delay before training divergence) differ between low-capacity language models (Phi-2 1.4B vs Qwen-1.8B) when trained asynchronously on the GSM8K dataset using CPU-only resources? **Note:** The goal is to identify **model-specific thresholds** and a **difference in tolerance**, not to establish a universal scaling law, due to architectural differences and the limitation of n=2.

## Background & Related Work

The parent study (arXiv:2607.07508) investigates the relationship between model capacity and staleness tolerance in asynchronous RL. This project extends that work by focusing specifically on the **low-capacity regime** (<2B parameters) and **CPU-only execution**, which introduces unique constraints on gradient computation and memory. The hypothesis is that smaller models may exhibit different staleness tolerance profiles due to their sensitivity to gradient noise and lower parameter redundancy.

## Dataset Strategy

**Source**: GSMK (Grade School Math 8K)
**Access Method**: `datasets.load_dataset('openai/gsm8k', 'main')`
**Verified URL**: `
**Rationale**: GSMK provides a standardized reasoning task with a clear reward signal (correctness of the final answer). The dataset is open, directly downloadable, and fits within the memory constraints when streamed.

| Dataset | Purpose | Access Method | Verification Status |
|:--- |:--- |:--- |:--- |
| **GSM8K** | Training & Evaluation (Reward Signal) | `datasets.load_dataset('openai/gsm8k', 'main')` | **Verified** (Direct download from HF Hub) |
| **Phi (1.4B)** | Model A (Low Capacity) | `transformers.AutoModelForCausalLM` (8-bit quantized) | **Verified** (HuggingFace Model Hub) |
| **Qwen1.5-1.8B** | Model B (Low Capacity) | `transformers.AutoModelForCausalLM` (8-bit quantized) | **Verified** (HuggingFace Model Hub) |

**Data Loading Strategy**:
1. **Streaming**: The dataset will be loaded with `streaming=True` to avoid loading the entire dataset into RAM.
2. **Sharding**: The dataset will be processed in chunks to ensure the memory footprint remains within acceptable limits.
3. **Checksum**: The raw downloaded parquet files will be checksummed (SHA-256) and stored in `data/raw/` to satisfy the Data Hygiene principle.
4. **Independence**: The test split will be strictly separated from the training staleness queue to prevent data leakage (FR-006).

## Methodology

### Experimental Design
The experiment follows a **2 (Model) × 3 (Regime) × 5 (Seeds)** factorial design.
- **Models**: Phi-2 (1.4B), Qwen1.5-1.8B.
- **Regimes**:
 1. **Low Staleness**: `staleness=0` (Synchronous baseline).
 2. **High Staleness**: `staleness=10` (Simulated high latency).
 3. **Adaptive Staleness**: `staleness` varies dynamically based on gradient norm (Mandatory, per Constitution Principle VI).
- **Seeds**: Multiple distinct integer seeds per model/regime. **All seeds are retained regardless of baseline stability.**

### Training Loop (CPU-Optimized)
1. **Initialization**: Load model with `load_in_8bit=True` and `device_map="cpu"`.
2. **Staleness Queue**: Implement a FIFO buffer that delays gradient application by `k` steps.
3. **Reward Calculation**: Evaluate the model on a batch of GSM8K questions; reward = 1.0 if correct, 0.0 otherwise.
4. **Gradient Update**: Compute gradients, push to queue, apply after delay.
5. **Divergence Check (Intrinsic)**:
 - Compute running mean and variance of reward and gradient norm over a recent sliding window of steps.
 - Flag `DIVERGED` if `reward_variance > 2 * reward_mean` OR `gradient_norm_variance > 2 * gradient_norm_mean` for 50 consecutive steps.
 - This definition is intrinsic to the run and does not rely on a synchronous baseline, avoiding circular validation.

### Statistical Analysis
- **Primary Metric**: Time-to-divergence (steps until instability).
- **Primary Test**: **Survival Analysis (Kaplan-Meier estimator)** with **Log-Rank test** to compare survival curves between Low and High staleness regimes. This handles censored data (runs that diverge early) correctly.
- **Secondary Metric**: Final reward variance for surviving runs.
- **Secondary Test**: **Levene's test** for equality of variance and **Two-sample t-test** (for surviving runs only).
- **Effect Size**: Report Cohen's d with 95% confidence intervals.
- **Significance Level**: $\alpha = 0.05$.
- **Hypothesis**: High staleness regime will show significantly shorter time-to-divergence (lower survival probability) and higher variance.

## Decision/Rationale

### CPU vs. GPU
- **Decision**: **CPU-First**.
- **Rationale**: The project explicitly targets the GitHub Actions free-tier (limited CPU, 7GB RAM). While GPUs offer speed, the models (1.4B/1.8B) are small enough to run on CPU with 8-bit quantization. Using a GPU would require a different infrastructure (Kaggle) and is unnecessary for the proof-of-concept. The plan ensures the CPU form is "faithful" (using real quantization) rather than a simulation.
- **Fallback**: If OOM occurs, the batch size will be reduced (Assumption: bitsandbytes CPU quantization fallback).

### Dataset Choice
- **Decision**: **GSM8K**.
- **Rationale**: It is the only verified, open, and directly downloadable dataset that provides a clear binary reward signal suitable for RL. Other datasets (e.g., MATH) are larger or harder to parse. The verified URLs in the `research.md` block confirm GSM8K's availability.

### Statistical Test
- **Decision**: **Survival Analysis (Log-Rank)** as primary, **Levene's Test** and **t-test** as secondary.
- **Rationale**: The hypothesis concerns the *process* of divergence (time-to-event), not just the final state. Survival Analysis handles censored data (early divergence) correctly, avoiding survivorship bias. Levene's test is required by the output schema to assess variance homogeneity.

### Divergence Definition
- **Decision**: **Intrinsic Variance Threshold**.
- **Rationale**: Defining divergence as a deviation from a synchronous baseline creates a tautology (divergence = not synchronous). Using an intrinsic threshold (variance > 2*mean) measures the *stability* of the asynchronous run itself, providing an independent ground truth for instability.

## Feasibility Assessment

- **Memory**: Model at reduced precision ~ 1.5GB; B ~ 2GB. Overhead for CPU quantization and data loading fits within 7GB.
- **Time**: 500 steps × 5 seeds × 2 models × 3 regimes = 15,000 steps total. At an estimated moderate step rate on CPU, total runtime is well within limits.
- **Data**: GSMK is small (~k examples) and streams efficiently.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **OOM on CPU** | Run fails | Reduce batch size to 2; use `streaming=True`; monitor memory. |
| **Divergence too early** | No data collected | Adjust staleness thresholds dynamically; ensure baseline is stable. |
| **Dataset download failure** | Run fails | Use `datasets` library with retry logic; cache locally. |
| **Non-convergence of baseline** | Invalid thresholds | **All seeds retained**; unstable baselines are recorded, not discarded. |