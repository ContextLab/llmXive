# Research: Self-improving LLM: recursive architecture refinement and re‑training

## Executive Summary

This research investigates the feasibility of recursive self-improvement in language models via explicit architectural modification and re-training. The core hypothesis is that a model, when prompted to analyze its own performance bottlenecks and propose structural changes, can incrementally improve on reasoning (GSM8K, ARC) and calibration (BoolQ) benchmarks across multiple cycles. The study is constrained to CPU-only execution on a GitHub Actions free-tier runner, necessitating a GPT small-scale baseline, streamed OpenWebText subsets, and rigorous resource management.

## Dataset Strategy

The project relies on open, directly-downloadable datasets verified for programmatic access. No access-gated data is used.

| Dataset | Purpose | Source / Loader | Verification Status |
|:--- |:--- |:--- |:--- |
| **GPT-2 124M** | Base model weights | `transformers` (HF Hub) | Public, no auth required. |
| **OpenWebText** | Training corpus | `datasets.load_dataset("Skylion007/openwebtext", streaming=True)` | Verified via `. Streaming used to fit within a standard RAM capacity. |
| **GSM8K** | Reasoning eval (100 samples) | `datasets.load_dataset("openai/gsm8k", "main", streaming=True)` | Verified via `. |
| **ARC-Challenge** | Reasoning eval (100 samples) | `datasets.load_dataset("allenai/ai2_arc", "ARC-Challenge", streaming=True)` | Verified via `. |
| **BoolQ** | Calibration eval (500 samples) | `datasets.load_dataset("google/boolq", streaming=True)` | Verified via ` |

**Data Hygiene Strategy**:
1. **Checksumming**: Upon loading a shard, `utils/data_loader.py` computes SHA256 and records it in `data/checksums.json`.
2. **Streaming**: To avoid OOM, `datasets` library streaming mode is used. The training loop iterates over the stream, accumulating a fixed number of samples (e.g., 100k) before stopping, ensuring the dataset fits in memory.
3. **No Synthetic Data**: All training and evaluation data is real. If a full dataset is too large, a deterministic sample (first N rows or fixed-seed random) is taken, not a synthetic replacement.

## Methodology

### 1. Baseline Establishment (Cycle 0) with Variance Estimation
- **Load**: Load GPT-2 124M (`device="cpu"`).
- **Evaluation Variance Estimation**: To establish a baseline variance floor without violating the 2-hour time limit or FR-004 (1 epoch training), the evaluation phase is executed **3 times** with different random seeds for data shuffling/sampling (seeds: 42, 123, 456).
 - This produces 3 sets of metrics for GSM8K, ARC-Challenge, and BoolQ.
 - The mean and standard deviation of these 3 runs are recorded as the baseline variance.
 - *Note*: This is an *inference-only* operation; no training is performed. This satisfies the statistical rigor requirement while adhering to the spec's time constraints.
- **Record Baseline**: Record the mean metrics and the standard deviation as the baseline variance.

### 2. Recursive Refinement Loop (Cycles 1-3)
For each cycle `i` (1 to 3):
1. **Proposal Generation**:
 - Construct prompt including: (a) Previous cycle metrics, (b) Current architecture config, (c) Constraint: "Modify one hyperparameter or layer count. Max a moderate increase in params. Distinct from previous."
 - Execute prompt on the *current* model (using a small inference pass or a separate lightweight LLM if the current model is too small to generate valid code, but spec implies self-prompting).
 - **Oracle Validation (FR-021)**: Parse the proposal. Check:
 - Is it a valid architectural change?
 - Does it exceed a significant threshold of parameters? (Reject if yes).
 - Is it distinct from previous cycles (Hamming distance ≥ 1)? (Reject if no). If rejected, attempt to generate an alternative modification that satisfies both constraints and parameter efficiency. The oracle will prioritize proposals with a higher estimated performance gain per added parameter.
 - If all attempts fail, log error and proceed to next cycle with no change.
