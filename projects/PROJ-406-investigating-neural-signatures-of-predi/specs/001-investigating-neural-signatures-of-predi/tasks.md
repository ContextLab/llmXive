# Tasks: Investigating Neural Signatures of Predictive Processing in Visual Illusions  

**Inputs**: `spec.md`, `plan.md`, existing code under `src/`, and any reviewer feedback (none at this stage).  

The checklist implements the complete research pipeline required by the specification.  
Each task lists the scientific requirement it satisfies, the concrete output file(s), and the verification steps that the CI will run.

---  

### Phase 0 – Reproducibility  

- [~] **T000** [US0] Implement a global random‑seed utility, generate a deterministic‑seed verification log, and verify reproducibility.  
  - **File(s)**: `src/utils/seed.py` (defines `set_global_seed(42)`), `src/__init__.py` (imports the seed on package import), `outputs/seed_verification.log`.  
  - **Requirement**: Constitution I – all stochastic scripts must use a pinned seed and produce identical results on repeated runs.  
  - **Verification**:  
    1. Run `python -c "import src, numpy as np; src.utils.seed.set_global_seed(42); print(np.random.rand())"` twice, appending each output line to `outputs/seed_verification.log`.  
    2. CI asserts that the two captured values are identical and that the log contains exactly two identical lines.  

---  

### Phase 1 – Data ingestion & preprocessing  

- [ ] **T001** [P1] [US1] Download the Müller‑Lyer training dataset from the verified public source and store the raw parquet file.   <!-- FAILED-IN-EXECUTION: src/ingest/load_illusions.py exit=1 --> <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: src/ingest/load_illusions.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/ingest/load_illusions.py exit=1; src/ingest/load_illusions.py exit=1 -->
  - **File(s)**: `data/raw/muller_lyer.parquet` (raw).  
  - **Requirement**: **FR‑001** – download dataset; enforce required columns; **subject_id** must be unique (error on duplicates).  
  - **Verification**:  
    1. Execute `python -m src.ingest.load_illusions download_muller`.  
    2. Compute and record the SHA‑256 checksum of the downloaded file in `data/manifest.yaml`.  
    3. Validate that the raw parquet contains columns `subject_id`, `trial_id`, `stimulus_length`, `response_length`, `stimulus_parameters`.  
    4. CI fails if any duplicate `subject_id` values are present.  

- [ ] **T002** [P1] [US2] Download the Ponzo test dataset from the verified HuggingFace URL and store the raw parquet file.   <!-- FAILED-IN-EXECUTION: src/ingest/load_illusions.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/ingest/load_illusions.py exit=1 -->
  - **File(s)**: `data/raw/ponzo.parquet` (raw).  
  - **Requirement**: **FR‑001** – same as T001 for the second dataset; **subject_id** uniqueness enforced.  
  - **Verification**:  
    1. Execute `python -m src.ingest.load_illusions download_ponzo`.  
    2. Record the SHA‑256 checksum in `data/manifest.yaml`.  
    3. Validate required columns `subject_id`, `trial_id`, `arrow_angle`, `depth_cue`, `perceived_length`.  
    4. CI fails on any duplicate `subject_id`.  

- [ ] **T003** [P1] [US3] Clean both raw datasets: remove rows with missing critical fields, coerce types, enforce column presence, and write standardized CSVs.  
  - **File(s)**: `data/clean/clean_muller_lyer.csv`, `data/clean/clean_ponzo.csv`.  
  - **Requirement**: **FR‑001** – data‑hygiene; no fabricated data.  
  - **Verification**:  
    1. Run `python -m src.ingest.clean_illusions`.  
    2. CI validates each CSV against its respective schema (`clean-muller-lyer.schema.yaml`, `clean-ponzo.schema.yaml`).  
    3. CI confirms that after cleaning each CSV has > 0 rows and no missing values in required columns.  

- [ ] **T004** [P1] [US4] Align the two cleaned datasets, retaining only subjects present in **both** files.  
  - **File(s)**: `data/clean/aligned_subjects.csv` (single column `subject_id`).  
  - **Requirement**: **FR‑001** – exclusion of unmatched subjects before any modeling.  
  - **Verification**:  
    1. Execute `python -m src.ingest.align_subjects`.  
    2. CI checks that every `subject_id` in `aligned_subjects.csv` appears in both `clean_muller_lyer.csv` and `clean_ponzo.csv`.  
    3. CI fails if the retained subject count is < 10 (pre‑registered minimum for power analysis).  

