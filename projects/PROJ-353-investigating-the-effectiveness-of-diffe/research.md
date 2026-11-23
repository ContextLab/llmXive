# Research Questions and Methodology

## Project: Investigating the Effectiveness of Contrastive Loss on Small-World Graphs

### Primary Research Question
Does the use of contrastive learning (InfoNCE loss) lead to faster convergence and better generalization on node classification tasks compared to standard supervised learning (Cross-Entropy loss) as the graph topology transitions from regular lattice to random graph (varying rewiring probability $\beta$)?

### Secondary Questions
1. How does the clustering coefficient of the underlying graph structure correlate with the convergence speed of different loss functions?
2. Is there a statistically significant interaction effect between the graph rewiring parameter ($\beta$) and the loss function type on the number of steps to convergence?
3. Do contrastive methods exhibit different resilience to censored data (training runs that do not converge within the maximum epoch limit) compared to supervised methods?

### Methodology Summary

#### 1. Data Generation (Synthetic Graphs)
- **Model**: Watts-Strogatz small-world network model.
- **Parameters**:
 - $N = 110$ graphs total.
 - Rewiring probability $\beta \in [0.0, 1.0]$ with 10 distinct levels.
 - 11 graphs per $\beta$ level (to reach $N=110$).
 - Fixed node count and initial degree per spec constraints.
- **Labeling**: Community labels derived from the initial lattice structure before rewiring to preserve ground-truth community structure.
- **Validation**: Ensure no disconnected components and balanced class distribution (<80% max class ratio).

#### 2. Model Architecture & Training
- **Architecture**: 2-Layer Graph Convolutional Network (GCN).
- **Loss Functions**:
 - **Supervised**: Cross-Entropy Loss (standard node classification).
 - **Contrastive**: InfoNCE Loss (instance-level contrastive) + Linear Probe for accuracy measurement.
- **Training Protocol**:
 - CPU-only execution.
 - Maximum Epochs ($T_{max}$) = 1000.
 - Convergence Threshold: Accuracy $\ge 0.90$.
 - **Censoring**: Runs not reaching threshold by $T_{max}$ are flagged as censored.
- **Metrics**: Per-epoch loss, accuracy, steps to convergence, convergence status.

#### 3. Statistical Analysis
- **Objective**: Test the interaction between graph topology ($\beta$) and loss type on convergence time.
- **Models**:
 1. **Tobit Regression**: To handle censored convergence data.
 - Formula: `steps_to_convergence ~ C(loss_type) * beta`
 2. **Cox Proportional Hazards**: Survival analysis for time-to-convergence.
 - Formula: `steps_to_convergence ~ C(loss_type) * beta`
- **Correction**: Bonferroni correction applied to interaction p-values from both models.
- **Significance**: Interaction is significant if corrected $p < 0.05$.

### Constraints & Assumptions
- Sample size is fixed at $N=110` (Spec FR-001).
- All experiments run on CPU to ensure reproducibility across hardware.
- No early stopping based on loss plateaus; strict epoch limits apply.
- Data generation uses seeded random processes for reproducibility.