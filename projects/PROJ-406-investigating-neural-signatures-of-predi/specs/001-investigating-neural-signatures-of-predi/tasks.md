# Tasks: Investigating Neural Signatures of Predictive Processing in Visual Illusions  

**Inputs**: `spec.md`, `plan.md`, any existing code in `src/`, and reviewer feedback (none at this stage).  

The checklist below implements the full research pipeline required by the specification.  
Each task lists the scientific requirement it satisfies, the concrete output file(s), and the verification steps that the CI will run.

---  

### Phase 0 – Reproducibility setup  

- [ ] T000 [P?] [US0] Pin a global random seed (e.g., 42) and verify deterministic behavior across all analysis modules.  
  - **File(s)**: `src/utils/seed.py` (defines `set_global_seed(42)`), `src/__init__.py` (imports seed on package load).  
  - **Requirement**: Constitution Principle I (Reproducibility) – all stochastic scripts must use the pinned seed.  
  - **Verification**:  
    1. Run `python -c "import src, numpy as np; src.utils.seed.set_global_seed(42); print(np.random.rand())"` and capture the output.  
    2. Re‑run the same command a second time; assert the two outputs are identical.  

### Phase 1 – Data ingestion & preprocessing  

- [ ] T001 [P1] [US1] Download the Müller‑Lyer training dataset from the verified OpenNeuro URL and store the raw parquet file.   <!-- FAILED-IN-EXECUTION: src/ingest/load_illusions.py exit=1 -->
  - **File(s)**: `data/raw/muller_lyer.parquet` (raw), `data/clean/clean_muller_lyer.csv` (cleaned).  
  - **Requirement**: FR‑001 – download and parse dataset; enforce column presence and subject‑ID uniqueness.  
  - **Verification**:  
    1. Run `python -m src.ingest.load_illusions download_muller`.  
    2. Validate `clean_muller_lyer.csv` against `contracts/clean-muller-lyer.schema.yaml`.  
    3. Check that critical columns (`subject_id`, `stimulus_type`, `response`, `trial_id`, `stimulus_parameters`) contain no missing values and that duplicate `subject_id` entries within the file are flagged as warnings (not errors).  

- [ ] T002 [P1] [US2] Download the Ponzo test dataset from the verified OpenNeuro URL and store the raw parquet file.  
  - **File(s)**: `data/raw/ponzo.parquet` (raw), `data/clean/clean_ponzo.csv` (cleaned).  
  - **Requirement**: FR‑001 – same as above for the second dataset.  
  - **Verification**:  
    1. Run `python -m src.ingest.load_illusions download_ponzo`.  
    2. Validate `clean_ponzo.csv` against `contracts/clean-ponzo.schema.yaml`.  
    3. Ensure no missing values in `subject_id`, `response`, or geometric parameters (`arrow_angle`, `depth_cue`).  

- [ ] T003 [P1] [US3] Consolidate and align the two cleaned CSVs, keeping only subjects present in **both** files.  
  - **File(s)**: `data/clean/aligned_subjects.csv` (list of matched IDs).  
  - **Requirement**: FR‑001 – exclusion of unmatched subjects.  
  - **Verification**:  
    1. Run `python -m src.ingest.align_subjects`.  
    2. Assert that every `subject_id` in the output appears in both `clean_muller_lyer.csv` and `clean_ponzo.csv`.  
    3. Record the number of retained subjects; fail if < 10 (pre‑registered minimum for power analysis).  

---  

### Phase 2 – Model fitting (training illusion)  

- [ ] T004 [P2] [US4] Implement the hierarchical predictive‑coding model and fit it to each subject’s Müller‑Lyer data using CPU‑only MLE.  
  - **File(s)**: `src/model/predictive_coding.py` (model definition), `data/derived/precision_parameters.csv`.  
  - **Requirement**: FR‑002 – hierarchical model; FR‑003 – parameter bounds `[0.01, 10.0]`.  
  - **Verification**:  
    1. Execute `python -m src.model.fit_muller --input data/clean/clean_muller_lyer.csv --output data/derived/precision_parameters.csv`.  
    2. Confirm that `scipy.optimize.minimize` converges within 1000 iterations for every subject (log‑likelihood improves monotonically).  
    3. Validate that `precision_parameters.csv` conforms to `contracts/precision-parameters.schema.yaml` (no NaN/Inf, bounds respected).  

- [ ] T005 [P2] [US5] Generate diagnostic plots for model fit quality.  
  - **File(s)**: `outputs/figures/muller_fit_residuals.png`, `outputs/figures/subject_loglikelihood.png`.  
  - **Requirement**: FR‑004 – fit diagnostics.  
  - **Verification**:  
    1. Run `python -m src.analysis.plot_fit_diagnostics`.  
    2. CI checks that the PNG files exist and are > 0 KB.  

