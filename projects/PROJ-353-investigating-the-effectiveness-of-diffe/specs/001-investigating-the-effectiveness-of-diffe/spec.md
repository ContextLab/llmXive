# Specification: Investigating Loss Functions on Small-World Graphs

## 1. Introduction

This project investigates the effectiveness of different loss functions (Cross-Entropy vs. InfoNCE) on the convergence speed of Graph Neural Networks (GNNs) trained on small-world graphs with varying rewiring probabilities ($\beta$).

## 2. Functional Requirements

### FR-001: Graph Generation
The system must generate 110 Watts-Strogatz small-world graphs (10 per $\beta$ level from 0.0 to 1.0).
- **Input**: $\beta \in \{0.0, 0.1, \dots, 1.0\}$, $N=110$ total graphs.
- **Output**: Graphs saved to `data/raw/graphs.jsonl` with metadata.

### FR-002: Community Labeling
The system must derive community labels from the initial ring lattice structure before rewiring occurs.
- **Constraint**: Labels must be balanced (<80% max class frequency).

### FR-003: Model Architecture
The system must implement a 2-layer Graph Convolutional Network (GCN) capable of node classification.
- **Constraint**: CPU-only execution.

### FR-004: Dual-Loss Training
The system must train models using two loss functions:
1. Cross-Entropy (Supervised)
2. InfoNCE (Contrastive) with a fixed temperature $\tau=0.5$ and frozen linear probe.

### FR-005: Convergence Definition
Convergence is defined as the epoch where the model achieves an accuracy **≥ 0.90**.
- If the model does not reach this threshold within the maximum epoch limit, the run is flagged as **censored**.
- **US-2 Acceptance Scenario 1**: For a graph with $\beta=0.5$, the system must record the step count when accuracy hits **≥ 0.90** or mark the run as censored if the limit is reached without hitting this threshold.

### FR-006: Statistical Analysis (Tobit)
The system must perform Tobit Regression to model the relationship between $\beta$, loss type, and convergence steps, handling censored data appropriately.
- **Hypothesis**: Interaction term between $\beta$ and loss type is significant.

### FR-007: Statistical Analysis (Cox)
The system must perform Cox Proportional Hazards survival analysis on the convergence "time" (steps).
- **Hypothesis**: Hazard ratio for contrastive loss vs. supervised loss varies with $\beta$.

### FR-008: Multiple Comparison Correction
The system must apply Bonferroni correction to the interaction p-values obtained from Tobit and Cox models.
- **Output**: Corrected p-values and a boolean `is_significant` flag (p < 0.05).

## 3. User Stories

### US-1: Synthetic Graph Generation
**As a** researcher,
**I want** to generate a dataset of 110 small-world graphs with known community structures,
**So that** I can train models on a controlled topology with varying randomness.

**Acceptance Criteria:**
1. 110 graphs generated with $\beta$ evenly distributed.
2. Community labels derived from pre-rewiring lattice.
3. Class balance verified (<80% max).
4. Data saved to `data/raw/graphs.jsonl`.

### US-2: Dual-Loss Training and Convergence Tracking
**As a** researcher,
**I want** to train GCNs using Cross-Entropy and InfoNCE losses and track when they converge,
**So that** I can compare their efficiency across different graph topologies.

**Acceptance Criteria:**
1. Two models trained per graph (one per loss).
2. Convergence defined as accuracy **≥ 0.90**.
3. Censored data (max epochs reached) handled correctly.
4. Logs saved to `data/logs/training_run_{id}_{loss_type}.json`.

### US-3: Statistical Interaction Analysis
**As a** researcher,
**I want** to analyze the interaction between graph topology ($\beta$) and loss type on convergence speed,
**So that** I can determine if contrastive learning benefits more from small-world properties.

**Acceptance Criteria:**
1. Tobit and Cox models fitted to censored convergence data.
2. Interaction terms extracted and corrected for multiple comparisons.
3. Results saved to `data/analysis_results.json`.
4. Final report generated in `data/report.md`.

## 4. Data Model

### SyntheticGraph
- `id`: str
- `beta`: float
- `seed`: int
- `clustering_coeff`: float
- `edge_list`: List[Tuple[int, int]]
- `labels`: List[int]

### TrainingRun
- `run_id`: str
- `graph_id`: str
- `loss_type`: str (CE or InfoNCE)
- `trajectory`: List[Dict[epoch, loss, accuracy]]
- `convergence_step`: int | null
- `is_censored`: bool
- `final_accuracy`: float

### AnalysisResult
- `model_type`: str (Tobit or Cox)
- `interaction_p_value`: float
- `interaction_hazard_ratio`: float (Cox only)
- `is_significant`: bool

## 5. Acceptance Scenarios

**Scenario 1 (US-2)**:
Given a graph with $\beta=0.5$,
When the InfoNCE model is trained,
And the accuracy reaches 0.92 at epoch 15,
Then `convergence_step` is recorded as 15 and `is_censored` is false.

**Scenario 2 (US-2)**:
Given a graph with $\beta=0.8$,
When the Cross-Entropy model is trained for 100 epochs without reaching 0.90 accuracy,
Then `convergence_step` is null, `is_censored` is true, and the run is included in the censored dataset for analysis.

**Scenario 3 (US-3)**:
Given the aggregated training logs,
When Tobit regression is performed,
Then the interaction p-value is corrected via Bonferroni,
And `is_significant` is set to true if corrected p < 0.05.