---  

### Phase 2 – Model fitting (training illusion)  

- [ ] **T005** [P2] [US5] Implement the hierarchical predictive‑coding model and fit it to each subject’s Müller‑Lyer data using CPU‑only MLE with bounds [0.01, 10.0].  
  - **File(s)**: `src/model/predictive_coding.py` (model definition & fitting routine), `data/derived/precision_parameters.csv`.  
  - **Requirement**: **FR‑002**, **FR‑003**, **FR‑004** (fit diagnostics).  
  - **Verification**:  
    1. Run `python -m src.model.fit_muller --input data/clean/clean_muller_lyer.csv --subjects data/clean/aligned_subjects.csv --output data/derived/precision_parameters.csv`.  
    2. CI validates `precision_parameters.csv` against `precision-parameters.schema.yaml`.  
    3. CI parses the fit log to ensure `scipy.optimize.minimize` converged for every subject within 1000 iterations, that log‑likelihood improved monotonically, that no NaN/Inf values appear, **and that all estimated `lambda` values lie within [0.01, 10.0]**.  

- [ ] **T006** [P2] [US6] Generate diagnostic plots for the Müller‑Lyer model fits (subject‑wise log‑likelihoods and residual histograms).  
  - **File(s)**: `outputs/figures/muller_loglikelihood.png`, `outputs/figures/muller_residuals.png`.  
  - **Requirement**: **FR‑004** – model‑fit quality visualization.  
  - **Verification**:  
    1. Execute `python -m src.analysis.plot_muller_diagnostics --input data/derived/precision_parameters.csv --output_dir outputs/figures`.  
    2. CI asserts that both PNG files exist, are non‑empty, and that the residual histogram shows a roughly normal shape.  

---  

### Phase 3 – Susceptibility scoring (held‑out illusion)  

- [ ] **T007** [P3] [US7] Compute per‑subject Ponzo susceptibility scores (β) using the unified generative model that accounts for `arrow_angle` and `depth_cue`.  
  - **File(s)**: `src/analysis/ponzo_scoring.py`, `data/derived/ponzo_susceptibility.csv`.  
  - **Requirement**: **FR‑009**, **FR‑002** (CPU‑only implementation).  
  - **Verification**:  
    1. Run `python -m src.analysis.compute_ponzo --input data/clean/clean_ponzo.csv --subjects data/clean/aligned_subjects.csv --output data/derived/ponzo_susceptibility.csv`.  
    2. CI validates the CSV against `ponzo-susceptibility.schema.yaml`.  
    3. CI checks that all `beta` values are finite and that `r2` lies in [0, 1].  

- [ ] **T008** [P3] [US8] Produce visual diagnostics for the Ponzo susceptibility fits (residuals and observed vs. predicted length scatter).  
  - **File(s)**: `outputs/figures/ponzo_residuals.png`, `outputs/figures/ponzo_scatter.png`.  
  - **Requirement**: **FR‑007** – diagnostic visualizations.  
  - **Verification**:  
    1. Execute `python -m src.analysis.plot_ponzo_diagnostics --input data/derived/ponzo_susceptibility.csv --output_dir outputs/figures`.  
    2. CI asserts existence and non‑zero size of both PNGs; the scatter plot must contain a regression line.  

---  

### Phase 4 – Cross‑illusion prediction & validation  

- [ ] **T009** [P3] [US9] Merge the precision‑parameter table with the Ponzo susceptibility table on the aligned subject list, adding null‑model AIC/BIC placeholders.  
  - **File(s)**: `data/merged/merged_results.csv`.  
  - **Requirement**: **FR‑001** (matched IDs) and **merged‑results.schema.yaml**.  
  - **Verification**:  
    1. Run `python -m src.analysis.merge_results --precision data/derived/precision_parameters.csv --susceptibility data/derived/ponzo_susceptibility.csv --subjects data/clean/aligned_subjects.csv --output data/merged/merged_results.csv`.  
    2. CI validates the CSV against `merged-results.schema.yaml`.  

- [ ] **T016** [P3] [US10] Perform a power‑analysis using the paired subject count; abort the pipeline with a clear message if N is below the required threshold for detecting *r*≈0.30 (α = 0.05, power = 0.80).  
  - **File(s)**: `outputs/power_analysis.txt`.  
  - **Requirement**: Implements the methodological step described in the plan.  
  - **Verification**:  
    1. Execute `python -m src.analysis.power_analysis --input data/clean/aligned_subjects.csv --output outputs/power_analysis.txt`.  
    2. CI parses the text; if the required N exceeds the actual N, the run terminates with exit 1 and the message “Insufficient paired subjects for planned power.”  

