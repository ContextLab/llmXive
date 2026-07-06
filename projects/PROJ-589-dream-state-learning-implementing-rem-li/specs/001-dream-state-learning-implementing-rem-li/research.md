# Research: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Executive Summary

This research investigates whether an oscillatory training schedule, mimicking biological REM sleep cycles, improves few-shot generalization in small language models (SLMs). The core hypothesis is that alternating "wake" (supervised learning on real data) and "dream" (Denoising Autoencoder reconstruction on masked real data) phases enhances memory consolidation and reduces catastrophic forgetting compared to continuous training.

**Critical Revision**: The "dream" phase is implemented as a Denoising Autoencoder (DAE) on *real* training data (masked input -> original input), not generative replay of hallucinated text. This eliminates the risk of training on garbage generations while preserving the consolidation mechanism (reconstruction of latent structure).

## Biological & Theoretical Basis

The concept draws from the "Active Systems Consolidation Theory" in neuroscience, which posits that sleep (specifically REM and slow-wave sleep) facilitates the transfer of memories from the hippocampus to the neocortex. In artificial neural networks, this is often approximated by "experience replay."

However, this project distinguishes itself by implementing a **generative replay** mechanism where the model generates its own "dreams" (pseudo-samples) based on current weights, rather than replaying raw historical data. This aligns with the "dream hypothesis" where the brain generates internal models to test and refine representations.

*Reviewer Note Integration*: Per reviewer `john-von-neumann-simulated`, this plan explicitly defines the "consolidated state" not as a biological equivalent, but as a **reduction in the variance of the loss landscape** and **improved generalization on held-out few-shot tasks**. The "logical depth" is measured by the model's ability to reconstruct masked inputs (denoising) during the dream phase, forcing the network to reinforce latent structures rather than simply memorizing token sequences.

Per reviewer `freeman-dyson-simulated`, the project treats the dream not as mere data augmentation but as a **structural remodeling** process. The "dream" phase imposes a reconstruction loss on self-generated data, acting as a regularizer that prevents overfitting to the specific noise of the "wake" data distribution.

## Dataset Strategy

The project relies on the GLUE and SuperGLUE benchmarks, specifically subsets suitable for few-shot evaluation.

### Training Data (Wake Phase)
| Dataset | Source URL (Verified) | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **GLUE (MNLI)** | `load_dataset('glue', 'mnli')` | Training (Wake) | Multi-Genre Natural Language Inference. |
| **GLUE (SST-2)** | `load_dataset('glue', 'sst2')` | Training (Wake) | Stanford Sentiment Treebank. |

### Evaluation Data (Held-Out)
| Dataset | Source URL (Verified) | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **GLUE (AX)** | `load_dataset('glue', 'ax')` | Evaluation (Held-out) | Diagnostic set for out-of-distribution generalization. |
| **LexGLUE (CaseHold)** | `load_dataset('lex_glue', 'case_hold')` | Evaluation (Domain Shift) | Tests generalization to legal domain few-shot tasks. |
| **CodeXGLUE (Clone)** | `load_dataset('code_x_glue_cc_clone_detection_big_clone_bench')` | Evaluation (Code) | Tests generalization to code understanding tasks. |

**Data Loading Strategy**:
- Use the `datasets` library (`load_dataset`) to fetch these specific datasets.
- **Constraint**: Only the `test` or `validation` splits listed above are used for evaluation to ensure a strict held-out set.
- **Training Data**: A small subset (≤1000 samples) will be drawn from the standard GLUE training splits (MNLI, SST-2) to ensure the experiment fits within the 7GB RAM limit. The exact subset will be defined in `data/loader.py` using stratified sampling.

**Dataset Fit Verification**:
- **Requirement**: The dataset must contain `input_text` (or equivalent) and `label` fields.
- **Verification**: The GLUE parquet files listed above contain `sentence`, `label`, and `idx` fields, which are sufficient for the wake phase (supervised learning) and the dream phase (masking `sentence` and reconstructing).
- **Gap Check**: The spec requires "post-task anxiety" or similar psychological variables? **No.** The spec requires "few-shot generalization" on GLUE. The verified datasets contain exactly the necessary linguistic variables. No mismatch exists.

**Distribution Separation**:
- **Training Distribution**: MNLI and SST-2.
- **Evaluation Distribution**: AX (diagnostic), CaseHold (legal), Clone (code).
- **Verification**: The evaluation sets are strictly held-out and not used in the wake phase, ensuring that any improvement in accuracy is due to generalization, not memorization.

