# Research: 001-session-first-reconstruction

## Research Question

Does a "Session-First" architecture (atomic state recording) provide statistically significant higher resilience compared to a "Baseline Event-Log" architecture (fragmented, async logging) when subjected to stochastic network delays and random log corruption?

## Methodology Overview

### Experimental Design
A within-subjects simulation design where each synthetic workflow is executed twice: once via the Baseline Event-Log model and once via the Session-First model. The same corruption pattern (seeded) is applied to both to ensure a fair comparison of architectural resilience.

### Data Strategy
- **Source**: Synthetic data generated locally by `code/generators/workflow_generator.py`.
- **Variables**:
 - *Predictors*: Architecture Type (Event-Log vs. Session-First), Corruption Rate ([deferred], [deferred], [deferred]).
  - *Outcome*: Binary Resilience Status (Success vs. Failure/Unrecoverable).
  - *Covariates*: Workflow Complexity (number of steps), Random Seed.
- **Dataset Fit**: The generator produces all required variables (tool outputs, state snapshots, decision trees) as defined in FR-001 and SC-005. No external dataset is needed.

### Statistical Analysis Plan
1.  **Primary Metric**: **Total Resilience** (Success / Total).
    -   *Calculation*: For each architecture, count `Success` (exact match) and `Total` (all workflows).
    -   *Definition*: 'Unrecoverable' cases (critical data deleted) are counted as **Failures** in the denominator. This eliminates selection bias and measures true architectural resilience.
2.  **Primary Hypothesis Test**: **Cochran's Q Test**.
    -   *Design*: 2x2x3 design (Architecture x Outcome x Corruption Rate).
    -   *Null Hypothesis*: The proportion of successes is the same across all k conditions (rates) and architectures.
    -   *Assumption Check*: If asymptotic assumptions are violated (low N), use **Monte Carlo simulation** (10,000 replicates).
3.  **Post-Hoc Analysis**: **McNemar's Test**.
    -   *Usage*: For pairwise comparisons of success rates at specific corruption rates.
    -   *Correction*: **Holm-Bonferroni** correction applied to p-values for multiple comparisons.
    -   *Small N*: If discordant pairs < 25, use **Exact McNemar** test.
4.  **Secondary Metric**: **Recoverable State Fidelity** (Success / Recoverable).
    -   *Calculation*: Success / (Total - Unrecoverable).
    -   *Purpose*: Descriptive metric only; not used for primary hypothesis testing to avoid selection bias.
5.  **Latency Analysis**: **Paired t-test** (or Wilcoxon Signed-Rank if non-normal) for Replay Latency.
    -   *Design*: Within-subjects (same workflow executed by both architectures).
    -   *Note*: Mann-Whitney U is explicitly rejected for this paired design.

## Dataset Strategy

| Dataset Name | Source/Loader | Variables Provided | Fit Verification |
| :--- | :--- | :--- | :--- |
| **Synthetic Multi-Agent Workflows** | `code/generators/workflow_generator.py` (Local) | `workflow_id`, `decision_tree`, `tool_outputs`, `state_snapshots`, `ground_truth_hash` | **Verified**: Generator explicitly creates all variables required for reconstruction and fidelity calculation. No external source needed. |

*Note: No external datasets are used. All data is generated deterministically to ensure reproducibility and avoid access-gated data issues.*

## Compute Feasibility & Method Selection

### CPU-First Strategy
- **Method**: All logic is implemented in pure Python with `scipy` for statistics.
- **Justification**: The simulation involves deterministic state transitions and simple file I/O. No heavy model training or GPU inference is required.
- **Resource Fit**:
  - *RAM*: < 2GB (estimated for 500 workflows in memory during processing).
  - *Disk*: < 5GB (estimated for 500 workflows x 3 corruption levels x 2 architectures).
  - *Time*: < 2 hours (estimated for 500 workflows x 2 architectures).
- **Conclusion**: The entire experiment runs comfortably on the GitHub Actions free-tier (2 CPU, 7GB RAM) without needing the GPU escape hatch.

### Decision/Rationale
- **Why CPU?**: The "Session-First" vs. "Event-Log" comparison is a logic/architecture simulation, not a neural network training task. The "corruption" and "reconstruction" are deterministic algorithmic steps.
- **Why not GPU?**: No tensor operations or large language model inference is performed. Using a GPU would be wasteful and unnecessary.
- **Scaling**: If the workflow count increases to 5000, the plan will switch to streaming processing (iterate and discard) to maintain < 7GB RAM usage, but 500 is well within limits.

## Risk Mitigation

- **Risk**: Corruption deletes all copies of a critical tool output.
  - *Mitigation*: The "Unrecoverable" detection logic (FR-007) explicitly identifies these cases and treats them as **Failures** in the primary metric (Total Resilience), preventing false negatives in the architectural comparison.
- **Risk**: Non-deterministic execution due to system load.
  - *Mitigation*: Fixed random seeds in `config.py` and strict isolation of the RNG state. Checkpointing ensures resume capability without re-running completed workflows.
- **Risk**: Statistical invalidity due to multiple testing.
  - *Mitigation*: Explicit implementation of **Holm-Bonferroni** correction in `statistical_test.py` for the sensitivity sweep.
- **Risk**: Small sample size for McNemar post-hoc.
  - *Mitigation*: Use of **Exact McNemar** test if discordant pairs < 25.
- **Risk**: Violation of Cochran's Q assumptions.
  - *Mitigation*: Use of **Monte Carlo simulation** (10,000 replicates) if asymptotic assumptions are not met.

## References

- **Spec**: `specs/001-session-first-reconstruction/spec.md` (Primary source for FR/SC definitions).
- **Constitution**: `projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/.specify/memory/constitution.md` (Governing principles for hygiene and reproducibility).
- **Statistical Method**: *Cochran, W. G. (1950). "The comparison of percentages in matched samples". Biometrika.* (Standard for k related samples).
- **Statistical Method**: *Holm, S. (1979). "A simple sequentially rejective multiple test procedure". Scandinavian Journal of Statistics.* (Standard for multiple comparison correction).
- **Statistical Method**: *McNemar, Q. (1947). "Note on the sampling error of the difference between correlated proportions or percentages". Psychometrika.* (Standard for paired nominal data).