---
description: "Task list for Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases"
---

# Tasks: Predict Protein‑Protein Interactions from Co‑expression Networks

**Input**: Design documents from `/specs/PROJ-185-predict-ppi-coexpression/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

**Tests**: Tests are defined where explicitly requested in the specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] description (file path)`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 0 – Project Setup (Shared Infrastructure)

- [ ] T001 Create repository skeleton (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`)  
- [ ] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)  
- [ ] T003 Initialize R environment with `renv.lock` and install Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `sva`, `GEOquery`)  
- [ ] T004 Add linting/formatting configuration (`ruff`, `black`, `styler`)  
- [ ] T005 Add CI workflow file `.github/workflows/ci.yml` that runs `make validate` on fresh runner  

## Phase 1 – Foundational (Blocking Prerequisites)

- [ ] T006 [P] Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log`  
- [ ] T007 [P] Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.)  
- [ ] T008 [P] Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check` (calls appropriate Python/R scripts)  
- [ ] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (default threshold 0.8, seed 42)  
- [ ] T010 Implement schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`)  
- [ ] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)  
- [ ] T012 Implement CLI argument validator (part of `run_pipeline.py`) that enforces `--threshold` ≥ 0.75 (per FR‑004)  
- [ ] T013 [P] Implement citation verification step that invokes the Reference‑Validator Agent on all markdown and code files during CI  
- [ ] T098 [P] Extend logger to record the exact command‑line invocation, software versions, and random seed in `pipeline.log` (FR‑035)  
- [ ] T099 [P] CI test that runs the CLI validator and asserts it rejects thresholds < 0.75  
- [ ] T100 [P] CI step that runs the Reference‑Validator Agent and fails the pipeline on any citation mismatch  

## Phase 2 – User Story 1 – Build & Export Co‑expression‑based PPI Predictions (US‑1)

- [ ] T064 US1 Implement GEO downloader `src/pipeline/download.py` (fetches count matrices, records SHA‑256 in `state/artifact_hashes.yaml`)  
- [ ] T043 US1 Abort on insufficient GEO samples: modify downloader to check sample count; if `< 20` abort that series, log `Insufficient sample count (<20)` in `pipeline.log` and continue with remaining series  
- [ ] T042 US1 Verify edge‑list size: unit/integration test that asserts `predicted_ppi_<species>.tsv` contains ≥ 10 000 edges (or is header‑only)  
- [ ] T069 US1 Unit test to verify abort behavior for GEO series with < 20 samples (ensures proper logging and graceful continuation)  
- [ ] T113 US1 Unit test for GEO downloader (checksum recording, error handling)  
- [ ] T065 US1 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2` or subprocess)  
- [ ] T014 US1 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`  
- [ ] T093 US1 Unit tests for normalization (both VST and TPM)  
- [ ] T015 US1 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80 % samples) and write provenance JSON (`results/provenance_<species>.json`)  
- [ ] T094 US1 Unit tests for gene‑filtering (CPM filter and variance‑based sub‑selection)  
- [ ] T016 US1 Implement Pearson correlation matrix and edge extraction `src/pipeline/correlation.py` (threshold `--threshold`, default 0.8, enforce ≥ 0.75)  
- [ ] T095 US1 Unit tests for correlation module (Pearson/Spearman, threshold enforcement)  
- [ ] T083 US1 Implement Benjamini‑Hochberg FDR correction (adjusted p‑value ≤ 0.05) on correlation p‑values (FR‑045)  
- [ ] T084 US1 Unit test for BH correction implementation  
- [ ] T017 US1 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; write `results/mapping_warnings_<species>.log` for unmapped genes  
- [ ] T096 US1 Unit tests for identifier mapping (unmapped logging, schema compliance)  
- [ ] T018 US1 Write edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`)  
- [ ] T097 US1 Unit tests for edge‑list exporter (format, warnings)  
- [ ] T020 US1 Integration test `tests/integration/test_end_to_end_us1.py` that runs `make all` on a tiny mock dataset and checks edge‑list header and **edge‑count ≥ 10 000** (or header‑only) via T042  

## Phase 3 – User Story 2 – Quantitative Evaluation Against STRING (US‑2)

- [ ] T021 US2 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – provides **full high‑confidence set** (combined score ≥ 700) without evidence‑type restriction  
- [ ] T022 US2 Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges, (b) loads STRING high‑confidence interactions, (c) computes AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json`  
- [ ] T023 US2 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC  
- [ ] T091 US2 Implement balanced negative‑sampling module `src/pipeline/negative_sampling.py` that draws a set of gene‑pair negatives equal in size to the positive set, sampled uniformly from all possible pairs absent from STRING, using the global random seed (FR‑032)  
- [ ] T102 US2 Unit test for balanced negative‑sampling (size, seed reproducibility)  
- [ ] T024 US2 Extend `src/cli/run_pipeline.py` to expose `evaluate` sub‑command and pass seed/threshold flags  
- [ ] T025 US2 Add unit tests `tests/unit/test_evaluate.py` and `test_baseline.py` (mock small graph, check metric calculation)  
- [ ] T045 US2 Verify evaluation metrics: CI step that parses `evaluation_metrics.json` and asserts AUROC > 0.70, AUPRC ≥ 0.65, and baseline AUROC ≤ 0.55 for each species; fails the pipeline otherwise  
- [ ] T026 US2 Integration test `tests/integration/test_end_to_end_us2.py` that runs `make evaluate` on the mock data from US1 and asserts metric thresholds are met (uses pre‑computed expected values)  
- [ ] T114 US2 Integration test that runs `make evaluate` on a representative subset of real data and checks that AUROC > 0.70 and AUPRC ≥ 0.65 (addresses FR‑045 & FR‑046)  
- [ ] T115 US2 CI step that runs schema‑validation tests for the updated `evaluation.schema.yaml` (including `precision_at_1000` field)  