2. **Modification**: Apply the validated change to the model architecture (e.g., increase hidden size, add layer).
3. **Training**:
 - Load OpenWebText stream.
 - Train for **1 epoch** (FR-004) on a subset (e.g., 100k samples) using AdamW, lr=5e-5, bs=4.
 - Profile FLOPs using `torch.profiler`.
 - **Retry Logic**: If training fails (OOM, crash), retry up to 2 times. If 2 retries fail, log cycle as "failed" and increment the cycle counter.
4. **Evaluation**:
 - Evaluate on same benchmarks (GSM8K, ARC, BoolQ) using a single seed (seed=42) for consistency with the baseline mean.
 - Compute metrics with high decimal precision.
5. **Statistical Analysis**:
 - Perform paired bootstrap test between Cycle `i` and Cycle `i-1` for each metric.
 - **Variance Adjustment**: The significance threshold (p < 0.05) is interpreted in the context of the baseline variance established in Step 1. If the observed improvement is smaller than the baseline standard deviation, the claim of improvement is qualified as "within variance noise".
 - Record p-values. Significance if `p < 0.05`.
6. **Termination Check**:
 - If performance degradation ≥ 5% from Cycle 0 baseline, terminate early.
 - Record trajectory.

### 3. Analysis & Reporting
- **Trajectory**: Fit linear regression to performance vs. cycle number. Report slope, R², trend.
- **Cost-Effectiveness**: Calculate `accuracy / FLOPs` and `accuracy / training_hours`.
- **Output**: `results/trajectory.json`, `results/logs/cycle_N.log`.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Since multiple metrics are tracked across multiple cycles, a Bonferroni correction or False Discovery Rate (FDR) control is applied to the p-values when claiming "significant improvement" across the board.
- **Power Limitation**: The sample sizes (GSM8K, ARC) are small. The plan acknowledges this limitation: results are exploratory. The bootstrap method is chosen specifically because it does not assume normality, which is robust for small N.
- **Baseline Variance**: The 3-seed evaluation step (inference only) provides a robust estimate of evaluation noise, ensuring that observed changes are not artifacts of random data shuffling. This approach respects the 2-hour time limit of User Story 1 by avoiding re-training.
- **Causal Inference**: This is an observational study of the model's self-modification. Claims are framed as *associational* improvements. No randomization of the modification type is performed; the model chooses.
- **Collinearity**: Architectural changes (e.g., hidden size vs. parameter count) are inherently collinear. The plan reports parameter count and performance separately but does not claim independent effects of "hidden size" without controlling for total params.
- **Compute Feasibility**:
 - **CPU-First**: GPT-2 124M on CPU with batch size 4 and gradient checkpointing is estimated to fit in ~6-7 GB RAM.
 - **GPU Escape Hatch**: Not planned. The spec explicitly states "No CUDA" and the model size is small enough for CPU. If OOM occurs, the retry logic and smaller sample sizes (streaming) are the mitigation. It is acknowledged that completing all 3 cycles within the time budget may be challenging but remains the goal.
 - **Time**: A single epoch on a large-scale dataset for a medium-scale model on 2 vCPU may take ~2-4 hours. Multiple cycles + eval + bootstrap ~ several hours total. The baseline variance step (multiple inference passes) adds negligible time compared to training, preserving the total time budget.

## Decision Rationale

- **Why GPT-2 124M?** It is the smallest standard GPT-2 variant that still exhibits non-trivial reasoning capabilities, fitting within CPU constraints.
- **Why Streaming?** OpenWebText is too large to download and store. Streaming allows processing the full dataset logic without storing it, adhering to the "Real Data" requirement while respecting memory limits.
- **Why Paired Bootstrap?** With N=100, the distribution of accuracy scores may not be normal. Bootstrap provides a reliable p-value without parametric assumptions.
- **Why External Oracle?** To prevent the model from proposing impossible or self-referential changes, an external heuristic is mandatory.
- **Why 3 Evaluation Seeds for Baseline?** To distinguish true architectural improvement from evaluation noise without violating the 2-hour time limit or the "1 epoch training" constraint. Re-training the baseline 3 times would exceed the time limit; re-evaluating 3 times is computationally trivial and statistically necessary.