- [ ] **T017** [P3] [US11] Regress λ and β on age, gender, trial count, and response‑SD; output residual CSVs for use in correlation.  
  - **File(s)**: `data/derived/lambda_residuals.csv`, `data/derived/beta_residuals.csv`.  
  - **Requirement**: Confound control before primary analysis.  
  - **Verification**:  
    1. Run `python -m src.analysis.confound_regression --merged data/merged/merged_results.csv --output_dir data/derived`.  
    2. CI checks that both residual CSVs exist, contain the same `subject_id` set as `merged_results.csv`, and that no NaN values are present.  

- [ ] **T018** [P3] [US12] Linearity diagnostics: generate scatter plot, compute Pearson *r*, Spearman ρ, fit a quadratic term, and output a diagnostics JSON report.  
  - **File(s)**: `outputs/linearity_diagnostics.json`, `outputs/figures/linearity_scatter.png`.  
  - **Requirement**: Ensure linearity assumption before primary correlation.  
  - **Verification**:  
    1. Execute `python -m src.analysis.linearity_check --lambda_residuals data/derived/lambda_residuals.csv --beta_residuals data/derived/beta_residuals.csv --output_json outputs/linearity_diagnostics.json --plot outputs/figures/linearity_scatter.png`.  
    2. CI asserts that the JSON contains keys `pearson_r`, `spearman_rho`, `quadratic_p`, and that `quadratic_p` > 0.05 (i.e., no significant non‑linearity).  

- [ ] **T010** [P3] [US13] Perform the primary Pearson correlation between λ‑residuals and β‑residuals, compute a two‑tailed p‑value, and generate a 95 % bootstrap confidence interval (≥ 1000 resamples). Save results and primary plots.  
  - **File(s)**: `outputs/correlation_results.json`, `outputs/figures/correlation_scatter.png`, `outputs/figures/bootstrap_distribution.png`.  
  - **Requirement**: **FR‑004**, **FR‑005**, **FR‑007**.  
  - **Verification**:  
    1. Execute `python -m src.analysis.correlation --lambda data/derived/lambda_residuals.csv --beta data/derived/beta_residuals.csv --output_json outputs/correlation_results.json --bootstrap 1000 --plot_dir outputs/figures`.  
    2. CI checks that the JSON contains keys `r`, `p_value`, `ci_lower`, `ci_upper`, `n_subjects`, and that `bootstrap_iterations` ≥ 1000.  
    3. CI confirms the scatter plot includes a regression line and the bootstrap histogram is present.  

- [ ] **T011** [P3] [US14] Run the shuffled‑ID control analysis with **10 000** permutations; store the null‑distribution JSON and plot.  
  - **File(s)**: `outputs/null_distribution.json`, `outputs/figures/null_histogram.png`.  
  - **Requirement**: **FR‑006** – control analysis.  
  - **Verification**:  
    1. Run `python -m src.analysis.shuffle_control --input data/merged/merged_results.csv --output_json outputs/null_distribution.json --permutations 10000 --plot_dir outputs/figures`.  
    2. CI asserts that the JSON contains `num_permutations` = 10000 and that the mean of the null distribution is ≈ 0 (±0.01).  
    3. CI checks that the histogram PNG exists.  

- [ ] **T012** [P3] [US15] Fit a Ponzo‑specific predictive‑coding model (task‑specific null) and compare its AIC/BIC to the domain‑general model; produce a side‑by‑side bar plot and a JSON comparison report.  
  - **File(s)**: `data/derived/ponzo_null_parameters.csv`, `outputs/figures/null_model_comparison.png`, `outputs/null_model_comparison.json`.  
  - **Requirement**: **FR‑008** – null‑model validation.  
  - **Verification**:  
    1. Execute `python -m src.analysis.fit_ponzo_null --input data/clean/clean_ponzo.csv --subjects data/clean/aligned_subjects.csv --output data/derived/ponzo_null_parameters.csv --plot outputs/figures/null_model_comparison.png --json outputs/null_model_comparison.json`.  
    2. CI checks that the CSV, PNG, and JSON exist; the JSON must contain keys `domain_general_aic`, `domain_general_bic`, `ponzo_null_aic`, `ponzo_null_bic`, and a paired‑t test result with `p < 0.05`.  

