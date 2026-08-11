# Research: Self-improving LLM: recursive architecture refinement and re‑training

## Summary

This research investigates the feasibility of recursive self-improvement in LLMs by allowing a base model (GPT-2 124M) to propose architectural modifications, which are then validated, re-trained, and evaluated. The study focuses on three cycles of refinement, tracking performance on **Perplexity (PPL)** on **Wikitext-2** (replacing reasoning benchmarks due to statistical validity concerns). A **Control Arm** with random modifications is included to disentangle the effect of the model's proposal logic from general parameter increases.

## Dataset Strategy

### Verified Datasets

The following datasets are used, sourced exclusively from verified URLs provided in the project context:

| Dataset | Purpose | Verified Source URL | Loading Strategy |
|---------|---------|---------------------|------------------|
| **OpenWebText** | Training corpus for fine-tuning | ` | Streamed via `datasets.load_dataset(..., streaming=True)` to stay within RAM limits. A fixed seed random sample is used for training. |
| **Wikitext-2** | Evaluation benchmark (PPL) | ` | Loaded fully and sampled to [deferred] rows for evaluation. |
| **AllenAI ARC** | (Removed from primary metrics) | ` | Not used in primary analysis due to invalidity for base GPT-2. |

### Data Availability & Feasibility

- **OpenWebText**: The dataset is large. The plan uses **streaming** to avoid loading the full dataset into memory. A fixed seed random sample of **[deferred] samples** is selected for training to ensure reproducibility and fit within the 6-hour time budget.
- **Wikitext-2**: Small enough to be fully loaded. [deferred] samples are used for evaluation to ensure statistical stability of PPL.
- **Access**: All datasets are open and do not require authentication or data-use agreements.

## Methodology

### 1. Model Loading & Baseline
- **Base Model**: GPT-2 124M (`facebook/gpt2`).
- **Device**: CPU only (`device='cpu'`).
- **Baseline**: Evaluate the base model on Wikitext-2 to establish Cycle 0 PPL.

### 2. Refinement Cycle (Iterated 3 times)
1. **Proposal**: The model is prompted to suggest a modification (e.g., "increase hidden size by [deferred]"). The prompt includes the current architecture and baseline performance.
2. **Proposal Quality Check**: The model is evaluated on a held-out validation set to estimate if the proposal is likely to help. If the model cannot demonstrate a "reasoning" capability to justify the change, the proposal is rejected or flagged.
3. **Validation (Oracle)**: The proposal is passed to an external oracle (`pipeline/validator.py`) which checks:
 - Parameter count increase ≤ 30% (FR-003, FR-019).
 - Distinctness from previous modifications (FR-002, FR-020).
 - Feasibility (e.g., valid layer types).
 - If invalid, the model is re-prompted (with a limited number of retries).
4. **Modification**: The architecture is modified programmatically.
5. **Training**:
 - Dataset: Streamed OpenWebText subset ([deferred] samples).
 - Hyperparameters: AdamW, LR=5e-5, Batch=4, 1 Epoch.
 - Retry: Up to 2 retries on failure (FR-012).
6. **Evaluation**:
 - Wikitext-2 ([deferred] samples): Perplexity (PPL).
 - FLOPs: Calculated via `torch.profiler`.
7. **Statistical Analysis**: Bootstrap confidence intervals (1,000 resamples) against the previous cycle (FR-006).
8. **Termination Check**: If performance degrades ≥5% from baseline, stop early (FR-015).

### 3. Control Arm
- A parallel track where random architectural perturbations (of similar magnitude) are applied.
- This allows the study to disentangle the effect of the "model's proposal logic" from the general effect of "parameter increase".

### 4. Trajectory & Trade-off Analysis
- **Trend**: Use a heuristic: if PPL decreases in 2 consecutive cycles, trend is "improving"; if increases in 2, "declining"; else "flat". (Linear regression is invalid for N=3).
- **Cost-Effectiveness**: Compute PPL/FLOPs and PPL/hour for each cycle.

## Statistical Rigor

- **Multiple Comparisons**: Since we are comparing successive cycles, we will apply a **Bonferroni correction** or **Holm-Bonferroni** to the significance threshold (α = 0.05 / 3 ≈ 0.0167) to control family-wise error rate.
- **Power Analysis**: The sample sizes ([deferred] training, [deferred] test) are small. We acknowledge a **power limitation**. The bootstrap method is chosen specifically for its ability to estimate confidence intervals without assuming a normal distribution. However, the ability to detect small effect sizes is limited.
- **Causal Inference**: This is an **observational** study of the model's self-modification process. We cannot claim causality in the strict sense. Claims will be framed as **associational**. The **Control Arm** helps disentangle the proposal logic from general parameter increases.
- **Measurement Validity**:
 - **Wikitext-2 PPL**: Standard metric for language modeling; widely validated.
 - **FLOPs**: Calculated via standard `torch.profiler` methods.
- **Collinearity**: Architectural parameters are often correlated. We will report them descriptively and acknowledge that independent effects cannot be fully disentangled.

## Compute Feasibility

- **CPU-First**: The entire pipeline is designed for CPU execution.
 - **Model**: GPT-2 124M is small enough for CPU inference and training with batch size 4.
 - **Training**: 1 epoch on [deferred] samples should complete within 1-2 hours per cycle on 2 CPU cores.
 - **Evaluation**: Inference on [deferred] samples is trivial on CPU.
- **GPU Escape Hatch**: Not required for this specific scope.
- **Memory**: Streaming OpenWebText ensures peak RAM usage remains within manageable limits.

## Decision/Rationale

- **Why CPU?**: The spec explicitly targets GitHub Actions free-tier. GPT-2 124M is the smallest viable model for this experiment.
- **Why Streaming?**: OpenWebText is too large to fit in RAM.
- **Why Bootstrap?**: Small test sets make parametric tests unreliable.
- **Why External Oracle?**: To satisfy Constitution Principle VII and prevent circular validation.
- **Why Wikitext-2?**: PPL is the only statistically valid metric for a base GPT-2 model on this training objective. Accuracy on reasoning tasks is indistinguishable from zero.
- **Why Control Arm?**: To disentangle the "self-improving" claim from general parameter increase effects.
- **Why Heuristic Trend?**: Linear regression is invalid for N=3.