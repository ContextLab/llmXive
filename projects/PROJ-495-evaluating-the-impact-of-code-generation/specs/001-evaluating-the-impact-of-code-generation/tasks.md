# Tasks: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Inputs**: `spec.md`, `plan.md`, existing code and data artifacts, reviewer feedback (none pending).

The goal is to build a reproducible, CPU‑only research pipeline that ingests real code samples, runs static analysis, computes vulnerability density, performs statistical comparison, audits a subset, and produces the required figures and summary tables. The tasks are ordered to respect data flow and to enable an early end‑to‑end smoke run on a small subset of the data.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal pipeline on a verified small subset to prove that the whole workflow can execute end‑to‑end on real data. |
|------|--------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T001** [US1] Create a **quickstart.md** that documents the full pipeline command, required environment variables, and a “smoke‑run” flag.  
  *File*: `quickstart.md`  
  *Verification*: `make quickstart && ./code/src/pipeline.py --smoke 50` completes without error and produces `data/results/smoke_report.json` containing vulnerability counts for exactly 50 files.

- [ ] **T002** [US1] Implement **ingest.py** to download the verified human‑written Juliet suite and a verified substitute for CodeVulnBench (e.g., the HuggingFace dataset `codevulnbench`).  
  *File*: `code/src/ingest.py`  
  *Verification*: Unit test `tests/integration/test_ingest.py` checks that `data/derived/file_manifest.csv` contains at least one entry for each source group and that SHA‑256 checksums match the recorded values in `data/checksums.json`.  

- [ ] **T003** [US1] Add a **smoke‑run mode** to `pipeline.py` that limits processing to the first *N* rows of `file_manifest.csv`.  
  *File*: `code/src/pipeline.py`  
  *Verification*: Running `./code/src/pipeline.py --smoke 20` creates `data/results/smoke_per_file_analysis.csv` with exactly 20 rows and no missing required columns.

- [ ] **T004** [US2] Implement **static_analysis.py** to invoke Bandit (Python), Semgrep (Java/JavaScript), and SonarQube (Docker) on each file listed in the manifest.  
  *File*: `code/src/static_analysis.py`  
  *Verification*: Integration test `tests/integration/test_static_analysis.py` runs the script on the 20‑file smoke set and asserts that `data/derived/per_file_analysis.csv` contains the columns `vulnerability_count`, `cwe_ids`, and `tools_run` for every processed file; files that fail to parse are logged with status `parse_error` but do not abort the run.

- [ ] **T005** [US3] Implement **density.py** to compute LOC, raw density, and handle zero‑LOC files by writing `"undefined"` in the `density` column.  
  *File*: `code/src/density.py`  
  *Verification*: Unit test `tests/unit/test_density.py` feeds a mini‑manifest with a zero‑LOC entry and checks that the resulting `density` field equals `"undefined"` and that the file is excluded from the downstream modeling CSV.

- [ ] **T006** [US3] Extend `pipeline.py` to chain the new modules and produce a minimal end‑to‑end output: `data/results/smoke_group_summary.csv`.  
  *File*: `code/src/pipeline.py`  
  *Verification*: After the smoke run, the summary file contains rows for both `llm` and `human` groups with non‑null `mean_density` (or `"undefined"` where appropriate) and the script exits with status 0.

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Run the full pipeline on the complete verified datasets, compute corrected metrics, perform statistical tests, audit a stratified sample, and generate the required figures. |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T007** [US2] Finalize **ingest.py** to download the full datasets, verify checksums, and record provenance in `data/derived/provenance.json`.  
  *File*: `code/src/ingest.py`  
  *Verification*: After a full run, `data/checksums.json` contains SHA‑256 values for every downloaded file; the pipeline aborts with a clear error if any checksum mismatches.

- [ ] **T008** [US2] Run **static_analysis.py** on the complete manifest, storing raw findings in `data/derived/findings.csv` and per‑file aggregates in `data/derived/per_file_analysis.csv`.  
  *File*: `code/src/static_analysis.py`  
  *Verification*: Contract test `tests/contract/test_per_file_schema.py` validates that `per_file_analysis.csv` conforms to `per-file-analysis.schema.yaml`; any file with `status != ok` is excluded from the density calculation but logged.

- [ ] **T009** [US2] Extend **density.py** to apply the false‑positive correction derived from the audit (see T011) and write the corrected columns `corrected_vulnerability_count`, `density_corrected` to `data/derived/per_file_analysis.csv`.  
  *File*: `code/src/density.py`  
  *Verification*: After applying a mock audit correction (e.g., 10 % FPR), a unit test confirms that corrected counts are reduced accordingly and that `density_corrected` updates consistently.

- [ ] **T010** [US3] Implement **stats.py** to:  
    1. Perform an over‑dispersion check and select Negative Binomial GLM (or Poisson fallback).  
    2. Fit the NB GLM with offset `log(loc)` and predictor `source_group` (plus optional covariates).  
    3. Run a Mann‑Whitney U test on `density_corrected`.  
    4. Apply Holm‑Bonferroni correction across the two p‑values.  
    5. Output `results/tables/statistical_tests.csv` with raw and adjusted p‑values, coefficients, confidence intervals, and a `significant` flag.  
  *File*: `code/src/stats.py`  
  *Verification*: Contract test `tests/contract/test_aggregate_schema.py` validates that `statistical_tests.csv` conforms to `aggregate-results.schema.yaml`; a sanity‑check script confirms that p‑values lie in `[0,1]`.

