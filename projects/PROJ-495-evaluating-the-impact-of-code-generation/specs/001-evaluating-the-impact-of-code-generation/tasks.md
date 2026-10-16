# Tasks: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Inputs**: `spec.md`, `plan.md`, existing code and data artifacts, reviewer feedback (none pending).

This is a reproducible, CPU‑only research pipeline: ingest real LLM‑generated and human‑written code, run Bandit/Semgrep/SonarQube static analysis, deduplicate findings, compute cyclomatic‑complexity proxies, calculate vulnerability density, perform statistical comparison with multiple‑comparison correction, audit a stratified sample for false‑positive rates, compute the between‑group FPR difference, and produce tables and figures. Tasks are ordered to respect the data‑flow chain in `data-model.md` and to deliver an early end‑to‑end smoke run on a small real subset.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P1] [US1] Implement `code/src/ingest.py` (FR‑001)  
  • Download the **CodeVulnBench** dataset from the verified URL `https://huggingface.co/datasets/bigcode/codeparrot`.  
  • Verify checksums against the official SHA‑256 values provided in the specification (to be supplied in a spec amendment).  
  • Download the **Juliet Test Suite** Java subset from a verified public URL (currently missing – flagged for upstream amendment).  
  • Verify checksums, write raw files under `data/raw/`, record hashes in `data/checksums.json`, and generate `data/derived/file_manifest.csv` conforming to `file-manifest.schema.yaml`.  
  • Detect language from file extensions, flag files > 100 k LOC as `skipped_size`, and mark zero‑LOC files with `status` `ok`.  
  • **Verification**: `code/tests/integration/test_ingest.py` asserts at least one file for each `source_group`, all paths exist, and checksums match.

- [ ] T002 [P1] [US1] Implement `code/src/static_analysis.py` (FR‑002)  
  • Iterate over `file_manifest.csv`; run **Bandit** (Python files), **Semgrep** (Java/JavaScript), and **SonarQube Community Edition** via Docker image `sonarqube:9.9-community` with `sonarqube-scanner==4.7.0.2747`.  
  • Parse each tool’s JSON output, extract CWE ID, severity, and line number, and write raw findings to `data/derived/findings_raw.csv`.  
  • Files that fail to parse receive `status` `parse_error` in the manifest; processing continues.  
  • Record wall‑clock time and peak RSS per tool in `results/tables/resource_usage.csv`.  
  • **Verification**: `code/tests/integration/test_static_analysis.py` runs on a 20‑file smoke subset and checks that every `ok` file appears in `findings_raw.csv` with required columns; malformed files are logged as `parse_error` without aborting.

- [ ] T014 [P1] [US1] Implement `code/src/deduplication.py` (deduplication step)  
  • Read `findings_raw.csv`, collapse duplicate findings that share `file_id`, `line_number`, and `cwe_id` across tools, retaining a single record per unique finding.  
  • Write deduplicated results to `data/derived/findings.csv` and add a `tools_run` array column indicating which tools reported each finding.  
  • **Verification**: `code/tests/unit/test_deduplication.py` confirms that duplicate rows are removed and that the count of unique `(file_id, cwe_id)` pairs matches the expected value on a synthetic dataset.

- [ ] T015 [P1] [US2] Implement `code/src/complexity.py` (complexity proxy)  
  • Use `radon` to compute average cyclomatic complexity for each source file (language‑agnostic where possible).  
  • Append a `complexity_proxy` column to `data/derived/file_manifest.csv`.  
  • **Verification**: `code/tests/unit/test_complexity.py` validates that the proxy is a non‑negative float and that files with parsing errors retain a `null` value.

- [ ] T003 [P1] [US2] Implement `code/src/density.py` (FR‑003)  
  • Compute LOC per file (exclude comments and blank lines) using the language‑agnostic counter.  
  • Calculate **raw density** = `vulnerability_count / loc`; for `loc == 0` set `density = "undefined"` and exclude those rows from downstream modeling.  
  • Produce `data/derived/per_file_analysis.csv` conforming to `per-file-analysis.schema.yaml` (including `density`).  
  • Generate an interim group‑level summary `results/tables/group_summary_raw.csv` (mean/median/sd density per `source_group`).  
  • **Verification**: `code/tests/unit/test_density.py` validates density calculations on a synthetic manifest, correct handling of zero‑LOC files, and proper group aggregation.

