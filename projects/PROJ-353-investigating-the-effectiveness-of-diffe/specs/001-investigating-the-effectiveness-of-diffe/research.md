# Research Questions and Methodology

## Project Overview

This research investigates the effectiveness of contrastive learning (InfoNCE) versus standard supervised learning (Cross-Entropy) on small-world graph topologies. The study aims to determine whether the structural properties of small-world graphs (specifically the rewiring probability $\beta$) interact with loss function choice to influence convergence speed and final model performance.

## Research Questions

1. **Primary Question**: Does the use of InfoNCE loss lead to faster convergence compared to Cross-Entropy loss on Watts-Strogatz small-world graphs, and does this effect vary with the rewiring probability $\beta$?
2. **Secondary Question**: Is there a statistically significant interaction between the graph topology parameter $\beta$ and the loss function type on the number of steps required to reach the convergence threshold?
3. **Tertiary Question**: How does the censorship of training runs (those failing to converge within `MAX_EPOCHS`) affect the statistical inference regarding loss function efficacy?

## Hypothesis

**H1 (Main Effect)**: InfoNCE loss will demonstrate a lower mean steps-to-convergence compared to Cross-Entropy loss across the sample of graphs.

**H2 (Interaction Effect)**: The performance advantage of InfoNCE over Cross-Entropy will be modulated by the small-world parameter $\beta$. Specifically, we hypothesize that the contrastive approach will be more robust (or show a different convergence trajectory) as the graph transitions from a regular lattice ($\beta \approx 0$) to a random graph ($\beta \approx 1$), potentially exploiting the "short path" property differently than supervised classification.

**Null Hypothesis ($H_0$)**: There is no interaction between loss type and $\beta$ on convergence steps; any observed differences are due to random variation.

## Methodology

### Data Generation
- **Graph Model**: Watts-Strogatz small-world network.
- **Parameters**:
 - Node count ($N$): Fixed at 110 (derived from power analysis, see `code/power_analysis.py`).
 - Rewiring probability ($\beta$): 11 levels uniformly distributed from 0.0 to 1.0.
 - Replicates: 10 independent graphs per $\beta$ level (Total $N=110$).
- **Labels**: Community labels derived from the initial ring lattice structure before rewiring, ensuring a ground truth that is structurally defined.

### Experimental Procedure
1. **Model Architecture**: A 2-layer Graph Convolutional Network (GCN) as defined in `code/models.py`.
2. **Training Regimes**:
 - **Cross-Entropy (CE)**: Standard supervised node classification.
 - **InfoNCE**: Contrastive learning followed by a linear probe for accuracy measurement (as per US-2).
3. **Stopping Criteria**:
 - **Convergence**: Accuracy $\ge$ `CONVERGENCE_THRESHOLD` (0.90).
 - **Censoring**: Maximum epochs (`MAX_EPOCHS` = 1000) reached without convergence.
4. **Data Recording**: Full per-epoch loss and accuracy trajectories are stored in `data/processed/trajectories/`.

### Statistical Analysis Plan

To address the censored nature of the data (some runs do not converge), standard linear regression is inappropriate. We employ two complementary survival analysis techniques:

1. **Tobit Regression**:
 - **Model**: `steps_to_convergence ~ C(loss_type) * beta`
 - **Purpose**: To estimate the effect of loss type and $\beta$ on convergence time while accounting for right-censoring at `MAX_EPOCHS`.
 - **Implementation**: `statsmodels.discrete.discrete_model.Tobit`.

2. **Cox Proportional Hazards Model**:
 - **Model**: `steps_to_convergence ~ C(loss_type) * beta`
 - **Purpose**: To model the hazard rate of convergence, providing a hazard ratio for the interaction term. This offers a non-parametric check on the Tobit assumptions.
 - **Implementation**: `lifelines.CoxPHFitter`.

### Significance Testing
- **Interaction Term**: The primary test is the significance of the interaction term ($\beta \times \text{loss\_type}$) in both models.
- **Correction**: Bonferroni correction will be applied to the p-values of the two primary tests (Tobit and Cox) to control for family-wise error rate ($\alpha_{corrected} = 0.05 / 2$).
- **Decision Rule**: If the corrected p-value for the interaction term is $< 0.05$, we reject the null hypothesis and conclude that the effectiveness of the loss function depends on the small-world topology.

## Expected Deliverables
- `data/raw/graphs.jsonl`: Generated synthetic graph data.
- `data/processed/trajectories/`: Per-run training logs.
- `data/processed/convergence_logs.csv`: Aggregated scalar data for analysis.
- `data/analysis_results.json`: Statistical results including coefficients, p-values, and significance flags.
- `data/report.md`: Final narrative report interpreting the statistical findings.