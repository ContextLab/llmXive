# Tasks: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Inputs**: The active `spec.md`, `plan.md`, `data-model.md`, and `contracts/`.

This research implementation evaluates how client data heterogeneity (controlled via Dirichlet $\alpha$) modulates the privacy-utility trade-off in differentially private federated learning, specifically focusing on whether minority clients suffer disproportionate accuracy degradation.

**Note on plan-root ambiguities (flagged for kickback)**: `plan.md`'s Minority Definition section still contains a `[deferred]` placeholder for the entropy percentile, contradicting the plan's own Constitution Check table ("bottom 30%"). The tasks below adopt the concrete **bottom 30%** value so the requirement is testable; the plan should be updated upstream to match. Likewise, the plan's "5 ε" sweep is never enumerated in `plan.md` or `spec.md`; the tasks below fix it as $\epsilon \in \{0.1, 0.5, 1.0, 5.0, \infty\}$ (with $\epsilon=\infty$ as the non-DP baseline), consistent with the plan's emphasis on $\epsilon \le 0.5$ in H13.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the pipeline from streaming data download to a small-scale result to verify the compute budget and data flow.

- [X] T001 Establish the project structure, install dependencies (`torch`, `opacus`, `datasets`, `pandas`, `scipy`, `statsmodels`, `pyarrow`), and document the runnable entry point in `quickstart.md`.
- [ ] T002 Implement the FEMNIST data loader in `code/data/download.py` using `datasets.load_dataset(..., streaming=True)` to materialize the dataset into `data/raw/femnist.parquet` with a corresponding `data/raw/femnist.sha256`. <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->
    The loader must fail loudly on fetch failure; no synthetic fallback is permitted. It must raise `ValueError("Shakespeare excluded per plan.md Gap Analysis")` if the dataset is set to "shakespeare".
- [ ] T003 Implement a thin end-to-end pilot run in `code/main.py` using a single seed, one $\alpha=0.1$, and one $\epsilon=1.0$.
    This must execute the full chain: Download $\rightarrow$ Partition $\rightarrow$ DP-FedAvg $\rightarrow$ Result logging.
    Verification: Produce `results/raw_logs.csv` containing at least one row with all fields defined in `contracts/results.schema.yaml`.

**Checkpoint**: The documented command executes and produces real numerical outputs in `results/raw_logs.csv`.

## Phase 2: Complete the study and validate its evidence

**Goal**: Execute the full experimental matrix across 5 seeds, multiple $\alpha$ and $\epsilon$ values, and perform the mandated statistical analysis.

- [ ] T004 Implement the Dirichlet partitioning logic in `code/data/partition.py` to generate `data/partitions/partition_femnist_{seed}_{alpha}.json` for $\alpha \in \{0.1, 0.5, 1.0\}$.
    The logic must compute empirical label entropy per client and flag `is_minority=True` for clients in the **bottom 30% percentile of the within-partition empirical label-entropy distribution** (bits), computed independently of $\alpha$ per Constitution Principle VI. The 30% threshold matches the plan's Constitution Check table.
- [ ] T005 Implement the DP-FedAvg training loop in `code/training/fedavg.py` and `code/training/dp_utils.py` using Opacus.
    Must implement: (1) Gaussian noise addition, (2) Privacy budget tracking via Moments Accountant, and (3) A non-DP baseline ($\epsilon=\infty, is\_dp=False$).
- [ ] T006 Implement the 5-seed orchestrator in `code/main.py` to run the full matrix: 5 seeds $\times$ 3 $\alpha$ $\times$ 5 $\epsilon$, where $\epsilon \in \{0.1, 0.5, 1.0, 5.0, \infty\}$ and $\epsilon=\infty$ denotes the non-DP baseline.
    Must implement the deterministic time-budget logic: check wall-clock time after each round; if the remaining budget is insufficient, cap rounds at `max_rounds` and set `is_time_limited=True`.
    Must implement the plan's retry mechanism: if a seed crashes (OOM, timeout), a fresh seed (incremented integer) is drawn and retried up to 3 attempts to guarantee 5 successful runs per configuration.
    Verification: `results/raw_logs.csv` must contain exactly 5 successful runs per $(\alpha, \epsilon)$ configuration (15 configurations, 75 successful runs total).
- [ ] T007 Implement data filtering and convergence detection in `code/analysis/stats.py` to produce `results/filtered_data.csv` and `results/filtered_time.csv`.
    Must remove: (1) Runs where `global_accuracy < 1/62` (utility collapse), and (2) Runs where `is_time_limited=True` — time-limited runs are excluded from **all** downstream statistical analyses (paired t-tests, LMM, filtering) per the plan's bias-avoidance rule; `filtered_data.csv` therefore excludes both utility-collapsed and time-limited runs.
    Must also implement convergence detection per the plan's T025: compute `rounds_to_80` = the first round where `global_accuracy >= 0.80`, computed on time-limit-excluded data and written to `results/filtered_time.csv`.