---  

### Phase 3 – Susceptibility scoring (held‑out illusion)  

- [ ] T006 [P3] [US6] Compute per‑subject Ponzo susceptibility scores using the unified generative model (accounts for arrow angle, depth cue, etc.).  
  - **File(s)**: `src/analysis/ponzo_scoring.py`, `data/derived/ponzo_susceptibility.csv`.  
  - **Requirement**: FR‑009 – generative model for β; FR‑002 (use only CPU libraries).  
  - **Verification**:  
    1. Run `python -m src.analysis.compute_ponzo --input data/clean/clean_ponzo.csv --output data/derived/ponzo_susceptibility.csv`.  
    2. Validate against `contracts/ponzo-susceptibility.schema.yaml` (β unrestricted, `beta_r2` ∈ [0,1]).  

- [ ] T007 [P3] [US7] Produce visual diagnostics for the Ponzo fit ( residuals, observed vs. predicted length).  
  - **File(s)**: `outputs/figures/ponzo_fit_residuals.png`, `outputs/figures/ponzo_scatter.png`.  
  - **Requirement**: FR‑007 – diagnostic plots.  
  - **Verification**:  
    1. Run `python -m src.analysis.plot_ponzo_diagnostics`.  
    2. CI asserts PNG existence and that the scatter plot includes a regression line.  

---  

### Phase 4 – Cross‑illusion prediction & validation  

- [ ] T008 [P3] [US8] Merge the precision‑parameter table with the Ponzo susceptibility table on the aligned subject list.  
  - **File(s)**: `data/merged/merged_results.csv`.  
  - **Requirement**: FR‑001 (matching IDs) + schema `contracts/merged-results.schema.yaml`.  
  - **Verification**:  
    1. Run `python -m src.analysis.merge_results`.  
    2. Validate the CSV against `merged-results.schema.yaml`.  

- [ ] T009 [P3] [US9] Perform the primary Pearson correlation between λ (precision) and β (susceptibility), outputting coefficient, p‑value, 95 % CI from ≥ 1000 bootstrap resamples, and record the iteration count.  
  - **File(s)**: `outputs/correlation_results.json`, `outputs/figures/correlation_scatter.png`, `outputs/figures/bootstrap_distribution.png`.  
  - **Requirement**: FR‑004, FR‑005, FR‑006, FR‑007.  
  - **Verification**:  
    1. Run `python -m src.analysis.correlation --input data/merged/merged_results.csv --output outputs/correlation_results.json`.  
    2. CI checks that the JSON contains keys `r`, `p_value`, `ci_lower`, `ci_upper`, `n_subjects`, **and** `bootstrap_iterations` (≥ 1000).  
    3. Load `outputs/null_distribution.json` (produced by T010) and verify that `r` exceeds the null‑distribution mean with a two‑sided p < 0.05.  
    4. Verify that the bootstrap histogram PNG exists and that the scatter plot PNG includes the regression line and 95 % CI shading.  

- [ ] T010 [P3] [US10] Execute the shuffled‑ID control analysis with exactly 10 000 permutations and store the null‑distribution JSON.  
  - **File(s)**: `outputs/null_distribution.json`, `outputs/figures/null_histogram.png`.  
  - **Requirement**: FR‑006 – control analysis.  
  - **Verification**:  
    1. Run `python -m src.analysis.shuffle_control --input data/merged/merged_results.csv --output outputs/null_distribution.json --permutations 10000`.  
    2. CI asserts that the JSON contains a field `num_permutations` equal to 10000 and that the mean of the null distribution is ≈ 0.  
    3. CI asserts that the histogram PNG exists.  

- [ ] T011 [P3] [US11] Fit a Ponzo‑specific predictive‑coding model (task‑specific null) and compare its predictive performance to the domain‑general model.  
  - **File(s)**: `data/derived/ponzo_null_parameters.csv`, `outputs/figures/null_model_comparison.png`.  
  - **Requirement**: FR‑008 – null model validation.  
  - **Verification**:  
    1. Run `python -m src.analysis.fit_ponzo_null --input data/clean/clean_ponzo.csv --output data/derived/ponzo_null_parameters.csv`.  
    2. Compute AIC/BIC for both models and generate a side‑by‑side bar plot.  
    3. CI checks that the domain‑general model has a lower (better) AIC/BIC with a paired‑t test p < 0.05 **and** that the final report (see T015) contains a statement acknowledging the single‑test nature of the primary hypothesis.  

