# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/taxa_results.schema.yaml`, existing code under `code/src/pipeline/`, and the user‑provided raw files in `data/raw/`.

The goal is to deliver a reproducible, CPU‑tractable end‑to‑end analysis that satisfies **all** functional requirements (FR‑001 – FR‑010) and success criteria (SC‑001 – SC‑006).  
Tasks are ordered to respect data flow; independent tasks are marked `[P]` only when they truly have no ordering constraints.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run an executable analysis on valid, small real inputs early. |
|------|---------------------------------------------------------------|

- [ ] T001 Validate raw input files and provenance (pre‑processed requirement)   <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
  - **Description**: `code/src/pipeline/ingest.py` checks that `data/raw/open_asv.csv` and `data/raw/open_clinical.parquet` exist, contain the required columns, **and** that the ASV table includes a column `preprocessed` with value `True` indicating it has passed the PPMI QC pipeline. It aborts with a clear error if any check fails.  
  - **File(s)**: `data/raw/open_asv.csv`, `data/raw/open_clinical.parquet`  
  - **Verification**: Unit tests `code/tests/test_ingest_preprocessed.py` pass; the command `python -m code.src.pipeline.ingest` exits with status 0 and logs the SHA‑256 checksums of the raw files.

- [ ] T002 Preprocess data: filter, CLR transform, and top‑100 taxa subsampling  
  - **Description**: `code/src/pipeline/preprocess.py` (a) loads the raw CSV/Parquet, (b) merges on `patient_id` + `visit_date`, (c) retains only PD patients with **≥ 2 visits** (logs exclusion count, FR‑002), (d) drops taxa with all‑zero counts (warning), (e) adds a pseudocount = 1e‑6 and applies a centered‑log‑ratio (CLR) transformation via `scikit‑bio` (FR‑003), (f) if the retained taxa exceed the RAM budget, selects the **top 100 most abundant taxa** (FR‑010).  
  - **Outputs**: `data/processed/filtered_samples.parquet`, `data/processed/clr_abundances.parquet`  
  - **Verification**: `code/tests/test_preprocess.py` confirms correct patient‑visit filtering, CLR shape, and that the taxa count does not exceed 100 when the RAM guard triggers.

- [X] T003 Compute per‑patient slopes for taxa abundances and clinical outcome  
  - **Description**: `code/src/pipeline/slopes.py` parses `visit_date` to exact years, fits a simple linear regression for each patient‑taxon pair on the CLR‑transformed abundances to obtain a slope (FR‑004), and fits a regression of `MDS_UPDRS_total` vs. time per patient to obtain the clinical slope.  
  - **Outputs**: `data/processed/patient_taxon_slopes.parquet`, `data/processed/patient_outcome_slopes.parquet` (the latter is omitted only if the outcome column is missing, as flagged by T001).  
  - **Verification**: `code/tests/test_slopes.py` checks correct handling of exactly two visits, correct year calculation, and that single‑visit patients are excluded.

- [ ] T004 Compute covariate‑adjusted Spearman correlation of slopes with BH correction  
  - **Description**: `code/src/pipeline/correlation.py` loads the two slope files, **first residualizes** both taxon‑slope and outcome‑slope on age, sex, and levodopa dose (linear regression), then computes a Spearman rank correlation between the residualized vectors for each taxon (partial correlation, satisfying User Story 1). It applies Benjamini‑Hochberg FDR correction across all taxa (FR‑006) and writes two result files:  
    - `results/taxa_correlations.csv` (unadjusted Spearman, for reference)  
    - `results/taxa_correlations_adj.csv` (covariate‑adjusted Spearman)  
  - **Output**: `results/taxa_correlations_adj.csv` conforms to the `correlation` section of `taxa_results.schema.yaml`.  
  - **Verification**: Contract test `code/tests/contract/test_contracts.py` validates the CSV schema; `code/tests/test_correlation_adj.py` asserts that residualization was performed and that BH‑adjusted p‑values are monotonic.

- [X] T005 Fit Linear Mixed‑Effects models with covariate adjustment and BH correction  
  - **Description**: `code/src/pipeline/mixed_effects.py` builds a long‑format table, drops any zero‑variance covariates with a warning, and for each retained taxon fits a mixed‑effects model  
    `MDS_UPDRS_total ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)`  
    using `statsmodels`. It extracts the `Time × Taxon` interaction coefficient, its standard error, raw p‑value, and applies BH correction (FR‑005, FR‑006).  
  - **Output**: `results/mixed_effects_summary.csv` (conforms to the `mixed_effects` section of the schema).  
  - **Verification**: `code/tests/test_mixed_effects.py` fits the model on a tiny synthetic dataset with a known interaction and checks the recovered coefficient; contract test validates the CSV.

