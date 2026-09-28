# Specification: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Project ID**: PROJ-044
**Version**: 1.0
**Status**: Draft

## 1. Introduction

This project evaluates the impact of Differential Privacy (DP) on the convergence and utility of Federated Learning (FL) models under varying degrees of data heterogeneity. The study focuses on the FEMNIST dataset, excluding other datasets due to verified source constraints identified in the project plan.

## 2. Functional Requirements

### FR-001: Supported Datasets
- The system MUST support the **FEMNIST** dataset for all experiments.
- **Shakespeare** dataset is explicitly **EXCLUDED** from supported datasets per the plan.md Gap Analysis due to lack of verified sources.
- Any attempt to configure the system for "Shakespeare" MUST raise a `ValueError` with the message: "Shakespeare excluded per plan.md Gap Analysis".
- Future dataset support requires a verified source and plan update.

### FR-002: Heterogeneity Simulation
- The system MUST simulate data heterogeneity using Dirichlet distributions with configurable alpha (α) values (0.1, 0.5, 1.0).
- The system MUST generate reproducible client partitions based on a seed value.

### FR-003: Differential Privacy Implementation
- The system MUST implement DP using the Opacus library with Gaussian noise.
- The system MUST track the privacy budget (ε) using the Moments Accountant.

### FR-004: Experimental Design
- The system MUST run experiments across multiple seeds per configuration to ensure statistical power.
- The system MUST compare DP-trained models against non-DP baselines (ε=∞).

### FR-005: Statistical Analysis
- The system MUST perform paired t-tests comparing DP vs. Non-DP accuracy for each seed.
- The system MUST perform statistical tests comparing majority vs. minority client performance.

## 3. User Stories

### US-1: Baseline Heterogeneity Simulation
**As a** researcher,
**I want** to generate reproducible client data partitions from FEMNIST using Dirichlet distributions,
**So that** I can establish a controlled baseline for heterogeneity.

**Scenario 1: FEMNIST Partitioning**
Given the system is configured with dataset="femnist", seed=42, and alpha=0.1,
When the partitioning script is executed,
Then the system generates client partitions with high label variance and saves metadata to `data/partitions/`.

**Scenario 2: Excluded Dataset Handling**
Given the system is configured with dataset="shakespeare",
When the partitioning script is executed,
Then the system MUST raise a `ValueError` with the message "Shakespeare excluded per plan.md Gap Analysis".

### US-2: DP-FL Training and Convergence
**As a** researcher,
**I want** to train models using FedAvg with DP noise across varying ε and α,
**So that** I can measure the convergence impact of privacy constraints.

**Scenario 1: DP Training**
Given a valid FEMNIST partition and DP configuration (ε=1.0),
When the training loop is executed,
Then the system logs global and per-client accuracy while tracking the privacy budget.

### US-3: Statistical Analysis
**As a** researcher,
**I want** to perform statistical tests on the training results,
**So that** I can validate the hypothesis regarding heterogeneity and DP effectiveness.

**Scenario 1: T-Test Execution**
Given the training logs from 5 seeds,
When the analysis script is executed,
Then the system outputs p-values for DP vs. Non-DP comparisons and generates sensitivity plots.

## 4. Data Model

The system uses the following primary data artifacts:
- `data/raw/femnist.parquet`: Raw FEMNIST dataset (downloaded via streaming).
- `data/partitions/partition_femnist_{seed}_{alpha}.json`: Client partition metadata.
- `results/raw_logs.csv`: Aggregated training metrics.
- `results/filtered_data.csv`: Data after time and utility collapse filtering.
- `results/summary.csv`: Final statistical summary.

## 5. Constraints

- **Time Budget**: Experiments must complete within a feasible CPU window per configuration set.
- **Memory**: Streaming download and processing must be used to handle large datasets.
- **Reproducibility**: All random number generators must be seeded explicitly.
- **Exclusion**: No code path may successfully load or process the Shakespeare dataset.

## 6. Verification

- **T000 Verification**: Run `grep -r "Shakespeare" specs/001-evaluating-dp-federated-learning/spec.md`. Exit code must be 1 for "supported" references, but 0 for exclusion/error message references.
- **T011 Verification**: `data/raw/femnist.parquet` and `data/raw/femnist.sha256` must exist.
- **T013 Verification**: `data/partitions/partition_femnist_{seed}_{alpha}.json` files must exist with valid schema.