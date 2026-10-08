# Research Documentation: Investigating Loss Functions on Small-World Graphs

## Project Overview
This research project investigates the effectiveness of different loss functions, specifically **InfoNCE** (contrastive) versus **Cross-Entropy (CE)**, in training Graph Neural Networks (GNNs) on small-world graph topologies. The study focuses on how the rewiring probability ($\beta$) in Watts-Strogatz graphs influences convergence speed and final model performance.

## Primary Hypothesis
**H1**: The contrastive loss function (InfoNCE) will demonstrate significantly faster convergence (fewer epochs to reach the accuracy threshold) compared to Cross-Entropy (CE) loss as the small-world parameter $\beta$ increases.

**H0**: There is no significant difference in the convergence speed between InfoNCE and CE loss functions across the spectrum of $\beta$ values.

## Research Questions
1. How does the rewiring probability $\beta$ (ranging from 0.0 to 1.0) affect the number of epochs required for a GCN to converge on a node classification task?
2. Is there a statistically significant interaction effect between the loss function type (InfoNCE vs. CE) and the graph topology parameter $\beta$ on convergence steps?
3. Does the contrastive nature of InfoNCE provide a robustness advantage in highly randomized (high $\beta$) graph structures compared to standard supervised learning?

## Methodology

### 1. Data Generation
- **Graph Model**: Watts-Strogatz small-world network.
- **Parameters**:
 - $N = 110$ (Total sample size, derived from power analysis).
 - $k$ (Initial neighbors): Fixed based on standard small-world construction.
 - $\beta$ (Rewiring probability): Explicitly enumerated levels: `[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]`.
 - **Sampling**: 10 graphs generated per $\beta$ level.
- **Labels**: Community labels derived from the initial ring lattice before rewiring.
- **Validation**: Graphs are validated for connectivity and clustering coefficient bounds. Disconnected graphs are regenerated.

### 2. Experimental Protocol
- **Model**: Multi-layer Graph Convolutional Network (GCN).
- **Training**:
 - Two separate training runs per graph: one with Cross-Entropy loss, one with InfoNCE loss.
 - **Seed Control**: Random seeds are reset to a common value between loss types for the same graph to isolate the loss function effect.
 - **Convergence Threshold**: Accuracy $\ge 0.90$.
 - **Max Epochs**: 1000.
- **Censoring**: Runs that do not reach the convergence threshold within `MAX_EPOCHS` are marked as "censored" (right-censored data).

### 3. Statistical Analysis
The analysis employs survival analysis techniques to handle the censored data naturally arising from the max-epoch limit.

#### A. Tobit Regression
- **Purpose**: To model the latent "true" convergence time while accounting for the upper censoring limit.
- **Model**: `steps_to_convergence ~ C(loss_type) * beta`
- **Censoring Bounds**: Lower = 0, Upper = `MAX_EPOCHS` (1000).
- **Library**: `lifelines.TobitFitter`.
- **Target Metric**: The p-value of the interaction term between `loss_type` and `beta`.

#### B. Cox Proportional Hazards Model
- **Purpose**: To estimate the hazard ratio of converging at any given step, comparing the two loss functions across varying topologies.
- **Model**: `steps_to_convergence ~ C(loss_type) * beta`
- **Event Definition**: `event = 1` if converged, `event = 0` if censored.
- **Library**: `lifelines.CoxPHFitter`.
- **Target Metric**: The p-value of the interaction term hazard ratio.

### 4. Significance Testing
- **Multiple Comparison Correction**: Bonferroni correction will be applied to the interaction p-values from both models ($n=2$ tests).
- **Significance Level**: $\alpha = 0.05$.
- **Decision Rule**: If the corrected minimum p-value is $< 0.05$, we reject the null hypothesis and conclude that the effectiveness of the loss function depends on the graph topology ($\beta$).

## Expected Deliverables
1. **Raw Data**: `data/raw/graphs.jsonl` containing 110 annotated graphs.
2. **Training Trajectories**: Per-run JSON files in `data/processed/trajectories/`.
3. **Aggregated Results**: `data/processed/convergence_logs.csv`.
4. **Statistical Results**: `data/analysis_results.json` containing interaction p-values and significance flags.
5. **Final Report**: `data/report.md` summarizing the findings regarding the hypothesis.