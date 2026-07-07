# Specification: Investigating the Effectiveness of Contrastive Loss on Small-World Graphs

## 1. Introduction

This project investigates the impact of network topology (specifically the small-world parameter $\beta$) on the convergence speed of Graph Neural Networks (GNNs) trained with Contrastive Loss (InfoNCE) versus standard Cross-Entropy loss.

## 2. Functional Requirements

### FR-001: Graph Generation
The system must generate 110 synthetic Watts-Strogatz graphs.
- **Parameters**:
 - $N=110$ nodes per graph.
 - $k=6$ (initial nearest neighbors).
 - $\beta$ (rewiring probability) ranges from 0.0 to 1.0 in steps of 0.1.
 - **Sample Size**: 10 graphs per $\beta$ level (Total $10 \times 11 = 110$).
- **Output**: Graphs must be saved in `data/raw/graphs.jsonl` with metadata including the specific $\beta$ used.

### FR-002: Node Labeling
Nodes must be annotated with community labels derived from the initial ring lattice structure before rewiring occurs to ensure ground-truth community structure exists.

### FR-003: Model Architecture
The system must implement a 2-layer Graph Convolutional Network (GCN) compatible with CPU execution.

### FR-004: Loss Functions
The system must implement:
1. Cross-Entropy Loss (Standard classification).
2. InfoNCE Loss (Contrastive learning with $\tau=0.5$ and fixed negatives).

### FR-005: Convergence Definition
A training run is considered converged when the validation accuracy reaches **$\ge 0.90$**.
- Runs failing to reach this threshold within the maximum epoch limit must be flagged as censored.

### FR-006: Statistical Analysis (Tobit)
The system must perform Tobit Regression to model the relationship between $\beta$, loss type, and steps to convergence, handling censored data points.

### FR-007: Statistical Analysis (Cox)
The system must perform Cox Proportional Hazards analysis to estimate the hazard ratio of convergence for Contrastive vs. Cross-Entropy loss across varying $\beta$.

### FR-008: Interaction Testing
The analysis must specifically test for an interaction effect between $\beta$ and loss type. The output must include the F-statistic/p-value (Tobit) and Hazard Ratio/p-value (Cox) for this interaction, with Bonferroni correction applied.

## 3. User Stories

### US-1: Synthetic Graph Generation and Topology Annotation
**As a** researcher,
**I want** to generate a dataset of 110 Watts-Strogatz graphs with varying small-world parameters ($\beta$),
**So that** I can evaluate how network topology affects model convergence.

**Acceptance Criteria:**
1. The system generates exactly 110 graphs.
2. The distribution of $\beta$ is uniform (10 per level from 0.0 to 1.0).
3. Node labels are derived from the pre-rewiring lattice.
4. **Acceptance Scenario 1**:
 - **Given** the power analysis determined a required sample size of 110,
 - **When** the data generation script runs,
 - **Then** it produces 110 graph entries in `data/raw/graphs.jsonl` with correct metadata.

### US-2: Dual-Loss Training and Convergence Tracking
**As a** researcher,
**I want** to train GCN models on the generated graphs using both Cross-Entropy and InfoNCE losses,
**So that** I can compare their convergence speeds under different topological conditions.

**Acceptance Criteria:**
1. Training runs complete for all 110 graphs with both loss types.
2. Convergence is defined as accuracy **$\ge 0.90$**.
3. Censored data (runs not converging) are flagged.
4. **Acceptance Scenario 1**:
 - **Given** a graph with $\beta=0.5$,
 - **When** trained with InfoNCE,
 - **Then** the system records the step count to reach accuracy **$\ge 0.90$** or marks it as censored if the limit is reached.

### US-3: Statistical Interaction Analysis and Reporting
**As a** researcher,
**I want** to perform Tobit and Cox regression analyses on the training results,
**So that** I can determine if the small-world parameter $\beta$ interacts with the loss type to influence convergence.

**Acceptance Criteria:**
1. Tobit and Cox models are fitted to the censored convergence data.
2. Interaction terms ($\beta \times \text{loss\_type}$) are extracted and tested.
3. P-values are corrected for multiple comparisons.
4. A boolean `is_significant` flag is generated in the final report.

## 4. Data Model

### 4.1 SyntheticGraph
- `id`: string (UUID)
- `beta`: float (0.0 - 1.0)
- `seed`: int
- `clustering_coeff`: float
- `edge_list`: list of tuples
- `labels`: list of int

### 4.2 TrainingRun
- `run_id`: string
- `graph_id`: string
- `loss_type`: string ("CE" or "InfoNCE")
- `steps_to_converge`: int | null
- `is_censored`: boolean
- `trajectory`: list of {epoch, loss, accuracy}

### 4.3 AnalysisResult
- `tobit_interaction_p`: float
- `tobit_interaction_f`: float
- `cox_interaction_hr`: float
- `cox_interaction_p`: float
- `is_significant`: boolean

## 5. Constraints
- **Hardware**: CPU only (no CUDA).
- **Time**: Full pipeline must complete in < 6 hours.
- **Reproducibility**: All random seeds must be logged and controlled.
- **Sample Size**: N=110 (based on power analysis for $f^2=0.15$, power $\ge 0.80$).