- [ ] T008 Perform the statistical analysis in `code/analysis/stats.py` using `results/filtered_data.csv` (which excludes both utility-collapsed and time-limited runs).
    Must implement: (1) Paired t-tests comparing DP vs. Non-DP global accuracy per seed, and (2) A Linear Mixed-Effects Model (LMM) to compare degradation between majority and minority clients (degradation ~ Group + (1|Seed) + (1|Seed:Client), with robust SEs if the nested model is infeasible).
    Must apply **Bonferroni correction** across the 15 simultaneous $(\alpha, \epsilon)$ tests ($\alpha_{adj} = 0.05/15 \approx 0.0033$), reporting both raw and adjusted p-values.
    Verification: Produce `results/final_stats.csv` with raw and Bonferroni-adjusted p-values, effect sizes, and confidence intervals.
- [ ] T009 Generate the required scientific figures in `code/analysis/plots.py`.
    Must produce: (1) `figures/sensitivity_alpha.png` (Accuracy vs $\epsilon$ for different $\alpha$), and (2) `figures/minority_vs_global_overlay.png` (Overlay of minority client degradation vs global accuracy).

**Checkpoint**: All required runs complete; statistical tests are performed on filtered real data; figures are generated from validated outputs.

## Phase 3: Reproducible results and paper handoff

**Goal**: Consolidate results into a final report, verify the end-to-end reproducibility of the workflow, and lock in test coverage.

- [ ] T010 Generate the final result aggregation artifacts: `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.
    The summary must include mean accuracies, degradation, and convergence rounds (`rounds_to_80`, computed by T007) per configuration.
- [ ] T011 Update `README.md` with detailed "Installation", "Usage", and "Results" sections, including the explicit statement that the Shakespeare dataset is excluded per the plan.
- [ ] T012 Execute a final end-to-end reproducibility check from `quickstart.md` on a fresh environment, confirming that all artifacts in `results/` and `figures/` are reproduced.
    Verification: Produce `quickstart_verification.log` showing successful execution and checksum match for `data/raw/femnist.parquet`.
- [ ] T013 Implement the unit/integration test suite per the plan's T032, using `pytest` under `tests/unit/` and `tests/integration/`.
    Must cover: (1) partition reproducibility (same seed → identical partition JSON), (2) missing-classes handling in partitioning, (3) DP-vs-non-DP logging (epsilon, is_dp, actual_epsilon fields), (4) timeout flagging (`is_time_limited=True` when the round cap triggers), and (5) the utility-collapse filter (rows with `global_accuracy < 1/62` are removed from `filtered_data.csv`).
    Verification: `pytest tests/` passes with at least one test per listed behavior.

## Dependencies and requirement coverage

| Requirement | Task(s) | Verification |
|---|---|---|
| **FR-001** (FEMNIST / $\neg$Shakespeare) | T002, T011 | `ValueError` on "shakespeare" / `femnist.parquet` exists |
| **FR-002** (Dirichlet $\alpha$) | T004 | `partition_*.json` exists with correct entropy flags |
| **FR-003** (DP / Opacus / $\epsilon$) | T005 | `actual_epsilon` logged in `raw_logs.csv` |
| **FR-004** (5 Seeds) | T006 | `raw_logs.csv` contains 5 entries per config (15 configs, 75 runs) |
| **FR-005** (Paired t-tests / LMM) | T008 | `final_stats.csv` contains raw and Bonferroni-adjusted p-values |
| **Utility-Collapse Filter** (plan.md Statistical Analysis Plan) | T007 | `filtered_data.csv` excludes accuracy $< 0.01613$ |
| **Time-Limit Exclusion** (plan.md Early-Stop Logic) | T007, T008 | `is_time_limited` runs excluded from all statistical analyses |
| **Convergence Detection** (plan.md T025) | T007 | `rounds_to_80` in `filtered_time.csv` |
| **Compute Budget** (6h / Early Stop) | T006 | `is_time_limited` flag present in `raw_logs.csv` |
| **Minority Definition** (bottom 30% entropy percentile) | T004 | `is_minority` field in partition JSONs |
| **Test Coverage** (plan.md T032) | T013 | `pytest tests/` passes |

**Execution Order**: T001 $\rightarrow$ T002 $\rightarrow$ T003 $\rightarrow$ T004 $\rightarrow$ T005 $\rightarrow$ T006 $\rightarrow$ T007 $\rightarrow$ T008 $\rightarrow$ T009 $\rightarrow$ T010 $\rightarrow$ T011 $\rightarrow$ T012 $\rightarrow$ T013.