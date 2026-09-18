# Research: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Executive Summary

This research investigates whether an oscillatory training schedule, mimicking biological REM sleep cycles, can enhance few-shot generalization in small language models (≤100M parameters). The core hypothesis is that alternating "wake" (supervised learning) and "dream" (generative replay with denoising) phases promotes better consolidation of learned representations compared to continuous supervised training. The implementation is constrained to run entirely on CPU hardware within GitHub Actions free-tier limits (2 vCPU, 7GB RAM, 6h), necessitating the use of small models (DistilBERT/TinyLlama) and efficient data streaming.

## Dataset Strategy

The project relies on the **GLUE** and **SuperGLUE** benchmarks for evaluation and training data. These datasets are open, programmatic, and verified.

| Dataset Name | Purpose | Source URL (Verified) | Loading Strategy |
| :--- | :--- | :--- | :--- |
| **GLUE (MRPC, SST-2)** | Training (Wake phase) | `https://huggingface.co/datasets/glue` | `datasets.load_dataset("glue", "mrpc", split="train")` |
| **SuperGLUE (CB, RTE)** | Few-shot Evaluation | `https://huggingface.co/datasets/super_glue` | `datasets.load_dataset("super_glue", "cb", split="validation")` |
| **GLUE (MNLI)** | Held-out Evaluation | `https://huggingface.co/datasets/glue` | `datasets.load_dataset("glue", "mnli", split="validation")` |

**Data Availability Note**: All selected datasets are available via Hugging Face `parquet` files and can be loaded programmatically without authentication or data-use agreements. This ensures full reproducibility on the CI runner. No access-gated data (e.g., ADNI, UK Biobank) is used.

**Dataset Variable Fit**:
- **Predictors**: Input text sequences (e.g., premise, hypothesis).
- **Outcomes**: Labels (e.g., entailment, contradiction) for supervised wake phases; generated tokens for dream reconstruction.
- **Covariates**: Sequence length, token entropy (defined in Edge Cases).
- **Fit Confirmation**: The GLUE/SuperGLUE datasets contain the necessary text sequences and labels for the supervised wake phase. For the dream phase, the model generates pseudo-samples from its own internal distribution; no external "dream" dataset is required, avoiding the need for a dataset that contains "dream-like" text. The setup is valid.

**Few-Shot Subset Size**: The evaluation subsets are limited to **≤1000 samples** to satisfy Constitution Principle VII.

**Task Mapping**:
- **Training (Wake)**: GLUE MRPC, SST-2.
- **Evaluation (Few-Shot)**: SuperGLUE CB, RTE, GLUE MNLI.
This separation ensures validation on held-out subsets as required by Constitution Principle VII.

## Methodological Rigor

### Statistical Analysis Plan
- **Primary Metric**: Accuracy on held-out few-shot subsets (SC-001).
- **Statistical Test**: **Paired t-test** (SC-002) comparing Wake/Dream vs. Continuous Baseline across 5 random seeds.
  - *Rationale*: The Specification (SC-002) mandates the paired t-test. The Plan implements this as the primary acceptance metric.
  - *Robustness Check*: A secondary **Wilcoxon signed-rank test** will be computed to assess robustness against non-normality and small sample size (n=5).
- **Power Analysis**: 5 seeds provide a minimal power baseline. The Minimum Detectable Effect Size (MDES) for n=5 (at 80% power, alpha=0.05) is approximately **0.08 ([deferred] absolute accuracy gain)**, assuming a standard deviation of 0.05 (based on typical GLUE variance). Results with p < 0.05 will be reported as "statistically significant" per Spec, but effect sizes and confidence intervals will be included to contextualize the finding. If the observed effect is smaller than the MDES, the result will be reported as "inconclusive due to power".
- **Multiple Comparisons**: If multiple GLUE tasks are evaluated, a Bonferroni correction will be applied to the family-wise error rate to control for Type I errors.

### Measurement Validity
- **Instruments**: Standard GLUE/SuperGLUE evaluation metrics (Accuracy) are widely validated in NLP literature.
- **Consolidation Proxy**: The "dream" phase is implemented as a Denoising Autoencoder (DAE) task on model-generated text. This serves as a computational proxy for biological consolidation (replay + refinement), validated by its ability to reduce loss on generated samples. The target for reconstruction is the **original real input**, ensuring the learning signal is grounded in reality and not purely self-reinforcing.

### Causal Inference & Collinearity
- **Observational Nature**: The study is experimental (controlled training runs), not observational. Causal claims are limited to "Wake/Dream training *causes* X improvement relative to Continuous training *under these conditions*."
- **Collinearity**: Predictors in the dream phase (generated tokens) are derived from the model's current state. This introduces inherent collinearity between the generated input and the target. The plan addresses this by:
  1. Using a **frozen teacher model** to generate pseudo-samples (broken immediate feedback loop).
  2. Defining the **target** as the **original real input** (not the generated sample), ensuring the learning signal is grounded in reality.
  3. Reporting the collinearity metric (correlation between generated input and target) in the logs.
  4. **Quality Control**: Generated pseudo-samples are evaluated against a held-out real corpus (GLUE validation) for perplexity. If perplexity exceeds a threshold, the dream batch is discarded to prevent training on garbage.

## Compute Feasibility & GPU Escape Hatch

### CPU-First Strategy
- **Model Choice**: DistilBERT-base (66M params). TinyLlama is excluded due to RAM constraints.
- **Memory Management**:
  - Batch size: 8 (adjustable).
  - Gradient accumulation: 4 steps.
  - Streaming: Datasets loaded via `streaming=True` to avoid loading full corpus into RAM.
  - Memory Monitor: `FR-005` enforces a hard abort at 6.0 GB RSS.
- **Time Budget**: The full pipeline (seeds × runs + temperature sweep) is estimated to take ~4-5 hours on a 2-core CPU runner.
- **GPU Escape Hatch**: **Removed**. The plan commits to a strict CPU-only strategy with model size constraints (DistilBERT) and quantization to fit within 7GB RAM, ensuring reproducibility on the GitHub Actions runner. No external GPU resources (Kaggle) are used. If the model requires >7GB RAM or the training loop exceeds 6 hours on CPU, the experiment is **aborted** and the result is reported as "infeasible on CPU".

## Decision Rationale

1.  **DAE vs. Generative Replay**: The Spec (FR-002) mentions "generative replay with masked inputs". We implement this as a Denoising Autoencoder (DAE) where the model generates a sequence, masks tokens, and tries to reconstruct the *original* sequence. This is computationally cheaper than full generative replay and aligns with the "consolidation" hypothesis (refining existing representations). This explicitly satisfies FR-002's "generative replay" requirement.
2.  **Statistical Test**: We implement the **paired t-test** as the primary metric to satisfy SC-002. A secondary Wilcoxon test is reported for robustness.
3.  **Dataset Selection**: GLUE/SuperGLUE are chosen for their open availability and standardization in few-shot research. No access-gated data is used.
4.  **Circularity Mitigation**: The "Frozen Teacher" mechanism (updated every cycle) and explicit target definition (original real input) ensure the learning signal is not purely self-reinforcing.
5.  **Power Analysis**: The MDES of 0.08 ([deferred] absolute accuracy gain) for n=5 seeds is calculated to contextualize the statistical power of the experiment.
6.  **Scope**: T040-T044 are excluded as unapproved scope creep.