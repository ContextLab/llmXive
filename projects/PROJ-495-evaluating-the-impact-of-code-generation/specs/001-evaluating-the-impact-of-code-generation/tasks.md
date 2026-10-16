# Tasks: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Inputs**: `spec.md`, `plan.md`, existing code and data artifacts, reviewer feedback (none pending).

This is a reproducible, CPU-only research pipeline: ingest real LLM‑generated and human‑written code, run Bandit/Semgrep/SonarQube static analysis, compute vulnerability density, perform statistical comparison with multiple‑comparison correction, audit a stratified sample for false‑positive rates, compute the between‑group FPR difference, and produce tables and figures. Tasks are ordered to respect the data‑flow chain in `data-model.md` and to deliver an early end‑to‑end smoke run on a small real subset.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P1] [US1] Implement `code/src/ingest.py` (FR‑001): **download the verified CodeVulnBench dataset** (public URL to be defined in the manifest) and the **Java subset of the Juliet Test Suite** (human baseline). Use `datasets.load_dataset` for CodeVulnBench (if hosted on Hugging Face) or `urllib.request` for a direct HTTP URL; for Juliet, fetch only `.java` files via the GitHub raw archive. The loader must **FAIL LOUDLY** if any source is unreachable – no synthetic fallback. Write raw files under `data/raw/`, compute SHA‑256 checksums into `data/checksums.json`, and build `data/derived/file_manifest.csv` conforming to `file-manifest.schema.yaml` (fields: `file_id, rel_path, source_group, language, loc, status`). Detect language from file extension (`.py → python`, `.js → javascript`, `.java → java`, others → other). Flag files > 50 k LOC as `skipped_size`. Zero‑LOC files are kept with status `ok` and will receive `"undefined"` density later. Record provenance in `data/derived/provenance.json`.

  - Verification: integration test `code/tests/integration/test_ingest.py` asserts the manifest contains ≥ 1 file for each `source_group`, all `rel_path` values exist, and checksums match.

- [ ] T002 [P1] [US1] Implement `code/src/static_analysis.py` (FR‑002): iterate `data/derived/file_manifest.csv`; run **Bandit** (Python API) on Python files, **Semgrep** with appropriate rule sets on Java/JavaScript files, and **SonarQube Community Edition** via **pinned Docker image `sonarqube:9.9-community`** together with `sonarqube-scanner==4.7.0.2747`. Parse findings into `data/derived/findings.csv` (`finding_id, file_id, tool, cwe_id, severity, line_number`). Files that fail to parse receive `status` `parse_error` in the manifest and are logged but do not halt the run. Record wall‑clock time and peak RSS per tool into `results/tables/resource_usage.csv`. Files with zero findings must still appear with `vulnerability_count = 0` in later steps.

  - Verification: `code/tests/integration/test_static_analysis.py` runs on a 20‑file smoke subset and asserts that every file with status `ok` appears in `data/derived/findings.csv` with correct columns; a deliberately malformed file is recorded as `parse_error` without aborting.

- [ ] T003 [P1] [US2] Implement `code/src/density.py` (FR‑003): compute LOC per file (exclude comments and blank lines), calculate **raw density** = `vulnerability_count / loc`; for `loc == 0` set `density = "undefined"` and **exclude** those rows from downstream modeling. Produce `data/derived/per_file_analysis.csv` conforming to `per-file-analysis.schema.yaml` (including `density`). Generate group‑level summary `results/tables/group_summary_raw.csv` (mean/median/sd density per `source_group`) for internal use.

  - Verification: `code/tests/unit/test_density.py` validates density calculations on a synthetic manifest, correct handling of zero‑LOC files, and proper group separation.

- [ ] T004 [P1] [US1] Implement `code/src/pipeline.py` orchestrator with a `--smoke N` flag that runs **ingest → static analysis → density** on the first `N` manifest rows and writes the intermediate artifacts (`file_manifest.csv`, `findings.csv`, `per_file_analysis.csv`, `group_summary_raw.csv`). Update `specs/001-evaluating-the-impact-of-code-generation/quickstart.md` with the exact command.

  - Verification: `python code/src/pipeline.py --smoke 20` exits 0 and produces the expected files with non‑null mean density (or `"undefined"` where appropriate). The smoke run does **not** expect `aggregate_results.json` yet.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [P1] [US1] Run the full ingestion and static analysis over the complete manifest (FR‑001, FR‑002): produce full `findings.csv`, `per_file_analysis.csv`, and `resource_usage.csv`. Report the proportion of files successfully analyzed vs. total (SC‑005) and confirm runtime ≤ 6 h and peak RSS ≤ 7 GB (SC‑003, SC‑004).

  - Verification: contract test `per_file_analysis.csv` against `per-file-analysis.schema.yaml`; `resource_usage.csv` shows limits respected.