## Phase 4 – User Story 3 – Functional Enrichment of Predicted Interactome (US‑3)

- [ ] T027 US3 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology 2023‑12‑01) with Fisher’s exact test and Benjamini–Hochberg correction; output `results/go_enrichment_<species>.tsv`  
- [ ] T028 US3 Add CLI flag `--go-ontology` (default points to cached 2023‑12‑01 file) and integrate into `run_pipeline.py` as `enrich` sub‑command  
- [ ] T029 US3 Write unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation  
- [ ] T044 US3 Verify GO‑enrichment FDR: CI step that parses `go_enrichment_<species>.tsv` and asserts at least one term has adjusted p < 0.05; if none, the pipeline records “No significant enrichment” but the check passes only when the file is correctly formatted  
- [ ] T030 US3 Integration test `tests/integration/test_end_to_end_us3.py` that runs `make enrich` after US1 & US2 and validates presence of at least one significant term (or graceful “No significant enrichment” handling)  

## Phase 5 – Sensitivity Analysis & Supporting Tasks

- [ ] T085 Perform correlation‑threshold sensitivity analysis for thresholds 0.75, 0.80, 0.85, 0.90; write results to `results/threshold_sensitivity_<species>.tsv` (FR‑023)  
- [ ] T086 Schema validation for `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml` (FR‑030)  
- [ ] T087 Unit test for sensitivity analysis output (correct columns, monotonic behavior)  

## Phase 6 – Reporting & Summary (Construct Validity & Final Report)

- [ ] T126 US1 Generate per‑species summary report `summary_<species>.txt` that includes edge count, evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC, precision@1000), top GO terms, threshold‑sensitivity results, and a construct‑validity justification citing the literature (FR‑026)  
- [ ] T127 US1 Aggregate all per‑species summaries into `final_report.txt`, presenting overall performance statistics and restating the construct‑validity justification for the entire study (FR‑028)  

## Phase 7 – Polish & Cross‑Cutting Concerns

