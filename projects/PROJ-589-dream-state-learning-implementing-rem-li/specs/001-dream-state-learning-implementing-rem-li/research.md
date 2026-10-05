# Research: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Executive Summary

This research investigates whether an oscillatory training schedule mimicking REM sleep (generative replay with denoising reconstruction) enhances few-shot generalization in small language models compared to standard continuous supervised fine-tuning. The "logical depth" of consolidation is defined computationally as the model's ability to reconstruct masked input tokens after a cycle of generative replay, serving as a proxy for synaptic stabilization. The study adheres to strict CPU-only constraints, utilizing a defined wake-to-dream ratio, a 20-step warm-up, and rigorous statistical validation (paired t-tests across 5 seeds) on GLUE/SuperGLUE subsets. **Note**: This is explicitly framed as a **feasibility/pilot study** due to power limitations with n=5.

## Theoretical Background & Logical Depth

### Defining "Consolidation" in Digital Systems
Biological consolidation (as noted by Kandel) involves structural remodeling and protein synthesis to stabilize short-term memories. In a digital system, we cannot simulate protein synthesis. Instead, we define **digital consolidation** as the reduction in the discrepancy between the model's generative distribution and the original data distribution after a "dream" cycle.
- **Hypothesis**: The dream phase acts as a regularizer, preventing overfitting to the specific order of wake-phase data by forcing the model to reconstruct inputs from noisy, self-generated representations. This regularization is hypothesized to improve generalization to **unseen tasks** (cross-task transfer).
- **Logical Depth**: Unlike simple data augmentation, the dream phase uses the *current* model state to generate data, then trains the model to recover the *original* ground truth input. This creates a closed loop of "prediction -> reconstruction -> correction," theoretically stabilizing the weights against catastrophic forgetting and improving generalization.

### Addressing Reviewer Concerns
- **Freeman Dyson**: The dream is not merely data augmentation; it is a *self-corrective* loop. The target is the original ground truth, not the generated sample. This distinguishes it from standard generative pre-training.
- **John von Neumann**: The "consolidated state" is quantified by the reconstruction loss on masked tokens. If the model can reconstruct the original input from a noisy version of its own generation, it has stabilized the representation.
- **Eric Kandel**: The "cost" of consolidation is the computational overhead of the dream phase, which is offset by the potential gain in generalization.

## Dataset Strategy

The study requires a dataset for the "wake" phase (standard SFT) and a **held-out, cross-task subset** for "few-shot" evaluation.

### Verified Datasets
The following datasets are verified for programmatic access and suitability via the `datasets` library:

| Dataset Name | Purpose | Source URL / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| **GLUE (MNLI)** | Wake phase training (SFT) | `datasets.load_dataset('glue', 'mnli')` (train split) | Verified |
| **GLUE (QNLI)** | Few-shot evaluation | `datasets.load_dataset('glue', 'qnli')` (validation split) | Verified |

**Strategy**:
1.  **Primary Source**: Use the GLUE dataset via the `datasets` library to ensure reproducibility.
2.  **Cross-Task Transfer**: The wake phase trains on **MNLI** (Multi-Genre Natural Language Inference). The few-shot evaluation is performed on **QNLI** (Question-answering NLI), a distinct task within the GLUE suite. This ensures the "generalization" claim is valid and not a result of overfitting to a single task distribution.
3.  **Streaming**: To handle potential memory constraints, the dataset will be loaded with `streaming=True` where possible, or a fixed random sample of ≤2000 examples will be downloaded to `data/raw/` to ensure it fits within the 7GB RAM limit.
4.  **No Gated Data**: No access-gated datasets are used. All data is open and directly downloadable.

## Methodological Rigor

### Statistical Power & Design
- **Design**: Paired experimental design. For each of 5 random seeds, two models are trained:
    1.  **Experimental**: Wake/Dream cycle (4:1 ratio).
    2.  **Baseline**: Continuous SFT (same total number of gradient steps, filling dream steps with additional wake steps or noise-injected real data).
- **Power Analysis**: The study targets an effect size of $d=0.8$. With $n=5$ pairs, the power to detect this effect at $\alpha=0.05$ is approximately 0.65. **This is insufficient to reliably claim statistical significance.** Therefore, this study is explicitly framed as a **feasibility/pilot**. The primary outcome is the estimation of the effect size (Cohen's d) and confidence intervals. Statistical significance (p-value) will be reported as exploratory only.
- **Multiple Comparisons**: If multiple GLUE subsets are tested, a Bonferroni correction will be applied to the $\alpha$ threshold to control the family-wise error rate.

### Computational Feasibility (CPU-First)
- **Model**: **DistilBERT-base-uncased** (~66M params). TinyLlama is excluded to ensure architectural consistency across all runs.
- **Hardware**: 2 CPU cores, 7GB RAM.
- **Strategy**:
    - Use `torch.cpu` explicitly.
    - Batch size set to 4 or 8 to keep peak RSS < 6.3 GB.
    - Dream phase generation is limited to short sequences (≤32 tokens) to reduce inference time.
    - If a step exceeds time/memory, the job aborts gracefully (FR-005).
- **GPU Escape Hatch**: Not applicable for this CPU-tractable design.

## Edge Case Handling

1.  **Low Entropy Collapse**: If generated pseudo-samples have average entropy < 0.5 bits/token, the batch is discarded, and re-sampling is triggered (up to 3 times). If it persists, the dream step is skipped.
2.  **High Perplexity**: If generated samples have perplexity > 50 against a held-out corpus, the dream step is skipped to prevent reinforcing hallucinations.
3.  **Insufficient Samples**: If the evaluation set has < 5 samples, the t-test is skipped, and the result is flagged as "insufficient power" (Edge Case).

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **DistilBERT-base-uncased** | Fixed architecture to prevent confounds. CPU-tractable. |
| **4:1 Wake/Dream Ratio** | Matches the "theta-like cycle" in the constitution (Principle VI) and biological REM approximations. |
| **20-Step Warm-up** | Prevents early collapse where the model has not learned enough to generate meaningful pseudo-samples. |
| **Reconstruction + Distillation Loss** | Using the original ground truth as the target (reconstruction) and matching the teacher's distribution (distillation) ensures the model learns to recover from noise and stabilizes representations, simulating "consolidation". |
| **Cross-Task Evaluation (MNLI -> QNLI)** | Validates true generalization to unseen tasks, not just overfitting to a single task distribution. |
| **Pilot Study Framing** | Acknowledges power limitations with n=5, focusing on effect size estimation rather than false claims of significance. |