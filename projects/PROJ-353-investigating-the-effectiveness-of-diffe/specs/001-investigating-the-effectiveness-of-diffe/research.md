# Research: Investigating Loss Functions on Small-World Graphs

## Overview

This research phase validates the feasibility of the experimental design, confirms dataset availability (synthetic), and outlines the statistical strategy for the interaction analysis.

## Dataset Strategy

Since the study relies on **synthetic** data generated via the Watts-Strogatz model, no external dataset URLs are required or cited. The "dataset" is procedurally generated at runtime.

| Dataset Name | Source/Loader | Variables | Verification |
| :--- | :--- | :--- | :--- |
| **Synthetic Watts-Strogatz** | `networkx.generators.random_graphs.watts_strogatz_graph` | `rewiring_probability` ($\beta$), `clustering_coefficient`, `node_count`, `edge_list`, `community_labels` | Verified via `networkx` documentation and theoretical properties of WS graphs. |

**Dataset Variable Fit**:
- **Required**: Rewiring probability ($\beta$), Clustering coefficient, Community labels, Node features (degree/position).
- **Available**: `networkx` generates $\beta$ and the graph structure. Clustering coefficient is computed post-generation. Labels are derived from the initial ring lattice indices (before rewiring), ensuring a known ground truth that degrades in separability as $\beta$ increases.
- **Fit**: Perfect. The synthetic generator allows precise control over $\beta$ (0.0 to 1.0) which is the primary independent variable.

## Methodology & Statistical Rigor

### Experimental Design
1.  **Independent Variables**:
    -   `loss_type`: Categorical (Cross-Entropy, InfoNCE).
    -   `beta`: Continuous (0.0, 0.1, ..., 1.0).
2.  **Dependent Variable**:
 - `steps_to_convergence`: Number of epochs to reach $\ge$ [deferred] accuracy (censored at 1000).
3.  **Model**:
    -   **ANCOVA**: `steps ~ loss_type * beta + covariates`.
    -   **Interaction Term**: `loss_type * beta` tests if the slope of convergence speed vs. $\beta$ differs between loss functions.

### Statistical Rigor (Addressing Methodological Panel Concerns)

1.  **Multiple-Comparison Correction (FR-008)**:
    -   We perform two Pearson correlations (one per loss type) and one ANCOVA interaction test.
    -   **Method**: Bonferroni correction will be applied to the set of primary tests.
    -   **Threshold**: $\alpha_{corrected} = 0.05 / 3 \approx 0.0167$.
    -   **Implementation**: `statsmodels.stats.multitest.multipletests` (method='bonferroni').

2.  **Sample Size / Power Justification (FR-010)**:
    -   **Target**: Detect a moderate interaction effect ($f^2 = 0.15$) with power $1-\beta = 0.80$.
    -   **Calculation**: Using G*Power logic for ANCOVA (Interaction: Fixed effects, special, main effects and interaction).
    -   **Parameters**: $\alpha = 0.05$, 2 groups (loss types), 1 covariate ($\beta$).
    -   **Result**: $N \approx 40$ is required for moderate effect. We plan for **50 graphs** (25 per loss type distribution across $\beta$) to provide a buffer for censored runs (non-convergence).
    -   **Limitation Acknowledgement**: If the effect is small ($f^2 < 0.05$), 50 samples may be underpowered. The report will explicitly state the achieved power for the observed effect size.

3.  **Causal Inference & Observational Nature**:
    -   This is a **controlled simulation**, not an observational study. The "randomization" is the random seed for graph generation and the assignment of $\beta$.
    -   Claims are limited to the synthetic domain: "In Watts-Strogatz graphs, X loss converges faster as $\beta$ increases." No causal claims about real-world social networks are made.

4.  **Measurement Validity**:
 - **Convergence**: Defined as $\ge$ [deferred] accuracy. This is a standard proxy for "learning" in classification tasks.
    -   **Topology**: Clustering coefficient is the canonical metric for small-worldness.
    -   **Loss Functions**: Cross-Entropy is the standard supervised baseline. InfoNCE is the standard contrastive objective.

5.  **Predictor Collinearity**:
    -   $\beta$ and Clustering Coefficient are definitionally related (higher $\beta$ $\to$ lower clustering).
    -   **Handling**: We use $\beta$ as the primary continuous predictor in the ANCOVA. We will **not** include both $\beta$ and clustering coefficient as simultaneous predictors to avoid perfect multicollinearity. We will report the correlation between $\beta$ and clustering as a descriptive statistic.

## Compute Feasibility

-   **Hardware**: 2 CPU cores, 7GB RAM.
-   **Load**: 50 graphs $\times$ 2 losses = 100 training runs.
-   **Model**: 2-layer GCN, $N=100$ nodes.
    -   Parameters: $\approx 100 \times 16 \times 2 + 16 \times 2 \approx 3.2k$ params. Extremely lightweight.
-   **Runtime Estimate**:
    -   Each epoch: < 0.1s (CPU).
    -   Max epochs: A sufficient number to ensure convergence.
    -   Worst case per run: bounded by a constant duration.
    -   Total worst case: $100 \times 100s = 10,000s \approx 2.7$ hours.
    -   **Buffer**: Fits comfortably within the GitHub Actions time limit.
-   **Memory**: Graphs are tiny (100 nodes). Tensors are small. Total memory usage < 500MB.

## Decision Rationale

-   **Why InfoNCE?** It is the standard contrastive loss for graph embeddings. It forces the model to learn structural invariances without explicit labels during the encoder phase.
-   **Why Linear Probe?** To fairly compare with Cross-Entropy (which uses labels during training), we must evaluate the *quality* of the InfoNCE embeddings using a supervised head.
-   **Why Watts-Strogatz?** It provides a continuous, controllable knob ($\beta$) to transition from a regular lattice (high clustering) to a random graph (low clustering), exactly matching the research question's need to isolate topology effects.