- [ ] T006 [P2] [US2] Implement `code/src/audit.py` (FR‑007, FR‑008): compute **audit sample size** = `min(0.05 * total_findings, 100)`. Stratify by `tool × CWE × source_group`, sample with fixed seed from `code/src/config.py`, and emit `data/derived/audit_sample.csv` (verdict column empty). **Require** `data/derived/audit_verdicts.csv` to be present; if missing, abort with clear error (no fallback). Read the verdicts, compute **precision, recall, and False Positive Rate (FPR)** per `source_group`, and write `data/derived/audit_metrics.csv`. If any required column is missing, abort.

  - Verification: `code/tests/unit/test_audit.py` checks sample size, stratification, and that computed FPR matches expected values given a synthetic verdict file.

- [ ] T007 [P2] [US2] Extend `code/src/density.py` to apply the per‑group FPR from `audit_metrics.csv` to obtain `corrected_vulnerability_count` and `density_corrected` in `per_file_analysis.csv`. Add corrected columns to a new summary `results/tables/group_summary_corrected.csv`. If audit metrics are unavailable (which cannot happen now), the task aborts.

  - Verification: unit test confirms corrected counts/densities adjust according to a known FPR (e.g., 10 %).

- [ ] T008 [P3] [US3] Implement `code/src/stats.py` (FR‑004, FR‑006): (1) **Power analysis** – compute detectable effect size given per‑group `n`; log power and abort if `< 0.8`. (2) **Over‑dispersion check** – compute variance/mean ratio of raw counts; if ≤ 1.5, fall back to Poisson GLM and note the choice. (3) **Negative Binomial GLM** – outcome = raw `vulnerability_count`, offset = `log(loc)`, predictors = `source_group` + `language`. (4) **Mann‑Whitney U** on `density_corrected` (excluding `"undefined"`). (5) Apply **Benjamini‑Hochberg** correction (as described in `aggregate-results.schema.yaml`) across the two p‑values. Produce a **single JSON artifact** `results/aggregate_results.json` that matches `aggregate-results.schema.yaml`, containing `groups` (means/medians/sds for raw and corrected densities) and `tests` (NB, Mann‑Whitney U results with BH‑adjusted p‑values, coefficients, CIs, and `significant` flag).

  - Verification: `code/tests/contract/test_aggregate_schema.py` validates the JSON file against the schema; sanity checks ensure p‑values ∈ [0,1] and `significant` matches `p_adjusted < 0.05`.

- [ ] T009 [P3] [US3] Implement `code/src/figures.py` (FR‑005): generate (a) boxplot of `density_corrected` by `source_group` saved as `results/figures/density_boxplot.png` & `.svg`; (b) bar chart of CWE‑class counts per group (using corrected counts) saved as `results/figures/cwe_distribution.png` & `.svg`. Figures read only validated result tables.

  - Verification: unit test asserts image files exist, are > 10 KB, and source data contain required columns.

- [ ] T010 [P1] Wire all modules into `code/src/pipeline.py` with phase flags (`--ingest`, `--analyze`, `--density`, `--stats`, `--audit`, `--figures`). The default run executes the full workflow in dependency order, logging per‑phase timing and peak memory into `results/tables/resource_usage.csv`.

  - Verification: full run completes within free‑tier limits and produces all final artifacts: `file_manifest.csv`, `per_file_analysis.csv`, `aggregate_results.json`, `resource_usage.csv`, and all figures.

- [ ] T011 [P3] Write `specs/001-evaluating-the-impact-of-code-generation/research.md`: concise methods and results account linking every table/figure in `results/` to the script and inputs that produced it; include **CWE taxonomy URLs**; report actual measured densities, raw and corrected statistics, p‑values, power estimate, audit metrics, FPR difference, files skipped (size or parse errors), and observational framing. Cite all artifact paths.

  - Verification: each artifact referenced exists; every cited statistic maps to a row in `aggregate_results.json` or `audit_metrics.csv`; CWE URLs are listed.

- [ ] T012 [P3] Create `specs/001-evaluating-the-impact-of-code-generation/paper_handoff.md` enumerating result artifact paths, statistical methods and BH correction, resource usage summary, and open limitations (e.g., power < 0.8, any missing audit verdicts). Pin exact dependency versions in `code/requirements.txt`.

  - Verification: a fresh run reproduces all listed artifacts; `pytest` passes; handoff lists only existing files.

- [ ] T013 [P3] Implement `code/src/fpr_difference.py` (covers SC‑007): read `audit_metrics.csv`, compute **FPR difference** = `FPR_llm - FPR_human`, write `results/tables/fpr_difference.csv` with the raw difference and a 95 % confidence interval (bootstrapped). Include this metric in `aggregate_results.json` under an optional `extra_metrics` field.

  - Verification: unit test verifies correct arithmetic on synthetic audit metrics and that the CSV is produced.

## Phase 3: Reproducible results and paper handoff

- (All tasks above collectively satisfy the research‑stage requirements and ensure full compliance with the specification, contracts, and constitution.)
