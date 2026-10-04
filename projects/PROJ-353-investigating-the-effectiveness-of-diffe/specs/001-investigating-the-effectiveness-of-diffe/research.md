# Research Documentation: Investigating Loss Functions on Small-World Graphs

## Project Overview
This research project investigates the effectiveness of contrastive learning (InfoNCE loss) versus standard classification (Cross-Entropy loss) when training Graph Neural Networks (GNNs) on small-world graph structures. Specifically, we examine how the rewiring probability ($\beta$) in Watts-Strogatz small-world graphs influences the convergence speed and final performance of these two loss functions.

## Hypothesis
**Primary Hypothesis**: InfoNCE loss will demonstrate faster convergence (fewer epochs to reach the accuracy threshold) compared to Cross-Entropy (CE) loss as the small-world parameter $\beta$ increases.

**Rationale**:
- **Low $\beta$ (Regular Lattices)**: High clustering and long path lengths may make local neighborhood aggregation (CE) sufficient, potentially reducing the advantage of contrastive methods.
- **High $\beta$ (Random Graphs)**: Short path lengths and lower clustering may benefit from the global structural invariance learned by InfoNCE, leading to faster convergence.
- **Small-World Regime ($\beta \approx 0.1$)**: This regime maximizes the trade-off between local clustering and global connectivity. We hypothesize that the interaction between loss type and $\beta$ is most pronounced here, where structural complexity is highest.

## Methodology

### 1. Data Generation
- **Graph Model**: Watts-Strogatz small-world model.
- **Parameters**:
 - $N = 110$ graphs (derived from power analysis for statistical significance).
 - $\beta$ levels: Discrete set $\{0.0, 0.1, 0.2, \dots, 1.0\}$.
 - 10 graph instances per $\beta$ level.
- **Validation**:
 - Ensure all graphs are connected (regenerate if disconnected).
 - Verify clustering coefficients fall within theoretical bounds.
 - Ensure class balance (<80% max class frequency) via community label derivation from the initial lattice.

### 2. Training Protocol
- **Model**: 2-layer Graph Convolutional Network (GCN).
- **Loss Functions**:
 - **Cross-Entropy (CE)**: Standard supervised node classification.
 - **InfoNCE**: Contrastive loss with a linear probe for accuracy measurement.
- **Constraints**:
 - CPU-only execution.
 - Fixed random seeds for reproducibility (reset between loss runs on the same graph).
 - Maximum epochs: $MAX\_EPOCHS = 1000$.
 - Convergence threshold: $ACCURACY \ge 0.90$.
- **Censoring**: Runs failing to converge by $MAX\_EPOCHS$ are flagged as "censored" for survival analysis.

### 3. Statistical Analysis
The core analysis focuses on the **interaction effect** between the loss type and the graph topology ($\beta$) on the "time" to convergence (steps to convergence).

#### A. Tobit Regression
- **Purpose**: Model censored dependent variables (steps to convergence).
- **Model**: $Steps \sim C(loss\_type) \times \beta + \epsilon$
- **Censoring Limits**: Lower bound = 0, Upper bound = $MAX\_EPOCHS$.
- **Target**: Extract the p-value for the interaction term ($loss\_type: \beta$).

#### B. Cox Proportional Hazards Model
- **Purpose**: Survival analysis to compare the "hazard" of converging between loss types across different $\beta$ values.
- **Model**: $h(t) = h_0(t) \exp(\beta_1 \cdot loss\_type + \beta_2 \cdot \beta + \beta_3 \cdot (loss\_type \times \beta))$
- **Event Definition**: Convergence (1) vs. Censoring (0).
- **Target**: Extract the hazard ratio and p-value for the interaction term.

### 4. Significance Testing
- **Correction**: Bonferroni correction applied for multiple comparisons ($n=2$ tests: Tobit interaction p-value, Cox interaction p-value).
- **Decision Rule**: The hypothesis is supported if the minimum of the two corrected p-values is $< 0.05$.

## Expected Deliverables
1. `data/raw/graphs.jsonl`: Validated small-world graph dataset.
2. `data/processed/trajectories/`: Per-run training logs with convergence status.
3. `data/processed/convergence_logs.csv`: Aggregated scalar metrics.
4. `data/analysis_results.json`: Statistical results including interaction p-values and significance flag.
5. `data/report.md`: Final interpretation of results.