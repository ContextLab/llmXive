# Tasks: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, and original research idea.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the project skeleton and run a thin, end-to-end pipeline on a small subset of real HCP data to verify the data flow from NIfTI to regression results.

- [ ] T001 [P] Establish project structure and environment. 
    Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`, and `tests/`. 
    Initialize `requirements.txt` (numpy, pandas, scikit-learn, statsmodels, nibabel, scipy, networkx, tqdm, pyyaml, nitime, pytest).
    Create `.ruff.toml` for linting and `code/config.py` with pinned seeds (42) and parameters (window=60s, step=1s, FD_threshold=0.2).
    Update `plan.md` Constitution Check to mark "DEVIATION (Justified in technical-design.md)" for window length and "REJECTED" for phase-shuffling.
    **Verification**: Run `tree code/` and `ruff check .` and assert directory structure and linting pass.
- [ ] T002 [US1] Implement the data ingestion and preprocessing pipeline. <!-- FAILED-IN-EXECUTION: tests/test_contracts.py exit=1 -->
    Implement `code/data/download.py` to fetch real HCP resting-state fMRI and behavioral data (NIH Toolbox Dimensional Change Card Sort) using the HCP API; fail loudly if data is unavailable.
    Implement logic to compute SHA-256 checksums for all downloaded raw fMRI and behavioral files, recording them in `data/checksums.txt` to satisfy Constitution Principle III.
    Implement `code/data/preprocess.py` to download the Schaefer 200-region atlas and parcellate fMRI time-series into `data/processed/parcellated/{subject_id}_timeseries.csv`.
    Implement `code/data/merge.py` and `code/utils/motion.py` to exclude subjects with Mean FD > 0.2mm or missing behavioral scores, logging exclusions to `data/processed/exclusion_log.csv`.
    **Verification**: Run on 5 subjects and verify `data/processed/parcellated/` contains CSVs, `data/checksums.txt` is populated, and `exclusion_log.csv` is populated.
- [ ] T003 [US2] Implement the dynamic connectivity metric computation. <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
    Implement `code/features/connectivity.py` to compute sliding-window Pearson correlations (60s window, 1s step) and calculate edge-wise standard deviation and Shannon entropy.
    Implement PCA dimensionality reduction on the edge-wise variability matrices to extract the top 10 principal components (`PCA_Component_1` through `PCA_Component_10`) for each subject, as required by the Plan and `dataset.schema.yaml`.
    Save results to `data/processed/metrics.csv` containing `Subject_ID` and the 10 PCA components.
    **Verification**: Run on the 5-subject subset; verify `metrics.csv` contains exactly 11 columns (ID + 10 PCA components) and values are floats.
- [ ] T004 [US3] Execute a thin end-to-end analysis.
    Implement `code/analysis/regression.py` to perform linear regression of flexibility scores on `PCA_Component_1` (the primary variability component), controlling for age, sex, Mean FD, and Total Scan Time.
    Run the pipeline on the 5-subject subset to produce a preliminary `data/results/regression_summary.json` and `data/processed/final_results.csv`.
    **Verification**: Assert `regression_summary.json` contains `Beta_Variability` and `Pearson_R` and conforms to `output.schema.yaml`.

**Checkpoint**: The documented command executes and produces real (albeit small-sample) numerical outputs.

## Phase 2: Complete the study and validate its evidence

**Goal**: Scale the analysis to the full cohort, implement robust statistical validation (permutation tests and null models), and ensure compute feasibility on CPU-only CI.

- [ ] T005 [US2] Implement batch processing for full-cohort scaling.
    Refactor `code/features/connectivity.py` to process subjects in batches (e.g., `batch_size=50`) using generators to keep peak RAM < 7GB.
    Run the full-scale parcellation and metric extraction for all available subjects in the HCP subset.
    **Verification**: Run `python -m memory_profiler code/features/connectivity.py` and assert peak RSS < 7GB.
- [ ] T006 [US2] Validate the construct validity of the RSFC variability metric.
    Implement `code/features/null_model.py` to generate AR-based surrogate time-series (as specified in plan.md Complexity Tracking) to avoid tautological validation.
    Compute the variability metric (PCA_Component_1) for 1,000 surrogates per subject and verify that the real data variability is significantly higher than the null distribution (p < 0.05).
    **Verification**: Assert `data/processed/metrics.csv` includes a `Null_Model_P` column for every subject.
- [ ] T007 [US3] Implement large-scale permutation testing.
    Implement `code/analysis/permutation.py` to execute 10,000 permutations of the behavioral scores to generate an empirical p-value for the regression coefficient.
    Include logic to report p-values of 0.0 as `< 0.0001`.
    **Verification**: Run permutation test on the full dataset and assert the output `P_Value` in `regression_summary.json` is a float or the string `< 0.0001`.
- [ ] T008 [US3] Perform final statistical refinement and FDR correction.
    Implement FDR correction using `statsmodels.stats.multitest` for any post-hoc network-specific analyses (q ≤ 0.05).
    Generate the final `data/results/regression_summary.json` and `data/processed/final_results.csv` (containing subject-level predicted scores and residuals) conforming to the defined contracts.
    **Verification**: Assert `FDR_Appplied` is boolean in the output JSON and `final_results.csv` contains no excluded subjects.
- [ ] T009 [US3] Generate research visualizations.
    Implement `code/utils/plotting.py` to create a scatter plot of `PCA_Component_1` vs. flexibility scores, including the regression line and 95% confidence interval.
    Save the figure to `figures/variability_vs_flexibility.png`.
    **Verification**: Assert the figure file exists and contains a labeled regression line.

**Checkpoint**: All required runs complete; artifacts match actual computations and satisfy the specification.

## Phase 3: Reproducible results and paper handoff

**Goal**: Document the findings and verify the end-to-end reproducibility of the pipeline.

- [ ] T010 Write the methods and results account in `docs/research.md`.
    Link the text to specific output cells in `regression_summary.json` and the figure in `figures/`.
    Honestly describe the proportion of subjects processed (SC-001) and any negative findings or limitations.
    **Verification**: Assert `docs/research.md` references `final_results.csv` and `regression_summary.json`.
- [ ] T011 Verify end-to-end reproducibility and handoff.
    Execute the full pipeline from `data/raw/` to `data/results/` using the commands documented in `docs/quickstart.md`.
    Run all `pytest` contract and unit tests to confirm that the final artifacts strictly adhere to `dataset.schema.yaml` and `output.schema.yaml`.
    **Verification**: Assert all tests pass and the final `P_Value` is reproducible across two separate runs.

## Dependencies and requirement coverage

| Requirement | Task | Verification Command |
| :--- | :--- | :--- |
| FR-001 (Download) | T002 | `python code/data/download.py --verify` |
| FR-002 (Parcellate) | T002 | `ls data/processed/parcellated/*.csv` |
| FR-003/004 (Metrics) | T003, T005 | `python code/features/connectivity.py --aggregate` |
| FR-005 (Regression) | T004, T008 | `python code/analysis/regression.py` |
| FR-006 (Permutation) | T007 | `python code/analysis/permutation.py` |
| FR-007 (CSV Output) | T008 | `python tests/test_contracts.py` |
| FR-008 (Null Model) | T006 | `python code/features/null_model.py` |
| FR-009 (FDR) | T008 | `grep "FDR_Q_Value" data/results/regression_summary.json` |
| SC-001 (Success Rate) | T002, T010 | `cat data/processed/exclusion_log.csv` |
| SC-003/004 (Stats) | T007, T008 | `cat data/results/regression_summary.json` |

**Execution Order**: T001 $\to$ T002 $\to$ T003 $\to$ T004 $\to$ T005 $\to$ T006 $\to$ T007 $\to$ T008 $\to$ T009 $\to$ T010 $\to$ T011.