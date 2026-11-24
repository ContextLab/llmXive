# Specification: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Project ID**: PROJ-044
**Version**: 1.1
**Status**: Draft

## 1. Introduction

This project evaluates the impact of Differential Privacy (DP) on the convergence and utility of Federated Learning (FL) models under varying degrees of data heterogeneity. The study focuses on the FEMNIST dataset. Although the original idea mentioned both FEMNIST and Shakespeare from the LEAF benchmark, Shakespeare is excluded because no verified source for it was identified (plan.md Gap Analysis); the narrowest scope that answers the research question with verified data is therefore FEMNIST-only. Adding Shakespeare would require an idea-level change and a verified source.

The central hypothesis is that lower heterogeneity concentration (α) amplifies the utility loss that DP imposes, particularly for minority clients. All statistical requirements below are designed to test this interaction directly.

## 2. Functional Requirements

### FR-001: Supported Datasets (See US-1)
- The system MUST support the **FEMNIST** dataset for all experiments.
- **Shakespeare** dataset is explicitly **EXCLUDED** from supported datasets per the plan.md Gap Analysis due to lack of verified sources.
- Any attempt to configure the system for "shakespeare" MUST raise a `ValueError` with the message: "Shakespeare excluded per plan.md Gap Analysis".
- Future dataset support requires a verified source and plan update.

### FR-002: Heterogeneity Simulation (See US-1)
- The system MUST simulate data heterogeneity using Dirichlet distributions with configurable alpha (α) values (0.1, 0.5, 1.0).
- The system MUST generate reproducible client partitions based on a seed value.
- Reproducibility MUST be verifiable: partitioning twice with the same (dataset, seed, α) MUST produce byte-identical partition files, confirmed by matching SHA-256 hashes.

### FR-003: Differential Privacy Implementation (See US-2)
- The system MUST implement DP using the Opacus library with Gaussian noise.
- The system MUST track the privacy budget (ε) using the Moments Accountant (RDP accountant).
- For each run, the accountant-reported ε at the end of training MUST match the configured target ε within an absolute tolerance of ±0.05; the reported value MUST be logged to `results/raw_logs.csv`.

### FR-004: Experimental Design (See US-2)
- The system MUST run experiments across at least **10 seeds** per (α, ε) configuration to ensure statistical power (see FR-009).
- The system MUST compare DP-trained models against non-DP baselines (ε=∞) under identical partitions and seeds.

### FR-005: Statistical Analysis (See US-3)
- The system MUST perform paired t-tests (significance threshold α=0.05) comparing DP vs. Non-DP final accuracy per seed for each (α, ε) configuration, AND MUST also perform the Wilcoxon signed-rank test as a non-parametric robustness check. Both p-values and Cohen's d effect sizes MUST be reported in `results/summary.csv`; where the two tests disagree, the non-parametric result is authoritative.
- The system MUST fit a mixed-effects model: `degradation ~ α * ε * is_minority + (1 + ε + α | seed)`, including random slopes for ε and α by seed, so that the α × ε and α × is_minority interaction terms directly test the central hypothesis. The **critical heterogeneity threshold** is defined as the largest α at which the α × is_minority (or α × ε) interaction term is significant at α=0.05.
- The system MUST perform statistical tests comparing majority vs. minority client per-client accuracy (paired, α=0.05, with effect sizes).

### FR-006: Minority Client Definition (See US-3)
- A **minority client** is defined as a client whose label entropy falls in the bottom quartile (≤ 25th percentile) of the **pooled label-entropy distribution computed across all α conditions jointly**, using a single fixed global threshold. This decouples minority-group membership from the heterogeneity factor α, preserving construct validity of the majority-vs-minority comparison.
- The threshold value and each client's minority flag MUST be recorded in the partition metadata files.

### FR-007: Run Inclusion and Flagging (See US-2, US-3)
- Runs with `global_accuracy < 1/62` (utility collapse) MUST NOT be excluded from the primary analysis; they MUST be flagged `is_collapsed=true` and retained. A sensitivity analysis excluding collapsed runs MUST also be reported so any selection effect is quantified.
- Runs that hit the per-run time-limit early-stop MUST NOT be excluded; they MUST be flagged `hit_time_limit=true` and retained, and convergence-speed metrics MUST treat them as censored observations.

