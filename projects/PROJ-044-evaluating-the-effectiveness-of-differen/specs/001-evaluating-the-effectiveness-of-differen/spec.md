# Specification: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## 1. Introduction

This project evaluates how Differential Privacy (DP) affects the utility and fairness of Federated Learning (FL) models under varying degrees of data heterogeneity. The study focuses on the **FEMNIST** dataset exclusively, as the Shakespeare dataset has been excluded due to lack of verified programmatic sources (see Plan.md Gap Analysis).

## 2. Goals and Non-Goals

### 2.1 Goals
- Quantify the accuracy degradation introduced by DP mechanisms (DP-SGD) in FL.
- Analyze the impact of data heterogeneity (Dirichlet α) on DP-FL convergence.
- Evaluate fairness implications: does DP disproportionately harm minority clients?
- Validate statistical significance of observed effects across multiple seeds.

### 2.2 Non-Goals
- Evaluation on the Shakespeare dataset (Excluded per Plan.md).
- Implementation of non-FL privacy mechanisms (e.g., centralized DP).
- Optimization of communication efficiency (focus is on privacy-utility trade-off).

## 3. Functional Requirements

### FR-001: Dataset Support
The system must support the **FEMNIST** dataset for all experiments.
- **Data Source**: Hugging Face `leaf/femnist` (Verified Source).
- **Exclusion**: The Shakespeare dataset is explicitly excluded from all requirements and implementations due to the absence of a verified, programmatic download source as identified in the Plan.md Gap Analysis.
- **Constraint**: Any attempt to configure "shakespeare" must raise a `ValueError` with the message: "Shakespeare excluded per plan.md Gap Analysis (no verified source)."

### FR-002: Heterogeneity Simulation
The system must generate client data partitions using Dirichlet distributions with configurable concentration parameters (α).
- **Values**: α ∈ {0.1, 0.5, 1.0}.
- **Reproducibility**: Partitions must be reproducible given a fixed seed.

### FR-003: Differential Privacy Configuration
The system must support DP-SGD with the following parameters:
- **Privacy Budget (ε)**: Configurable range (e.g., 0.1 to 10.0).
- **Delta (δ)**: Fixed at 1e-5.
- **Noise Multiplier**: Calculated via the Moments Accountant.

### FR-004: Experimental Orchestration
The system must execute experiments across a grid of configurations:
- **Seeds**: 5 independent random seeds.
- **Alpha**: 0.1, 0.5, 1.0.
- **Epsilon**: 0.5, 1.0, 5.0, ∞ (Non-DP baseline).
- **Output**: Aggregated logs in `results/raw_logs.csv`.

### FR-005: Statistical Analysis
The system must perform statistical testing to validate hypotheses:
- **Paired T-Test**: Compare DP vs. Non-DP accuracy per seed.
- **Unpaired T-Test / Mann-Whitney U**: Compare Majority vs. Minority client accuracy.
- **Sensitivity Analysis**: Plot accuracy gap vs. α.

## 4. User Stories

### US-1: Baseline Heterogeneity Simulation
**As a** researcher, **I want** to generate reproducible FEMNIST partitions with varying heterogeneity levels, **so that** I can establish a controlled baseline for FL performance.
- **Scenario 1**: Generate partitions for α=0.1 (High Heterogeneity).
- **Scenario 2**: Generate partitions for α=1.0 (Balanced).
- **Acceptance Criteria**: Partitions saved to `data/partitions/` with metadata JSON.

### US-2: DP-FL Training and Convergence
**As a** researcher, **I want** to train models using FedAvg with Opacus-enabled DP, **so that** I can measure the impact of privacy budgets on model convergence and client fairness.
- **Scenario 1**: Train with ε=0.5 and α=0.1.
- **Scenario 2**: Train with ε=∞ (No DP) for baseline comparison.
- **Acceptance Criteria**: Training completes, logs generated, privacy budget tracked.

### US-3: Statistical Analysis and Reporting
**As a** researcher, **I want** to analyze the training results using statistical tests, **so that** I can validate the "critical heterogeneity" hypothesis and report findings.
- **Scenario 1**: Calculate p-values for DP vs. Non-DP.
- **Scenario 2**: Generate accuracy gap plots.
- **Acceptance Criteria**: `results/summary.csv` and `results/plots/` generated.

## 5. Data Model

### 5.1 Partition Metadata
```json
{
 "client_id": "client_0",
 "label_distribution": {"0": 50, "1": 10,...},
 "total_samples": 60
}
```

### 5.2 Training Metrics
| Column | Type | Description |
|:--- |:--- |:--- |
| seed | int | Random seed used |
| alpha | float | Dirichlet concentration parameter |
| epsilon | float | Privacy budget |
| global_accuracy | float | Global model accuracy |
| minority_accuracy | float | Accuracy of minority clients |
| majority_accuracy | float | Accuracy of majority clients |
| rounds_to_target | int | Rounds to reach 90% accuracy |
| is_time_limited | bool | Flag if timeout occurred |
| is_utility_collapse | bool | Flag if accuracy < 5% |

## 6. Constraints and Assumptions

- **Hardware**: Experiments assumed to run on GPU-enabled environments (CUDA).
- **Timeout**: Each training run has a maximum duration (e.g., 2 hours).
- **Dataset**: Only FEMNIST is supported. Shakespeare is excluded.
- **Privacy**: δ is fixed at 1e-5 for all experiments.

## 7. Appendix

### 7.1 Exclusion of Shakespeare Dataset
The Shakespeare dataset was initially considered but excluded in the Plan.md Gap Analysis due to the lack of a verified, programmatic download source (no stable URL or pip package). All references to Shakespeare in requirements, code, and tests have been removed. The system must strictly enforce this exclusion.