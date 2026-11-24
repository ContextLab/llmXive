# Tasks: Gut Microbiome and Cognitive Decline Analysis

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Goal**: Investigate the correlation between gut microbiome composition (AGP) and cognitive decline (HRS) in aging populations (age $\ge 60$).

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the pipeline and run a thin, executable analysis on a small real-data subset to verify the full data flow from ingestion to prediction.

- [ ] T001 Establish the project layout, pinned dependencies in `code/requirements.txt`, and validate input provenance. <!-- FAILED-IN-EXECUTION: code/validate_provenance.py exit=1 --> <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: code/validate_provenance.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/validate_provenance.py exit=1 -->
    - Verify access to American Gut Project (AGP) via `datasets.load_dataset("american_gut_project", streaming=True)` and Health and Retirement Study (HRS) portal.
    - Document the runnable command in `docs/quickstart.md`.
    - Ensure the CPU-only resource guard is active ($\le 7$ GB RAM, $\le 6$ hours).
- [ ] T002 Implement the primary research pipeline scripts with granular verification: <!-- FAILED-IN-EXECUTION: code/01_data_ingestion.py exit=1; code/02_preprocessing.py exit=1; code/03_correlation_analysis.py exit=1; code/04_predictive_modeling.py exit=1 --> <!-- FAILED: unspecified -->
    - **Ingestion (`code/01_data_ingestion.py`)**: Stream AGP data, merge with HRS by participant ID. Calculate and log the merge success rate (overlap / total AGP IDs) to satisfy SC-001; fail loudly if overlap $< 500$ samples.
    - **Preprocessing (`code/02_preprocessing.py`)**: Filter age $\ge 60$, collapse to genus, apply Cumulative Sum Scaling (CSS) normalization (per plan.md), and impute BMI via MICE.
    - **Analysis (`code/03_correlation_analysis.py`)**: Apply CLR transformation. Compute Spearman rank correlations (per spec.md) AND SparCC/SPIEC-EASI compositional correlations (per plan.md). Apply Benjamini-Hochberg FDR ($\alpha=0.05$).
    - **Modeling (`code/04_predictive_modeling.py`)**: Train Random Forest regressor. Implement a hyperparameter grid search over `n_estimators` and `max_depth` as required by Constitution VII. Use 5-fold CV on CLR data.
- [ ] T003 Run a thin end-to-end analysis on a small valid sample (e.g., first 1000 participants) to produce initial results. <!-- FAILED: unspecified -->
    - Output: `data/results/thin_run_summary.json` containing sample count, merge success rate, number of significant taxa, and baseline $R^2$.
    - Check: Verify the pipeline completes without OOM errors and produces artifacts conforming to `dataset.schema.yaml` and `correlation.schema.yaml`.

## Phase 2: Complete the study and validate its evidence

**Goal**: Execute the full-scale analysis on the target population and perform rigorous statistical validation to ensure results are not artifacts of noise or collinearity.

- [ ] T004 Execute the complete analysis on the full target population (age $\ge 60$). <!-- FAILED: unspecified -->
    - Process the full merged dataset and save `data/processed/merged_age60.csv` and `data/processed/corpus_clr.parquet`.
    - Generate the final association table in `data/processed/correlation_results.csv`, ensuring all significant pairs are labeled as "associational".
    - Check: Verify the output matches the `correlation.schema.yaml` contract.
- [ ] T005 Perform robustness validation: Permutation null distribution and VIF collinearity check.
    - Compute a null distribution of $R^2$ via 1000 label shuffles; save the 95th percentile threshold to `data/processed/null_threshold.json`.
    - Calculate Variance Inflation Factors (VIF) for top predictive taxa; flag any pair with $\text{VIF} > 5$ in `data/processed/vif_report.json`.
    - **Resource Measurement**: Record and log peak memory usage during the permutation process to `data/processed/resource_usage.json` to satisfy SC-004.
    - Check: Verify the primary model's $R^2$ exceeds the null threshold in `data/processed/significance_verification.json`.
- [ ] T006 Run sensitivity analysis on rarefaction depth thresholds (FR-002).
    - Sweep the rarefaction depth over $\{5,000, \text{min\_depth}\}$ and re-evaluate model $R^2$ at each step to validate the CSS-based primary analysis.
    - Output: `data/processed/sensitivity_variance_report.json` reporting the variance in performance metrics.
    - Check: Ensure the process fails gracefully (exit code 1) if RAM exceeds 7 GB during the sweep.
- [ ] T007 Generate final scientific figures and interpretability artifacts.
    - Compute feature importance using BOTH permutation importance and SHAP values (per Constitution VII).
    - Save the top-ranking genera for both methods to `data/processed/importance_analysis.json`.
    - Produce a figure of the top 20 taxa by SHAP importance in `figures/shap_importance.png`.
    - Produce a plot of $R^2$ vs. rarefaction depth in `figures/rarefaction_sensitivity.png`.

## Phase 3: Reproducible results and paper handoff

**Goal**: Synthesize the findings into a reproducible account and prepare the project for the paper pipeline.

- [ ] T008 Write the methods and results account in `docs/paper_draft.md`.
    - Link the text directly to `data/processed/correlation_results.csv`, `data/processed/significance_verification.json`, and the figures in `figures/`.
    - Honestly document any negative findings (e.g., taxa that failed VIF check) and limitations regarding the associational nature of the data.
- [ ] T009 Perform a final reproducibility run and document the handoff.
    - Execute the full workflow from raw inputs to final figures using the documented quickstart.
    - Verify that all artifact checksums are consistent and the final $R^2$ is reproducible given the fixed random seed.
    - Output: `docs/handoff_receipt.md` confirming all requirements in `spec.md` are satisfied.

## Dependencies and requirement coverage

| Requirement | Task(s) | Verification Command |
| :--- | :--- | :--- |
| **FR-001 (Ingest/Merge)** | T002, T004 | `pytest tests/contract/test_data_merge.py` |
| **FR-002 (Rarefy/Genus)** | T006 | Check `data/processed/sensitivity_variance_report.json` |
| **FR-003 (Spearman/FDR)** | T002, T004 | `pytest tests/contract/test_correlation.py` |
| **FR-004 (Random Forest)** | T002, T004 | Check `data/models/model.pkl` and `hyperparams.json` |
| **FR-005 (Sensitivity)** | T006 | Check `data/processed/sensitivity_variance_report.json` |
| **FR-006 (VIF/CLR)** | T002, T005 | Check `data/processed/vif_report.json` |
| **FR-007 (Resource Limits)** | T001, T006 | Check `data/processed/run.log` for resource guards |
| **SC-001 (Merge Rate)** | T002, T003 | Check `data/results/thin_run_summary.json` for overlap rate |
| **SC-002 (Sig Assoc)** | T004 | Check `data/processed/correlation_results.csv` against $\alpha=0.05$ |
| **SC-003 (Null Dist)** | T005 | Check `data/processed/significance_verification.json` |
| **SC-004 (Peak RAM)** | T005 | Check `data/processed/resource_usage.json` |