- [ ] T006 Perform permutation robustness test (1 000 iterations) preserving within‑patient order   <!-- FAILED-IN-EXECUTION: code/src/pipeline/run_permutation.py exit=1 -->
  - **Description**: `code/src/pipeline/permutation.py` seeds `np.random.seed(42)`, shuffles **patient identifiers** while keeping each patient’s internal time series intact, re‑fits the same mixed‑effects model as in T005 for each iteration, records the interaction p‑value, and computes empirical p‑values as the proportion of permuted p‑values ≤ the observed raw p‑value. The script aborts gracefully if the block exceeds **4 hours**, writing any partial results and logging the breach (FR‑007).  
  - **Output**: `results/permutation_pvalues.csv` (conforms to the `permutation` section of the schema).  
  - **Verification**: `code/tests/test_permutation.py` confirms (i) patient‑level time ordering is unchanged after shuffling, (ii) empirical p‑values lie in [0, 1], (iii) the 4‑hour guard triggers on a mocked long run.

- [ ] T007 Runtime and resource monitoring (≤ 6 h total, ≤ 4 h permutation)  
  - **Description**: `code/src/pipeline/__main__.py` wraps each pipeline stage with a wall‑clock timer, writes per‑stage elapsed times to `results/runtime_log.txt`, and after the full run asserts total wall‑clock ≤ 6 h and permutation ≤ 4 h.  
  - **Output**: `results/runtime_log.txt`  
  - **Verification**: `code/tests/test_runtime_budget.py` runs a reduced‑size pipeline and checks that the log contains entries for every stage and that the assertions pass.

- [ ] T008a Execute User Story 1 (correlation‑only) end‑to‑end pipeline   <!-- FAILED-IN-EXECUTION: code/src/pipeline/run_us1.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/pipeline/run_us1.py exit=1 -->
  - **Command**: `python -m code.src.pipeline.run_us1` (or equivalent wrapper) which sequentially invokes T001 → T002 → T003 → T004 and writes `results/taxa_correlations_adj.csv` plus `results/runtime_log.txt`.  
  - **Verification**: New pytest `code/tests/test_us1_execution.py` asserts that `results/taxa_correlations_adj.csv` contains a row for every retained taxon, that BH‑adjusted p‑values are present, and that `results/runtime_log.txt` records total runtime ≤ 6 h.

- [ ] T008b Execute User Story 2 (mixed‑effects‑only) end‑to‑end pipeline  
  - **Command**: `python -m code.src.pipeline.run_us2` which runs T001 → T002 → T003 → T005 and produces `results/mixed_effects_summary.csv` plus the runtime log.  
  - **Verification**: New pytest `code/tests/test_us2_execution.py` checks schema compliance of `mixed_effects_summary.csv`, BH‑adjusted p‑values monotonicity, and runtime budget compliance.

- [ ] T008c Execute User Story 3 (permutation robustness) end‑to‑end pipeline  
  - **Command**: `python -m code.src.pipeline.run_us3` which runs T001 → T002 → T003 → T005 → T006 and yields `results/permutation_pvalues.csv` together with `results/runtime_log.txt`.  
  - **Verification**: New pytest `code/tests/test_us3_execution.py` validates schema of `permutation_pvalues.csv`, ensures empirical p‑values are in [0, 1], and confirms the permutation block respected the 4‑hour limit.

- [ ] T009 Independent validation of result integrity  
  - **Description**: `code/src/pipeline/validation.py` runs after any US execution and (i) checks that BH‑adjusted p‑values are ≥ raw p‑values and monotonically non‑increasing, (ii) verifies each taxon appears exactly once in each result file, (iii) confirms empirical permutation p‑values are reproducible under the fixed seed, and (iv) writes a human‑readable summary `results/validation_summary.txt`.  
  - **Verification**: The pytest suite must pass; the verifier reads `validation_summary.txt` to confirm consistency.

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Run the full specified analysis, produce all deliverables, and verify robustness. |
|------|-----------------------------------------------------------------------------------|