- [ ] T004 [P1] [US1] Implement a smoke‑run orchestrator `code/src/pipeline.py --smoke N` (Phase 1)  
  • Executes **ingest → static_analysis → deduplication → complexity → density** on the first `N` rows of the manifest.  
  • Writes the intermediate artifacts (`file_manifest.csv`, `findings_raw.csv`, `findings.csv`, `per_file_analysis.csv`, `group_summary_raw.csv`).  
  • Updates `specs/001-evaluating-the-impact-of-code-generation/quickstart.md` with the exact command.  
  • **Verification**: Running `python code/src/pipeline.py --smoke 20` exits with status 0 and produces non‑null mean density (or `"undefined"` where appropriate). No final aggregation artifacts are expected yet.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [P1] [US1] Execute the full ingestion and static‑analysis pipeline (FR‑001, FR‑002)  
  • Run `code/src/pipeline.py` without the `--smoke` flag to process the complete manifest.  
  • Produce final `data/derived/findings.csv`, `data/derived/per_file_analysis.csv`, and `results/tables/resource_usage.csv`.  
  • Report the proportion of files successfully analyzed (`SC‑005`) and confirm runtime ≤ 6 h and peak RAM ≤ 7 GB (`SC‑003`, `SC‑004`).  
  • **Verification**: Contract test validates `per_file_analysis.csv` against `per-file-analysis.schema.yaml`; `resource_usage.csv` shows limits respected.

- [ ] T006 [P2] [US2] Implement `code/src/audit.py` (FR‑007, FR‑008)  
  • Compute **audit sample size** = `min(0.05 * total_findings, 100)` (or 5 % whichever is smaller).  
  • Stratify by `tool × CWE × source_group`, sample with a fixed seed from `code/src/config.py`, and emit `data/derived/audit_sample.csv` (verdict column empty).  
  • Abort with a clear error if `data/derived/audit_verdicts.csv` is missing; no synthetic fallback.  
  • After human labeling, read `audit_verdicts.csv`, compute precision, recall, and **False Positive Rate (FPR)** per tool and per `source_group`, and write `data/derived/audit_metrics.csv`.  
  • **Verification**: `code/tests/unit/test_audit.py` checks sample size, stratification, and that computed FPR matches expected values on a synthetic verdict file.

- [ ] T007 [P2] [US2] Extend `code/src/density.py` to apply audit‑derived FPR corrections (FR‑008)  
  • Read `audit_metrics.csv`, adjust raw `vulnerability_count` to obtain `corrected_vulnerability_count` per file, and recompute `density_corrected`.  
  • Add the corrected columns to `data/derived/per_file_analysis.csv` and produce a corrected group summary `results/tables/group_summary_corrected.csv`.  
  • **Verification**: Unit test confirms that corrected counts decrease proportionally to the reported FPR (e.g., 10 % FPR reduces counts by 10 %).

- [ ] T008 [P3] [US3] Implement `code/src/stats.py` (FR‑004, FR‑006)  
  • **Power analysis**: compute detectable effect size given per‑group `n`; log power and abort if `< 0.8`.  
  • **Over‑dispersion check**: compute variance/mean ratio of raw counts; if ≤ 1.5, **log a warning** but continue with Negative Binomial GLM (no Poisson fallback).  
  • **Negative Binomial GLM**: outcome = `corrected_vulnerability_count`, offset = `log(loc)`, predictors = `source_group` + `language` + `complexity_proxy`.  
  • **Mann‑Whitney U** on `density_corrected` (excluding `"undefined"`).  
  • Apply **Benjamini‑Hochberg** correction across the two p‑values, using the adjusted alpha = 0.05 (SC‑002).  
  • Write `results/aggregate_results.json` conforming to `aggregate-results.schema.yaml`, including group‑level raw and corrected density statistics, test results with BH‑adjusted p‑values, coefficients, confidence intervals, and a `significant` flag.  
  • **Verification**: `code/tests/contract/test_aggregate_schema.py` validates the JSON; additional unit test checks that `significant` matches `p_adjusted < 0.05`.

