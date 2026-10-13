# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Parkinson’s Disease Progression

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/taxa_results.schema.yaml`, existing code under `code/src/pipeline/`, and the **PPMI pre‑processed dataset** (`data/raw/ppmi_asv.csv`, `data/raw/ppmi_clinical.parquet`).

The goal is to implement a reproducible, CPU‑tractable end‑to‑end analysis that satisfies every functional requirement (FR‑001 – FR‑010) and success criterion (SC‑001 – SC‑006). Tasks are ordered to respect data flow; independent tasks are marked `[P]` only when truly parallel‑safe.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [X] T013 **Verify PPMI dataset citation and provenance**  
  *Implementation*: `code/src/pipeline/verify_dataset.py` checks that the two raw files exist, validates their SHA‑256 checksums against the values recorded in the PPMI publication, and confirms the citation is reachable via the Reference‑Validator Agent (Principle II). If verification fails, the script aborts with an informative error.  
  *Verification*: Unit test `code/tests/test_verify_dataset.py` ensures correct handling of matching and mismatching checksums.

- [X] T001 **Validate input availability and provenance**  
  *Implementation*: `code/src/pipeline/ingest.py` checks that `data/raw/ppmi_asv.csv` and `data/raw/ppmi_clinical.parquet` contain the required columns and are readable. If a file is missing or malformed the script exits with a non‑zero status and a clear error message; if the `MDS_UPDRS_Total` column is absent it logs a warning and sets a skip‑flag for downstream correlation/LME steps (FR‑001, FR‑004).  
  *Verification*: Unit tests in `code/tests/test_ingest.py` cover (a) successful load, (b) missing file, (c) missing outcome column. The runnable command is documented in `specs/001-investigating-the-correlation-between-gu/quickstart.md`.

- [ ] T002 **Filtering, CLR transformation, and memory‑cap handling**   <!-- FAILED: unspecified -->
  *Implementation*: `code/src/pipeline/preprocess.py` (a) loads the raw files using **pandas + pyarrow**, (b) merges on `patient_id` + `visit_date`, (c) retains only PD patients with **≥ 2 visits** (logs exclusion count, FR‑002), (d) drops taxa whose counts are zero across all retained samples (warning logged), (e) adds a small pseudocount (1e‑6) and applies a centered‑log‑ratio (CLR) transform via `scikit_bio` (FR‑003), (f) detects zero‑variance covariates (e.g., constant levodopa dose) and removes them with a warning, (g) if the number of retained taxa would exceed the RAM budget, selects the **top 100 most abundant taxa** (FR‑010).  
  *Outputs*: `data/processed/filtered_samples.parquet`, `data/processed/clr_abundances.parquet`.  
  *Verification*: `code/tests/test_preprocess.py` checks patient‑visit filtering, zero‑taxa removal, correct CLR shape, and that the top‑100 subsampling rule is applied when needed.

- [ ] T003 **Per‑patient slope computation (taxa & clinical outcome)**  
  *Implementation*: `code/src/pipeline/slopes.py` parses `visit_date` with `pd.to_datetime`, computes elapsed time in **exact years** (`(date - first_date).dt.days / 365.25`), then fits a simple linear regression for each patient‑taxon pair on the CLR‑transformed abundances to obtain a slope (FR‑004). It also fits a regression of `MDS_UPDRS_Total` vs. time per patient to obtain the clinical slope; if the outcome column was flagged missing by T001 a warning is emitted and the clinical‑slope file is omitted.  
  *Outputs*: `data/processed/patient_taxon_slopes.parquet`, `data/processed/patient_outcome_slopes.parquet` (the latter only when the outcome exists).  
  *Verification*: `code/tests/test_slopes.py` validates correct handling of exactly two visits, correct year calculation, and proper exclusion of single‑visit patients.

- [ ] T004 **Plain Spearman correlation of slopes with BH correction**  
  *Implementation*: `code/src/pipeline/correlation.py` (a) loads the slope files, (b) directly computes a Spearman rank correlation **between the per‑patient taxon‑slope vector and the per‑patient clinical‑slope vector** for each taxon (no covariate adjustment, satisfying FR‑004), (c) applies Benjamini‑Hochberg FDR correction across all taxa (FR‑006). The raw Spearman results and BH‑adjusted p‑values are written to `data/results/taxa_correlations.csv` matching the contract schema. An optional exploratory file `data/results/partial_spearman_exploratory.csv` contains the unadjusted correlations for reference only.  
  *Verification*: Contract test `code/tests/contract/test_contracts.py` validates the CSV schema; `code/tests/test_correlation.py` checks monotonicity of BH‑adjusted p‑values and that the residual‑free correlation differs from a covariate‑adjusted version when covariates vary.

- [ ] T005 **Linear Mixed‑Effects modeling with proper imports and covariate handling**   <!-- FAILED-IN-EXECUTION: tests/test_mixed_effects_execution.py exit=5 --> <!-- FAILED-IN-EXECUTION: code/src/pipeline/mixed_effects.py exit=1 -->
  *Implementation*: `code/src/pipeline/mixed_effects.py` imports `statsmodels.api as sm` and `statsmodels.formula.api as smf`. It fits, for each retained taxon, a mixed‑effects model on the **longitudinal observation level** (`MDS_UPDRS_Total ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)`). Zero‑variance covariates are dropped with a logged warning. For each taxon the fixed‑effect coefficient of the `Time:Taxon` interaction, its standard error, and raw p‑value are extracted. BH correction across taxa yields `bh_adj_p`.  
  *Output*: `data/results/mixed_effects_summary.csv` (schema‑compliant).  
  *Verification*: Unit test `code/tests/test_mixed_effects.py` fits the model on a tiny synthetic dataset with a known interaction and asserts the recovered coefficient is within tolerance; contract test validates the CSV.

- [ ] T006 **Permutation robustness test preserving within‑patient temporal order**  
  *Implementation*: `code/src/pipeline/permutation.py` (a) seeds `np.random.seed(42)`, (b) for 1 000 iterations shuffles **patient identifiers** while keeping each patient’s internal time series of `MDS_UPDRS_Total` intact, (c) re‑fits the same mixed‑effects model as in T005 on the permuted data, (d) records the `Time:Taxon` interaction p‑value for each taxon per iteration, (e) computes empirical p‑values as the proportion of permuted p‑values ≤ the observed raw p‑value, (f) aborts gracefully if the permutation block exceeds **4 hours**, writes any partial results, and logs the breach (FR‑007, SC‑003).  
  *Output*: `data/results/permutation_pvalues.csv`.  
  *Verification*: `code/tests/test_permutation.py` confirms that (i) patient‑level time ordering is unchanged after shuffling, (ii) empirical p‑values lie in [0, 1], (iii) the runtime guard triggers appropriately on a tiny timed mock run.

- [ ] T007 **Runtime and resource monitoring**  
  *Implementation*: `code/src/pipeline/__main__.py` wraps each pipeline stage (ingest, preprocess, slopes, correlation, mixed‑effects, permutation) with a wall‑clock timer, logs per‑stage elapsed time to `data/results/runtime_log.txt`, and after the full run asserts total wall‑clock ≤ 6 h and permutation ≤ 4 h (SC‑003).  
  *Verification*: `code/tests/test_runtime_budget.py` runs a reduced‑size pipeline and checks that the log file contains the expected timing entries and that the assertions pass.

- [ ] T008a **Execute US1 pipeline (Correlation only)**   <!-- FAILED: unspecified -->
  *Command*: `python -m code.src.pipeline.run_us1` (or equivalent wrapper) which sequentially invokes T001 → T002 → T003 → T004 and writes `data/results/taxa_correlations.csv` plus runtime log.  
  *Pre‑conditions*: Raw PPMI files present and verified by T013.  
  *Verification*: After execution, a sanity‑check script confirms `taxa_correlations.csv` contains a row for every retained taxon and that runtime limits are respected.

- [ ] T008b **Execute US2 pipeline (Mixed‑effects only)**   <!-- FAILED: unspecified -->
  *Command*: `python -m code.src.pipeline.run_us2` which runs T001 → T002 → T003 → T005, producing `data/results/mixed_effects_summary.csv`.  
  *Verification*: Post‑run checks ensure the summary CSV matches the schema and that covariate handling obeys FR‑005.

- [ ] T008c **Execute US3 pipeline (Permutation robustness)**   <!-- FAILED-IN-EXECUTION: code/src/pipeline/run_us3.py exit=1 -->
  *Command*: `python -m code.src.pipeline.run_us3` which runs T001 → T002 → T003 → T005 → T006, producing `data/results/permutation_pvalues.csv` and respecting the 4‑hour guard.  
  *Verification*: Same as T006 verification plus runtime log check.

- [ ] T009 **Independent validation of result integrity**  
  *Implementation*: `code/tests/test_validation.py` runs after any US execution and (i) checks that BH‑adjusted p‑values are ≥ raw p‑values and monotonically non‑increasing, (ii) verifies that each taxon appears exactly once in each result file, (iii) confirms that empirical permutation p‑values are reproducible under the fixed seed, and (iv) writes a human‑readable summary `data/results/validation_summary.txt`.  
  *Verification*: The pytest suite must pass; the summary file is examined by the verifier for consistency.

## Phase 2 – Reproducible results and paper handoff  

- [ ] T010 **Generate the PDF report with bootstrap confidence intervals**  
  *Implementation*: `code/src/pipeline/report.py` (a) reads the three result CSVs, (b) performs **1 000 bootstrap resamples** of the mixed‑effects interaction coefficient per taxon to obtain 95 % confidence intervals (computed at runtime, no hard‑coded numbers), (c) ranks taxa by BH‑adjusted p‑value, (d) creates a table of the top 3 taxa showing Spearman ρ, BH‑adjusted p, interaction coefficient ± CI, and (e) inserts a methods paragraph that explicitly states the findings are **associational** and that no causal inference is claimed (FR‑009). The PDF is written to `data/results/PD_microbiome_progression_report.pdf`.  
  *Verification*: `code/tests/test_report.py` parses the PDF text (using `pdfminer.six`) and asserts that (i) the top‑3 table is present, (ii) each CI line contains numeric bounds, and (iii) the methods paragraph contains no causal‑language keywords (“cause”, “effect”, “mechanism”).

- [ ] T011 **Write a concise methods‑results handoff document**  
  *File*: `specs/001-investigating-the-correlation-between-gu/results.md`.  
  *Contents*: cohort size after filtering, number of taxa tested, summary of top taxa (values copied directly from the CSVs), permutation‑test outcome, any negative findings, and explicit limitations (observational design, no metabolite measurements, etc.). It also lists the four deliverables (`taxa_correlations.csv`, `mixed_effects_summary.csv`, `permutation_pvalues.csv`, `PD_microbiome_progression_report.pdf`) as the input set for the downstream paper pipeline.  
  *Verification*: A lint script checks that every numeric entry in `results.md` matches the corresponding entry in the CSVs.

- [ ] T012 **Provenance and compliance logging**  
  *Implementation*: `code/src/pipeline/provenance.py` is invoked at the end of each US‑specific run. It (a) computes SHA‑256 checksums for every file under `data/processed/` and `data/results/`, (b) records the random seeds used (`np.random.seed`, bootstrap seed, permutation seed), (c) records timestamps, and (d) writes a YAML state file `state/projects/PROJ-331-investigating-the-correlation-between-gu.yaml` adhering to Constitution Principles I, III, V. No other `state/` writes are performed elsewhere.  
  *Verification*: `code/tests/test_provenance.py` recomputes the hashes and confirms they match the entries in the state file; it also checks that the recorded seeds are exactly the ones set in the pipeline.

---

## Dependency & Requirement Coverage  

| Requirement | Task(s) | Demonstration command |
|-------------|---------|-----------------------|
| FR‑001 (ingest) | T001 | `python -m code.src.pipeline.ingest` |
| FR‑002 (≥2‑visit filter) | T002, T008a‑c | pipeline log “excluded patients” |
| FR‑003 (CLR) | T002 | `code/tests/test_preprocess.py` |
| FR‑004 (slope & plain Spearman) | T003, T004 | `data/results/taxa_correlations.csv` |
| FR‑005 (LME) | T005 | `data/results/mixed_effects_summary.csv` |
| FR‑006 (BH correction) | T004, T005, T009 | contract & validation tests |
| FR‑007 (permutation) | T006, T007, T008c | `data/results/permutation_pvalues.csv` & runtime log |
| FR‑008 (four deliverables) | T004, T005, T006, T010 | files under `data/results/` |
| FR‑009 (associational framing) | T010, T011 | methods paragraph & results handoff |
| FR‑010 (top‑100 taxa cap) | T002, T008a‑c | pipeline log “taxa subsampled to 100” |
| SC‑001 – SC‑006 | T004–T010 | validation suite & PDF report |

All tasks respect the data‑flow ordering: T013 → T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008a‑c → T009 → T010 → T011 → T012. Independent tasks (T013, T008a‑c) are marked `[P]` only when truly parallel‑safe.  

---

