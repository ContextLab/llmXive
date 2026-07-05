# Research: Dendritic Computation in Transformers

## Overview

This research document outlines the strategy for implementing and evaluating dendritic computation in transformer architectures under strict CPU-only constraints. The primary goal is to determine if compartmentalized dendritic units provide a measurable advantage in hierarchical feature detection and sample efficiency compared to standard point-neuron designs.

## Dataset Strategy

The study utilizes the GLUE sentiment analysis benchmark. The dataset is sourced exclusively from verified, reachable URLs to ensure reproducibility and compliance with Constitution Principle II.

| Dataset | Purpose | Source URL | Access Method |
|---------|---------|------------|---------------|
| SST-2 (Train/Dev) | Model training and validation | ` | `datasets.load_dataset("SetFit/sst2")` |
| SST-2 (Test) | Final evaluation (held-out) | ` | `pandas.read_csv` |

**Rationale**: The `SetFit/sst2` dataset provides a standard, well-curated split for training and development. The `gpt3mix` test set is used for final evaluation to ensure a consistent benchmark across seeds. The `mamau` URL previously referenced was unreachable (HTTP 401) and has been excluded per validator feedback.

**Data Hygiene**:
- Raw downloads are checksummed and stored in `data/raw/glue_sst2/`.
- No modifications are made to raw files; preprocessing creates new files in `data/processed/`.
- PII checks are run before any data commit.

## Methodology

### 1. Architecture Design

**Baseline**: Standard Transformer Encoder (Point Neuron)
- Feedforward layers use standard linear projection + ReLU activation.
- Parameter count $N_{base}$ and FLOPs $F_{base}$ are calculated via `torchinfo`.

**Dendritic Variant**: Transformer with Compartmentalized Units
- Feedforward layers replaced by `DendriticLayer`.
- **Components**:
 - *Local Nonlinearities*: Sub-branches with distinct activation functions (e.g., sigmoid/tanh) simulating dendritic spikes.
 - *Plateau Potentials*: Gating mechanism integrating branch outputs via a global soma.
 - *Calcium Modulation*: A gating signal that modulates the strength of synaptic integration during the forward pass (and thus influences gradients via backpropagation), distinct from a purely logged metric.
- **Matching Constraint**: To ensure $|N_{base} - N_{dend}| < 0.1\%$ and $|F_{base} - F_{dend}| / F_{base} < 1\%$, the plan explicitly compensates for the dendritic overhead by **reducing the hidden dimension ($d_{model}$) or number of FFN neurons in the baseline's main trunk**. This ensures the 'dendritic' mechanism is tested at full capacity relative to a proportionally reduced baseline, avoiding a confound where performance differences are due to reduced capacity in the baseline rather than the dendritic mechanism.

### 2. Training Protocol

- **Hardware**: CPU-only (2 cores, 7GB RAM).
- **Duration**: Hard stop at 6 hours.
- **Optimization**: Identical AdamW schedule, batch size, and learning rate for both models.
- **Stability**: Gradient clipping (threshold $\le 1.0$) to prevent explosion from dendritic nonlinearities.
- **Seeds**: 3-5 independent random seeds for statistical power.

### 3. Probing & Analysis

- **Probing**: Linear classifiers trained on frozen intermediate layer representations (each layer individually) for syntactic/semantic tasks.
- **Metrics**:
 - **Sample Efficiency**: Steps to reach a **fixed absolute accuracy threshold** (e.g., 85% on SST-2), eliminating circular dependency on the baseline's variable final accuracy.
 - **Hierarchical Quality**: **Area Under Curve (AUC) of accuracy vs. depth**, interpreted as a measure of the *distribution* of feature quality across layers (not just a monotonic transformation), by comparing the shape of the curve (e.g., slope or curvature) in addition to area.
- **Statistical Tests**:
 - **Primary Endpoint**: Paired Wilcoxon signed-rank test on the **AUC** metric across seeds.
 - **Secondary Endpoint**: Paired Wilcoxon signed-rank test on **sample efficiency** (steps to fixed threshold).
 - **Per-Layer Tests**: Paired Wilcoxon signed-rank test on per-layer probing accuracy.
 - **Multiple Comparison Correction**: **Benjamini-Hochberg** procedure applied **only to the per-layer exploratory tests** to control family-wise error rate (FR-006). The primary AUC test is a single scalar per seed and does not require layer-wise correction.
- **Sensitivity Analysis**: Sweep of `dendritic_threshold` parameter over values **0.1 (low), 0.5 (moderate), 0.9 (high)** to measure effect size stability (FR-007).

## Statistical Power Considerations

With N=3 to 5 seeds, the statistical power to detect an effect size of d=0.5 using Wilcoxon is low (power < 0.2 for N=3). To mitigate the risk of Type II errors (false negatives), the analysis will:
1. Prioritize reporting **effect sizes (Cohen's d)** with **95% confidence intervals** over binary p-value significance.
2. Explicitly label results as "exploratory" if p-values are not significant, avoiding claims of "no effect" based on underpowered tests.
3. If feasible, increase seeds to 5 to improve power.

## Decision Rationale

**CPU Feasibility**:
- The dendritic mechanism is implemented as a differentiable sub-network using standard PyTorch operations (matrix multiplications, element-wise nonlinearities).
- No GPU-specific kernels or quantization are used.
- Data is subsampled if necessary to fit within 7GB RAM, ensuring the job completes within 6 hours.

**Statistical Rigor**:
- Multiple seeds (3-5) provide a baseline for variance estimation.
- Effect sizes and confidence intervals are prioritized to address low power limitations.
- Benjamini-Hochberg correction addresses the inflation of Type I errors inherent in layer-wise probing (secondary endpoint).
- Sample efficiency is defined against a fixed absolute threshold (85%) to ensure independent comparison.

**Dataset Verification**:
- Only verified URLs from the prompt are used. The unreachable `mamau` URL has been removed.
- `SetFit/sst2` is confirmed reachable and provides the necessary train/dev splits.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Gradient explosion in dendritic units | Gradient clipping ($\le 1.0$); logging of clipped frequency. |
| Training exceeds 6 hours | Hard timeout signal handler; report "incomplete" state. |
| Insufficient statistical power | Prioritize effect sizes; increase seeds to 5 if feasible; report "exploratory" status. |
| Dataset mismatch | Verify variable presence (tokens, labels) before training; use only verified URLs. |
| Circular sample efficiency metric | Use fixed absolute accuracy threshold (85%) instead of baseline-relative percentage. |