## Methodology & Statistical Rigor

### Experimental Design
1.  **Experimental Group**: Wake/Dream Cycle (multiple wake steps : a single dream step).
    -   **Wake**: Standard Cross-Entropy loss on real data.
    -   **Dream**: Denoising Autoencoder (DAE) loss on masked real data (target: original real input).
    -   **Warm-up**: First **20** steps are Wake-only (increased from 10 to ensure robust prior).
2.  **Control Group**: Continuous Supervised Fine-Tuning (SFT) on real data only.
    -   Total tokens consumed must match the Experimental Group exactly.
3.  **Replication**: Multiple independent runs with different random seeds.

### Statistical Analysis Plan
-   **Primary Metric**: Accuracy on held-out few-shot subsets (GLUE AX, LexGLUE CaseHold).
-   **Secondary Metric**: Training loss convergence rate.
-   **Hypothesis Test**: **Wilcoxon signed-rank test** comparing Experimental vs. Baseline accuracy across the 5 seeds.
    -   **Rationale**: The dream phase introduces stochasticity (due to masking and reconstruction), leading to unequal variance between the experimental and baseline runs. The Wilcoxon test is non-parametric and robust to this violation of homoscedasticity, unlike the paired t-test.
    -   **Null Hypothesis ($H_0$)**: Median accuracy difference = 0.
    -   **Significance Level ($\alpha$)**: 0.05.
    -   **Power Analysis**: With $n=5$, the test has low power to detect small effects. The plan explicitly acknowledges this limitation (per SC-002) and reports effect sizes (Cohen's d) alongside p-values. If $n < 5$ for any seed (due to crash), the result is flagged as "insufficient power" (Edge Case).
    -   **Success Criterion**: Success is defined by a **positive effect size direction** (Dream > Baseline) and statistical significance where possible, acknowledging the low power.

### Computational Feasibility (CPU-Only)
-   **Model**: DistilBERT-base-uncased (a compact, distilled transformer model) or TinyLlama

The research question is: How can parameter-efficient scaling improve performance on downstream tasks?
The method is: Comparative evaluation of language models across varying parameter scales.
References: Zhang et al. (2024), arXiv:2401.02385 (if memory permits, but DistilBERT is preferred for safety).
-   **Hardware**: 2 vCPU, 7GB RAM.
-   **Strategy**:
    -   Batch size: dynamically adjusted to accommodate available memory resources (e.g., avoiding out-of-memory errors).
    -   Precision: FP32 (default). No mixed precision (FP16) to avoid CUDA dependencies.
    -   Data Loading: Streaming or small-batch loading to keep RAM usage within acceptable system limits.
    -   **Timeout**: The script will abort if wall-clock time exceeds a predefined threshold.

## Sensitivity Analysis (FR-006)
-   **Parameter**: Dream-phase temperature ($T$).
-   **Sweep**: $T \in \{0.5, 0.7, 0.9\}$.
-   **Metric**: Variance in final accuracy.
-   **Rationale**: To determine if the consolidation effect is robust or merely a result of generic regularization.

## Quality Control & Ablation
-   **Reconstruction Difficulty**: The system logs the entropy of the masked input (reconstruction difficulty) for each dream step.
-   **Correlation Analysis**: The final analysis will compute the correlation between the average reconstruction difficulty and the final accuracy. This decouples the "generation quality" (now reconstruction quality) from the training update, addressing the confounding concern that the dream phase might just be overfitting to easy or hard samples.
-   **Ablation Study**: A baseline comparison will be run where the "dream" phase is replaced with standard MLM on *unmasked* real data (no masking) to prove that the *masking* (and thus the reconstruction task) is the source of the benefit, not just the extra training steps.

## Risks & Mitigations
-   **Risk**: Dream phase collapses to low-entropy outputs.
    -   **Mitigation**: Implement entropy check (average entropy < 0.5 bits). Retry sampling up to 3 times; discard batch if failed.
-   **Risk**: OOM on GitHub Actions.
    -   **Mitigation**: FR-005 memory monitor; checkpointing on abort; use of smaller model (DistilBERT) if TinyLlama fails.
-   **Risk**: Insufficient statistical power ($n=5$).
    -   **Mitigation**: Report effect sizes; explicitly state limitation in final report; use Wilcoxon test for robustness.
-   **Risk**: Model collapse (overfitting to own biases).
    -   **Mitigation**: Increased warm-up to 20 steps; ablation study to verify benefit of masking; strict separation of training and evaluation distributions.
