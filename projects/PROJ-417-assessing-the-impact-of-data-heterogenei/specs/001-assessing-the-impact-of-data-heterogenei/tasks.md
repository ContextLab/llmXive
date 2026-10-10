# Tasks: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the simulation environment and run a thin, end-to-end analysis on a small valid sample to verify the data flow from perturbation to metric calculation.

- [ ] T001 Establish the project layout and verify input provenance.
    Implement the directory structure defined in `plan.md` and ensure `code/requirements.txt` contains only CPU-tractable dependencies (`numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `pyyaml`). 
    Implement the data loader in `code/scripts/fetch_cochrane.py` to fetch real data from Zenodo DOI `10.5281/zenodo.10286623` or fallback to the verified synthetic base (mu=0.0, sigma=1.0, N=20) cited from Jackson et al. (2010).
    The loader MUST raise `FileNotFoundError` on fetch failure rather than silently substituting fake data.
    **Verification**: `data/raw/cochrane_base.csv` (or `cochrane_base_synthetic.csv`) exists and contains valid effect sizes and standard errors.

- [X] T002 Implement the simulation generator.
    Implement `code/simulation/generator.py` to perturb between-study variance $\tau^2$ (FR-001).
    **Mandatory**: Implement deterministic random seeding using a pinned seed to ensure reproducibility (Constitution Principle I).
    **Verification**: `tests/unit/test_generator.py` confirms that the injected $\tau^2$ matches the empirical variance of generated effect sizes within 0.05.

- [X] T003 Implement meta-analysis estimators and heterogeneity logic.
    Implement `code/simulation/estimators.py` providing Fixed-Effects, DerSimonian-Laird, and REML estimators (FR-002).
    **Mandatory**: Implement calculation of $Q$ and $I^2$ statistics for every estimation (Constitution Principle VII).
    **Mandatory**: Implement logic to identify and flag datasets with $N < 5$ studies, ensuring they are either excluded or explicitly flagged to avoid unreliable degrees-of-freedom approximations (Spec: Edge Cases).
    Include REML convergence failure logic in `estimators.py` to log events to `data/results/reml_failures.json` and proceed with a fallback variance or exclusion (FR-006).
    **Verification**: Unit tests in `tests/unit/test_estimators.py` confirm $\tau^2=0$ stability and that pooled estimates match known normal cases within 0.001.

- [X] T004 Implement metric calculation logic.
    Implement `code/analysis/metrics.py` to calculate bias and 95% CI coverage, reading `true_effect` strictly from the `injected_true_effect` column of the simulation output (FR-003).
    **Verification**: Unit tests confirm that a pooled estimate exactly equal to the true effect results in zero bias and a coverage flag of True.

- [ ] T005 Execute a small-scale end-to-end pipeline run. <!-- FAILED-IN-EXECUTION: code/main.py exit=1; code/main.py exit=1 -->
    Connect the components via `code/main.py` and run a trial with 10 replicates across 2 heterogeneity levels ($\tau^2 \in \{0, 0.1\}$).
    **Schema Resolution**: Produce `data/results/estimation_results.csv` containing `pooled_effect`, `ci_lower`, `ci_upper`, `estimator_type`, and `sweep_type` as defined in `data-model.md`, and use `convergence_warning` for REML failures. Note: These fields are currently missing from `contracts/*.yaml` and are flagged for correction.
    **Verification**: `data/results/estimation_results.csv` contains non-null pooled effects, $I^2$, and $Q$ statistics for all replicates.

**Checkpoint**: The documented command in `quickstart.md` executes, and numerical outputs in `data/results/` can be verified against the input parameters.

## Phase 2: Complete the study and validate its evidence

**Goal**: Execute the full primary and sensitivity sweeps, perform rigorous statistical testing, and generate the final evidence artifacts.

- [ ] T006 Run the Primary Simulation Sweep.
    Execute `code/main.py` for the full domain: $\tau^2 \in \{0, 0.1, 0.5, 1.0, 2.0\}$ with $\ge 500$ replicates per level.
    **Verification**: `data/results/simulation_raw.json` contains at least 2,500 records; logs confirm the process completes within 6 hours and peak RAM usage is $< 7$ GB (SC-003).

- [ ] T007 Perform statistical analysis and aggregate metrics.
    Implement `code/analysis/stats.py` to calculate:
    1. Exact binomial tests for coverage deviation against the nominal 0.95 level (FR-004).
    2. Shapiro-Wilk normality tests on bias distributions (FR-008).
    3. Conditional branching: Kruskal-Wallis if $p < 0.05$, otherwise ANOVA, to compare bias across levels (FR-008).
    Apply a Bonferroni correction to the significance threshold ($\alpha = 0.05 / 5 = 0.01$) for all hypothesis tests (FR-007).
    **Verification**: `data/results/aggregated_metrics.csv` is produced, conforming to `contracts/aggregated_metric.schema.yaml`.

- [ ] T008 Execute Sensitivity Sweep and Stability Analysis.
    Run a secondary simulation sweep with $\tau^2 \in \{0.05, 0.1, 0.5\}$ to detect non-linearities in the low-to-moderate transition zone (SC-004).
    Implement stability analysis in `code/analysis/stats.py` to compare coverage rates between the primary and sensitivity sweeps for overlapping $\tau^2$ levels.
    **Verification**: `data/results/stability_analysis.json` reports the `max_diff` in coverage rates between the two sweeps.

- [ ] T009 Generate visualizations.
    Implement `code/visualization/plots.py` to produce PNGs of Coverage vs. $\tau^2$ and Mean Bias vs. $\tau^2$ (FR-005).
    **Verification**: `ls data/results/*.png` confirms the existence of both required plots.

- [ ] T010 Generate the final framed report.
    Implement `code/reporting/report_gen.py` to compile results into `data/results/report.md`, including REML failure counts and stability metrics.
    **Mandatory**: Insert explicit "associational" labeling in the report header and conclusions to avoid causal claims (SC-005).
    **Verification**: `data/results/report.md` contains the "associational" label and references the specific result files in `data/results/`.

**Checkpoint**: All required runs complete, and artifacts match the actual computations without fabrication.

## Phase 3: Reproducible results and paper handoff

**Goal**: Ensure the entire pipeline is reproducible from scratch and prepare the handoff for the paper pipeline.

- [ ] T011 Perform final reproducibility validation.
    Execute the full pipeline (T001 $\rightarrow$ T010) on a fresh environment.
    Generate SHA-256 checksums for all final artifacts in `data/results/` and record them in `state/artifact_hashes.yaml`.
    **Verification**: All integration tests in `tests/integration/test_pipeline.py` pass, and checksums match the original run.

- [ ] T012 Document the paper-stage handoff.
    Write a concise methods/results account in `data/results/handoff.md` linking to the actual output cells and figure files.
    Explicitly state any limitations, such as the impact of small study effects ($N < 5$) flagged during estimation.
    **Verification**: Handoff document includes a complete list of all generated artifacts and their corresponding scientific requirements (FR-IDs).

## Dependencies and requirement coverage

| Requirement | Task | Verification Command | Order |
| :--- | :--- | :--- | :--- |
| FR-001 (Generation) | T002, T006 | `jq length data/results/simulation_raw.json` | $\rightarrow$ |
| FR-002 (Estimators) | T003 | `pytest tests/unit/test_estimators.py` | $\rightarrow$ |
| FR-003 (Bias/Cov) | T004, T005 | `python code/scripts/validate_schema.py --input data/results/estimation_results.csv` | $\rightarrow$ |
| FR-004 (Binomial) | T007 | `grep "p_value_binomial" data/results/aggregated_metrics.csv` | $\rightarrow$ |
| FR-005 (Plots) | T009 | `ls data/results/*.png` | $\rightarrow$ |
| FR-006 (REML Fail) | T003 | `ls data/results/reml_failures.json` | $\rightarrow$ |
| FR-007 (Bonferroni) | T007 | `grep "alpha=0.01" code/analysis/stats.py` | $\rightarrow$ |
| FR-008 (KW/ANOVA) | T007 | `grep "Kruskal-Wallis" data/results/aggregated_metrics.csv` | $\rightarrow$ |
| SC-003 (Compute) | T006 | `grep "RAM < 7GB" data/results/runtime_logs.txt` | $\rightarrow$ |
| SC-004 (Sensitivity) | T008 | `ls data/results/stability_analysis.json` | $\rightarrow$ |
| SC-005 (Framing) | T010 | `grep "associational" data/results/report.md` | $\rightarrow$ |