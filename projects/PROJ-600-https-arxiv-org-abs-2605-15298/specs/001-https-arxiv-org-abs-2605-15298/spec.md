# Feature Specification: Evaluating Physics‑Informed Regularization for Neural ODE Forecasting

**Feature Branch**: `001-physics-informed-regularization`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: “Evaluating Physics‑Informed Regularization for Neural ODE Forecasting”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Benchmark baseline vs. physics‑informed models (Priority: P1)

A researcher wants to run a reproducible benchmark that trains a small MLP on synthetic ODE trajectories with (a) a data‑only loss and (b) a physics‑informed loss, across three data‑scarcity regimes, and retrieve the test‑set mean‑squared error (MSE) for each run.

**Why this priority**: This story delivers the core scientific evidence needed to answer the research question.

**Independent Test**: Execute the full training‑evaluation pipeline for a single ODE system (e.g., Lorenz) in the [deferred] regime and verify that two CSV files are produced – one containing baseline MSEs and one containing physics‑informed MSEs – each with 10 rows (one per random seed).

**Acceptance Scenarios**:

1. **Given** the ODEBench repository is available and the pipeline is invoked with `--regime 5` and `--seed 0`, **When** the baseline model finishes training, **Then** a file `baseline_mse.csv` containing a numeric MSE column is written.
2. **Given** the same invocation with `--physics` flag, **When** training finishes, **Then** a file `physics_mse.csv` is written and its numeric values are comparable to the baseline file.

---

### User Story 2 – Statistical significance reporting (Priority: P2)

A researcher wants the system to automatically perform paired statistical tests between baseline and physics‑informed MSEs for each regime and present p‑values corrected for multiple comparisons.

**Why this priority**: Without rigorous statistics the benchmark cannot support the claimed improvement.

**Independent Test**: Run the pipeline on all three regimes; after completion, a JSON report `stats.json` must contain entries `p_value_5`, `p_value_20`, `p_value_100` that are all ≤ 1.0 and reflect a Bonferroni‑adjusted paired t‑test.

**Acceptance Scenarios**:

1. **Given** ten baseline and ten physics‑informed MSEs for the [deferred] regime, **When** the statistical module is executed, **Then** the reported `p_value_5` equals the Bonferroni‑corrected two‑sided paired t‑test p‑value.
2. **Given** the same for the [deferred] regime, **When** the report is generated, **Then** `p_value_20` is present and follows the same correction procedure.

---

### User Story 3 – Regularization‑strength sensitivity analysis (Priority: P3)

A researcher wants to explore how the choice of the physics‑informed regularization weight λ influences forecasting performance and statistical significance.

**Why this priority**: The community expects any introduced threshold to be justified and its robustness demonstrated.

**Independent Test**: Invoke the pipeline with `--lambda 0.01 0.1 1.0`; after completion, a CSV `lambda_sweep.csv` must list each λ together with the mean MSE difference (baseline – physics) and the corresponding Bonferroni‑adjusted p‑value.

**Acceptance Scenarios**:

1. **Given** λ = 0.01, **When** the sweep finishes, **Then** the CSV contains a row where `lambda=0.01`, `mean_delta` is a numeric value, and `p_adj` is ≤ 1.0.
2. **Given** λ = 1.0, **When** the sweep finishes, **Then** the same columns are present, allowing the researcher to assess robustness across the three λ values.

---

### Edge Cases

- What happens when the ODE solver fails to converge for a particular step size?  
- How does the system handle a missing variable (e.g., a state component not present in the downloaded ODEBench files)?  
- What if the physics‑informed loss produces NaN gradients due to extreme λ values?  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download the ODEBench repository and generate training, validation, and test trajectories for each selected ODE using a 4th‑order Runge‑Kutta solver with step = 0.01. *(See US-1)*
- **FR-002**: The system MUST train a baseline MLP (≤ 2 hidden layers, 64 units each) with a data‑only MSE loss under the three data‑scarcity regimes ([deferred], [deferred], [deferred]) and 10 distinct random seeds. *(See US-1)*
- **FR-003**: The system MUST train a physics‑informed MLP identical to the baseline but with an additional loss term λ · MSE(residual of the governing ODE), where λ is selectable from a predefined set. *(See US-1 & US-3)*
- **FR-004**: The system MUST compute and store test‑set MSE for every trained model in CSV files (`baseline_mse.csv`, `physics_mse.csv`). *(See US-1 & US-2)*
- **FR-005**: The system MUST perform a paired two‑sided t‑test between baseline and physics‑informed MSEs within each regime and apply a Bonferroni correction for the three simultaneous comparisons. *(See US-2)*
- **FR-006**: The system MUST allow the regularization weight λ to be set to at least three values {0.01, 0.1, 1.0} and automatically sweep across them, reporting mean MSE differences and corrected p‑values per λ. *(See US-3)*
- **FR-007**: The system MUST halt training early if validation loss does not improve for 10 consecutive epochs (patience = 10). *(General robustness)*
- **FR-008**: The system MUST log all hyperparameters, random seeds, and software versions to a reproducibility manifest (`run_info.yaml`). *(General reproducibility)*

### Key Entities

- **ODESystem**: Represents a dynamical system (e.g., Lorenz) with its governing equations and state variables.  
- **TrajectoryDataset**: Contains generated time‑ordered state vectors for training, validation, and testing.  
- **ModelRun**: Records a single training run, including model type (baseline or physics‑informed), λ value, seed, and final test MSE.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In at least one data‑scarcity regime, the mean test MSE of the physics‑informed model must be ≤ 95 % of the baseline mean test MSE. *(See US-1)*
- **SC-002**: The Bonferroni‑adjusted paired t‑test p‑value for the [deferred] regime must be < 0.05, indicating a statistically significant improvement. *(See US-2)*
- **SC-003**: The λ‑sensitivity sweep must show that the MSE improvement satisfying SC‑001 holds for at least two of the three λ values, and the associated corrected p‑values must also be < 0.05. *(See US-3)*

## Assumptions

- The ODEBench repository contains all required state variables for Lorenz, Lotka‑Volterra, and Duffing systems; no additional variables are needed.  
- Automatic differentiation in PyTorch on CPU can compute the ODE residuals accurately for the chosen step size; thus no GPU is required.  
- The chosen λ values {0.01, 0.1, 1.0} are based on common regularization strengths reported in the PINN literature (e.g., Self‑Adaptive PINNs, 2020).  
- Early stopping with patience = 10 epochs is sufficient to prevent over‑fitting while keeping total compute ≤ 6 hours on the GitHub Actions runner.  
- The paired t‑test assumptions (approximately normal differences) are acceptable for the sample size of 10 seeds; if violated, a non‑parametric Wilcoxon signed‑rank test will be fall‑back (implementation‑agnostic note).  

[NEEDS CLARIFICATION: Does ODEBench provide separate validation trajectories, or must they be carved out from the training set?]  
[NEEDS CLARIFICATION: What is the exact random‑seed range to be used for reproducibility (e.g., 0–9, 100–109)?]  
[NEEDS CLARIFICATION: Should the significance level be α = 0.05 for each regime before correction, or a stricter family‑wise α = 0.0167 after Bonferroni?]