### FR-008: Convergence Speed Measurement (See US-2)
- Convergence speed MUST be measured as the number of communication rounds required to reach [deferred] of the corresponding non-DP baseline's final global accuracy, per (α, ε, seed). Runs that never reach the target are recorded as censored at their final round with `converged=false`.

### FR-009: Power / Sample-Size Analysis (See US-3)
- The system MUST run and report a power analysis before the full sweep: with n=10 paired seeds, a paired t-test at α=0.05 with power 0.80 detects Cohen's d ≈ 0.94. This minimum detectable effect size MUST be documented in `results/summary.csv` metadata. If the seed count is reduced below 10 under the budget policy in Section 5, the power analysis MUST be re-run and the larger minimum detectable effect (n=6 → d ≈ 1.3) documented.

### FR-010: Privacy-Utility Curves (See US-3)
- The system MUST generate privacy-utility curves (final global accuracy and convergence speed vs. ε) for each α value, with per-seed points and confidence intervals, saved to `results/`.

### FR-011: Result Summary Tables (See US-3)
- The system MUST produce `results/summary.csv` containing, per (α, ε): mean and standard deviation of final accuracy, mean degradation, paired t-test p-value, Wilcoxon p-value, Cohen's d, interaction-term estimates, counts of collapsed and time-limited runs, and the minority-vs-majority gap.

## 3. User Stories

### US-1: Baseline Heterogeneity Simulation
**As a** researcher,
**I want** to generate reproducible client data partitions from FEMNIST using Dirichlet distributions,
**So that** I can establish a controlled baseline for heterogeneity.

**Scenario 1: FEMNIST Partitioning**
Given the system is configured with dataset="femnist", seed=42, and alpha=0.1,
When the partitioning script is executed,
Then the system generates client partitions with high label variance, records each client's minority flag per FR-006, and saves metadata to `data/partitions/`.

**Scenario 2: Excluded Dataset Handling**
Given the system is configured with dataset="shakespeare",
When the partitioning script is executed,
Then the system MUST raise a `ValueError` with the message "Shakespeare excluded per plan.md Gap Analysis".

**Scenario 3: Determinism**
Given the partitioning script is executed twice with identical (dataset, seed, α),
When the two output files are compared,
Then their SHA-256 hashes MUST match exactly.

### US-2: DP-FL Training and Convergence
**As a** researcher,
**I want** to train models using FedAvg with DP noise across varying ε and α,
**So that** I can measure the convergence impact of privacy constraints.

**Scenario 1: DP Training**
Given a valid FEMNIST partition and DP configuration (ε=1.0),
When the training loop is executed,
Then the system logs global and per-client accuracy while tracking the privacy budget, and the accountant-reported ε matches the target within ±0.05.

**Scenario 2: Run Flagging**
Given a run whose global accuracy falls below 1/62 or that hits the time-limit early-stop,
When the run completes,
Then the run is retained in `results/raw_logs.csv` with `is_collapsed` and/or `hit_time_limit` set to true.

### US-3: Statistical Analysis
**As a** researcher,
**I want** to perform statistical tests on the training results,
**So that** I can validate the hypothesis regarding heterogeneity and DP effectiveness.

**Scenario 1: T-Test Execution**
Given the training logs from ≥ 10 seeds,
When the analysis script is executed,
Then the system outputs paired t-test and Wilcoxon p-values, Cohen's d, and the α × ε and α × is_minority interaction estimates for DP vs. Non-DP comparisons, and generates sensitivity plots and privacy-utility curves.

## 4. Data Model

The system uses the following primary data artifacts:
- `data/raw/femnist.parquet`: Raw FEMNIST dataset (downloaded via streaming).
- `data/partitions/partition_femnist_{seed}_{alpha}.json`: Client partition metadata, including per-client label entropy and the FR-006 minority flag.
- `results/raw_logs.csv`: Aggregated training metrics. Schema includes: `seed`, `alpha`, `epsilon`, `round`, `global_accuracy`, `per_client_accuracy`, `accountant_epsilon`, `is_collapsed`, `hit_time_limit`, `converged`, `rounds_to_target`, and `degradation`. The `degradation` column (= matched non-DP baseline accuracy − DP accuracy for the same seed and α) is populated at the analysis stage after baseline runs complete; the column is present in the schema from the first write.
- `results/filtered_data.csv`: Retained for backward compatibility; contains all runs with collapse/time-limit flags (no runs are dropped).
- `results/summary.csv`: Final statistical summary per FR-011.

