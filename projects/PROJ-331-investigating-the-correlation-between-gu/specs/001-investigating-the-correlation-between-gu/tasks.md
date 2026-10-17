# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/taxa_results.schema.yaml`, any existing code under `code/src/pipeline/`, and user‑provided raw files in `data/raw/`.

The goal is to deliver a reproducible, CPU‑tractable end‑to‑end analysis that satisfies **all** functional requirements (FR‑001 – FR‑010) and success criteria (SC‑001 – SC‑006).  
Tasks are ordered to respect data flow; independent tasks are marked `[P]` only when they truly have no ordering constraints.

---  

## Phase 1 – Data ingestion, preprocessing, and slope computation  

- [ ] **T001** [P] Validate raw input files and record provenance   <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: code/src/pipeline/generate_dummy_data.py exit=1; code/src/pipeline/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/pipeline/ingest.py exit=1 --> <!-- FAILED: unspecified -->
  - **Description**: `code/src/pipeline/ingest.py` checks that `data/raw/open_asv.csv` and `data/raw/open_clinical.parquet` exist, are readable, and contain the required columns (`sample_id`, `patient_id`, `visit_date`, taxon count columns; `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, `MDS_UPDRS_total`). It aborts with a clear error if any check fails. The script computes SHA‑256 hashes of both files and writes them to `state/ingest_provenance.json`.  
  - **Artifacts**: `data/raw/open_asv.csv`, `data/raw/open_clinical.parquet`, `state/ingest_provenance.json`  
  - **Verification**: Unit test `code/tests/test_ingest.py` passes; running `python -m code.src.pipeline.ingest` exits with status 0 and the JSON contains the two hashes.

- [ ] **T002** Preprocess data: filter, CLR transform, and deterministic top‑100 taxa selection  
  - **Description**: `code/src/pipeline/preprocess.py` (a) loads the raw files, (b) merges on `patient_id` + `visit_date`, (c) retains only PD patients with **≥ 2 visits** (logs exclusion count, satisfies FR‑002), (d) drops taxa that are all‑zero across retained samples (emits a warning), (e) adds a pseudocount = 1e‑6 and applies a centered‑log‑ratio (CLR) transformation via `scikit‑bio` (FR‑003), (f) computes the mean CLR abundance of each taxon across all retained samples, sorts taxa by this mean, and **keeps the top 100 most abundant taxa** (deterministic, no random seed), (g) writes the processed tables.  
  - **Artifacts**: `data/processed/filtered_samples.parquet`, `data/processed/clr_abundances.parquet`  
  - **Verification**: `code/tests/test_preprocess.py` confirms patient‑visit filtering, correct CLR shape, and that exactly 100 taxa are retained when the original set exceeds 100.

- [ ] **T003** Compute per‑patient slopes for CLR abundances and clinical outcome  
  - **Description**: `code/src/pipeline/slopes.py` parses `visit_date` to fractional years, fits an ordinary least‑squares regression for each patient‑taxon pair on the CLR‑transformed abundances to obtain a slope **whenever the patient has ≥ 2 visits** (the minimum for OLS). For patients with exactly 2 visits, the slope is the simple difference and a flag `unstable=True` is set. It similarly fits a regression of `MDS_UPDRS_total` vs. time per patient (requires ≥ 2 visits) to obtain the clinical slope.  
  - **Artifacts**: `data/processed/patient_taxon_slopes.parquet`, `data/processed/patient_outcome_slopes.parquet`  
  - **Verification**: `code/tests/test_slopes.py` checks correct handling of exactly two visits, correct year conversion, and that the `unstable` flag is set only for the 2‑visit case.

---  

## Phase 2 – Core statistical analyses and resource monitoring  

- [ ] **T004** Plain Spearman correlation with BH correction  
  - **Description**: `code/src/pipeline/correlation.py` loads the two slope files, uses `scipy.stats.spearmanr` to compute a **plain Spearman** rank correlation between each taxon‑slope and the outcome‑slope (no covariate adjustment). It collects raw ρ and p‑values, applies Benjamini‑Hochberg FDR across all taxa (FR‑006), and writes `results/taxa_correlations.csv`.  
  - **Artifacts**: `results/taxa_correlations.csv`  
  - **Verification**: Contract test `code/tests/contract/test_contracts.py` validates the CSV against `contracts/taxa_results.schema.yaml` (correlation section); `code/tests/test_correlation.py` asserts that BH‑adjusted p‑values are monotonic and that no covariates were used.

- [X] **T005** Linear Mixed‑Effects modeling per taxon with interaction term (exact spec formula)  
  - **Description**: `code/src/pipeline/mixed_effects.py` builds a long‑format dataset (one row per observation), drops any zero‑variance covariates with a warning, and fits for each retained taxon the model  
    `MDS_UPDRS_total ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)`  
    using `statsmodels`. It extracts the `Time × Taxon` interaction coefficient, its standard error, and raw p‑value, then applies BH correction (FR‑006). Results are written to `results/mixed_effects_summary.csv`.  
  - **Artifacts**: `results/mixed_effects_summary.csv`  
  - **Verification**: `code/tests/test_mixed_effects.py` fits the model on a tiny synthetic dataset with a known interaction and checks recovery; contract test validates schema (mixed_effects section).

- [ ] **T006** Permutation robustness test (1 000 block‑wise shuffles)  
  - **Description**: `code/src/pipeline/permutation.py` seeds `np.random.seed(42)`, shuffles **patient identifiers** while preserving each patient’s internal chronological order, re‑fits the LME (as in T005) for each iteration, records the interaction p‑value, and computes an empirical p‑value as the proportion of permuted p‑values ≤ the observed raw p‑value. The script aborts gracefully if the block exceeds **4 hours**, writing any partial results and logging the breach (FR‑007).  
  - **Artifacts**: `results/permutation_pvalues.csv`  
  - **Verification**: `code/tests/test_permutation.py` confirms (i) patient‑level time ordering is unchanged after shuffling, (ii) empirical p‑values lie in [0, 1], (iii) the 4‑hour guard triggers on a mocked long run.

- [ ] **T007** Runtime and resource monitoring (≤ 6 h total, ≤ 4 h permutation)   <!-- FAILED-IN-EXECUTION: code/src/pipeline/__main__.py exit=1; tests/test_runtime_budget_execution.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/src/pipeline/__main__.py exit=1 -->
  - **Description**: `code/src/pipeline/__main__.py` wraps each pipeline stage (T001‑T006) with a wall‑clock timer, writes per‑stage elapsed times to `results/runtime_log.txt`, and after the full run asserts total wall‑clock ≤ 6 h and permutation ≤ 4 h. It imports only the existing stage modules (`ingest`, `preprocess`, `slopes`, `correlation`, `mixed_effects`, `permutation`). If a limit is exceeded, the run aborts with an informative error.  
  - **Artifacts**: `results/runtime_log.txt`  
  - **Verification**: `code/tests/test_runtime_budget.py` runs a reduced‑size pipeline and checks that the log contains entries for every stage and that the assertions pass.

---  

## Phase 3 – End‑to‑end user‑story wrappers, reporting, and handoff  

- [ ] **T008** Execute User Story 1 (correlation‑only) end‑to‑end pipeline   <!-- FAILED-IN-EXECUTION: code/src/pipeline/run_us1.py exit=1 -->
  - **Description**: `code/src/pipeline/run_us1.py` sequentially invokes T001 → T002 → T003 → T004, then writes `results/taxa_correlations.csv` and `results/runtime_log.txt`.  
  - **Artifacts**: `results/taxa_correlations.csv`, `results/runtime_log.txt`  
  - **Verification**: `code/tests/test_us1_execution.py` asserts that the correlation file contains a row for every retained taxon, that BH‑adjusted p‑values are present, and that total runtime ≤ 6 h.

- [ ] **T009** Execute User Story 2 (mixed‑effects‑only) end‑to‑end pipeline  
  - **Description**: `code/src/pipeline/run_us2.py` runs T001 → T002 → T003 → T005, producing `results/mixed_effects_summary.csv` and the runtime log.  
  - **Artifacts**: `results/mixed_effects_summary.csv`, `results/runtime_log.txt`  
  - **Verification**: `code/tests/test_us2_execution.py` checks schema compliance, monotonic BH‑adjusted p‑values, and runtime budget compliance.

- [ ] **T010** Execute User Story 3 (permutation robustness) end‑to‑end pipeline  
  - **Description**: `code/src/pipeline/run_us3.py` runs T001 → T002 → T003 → T005 → T006, yielding `results/permutation_pvalues.csv` and the runtime log.  
  - **Artifacts**: `results/permutation_pvalues.csv`, `results/runtime_log.txt`  
  - **Verification**: `code/tests/test_us3_execution.py` validates the permutation CSV schema, empirical p‑value range, and that the permutation block respected the 4‑hour limit.

- [ ] **T011** Generate PDF report with bootstrap confidence intervals  
  - **Description**: `code/src/pipeline/report.py` reads the three result CSVs, performs **1 000 bootstrap resamples** of the LME interaction coefficient per taxon to obtain 95 % confidence intervals, ranks taxa by BH‑adjusted p‑value, selects the top 3, and creates a concise PDF (`results/PD_microbiome_progression_report.pdf`) containing: (i) a table of the top 3 taxa with Spearman ρ, BH‑adjusted p, interaction coefficient ± CI, (ii) a methods paragraph that explicitly states all findings are **associational** (FR‑009) and a brief power‑limitation statement.  
  - **Artifacts**: `results/PD_microbiome_progression_report.pdf`  
  - **Verification**: `code/tests/test_report.py` parses the PDF (via `pdfminer.six`) and asserts presence of the top‑3 table, numeric CI bounds, and absence of prohibited causal‑language keywords.

- [ ] **T012** Write results handoff document for downstream paper pipeline  
  - **Description**: Create `specs/001-investigating-the-correlation-between-gu/results.md` summarizing: cohort size after filtering, number of taxa tested, the exact values (Spearman ρ, BH‑adjusted p, interaction coefficient ± CI) for the top 3 taxa (copied verbatim from the CSVs), permutation‑test outcome, any negative findings, and explicit limitations (observational design, sample size, etc.). List the four primary deliverables.  
  - **Artifacts**: `specs/001-investigating-the-correlation-between-gu/results.md`  
  - **Verification**: Lint script `code/src/pipeline/validate_results_md.py` checks that every numeric entry matches the corresponding entry in the CSVs.

- [ ] **T013** Record provenance, checksums, and random seeds in project state file  
  - **Description**: `code/src/pipeline/provenance.py` computes SHA‑256 hashes for every file under `data/processed/` and `results/`, records the seeds used for permutation, bootstrap, and any other stochastic step, adds timestamps, and writes a YAML state file `state/projects/PROJ-331-investigating-the-correlation-between-gu.yaml` adhering to Constitution Principles I, III, V. No other module writes to `state/`.  
  - **Artifacts**: `state/projects/PROJ-331-investigating-the-correlation-between-gu.yaml`  
  - **Verification**: `code/tests/test_provenance.py` recomputes the hashes and confirms they match the entries; it also checks that the recorded seeds equal those set in the pipeline.

- [ ] **T014** Verify quickstart guide coverage  
  - **Description**: `code/src/pipeline/quickstart_verify.py` runs the exact steps documented in `specs/001-investigating-the-correlation-between-gu/quickstart.md` (ingest → preprocess → slopes → correlation), then checks that the expected artifacts exist and that `results/runtime_log.txt` reports a total duration ≤ 6 h.  
  - **Artifacts**: None additional (uses existing artifacts)  
  - **Verification**: `code/tests/test_quickstart_coverage.py` ensures each step completes without error, all expected files are present, and runtime budget is satisfied.

---  

### Dependency & Requirement Coverage  

| Requirement | Task(s) | Demonstration command |
|-------------|---------|-----------------------|
| FR‑001 (ingest) | T001 | `python -m code.src.pipeline.ingest` |
| FR‑002 (≥ 2‑visit filter) | T002, T008‑T010 | pipeline logs “excluded patients” |
| FR‑003 (CLR) | T002 | `code/tests/test_preprocess.py` |
| FR‑004 (slope & plain Spearman) | T003, T004 | `results/taxa_correlations.csv` |
| FR‑005 (LME) | T005 | `results/mixed_effects_summary.csv` |
| FR‑006 (BH correction) | T004, T005, T009 | contract & validation tests |
| FR‑007 (permutation) | T006, T007, T010 | `results/permutation_pvalues.csv` & runtime log |
| FR‑008 (four deliverables) | T004, T005, T006, T011 | files under `results/` |
| FR‑009 (associational framing) | T011, T012 | methods paragraph & handoff doc |
| FR‑010 (top‑100 taxa cap) | T002, T008‑T010 | pipeline log “taxa subsampled to 100” |
| SC‑001 – SC‑006 | T004‑T011 | validation suite & PDF report |

All tasks respect the required data‑flow ordering:  

**T001 → T002 → T003 → (T004 or T005) → T006 → T007 → (T008‑T010) → T011 → T012 → T013 → T014**.  

Independent tasks (e.g., dataset verification) have been removed or merged to avoid scope creep.  

---  

*End of `tasks.md`.* 