- [ ] T009 [P3] [US3] Implement `code/src/figures.py` (FR‑005)  
  • Generate a **boxplot** of `density_corrected` by `source_group` → `results/figures/density_boxplot.png` & `.svg`.  
  • Generate a **bar chart** of CWE‑class counts per group (using corrected counts) → `results/figures/cwe_distribution.png` & `.svg`.  
  • Figures must read only validated result tables (`group_summary_corrected.csv` and `per_file_analysis.csv`).  
  • **Verification**: Unit test asserts that image files exist, are > 10 KB, and that the source data contain required columns.

- [ ] T010 [P1] Wire all modules into `code/src/pipeline.py` with explicit phase flags (`--ingest`, `--analyze`, `--dedup`, `--complexity`, `--density`, `--audit`, `--stats`, `--figures`). The default run (`python code/src/pipeline.py`) executes the full workflow in the correct dependency order, logging per‑phase timing and peak memory into `results/tables/resource_usage.csv`.  
  • **Verification**: A full run completes within free‑tier limits and produces all final artifacts: `file_manifest.csv`, `findings.csv`, `per_file_analysis.csv`, `aggregate_results.json`, `resource_usage.csv`, and all figures.

- [ ] T011 [P3] Write `specs/001-evaluating-the-impact-of-code-generation/research.md` (methods & results handoff)  
  • Concise narrative linking every table/figure in `results/` to the script and inputs that produced it.  
  • Cite CWE taxonomy URLs, report raw and corrected density statistics, p‑values, power estimate, audit metrics, FPR difference, files skipped (size or parse errors), and frame findings as observational.  
  • **Verification**: Each referenced artifact exists; every cited statistic maps to a row in `aggregate_results.json` or `audit_metrics.csv`; all CWE URLs are listed.

- [ ] T012 [P3] Create `specs/001-evaluating-the-impact-of-code-generation/paper_handoff.md`  
  • Enumerate result artifact paths, statistical methods (including BH correction), resource‑usage summary, and open limitations (e.g., power < 0.8, missing audit verdicts).  
  • Pin exact dependency versions in `code/requirements.txt`.  
  • **Verification**: A fresh run reproduces all listed artifacts; `pytest` passes; handoff lists only existing files.

- [ ] T013 [P3] Implement `code/src/fpr_difference.py` (covers SC‑007)  
  • Read `audit_metrics.csv`, compute **FPR difference** = `FPR_llm - FPR_human`, write `results/tables/fpr_difference.csv` with the raw difference and a 95 % confidence interval (bootstrapped).  
  • Append this metric to `aggregate_results.json` under an optional `extra_metrics` field.  
  • **Verification**: Unit test verifies correct arithmetic on synthetic audit metrics and that the CSV is produced with the expected columns.

- [ ] T016 [P3] Verify Success Criterion SC‑001 (rate‑ratio deviation & significance)  
  • After `stats.py` completes, parse `aggregate_results.json` and assert that the NB regression `coefficient` (rate ratio) satisfies `|RR − 1| ≥ 0.10` and that `significant` is true (p < adjusted alpha).  
  • Fail the pipeline with an informative error if either condition is not met.  
  • **Verification**: unit test `code/tests/unit/test_sc001.py` reproduces the check on a synthetic results file.

- [ ] T017 [P3] Verify Success Criterion SC‑006 (precision ≥ 80 % & recall ≥ 80 %)  
  • After `audit.py` produces `audit_metrics.csv`, compute overall precision and recall across all tools and source groups.  
  • Assert both metrics meet the ≥ 0.80 threshold; otherwise raise an error.  
  • **Verification**: unit test `code/tests/unit/test_sc006.py` validates the assertion on synthetic audit metrics.

- [ ] T018 [P3] Define and enforce Success Criterion SC‑007 disparity threshold  
  • Establish a concrete absolute difference threshold for FPR disparity (e.g., 0.05).  
  • After `fpr_difference.py` generates `results/tables/fpr_difference.csv`, assert that the absolute FPR difference ≥ 0.05; otherwise log a warning and mark the study as exploratory in `research.md`.  
  • **Verification**: unit test `code/tests/unit/test_sc007.py` checks the enforcement on synthetic data.

## Phase 3: Reproducible results and paper handoff

- (All tasks above collectively satisfy the research‑stage requirements and ensure full compliance with the specification, contracts, and constitution.)