- [ ] **T011** [US2] Implement **audit.py** to:  
    1. Compute the required sample size (`min(0.05 * total_findings, 100)`).  
    2. Perform stratified random sampling by `tool × CWE × source_group` with a fixed seed.  
    3. Emit `data/derived/audit_sample.csv` (empty `verdict` column).  
    4. After manual annotation, read `data/derived/audit_verdicts.csv` and compute precision, recall, and **False Positive Rate** per group, writing `data/derived/audit_metrics.csv`.  
  *File*: `code/src/audit.py`  
  *Verification*: Integration test runs the sampling on a reduced dataset, checks that the sample size matches the formula, and that after loading a fabricated verdict file the computed FPR matches the expected value.

- [ ] **T012** [US3] Implement **figures.py** to generate:  
    1. Boxplot of `density_corrected` by `source_group` saved as `results/figures/density_boxplot.png` and `.svg`.  
    2. Bar chart of CWE‑class counts (using corrected counts) per group saved as `results/figures/cwe_distribution.png`.  
  *File*: `code/src/figures.py`  
  *Verification*: A pytest script loads the generated PNG files and asserts that their file size > 10 KB (ensuring a non‑empty image) and that the underlying data files (`group_summary.csv`, `per_file_analysis.csv`) contain the necessary columns.

- [ ] **T013** [US1] Wire all modules together in **pipeline.py** with clear CLI flags (`--ingest`, `--analyze`, `--density`, `--stats`, `--audit`, `--figures`). The default run executes the full workflow in the correct order.  
  *File*: `code/src/pipeline.py`  
  *Verification*: Running `./code/src/pipeline.py --all` on the full dataset completes within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM) and produces the final artifacts:  
    - `data/derived/file_manifest.csv`  
    - `data/derived/per_file_analysis.csv`  
    - `results/tables/group_summary.csv`  
    - `results/tables/statistical_tests.csv`  
    - `results/figures/*.png`  

- [ ] **T014** [US2] Add **resource monitoring** to the pipeline (using `psutil`) to log wall‑clock time and peak RSS for each phase into `results/tables/resource_usage.csv`.  
  *File*: `code/src/pipeline.py` (monitoring wrapper)  
  *Verification*: After a full run, the CSV contains rows for “ingest”, “static_analysis”, “density”, “stats”, “audit”, and “figures”, and the peak memory for any phase does not exceed 7 GB.

- [ ] **T015** [US3] Write a **methods & results handoff** document (`research.md`) that links each result artifact (tables, figures) to the exact script and version that produced it, and lists any limitations (e.g., power < 0.8, files skipped due to size).  
  *File*: `specs/001-evaluating-the-impact-of-code-generation/research.md`  
  *Verification*: Manual review checklist confirms that every table/figure referenced in the document exists in `results/` and that the document cites the corresponding script filenames and Git commit hash (captured via `git rev-parse HEAD`).

---

## Phase 3 – Reproducible results and paper handoff  

| Goal | Ensure that an external reviewer can rerun the entire study from scratch and obtain identical artifacts. |
|------|----------------------------------------------------------------------------------------------------------------|

- [ ] **T016** Archive the **environment** by pinning all Python dependencies in `code/requirements.txt` (including exact versions), and provide a Dockerfile (`Dockerfile.cpu`) that installs the requirements, pulls SonarQube Docker image, and sets the entrypoint to `pipeline.py`.  
  *Files*: `code/requirements.txt`, `Dockerfile.cpu`  
  *Verification*: Building the image with `docker build -t vuln-study .` succeeds, and running `docker run --rm vuln-study ./code/src/pipeline.py --all` reproduces the same `results/` artifacts (verified via checksum comparison).

- [ ] **T017** Add a **CI workflow** (`.github/workflows/research.yml`) that executes the full pipeline on the free‑tier GitHub Actions runner, caches the downloaded datasets, and fails if any contract test does not pass.  
  *File*: `.github/workflows/research.yml`  
  *Verification*: The workflow runs on every push; the badge shows “passing” only when all tasks from T001‑T016 complete successfully.

- [ ] **T018** Create a **paper‑stage handoff** checklist (`paper_handoff.md`) that enumerates:  
    1. Paths to all result tables and figures.  
    2. Description of statistical methods and correction procedures.  
    3. Summary of computational resources used.  
    4. Any open limitations (e.g., insufficient power, files skipped > 50 k LOC).  
  *File*: `paper_handoff.md`  
  *Verification*: The checklist is referenced from the final commit message of the release tag `v1.0.0`.

---

## Dependencies & Requirement Coverage  

| Spec / FR | Satisfied by Task(s) |
|-----------|----------------------|
| FR‑001 (download datasets) | T001, T007 |
| FR‑002 (run Bandit, Semgrep, SonarQube) | T004, T008 |
| FR‑003 (vulnerability density) | T005, T009 |
| FR‑004 (Negative Binomial & Mann‑Whitney) | T010 |
| FR‑005 (visualizations) | T012 |
| FR‑006 (multiple‑comparison correction) | T010 |
| FR‑007 (stratified audit sample) | T011 |
| FR‑008 (False Positive Rate) | T011 |
| SC‑001 (statistical significance) | T010 |
| SC‑002 (adjusted alpha) | T010 |
| SC‑003 (execution time) | T014 |
| SC‑004 (memory usage) | T014 |
| SC‑005 (proportion of files analyzed) | T008 |
| SC‑006 (precision/recall) | T011 |
| SC‑007 (FPR difference) | T011 |
| Data‑hygiene & provenance | T007, T014, T016 |
| Reproducibility (seeds, hashes) | T001, T003, T016 |
| Constitution VI (static analysis fidelity) | T004, T008 |

All tasks are unchecked (`[ ]`) to indicate they are pending implementation. Once a task is completed and its verification passes, the CI system will automatically check the box.