## 5. Constraints

- **Time Budget**: Before the full sweep, a pilot run (1 seed × 1 configuration × 5 rounds) MUST measure per-round wall-clock time; projected total time = measured per-round time × rounds × grid size. The full grid is 10 seeds × 3 α × 5 ε. If the projected total exceeds the available compute budget, grid dimensions are reduced in this order: (a) drop ε values to the set {0.5, 1.0, ∞-baseline}; (b) drop α values to {0.1, 1.0}; (c) as a last resort, reduce seeds to a floor of **6** per configuration, in which case the FR-009 power analysis MUST be re-run and the larger minimum detectable effect size (d ≈ 1.3 at n=6) documented in `results/summary.csv`. The seed count may never fall below 6.
- **Memory**: Streaming download and processing must be used to handle large datasets.
- **Reproducibility**: All random number generators must be seeded explicitly.
- **Exclusion**: No code path may successfully load or process the Shakespeare dataset.

## 6. Success Criteria

- **SC-001** (See US-1): Partition reproducibility — two executions with the same (dataset, seed, α) produce byte-identical partition files, verified by SHA-256 comparison.
- **SC-002** (See US-1): Excluded-dataset handling — configuring dataset="shakespeare" raises `ValueError` with the exact message "Shakespeare excluded per plan.md Gap Analysis", verified by an automated unit test.
- **SC-003** (See US-2): Privacy-budget tracking — for ≥ 95% of runs, the accountant-reported ε is within ±0.05 of the configured target.
- **SC-004** (See US-2): Convergence speed — rounds-to-90%-of-baseline accuracy is measured per FR-008 for every (α, ε, seed), with censored runs flagged.
- **SC-005** (See US-3): Statistical significance — paired t-test AND Wilcoxon signed-rank p-values plus Cohen's d are reported for every (α, ε) configuration at threshold α=0.05.
- **SC-006** (See US-3): Interaction testing — the mixed-effects model reports the α × ε and α × is_minority interaction estimates with p-values; the critical heterogeneity threshold (largest α with significant interaction) is stated.
- **SC-007** (See US-3): Minority-client degradation — the majority-vs-minority accuracy gap is quantified per (α, ε) with effect sizes, using the α-invariant FR-006 minority definition.
- **SC-008** (See US-3): Privacy-utility curves — accuracy and convergence speed vs. ε curves with confidence intervals are produced for every α.
- **SC-009** (See US-3): Collapse sensitivity — the primary analysis includes collapsed and time-limited runs (flagged, not dropped), and a sensitivity analysis excluding them is reported alongside so any selection effect is quantified.
- **SC-010** (See US-3): Result summary tables — `results/summary.csv` contains all FR-011 fields for every configuration.
- **SC-011** (See US-3): Power documentation — the minimum detectable effect size for the achieved seed count is computed and reported before inference.

## 7. Verification

- **T000 Verification (functional)**: An automated unit test (pytest) configures the system with dataset="shakespeare" and asserts that a `ValueError` is raised with the exact message "Shakespeare excluded per plan.md Gap Analysis". The test MUST pass (exit code 0). No grep-based textual check is used.
- **T011 Verification**: `data/raw/femnist.parquet` and `data/raw/femnist.sha256` must exist.
- **T013 Verification**: `data/partitions/partition_femnist_{seed}_{alpha}.json` files must exist with valid schema, including the per-client minority flag.
- **T-Determinism Verification**: Running the partitioning script twice with the same (seed, α) yields identical SHA-256 hashes for the partition files.
- **T-Accountant Verification**: For a sample of ≥ 3 runs per ε value, `accountant_epsilon` in `results/raw_logs.csv` is within ±0.05 of the configured target.
- **T-Summary Verification**: `results/summary.csv` contains non-empty p-value, effect-size, and interaction-estimate columns for every (α, ε) configuration, and reports the counts of collapsed and time-limited runs.

## Assumptions

- The FEMNIST dataset remains available for streaming download from its verified source.
- CPU-only execution is available; the Section 5 budget policy governs grid size.
- Opacus and the RDP accountant report ε values comparable to configured targets within ±0.05 for the noise multipliers used.