- [ ] T012 [P3] [US12] Conduct a sensitivity analysis by re‑running the correlation with three alternative precision‑bound windows (`[0.1,1.0]`, `[0.5,5.0]`, `[0.01,10.0]`) and record the resulting r‑values.  
  - **File(s)**: `outputs/sensitivity_results.csv`.  
  - **Requirement**: SC‑006 (robustness to bound choice).  
  - **Verification**:  
    1. Run `python -m src.analysis.sensitivity_bounds --input data/merged/merged_results.csv --output outputs/sensitivity_results.csv`.  
    2. CI ensures the CSV has three rows (one per bound set) and that r‑values do not vary beyond ±0.05.  

---  

### Phase 5 – Runtime enforcement  

- [ ] T016 [P?] [US16] Measure total pipeline wall‑time and enforce the ≤ 6 h limit on a free‑tier GitHub Actions runner.  
  - **File(s)**: `outputs/runtime_log.txt`.  
  - **Requirement**: SC‑003 – pipeline must complete within 6 h.  
  - **Verification**:  
    1. The top‑level orchestrator (`make run_all` or `src/utils/run_all.py`) records start and end timestamps to `outputs/runtime_log.txt`.  
    2. CI parses the log, computes elapsed seconds, and asserts it is ≤ 21600 s (6 h).  

---  

### Phase 6 – Reporting, reproducibility & handoff  

- [ ] T013 [P?] [US13] [SC-003] Assemble a JSON summary of all primary results (correlation, bootstrap CI, null‑control p‑value, sensitivity check) and compute SHA‑256 checksums for every artifact produced in Phases 1‑4.  
  - **File(s)**: `outputs/summary_report.json`, `outputs/artifact_checksums.txt`.  
  - **Requirement**: All FRs indirectly; SC‑003 (runtime & reproducibility).  
  - **Verification**:  
    1. Run `python -m src.utils.summarize_results`.  
    2. CI parses `summary_report.json` and confirms presence of keys `correlation`, `bootstrap_ci`, `null_p`, `sensitivity`.  
    3. Verify that each listed artifact path has a matching SHA‑256 entry in `artifact_checksums.txt`.  

- [ ] T014 [P?] [US14] [SC-003] Update the project‑state YAML (`state/projects/PROJ-406-investigating-neural-signatures-of-predi.yaml`) with the new checksums, timestamps, and a brief “validation‑complete” flag.  
  - **File(s)**: `state/projects/PROJ-406-investigating-neural-signatures-of-predi.yaml`.  
  - **Requirement**: Constitution principle V (single source of truth).  
  - **Verification**:  
    1. Run `python -m src.utils.update_state --summary outputs/summary_report.json`.  
    2. CI checks that the YAML contains `validation_status: complete` and that the checksum entries match those in `artifact_checksums.txt`.  

- [ ] T015 [P?] [US15] [SC-005] Create a short “research handoff” markdown (`research_handoff.md`) that lists: (i) the primary hypothesis, (ii) the final correlation result with CI, (iii) all figure filenames, (iv) any limitations discovered (e.g., sample‑size power shortfall), **and** an explicit acknowledgement that the primary analysis is a single‑test (or that a multiple‑comparison correction was applied).  
  - **File(s)**: `research_handoff.md`.  
  - **Requirement**: Phase 3 of the template – reproducible results and paper handoff; also satisfies SC‑005.  
  - **Verification**:  
    1. Run `python -m src.utils.generate_handoff`.  
    2. CI validates that the markdown contains a table with columns `Metric`, `Value`, includes a “Limitations” section, and contains the sentence “This analysis constitutes a single pre‑registered hypothesis; no multiple‑comparison correction was required.”  

---  

### Dependencies & requirement coverage  

| Task | FR(s) satisfied | SC(s) addressed |
|------|----------------|-----------------|
| T000 | Constitution I (seed) | — |
| T001‑T003 | FR‑001 | SC‑001, SC‑003 |
| T004‑T005 | FR‑002, FR‑003, FR‑004 | SC‑004 |
| T006‑T007 | FR‑009, FR‑007 | SC‑004 |
| T008‑T012 | FR‑004, FR‑005, FR‑006, FR‑007, FR‑008 | SC‑001, SC‑002, SC‑005, SC‑006 |
| T016 | — | SC‑003 (runtime) |
| T013‑T015 | All remaining FRs (metadata, reproducibility) | SC‑003, SC‑005 |
|  |  |  |

---  

**Execution order**: Tasks are listed in the order they must be run; each task depends on the outputs of the preceding ones (as indicated by file paths). Running the top‑level command `make run_all` (generated by the quickstart) will invoke the tasks sequentially and produce the end‑to‑end result required for the first checkpoint.  

---  

*All tasks are unchecked (`[ ]`) awaiting implementation; once a task passes its verification step it will be marked `[x]` by the CI.*  