- [ ] T036 [P] Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions, including the new false‑positive analysis and validation‑set calibration sections  
- [ ] T108 [P] Documentation update (renamed from duplicate T064) – ensures no ID conflict  
- [ ] T037 Run comprehensive performance benchmark script `scripts/benchmark.sh` to ensure total wall‑clock time ≤ 6 h on the GitHub Actions runner; log results in `results/benchmark_report.txt` (note: enforcement of the 6‑hour limit is performed by T046)  
- [ ] T038 Run CI step to enforce reproducibility: after a successful run, re‑run the pipeline with the same `--seed` and `git diff` the resulting `evaluation_metrics.json` and all `go_enrichment_*.tsv` files; fail if any differences are detected (FR‑012)  
- [ ] T121 CI step that executes the reproducibility re‑run (`make reproducibility-check`) and diffs outputs (ensures T038 is actually executed)  
- [ ] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`)  
- [ ] T122 CI step that runs `ruff`/`mypy` and writes `lint_report.txt` (verifies T039)  
- [ ] T040 Security hardening: verify that all external URLs are fetched over HTTPS and that each download includes a SHA‑256 checksum verification  
- [ ] T111 CI test that runs `scripts/audit_urls.py` to ensure all URLs are HTTPS and checksummed  
- [ ] T041 Documentation: Add a ‘Reproducibility Statement’ to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map  
- [ ] T123 Unit test that checks `docs/README.md` contains the reproducibility statement  
- [ ] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI (ensured by T100)  
- [ ] T050 [P] Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset  
- [ ] T051 CI test that executes the quickstart steps (`make quickstart-test`) and asserts successful completion and correct output file generation  
- [ ] T054 [P] CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.75 (per FR‑004)  
- [ ] T056 Extend `validate.py` (T011) to assert presence and parsability of **all** required output files (`predicted_ppi_*.tsv`, `evaluation_metrics.json`, `go_enrichment_*.tsv`, `pipeline.log`) after each target  
- [ ] T124 CI step that runs the extended `validate.py` after each Make target (ensures T056 is exercised)  
- [ ] T063 Automated check that the benchmark script (T037) reports runtime ≤ 6 h; CI fails otherwise (implemented via T125)  
- [ ] T125 CI step that runs the benchmark runtime check and fails if > 6 h  
- [ ] T062 Verify false‑positive analysis output: unit test that ensures `fp_analysis.py` produces a non‑empty report with expected numeric fields (already covered by T107)  
- [ ] T107 Unit test for false‑positive analysis module  
- [ ] T108 Documentation lint test that verifies `docs/false_positives.md` contains required sections (Poisson derivation, mitigation)  

## Phase 8 – Additional Validation & Maintenance

- [ ] T109 CI test that checks the updated `README.md` and `docs/quickstart.md` contain usage instructions (ensures T036 updates are effective)  
- [ ] T110 CI step that runs `scripts/benchmark.sh` and verifies runtime ≤ 6 h (duplicate of T125 for clarity)  
- [ ] T111 CI test that audits external URLs for HTTPS and checksum (as above)  
- [ ] T112 CI step that ensures the Reference‑Validator Agent is invoked and failures abort the pipeline (as above)  
- [ ] T113 Unit test for GEO downloader (already listed under US1)  
- [ ] T114 Integration test for evaluation on real data (already listed under US2)  
- [ ] T115 CI step for schema validation of updated evaluation schema (already listed)  
- [ ] T116 Unit test for false‑positive summary inclusion in per‑species reports (already listed)  
- [ ] T117 Unit test for precision@1000 inclusion in per‑species reports (already listed)  
- [ ] T118 CI step for final report verification (already listed)  
- [ ] T119 CI script that runs `scripts/check_construct_validity.py` (already listed)  
- [ ] T120 Log‑inspection test that ensures `pipeline.log` records false‑positive analysis and validation‑set steps (already listed)  
- [ ] T121 Reproducibility CI re‑run (already listed)  
- [ ] T122 Linting CI step (already listed)  
- [ ] T123 Reproducibility statement test (already listed)  
- [ ] T124 Extended validation CI step (already listed)  
- [ ] T125 Benchmark runtime CI enforcement (already listed)  