- [ ] **T013** [P3] [US16] Conduct a sensitivity analysis by re‑running the primary correlation under three alternative precision‑bound windows (`[0.1, 1.0]`, `[0.5, 5.0]`, `[0.01, 10.0]`). Record the resulting r‑values.  
  - **File(s)**: `outputs/sensitivity_results.csv`.  
  - **Requirement**: **SC‑006** – robustness to bound choice.  
  - **Verification**:  
    1. Run `python -m src.analysis.sensitivity_bounds --input data/merged/merged_results.csv --bounds "[0.1,1.0]" "[0.5,5.0]" "[0.01,10.0]" --output outputs/sensitivity_results.csv`.  
    2. CI ensures the CSV has three rows (one per bound set) and that the absolute difference between any two r‑values ≤ 0.05.  

---  

### Phase 5 – Reporting, reproducibility & handoff  

- [ ] **T014** [US17] Assemble a JSON summary of all primary results, compute SHA‑256 checksums for every artifact produced in Phases 1‑4, enforce the ≤ 6 h wall‑time limit, and write a runtime log.  
  - **File(s)**: `outputs/summary_report.json`, `outputs/artifact_checksums.txt`, `outputs/runtime_log.txt`.  
  - **Requirement**: Satisfies all remaining FRs indirectly, **SC‑003** (runtime), **SC‑005** (single‑test acknowledgement).  
  - **Verification**:  
    1. Run `python -m src.utils.summarize_and_check --artifacts data/clean/*.csv data/derived/*.csv data/merged/*.csv outputs/*.json outputs/figures/*.png --runtime_log outputs/runtime_log.txt`.  
    2. CI parses `summary_report.json` to confirm presence of keys `correlation`, `bootstrap_ci`, `null_control_p`, `sensitivity`, and that `runtime_seconds` ≤ 21600.  
    3. CI verifies that each file listed in `artifact_checksums.txt` has a matching SHA‑256 hash.  

- [ ] **T015** [US18] Create a short “research handoff” markdown that (i) restates the primary hypothesis, (ii) reports the final correlation coefficient with its 95 % CI and p‑value, (iii) lists all figure filenames, (iv) notes any limitations (e.g., power shortfall), and (v) explicitly acknowledges that the primary analysis is a single pre‑registered hypothesis.  
  - **File(s)**: `research_handoff.md`.  
  - **Requirement**: Phase 3 of the task template – reproducible results and paper‑stage handoff; also satisfies **SC‑005**.  
  - **Verification**:  
    1. Execute `python -m src.utils.generate_handoff --summary outputs/summary_report.json --figures outputs/figures/ --output research_handoff.md`.  
    2. CI checks that the markdown contains a table with columns `Metric` / `Value`, includes a “Limitations” section, lists every PNG filename, and contains the sentence: “**This analysis constitutes a single pre‑registered hypothesis; no multiple‑comparison correction was required.**”  

---  

### Dependency & requirement coverage  

| Task | FR(s) satisfied | SC(s) addressed |
|------|-----------------|-----------------|
| T000 | Constitution I (reproducibility) | — |
| T001‑T004 | FR‑001 (data download, cleaning, alignment) | SC‑001 (valid input), SC‑003 (runtime) |
| T005 | FR‑002, FR‑003, FR‑004 (model fitting & diagnostics) | SC‑004 (convergence) |
| T006‑T008 | FR‑009, FR‑007 (susceptibility scoring & diagnostics) | SC‑004 |
| T009‑T013 | FR‑004, FR‑005, FR‑006, FR‑007, FR‑008, FR‑009 (cross‑illusion analysis) | SC‑001 (null distribution), SC‑002 (bootstrap CI), SC‑005 (single‑test), SC‑006 (bound sensitivity) |
| T014‑T015 | All remaining FRs (metadata, reproducibility) | SC‑003 (≤ 6 h), SC‑005 (acknowledgement), SC‑006 (robustness) |

---  

**Execution order**: Tasks are listed in the exact order they must be run; each task depends on the outputs of the preceding ones (as indicated by the file paths). The top‑level command `make run_all` (generated by `quickstart.md`) will invoke the tasks sequentially and produce the end‑to‑end result required for the first checkpoint.  

---  

*All tasks are unchecked (`[ ]`) awaiting implementation; once a task passes its verification step the CI will automatically mark it `[x]`.**  