# Research: Dendritic Computation in Transformers

## Overview

This research phase investigates the hypothesis that biologically inspired dendritic compartmentalization (local nonlinearities, plateau potentials) improves hierarchical feature detection in transformers compared to standard point-neuron designs, under strict computational parity.

## Dataset Strategy

The study utilizes the **GLUE SST-2** (Stanford Sentiment Treebank v2) benchmark for the primary training task. This dataset provides binary sentiment classification (positive/negative) for movie reviews. While SST-2 is a semantic task, it is used here as a standard benchmark for training efficiency. To specifically address the "hierarchical feature detection" hypothesis (which SST-2 alone may not fully stress), the probing pipeline will include **syntactic probing tasks** (e.g., Part-of-Speech tagging, subject-verb agreement) on intermediate representations. This ensures the construct validity of measuring hierarchical capabilities.

| Dataset | Description | Source / Loader | Variables |
|:--- |:--- |:--- |:--- |
| **SST-2** | Binary sentiment classification. | `datasets.load_dataset("SetFit/sst2")` (Verified: `) | `sentence` (input tokens), `label` (0/1) |
| **GLUE (Aux)** | Validation split for GLUE tasks. | `datasets.load_dataset("nyu-mll/glue", "sst2")` (Verified: `) | `sentence`, `label` |
| **Synthetic Syntax** | Synthetic POS/Agreement probes (generated in-code). | N/A (Generated via `code/data/synthetic_probes.py`) | `tokens`, `pos_labels`, `agreement_labels` |

**Dataset Fit Confirmation**:
- The SST-2 dataset contains the necessary variables: input text (`sentence`) and binary labels (`label`).
- No external covariates (e.g., post-task anxiety) are required for this specific NLP task; the "variables" are the token embeddings and the target label.
- The dataset is small enough to be processed entirely in RAM on a memory-constrained runner.
- Synthetic probes are generated to ensure the hierarchical analysis is not limited to the shallow semantic nature of SST-2.

**Constraint Note**: The spec assumes "GLUE SST-2" is available. The verified URLs above confirm the existence of the data. We will use the `SetFit/sst2` loader as it provides a clean, pre-tokenized interface suitable for rapid CPU training.

## Dendritic Mechanism Formulation

To address the "logical economy" critique (Von Neumann) and ensure the mechanism is distinct from mere parameter depth (Von Neumann/Wolfram), the dendritic unit is defined as follows:

1. **Compartmentalization**: Instead of a single linear projection $W x + b$ followed by a nonlinearity $\sigma(\cdot)$, the feedforward layer is replaced by $K$ parallel "dendritic branches".
2. **Local Nonlinearity**: Each branch $k$ computes a local activation: $h_k = \sigma(W_k x + b_k)$.
3. **Plateau Potential Gating**: A global gating signal $g$ (derived from the soma's aggregate input) modulates the branch outputs. The final output is $\sum_k g_k \cdot h_k$, where $g_k$ is a sigmoidal function of the local branch sum (simulating calcium-dependent plateau potentials).
4. **Parameter Matching**: The total number of parameters in the $K$ branches and the gating mechanism is strictly constrained to equal the parameter count of the standard 2-layer MLP it replaces.
5. **FLOP Compensation**: The gating mechanism introduces additional non-linear operations (sigmoid, element-wise multiply). To maintain the <1% FLOP match (FR-002), the width of the linear projections in the dendritic branches will be slightly reduced to offset the computational cost of the gating logic.

**Rationale**: This design introduces *nonlinear logic* (branch-specific gating) rather than just *depth*. It directly tests the hypothesis that local, compartmentalized processing aids hierarchical feature detection.

## Experimental Design

### Phase 1: Architecture Matching (US-1)
- **Goal**: Instantiate `TransformerBaseline` and `TransformerDendritic`.
- **Method**: Calculate parameters and theoretical FLOPs using a custom counter that explicitly weights non-linear gates (1 FLOP) and matrix multiplications (2*H*W).
- **Success Criteria**: Parameter difference < 0.1%; FLOP difference < 1% (including gating overhead).
- **Fallback**: If FLOPs differ, adjust the width of the dendritic branches or the gating mechanism until matched.

### Phase 2: Training (US-2)
- **Hardware**: 2 CPU cores, 7GB RAM.
- **Timeout**: Hard stop at 6 hours.
- **Optimizer**: AdamW (learning rate scheduled).
- **Batch Size**: Dynamically adjusted (e.g., 8 or 16) to fit RAM.
- **Seeds**: 3 to 5 random seeds.
- **Metrics**: Accuracy, Loss (logged every 100 steps).
- **Stability**: Gradient clipping (threshold 1.0) to handle potential dendritic nonlinearity explosions.
- **Fallback Strategy**: If the 6-hour limit is reached before convergence, the run is marked "incomplete". The primary metric shifts from "steps to convergence" to "performance at fixed wall-clock time T". A paired t-test will be performed on the final state (accuracy at T) across seeds. If N < 3, the study will report the result as "inconclusive" rather than attempting an invalid statistical test.

### Phase 3: Probing & Analysis (US-3)
- **Probing**: Train linear classifiers on frozen representations from *every* intermediate layer.
- **Tasks**: Binary classification (sentiment) on the probing head, plus synthetic syntactic probes (POS, agreement).
- **Statistics**:
 - **Paired Test**: Paired t-test (with Welch's correction if variances differ) across seeds for each layer. (Wilcoxon is avoided as it lacks power for N < 5).
 - **Correction**: Benjamini-Hochberg (FDR) correction for multiple comparisons (across layers) to control the false discovery rate while maintaining statistical power.
 - **Effect Size**: Cohen's $d$.
- **Sensitivity**: Sweep dendritic threshold (low, medium, high) to check robustness (FR-007).

## Statistical Rigor & Methodology

- **Multiple Comparisons**: Per FR-006, **Benjamini-Hochberg (FDR)** correction will be applied to the per-layer p-values. This is chosen over Bonferroni to mitigate the high risk of Type II errors (false negatives) inherent in small-sample studies (N=3-5) with many comparisons (layers). Bonferroni would divide alpha by the number of layers, rendering the test virtually powerless.
- **Power Analysis**: With 3-5 seeds, the power to detect a large effect size ($d \ge 0.8$) is moderate. The study will explicitly report the power limitation if the effect size is small. The use of a paired t-test is preferred over Wilcoxon for N=3-5 as it has higher power if normality assumptions are approximately met (which is reasonable for accuracy metrics across seeds).
- **Causal Claims**: Claims will be framed as *associational* improvements in feature quality, not causal mechanisms of brain function. The "randomization" is the random seed and weight initialization.
- **Collinearity**: The dendritic branches are derived from the same input $x$. We will not claim "independent" effects of branches but rather the *aggregate* benefit of the compartmentalized structure.

## Compute Feasibility

- **Model Size**: We will use a small transformer (e.g., a few layers, reduced hidden size) to ensure the 6-hour limit is respected on CPU.
- **Data Subset**: If full training is too slow, we will use a subset of SST-2 for the initial sweep, with the full set for the final seed run.
- **Libraries**: `torch` (CPU), `scikit-learn` (probing). No CUDA, no 8-bit quantization.
- **Memory**: Data is loaded in batches. Intermediate activations are saved only for probing (not all at once) to stay under 7GB.