- [ ] T010 Generate the PDF report with bootstrap confidence intervals  
  - **Description**: `code/src/pipeline/report.py` reads the three result CSVs, performs **1 000 bootstrap resamples** of the mixed‑effects interaction coefficient per taxon to obtain 95 % confidence intervals, ranks taxa by BH‑adjusted p‑value, creates a table of the top 3 taxa (including Spearman ρ, BH‑adjusted p, interaction coefficient ± CI), and inserts a methods paragraph that explicitly states all findings are **associational** (FR‑009). The PDF is written to `results/PD_microbiome_progression_report.pdf`.  
  - **Verification**: `code/tests/test_report.py` parses the PDF (via `pdfminer.six`) and asserts that (i) the top‑3 table is present, (ii) each CI line contains numeric bounds, (iii) the methods paragraph contains no causal‑language keywords, and (iv) a new unit test `code/tests/test_report_causal_language.py` checks for absence of prohibited keywords.

- [ ] T011 Write a concise results handoff document for the downstream paper pipeline  
  - **File**: `specs/001-investigating-the-correlation-between-gu/results.md`  
  - **Contents**: cohort size after filtering, number of taxa tested, a short summary of the top 3 taxa (values copied verbatim from the CSVs), permutation‑test outcome, any negative findings, and explicit limitations (observational design, no metabolite data, etc.). It also lists the four primary deliverables (`taxa_correlations_adj.csv`, `mixed_effects_summary.csv`, `permutation_pvalues.csv`, `PD_microbiome_progression_report.pdf`).  
  - **Verification**: A lint script checks that every numeric entry in `results.md` matches the corresponding entry in the CSVs.

- [ ] T012 Record provenance, checksums, and random seeds in the project state file  
  - **Description**: `code/src/pipeline/provenance.py` is invoked at the end of each US run. It (a) computes SHA‑256 hashes for every file under `data/processed/` and `results/`, (b) records the random seeds used for permutation, bootstrap, and any other stochastic step, (c) records timestamps, and (d) writes a YAML state file `state/projects/PROJ-331-investigating-the-correlation-between-gu.yaml` adhering to Constitution Principles I, III, V. No other `state/` writes occur elsewhere.  
  - **Verification**: `code/tests/test_provenance.py` recomputes the hashes and confirms they match the entries in the state file; it also checks that the recorded seeds are exactly those set in the pipeline.

- [ ] T014 Verify quickstart guide coverage  
  - **Description**: `code/src/pipeline/quickstart_verify.py` runs the steps documented in `specs/001-investigating-the-correlation-between-gu/quickstart.md` (data ingestion, preprocessing, slope computation, and generation of `taxa_correlations_adj.csv`). It then checks that the resulting files exist and that the runtime log records a total duration ≤ 6 h.  
  - **Verification**: New pytest `code/tests/test_quickstart_coverage.py` ensures each step completes without error and that all expected artifacts are present.

---

## Phase 3 – Reproducible results and paper handoff  

| Goal | Provide a clean handoff to the paper‑generation stage. |
|------|------------------------------------------------------|

- [ ] T013 Verify PPMI dataset citation and provenance (enhanced)  
  - **Description**: `code/src/pipeline/verify_dataset.py` validates that the two raw files exist, checks their SHA‑256 checksums against the values recorded in the PPMI publication, and confirms the citation is reachable via the Reference‑Validator Agent **including a title‑token overlap ≥ 0.7** check.  
  - **Verification**: Unit test `code/tests/test_verify_dataset.py` passes; logs confirm successful verification and title‑token overlap metric.

### Dependency & Requirement Coverage  

| Requirement | Task(s) | Demonstration command |
|-------------|---------|-----------------------|
| FR‑001 (ingest) | T001 | `python -m code.src.pipeline.ingest` |
| FR‑002 (≥ 2‑visit filter) | T002, T008a‑c | pipeline logs “excluded patients” |
| FR‑003 (CLR) | T002 | `code/tests/test_preprocess.py` |
| FR‑004 (slope & Spearman) | T003, T004 | `results/taxa_correlations_adj.csv` |
| FR‑005 (LME) | T005 | `results/mixed_effects_summary.csv` |
| FR‑006 (BH correction) | T004, T005, T009 | contract & validation tests |
| FR‑007 (permutation) | T006, T007, T008c | `results/permutation_pvalues.csv` & runtime log |
| FR‑008 (four deliverables) | T004, T005, T006, T010 | files under `results/` |
| FR‑009 (associational framing) | T010, T011 | methods paragraph & handoff doc |
| FR‑010 (top‑100 taxa cap) | T002, T008a‑c | pipeline log “taxa subsampled to 100” |
| SC‑001 – SC‑006 | T004–T010 | validation suite & PDF report |

All tasks respect the required data‑flow ordering: T001 → T002 → T003 → (T004 or T005) → T006 → T007 → (T008a‑c) → T009 → T010 → T011 → T012 → T014 → T013. Independent tasks (e.g., T013) are marked as already completed.  

---

