# Tasks: Predict Protein‑Protein Interactions from Co‑expression Networks

**Input**: Design documents from `/specs/PROJ-185-predict-ppi-coexpression/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: Tests are defined where explicitly requested in the specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing each story.

## Format: `[ID] [P?] [Story] description (file path)`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 0 – Project Setup (Shared Infrastructure)

- [ ] T001 Create repository skeleton (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`)  
- [ ] T001c Verify repository skeleton directories exist after T001 execution (CI test)  
- [ ] T001d CI step that fails if any skeleton directory is missing  
- [X] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)  
- [ ] T003 Initialize R environment with `renv.lock` and install Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `sva`, `GEOquery`)  
- [ ] T003c Produce `renv.lock` file and ensure it records package versions  
- [ ] T003d Unit test that runs `Rscript -e "renv::status()"` and fails on non‑zero exit  
- [ ] T004 Add linting/formatting configuration (`ruff`, `black`, `styler`)  
- [ ] T004c Create `.ruff.toml` and add `ruff` section to `pyproject.toml`; CI lint job runs `ruff check .` and fails on violations  
- [ ] T005 Add CI workflow file `.github/workflows/ci.yml` that runs `make validate` on fresh runner  
- [ ] T005c Verify CI workflow file exists and contains a `validate` job  
- [ ] T005d CI step that validates the workflow file structure  

## Phase 1 – Foundational (Blocking Prerequisites)

- [ ] T006 [P] Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log`  
- [ ] T006c Unit test ensuring logger writes JSON‑Line entries with required fields (`timestamp`, `level`, `message`, `schema_version`) and conforms to `contracts/pipeline_log.schema.yaml`  
- [X] T007 [P] Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.)  
- [X] T008 [P] Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check` (calls appropriate Python/R scripts)  
- [ ] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (default threshold set to a high confidence level, using a standard random seed)  
- [ ] T009c Schema validation for `species.yaml` and `parameters.yaml` against `contracts/config.schema.yaml` (CI step)  
- [ ] T009d CI step enforcing overall pipeline runtime ≤ 6 h (uses benchmark script)  
- [ ] T010 Implement schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`, `threshold_sensitivity.schema.yaml`, `pipeline_log.schema.yaml`)  
- [ ] T010a Create `contracts/predicted_ppi.schema.yaml` (YAML schema for predicted edge list)  
- [ ] T010b Create `contracts/evaluation.schema.yaml` (YAML schema for evaluation metrics)  
- [ ] T010c Create `contracts/threshold_sensitivity.schema.yaml` (YAML schema for sensitivity analysis output)  
- [ ] T010d Create `contracts/pipeline_log.schema.yaml` (JSON‑Line schema for logging)  
- [X] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)  
- [ ] T011c Run verification script after every Make target (FR‑017)  
- [ ] T012 Implement CLI argument validator in `src/cli/validator.py` that enforces `--threshold` ≥ 0.75 (per FR‑004)  
- [ ] T012c Unit test for CLI validator rejecting thresholds < 0.75 (`tests/unit/test_cli_threshold.py`)  
- [ ] T012d Global seed propagation: ensure `--seed` is passed to all stochastic modules (correlation, baseline, negative sampling, sensitivity)  
- [ ] T013 Implement citation verification step as pre‑commit hook `scripts/run_reference_validator.sh` and CI job that runs the Reference‑Validator Agent, failing on mismatches  
- [ ] T013c CI job invoking Reference‑Validator and aborting on non‑zero exit  
- [ ] T098 Extend logger to record the exact command‑line invocation, software versions, and random seed in `pipeline.log` (FR‑035)  
- [ ] T098c Unit test confirming logger entries contain `command`, `versions`, and `seed` fields per schema  
- [ ] T098d Unit test for logger extension (already present)  
- [ ] T099 CI test that runs the CLI validator and asserts it rejects thresholds < 0.75 (`threshold-validator` job)  
- [ ] T099c CI step executing T012c unit test and failing on violation  
- [ ] T100 CI step that runs the Reference‑Validator Agent and fails the pipeline on any citation mismatch (`reference-validator-ci` job)  
- [ ] T100c CI job invoking Reference‑Validator and aborting on non‑zero exit  

## Phase 2 – User Story 2 – Quantitative Evaluation Against STRING (US‑2)

- [ ] T064 US1 Implement GEO downloader `src/pipeline/download.py` (fetches count matrices, records SHA‑256 in `state/artifact_hashes.yaml`)  
- [ ] T043 US1 Skip GEO series with < 30 samples: modify downloader to check sample count; if `< 30` skip that series with a warning in `pipeline.log` and continue with remaining series (per spec Edge Cases)  
- [ ] T042 US1 Verify edge‑list size: unit/integration test that asserts edge count ≥ 10 000 **or** file contains header only when no edges meet threshold (`tests/unit/test_edge_count.py`)  
- [ ] T069 US1 Unit test to verify skip behavior for GEO series with < 30 samples (ensures proper logging and graceful continuation)  
- [ ] T113 US1 Unit test for GEO downloader (checksum recording, error handling)  
- [ ] T065 US1 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2` or subprocess)  
- [ ] T065a US1 Implement confound regression `src/pipeline/confound_regression.py` to regress out expression‑level and gene‑length confounds as required by FR‑014; output corrected expression matrix  
- [ ] T065b Verify corrected expression matrix exists and confound regression applied (unit test)  
- [ ] T014 US1 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`  
- [ ] T093 US1 Unit tests for normalization (both VST and TPM) (`tests/unit/test_normalization.py`)  
- [ ] T015 US1 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80 % samples) and retain at most the N genes with highest variance, where N is read from `species.yaml` (default a substantial number); write provenance JSON (`results/provenance_<species>.json`)  
- [ ] T094 US1 Unit tests for gene‑filtering (CPM filter and variance‑based sub‑selection) (`tests/unit/test_filtering.py`)  
- [ ] T016a US1 Implement Pearson correlation matrix generation `src/pipeline/correlation_raw.py` to compute and stream full raw correlation scores for all gene‑pair candidates to `results/raw_correlations_<species>.tsv.gz` before any thresholding  
- [ ] T020c Verify `raw_correlations_<species>.tsv.gz` exists, is complete, and parsable (unit test)  
- [ ] T025c Confirm FR‑025 by checking raw correlation retention before thresholding (unit test)  
- [ ] T083 Implement Benjamini‑Hochberg FDR correction `src/pipeline/fdr_correction.py` on correlation p‑values from T016a; output adjusted p‑values (FR‑045)  
- [ ] T083c Unit test ensuring edges are filtered by adjusted p ≤ 0.05 before writing edge list (`tests/unit/test_fdr_correction.py`)  
- [ ] T016b US1 Implement edge extraction `src/pipeline/correlation_extract.py` to extract edges from T016a using FDR‑corrected p‑values from T083 and the `--threshold` parameter; output to `results/predicted_ppi_<species>.tsv`  
- [ ] T095 US1 Unit tests for correlation module (Pearson/Spearman, threshold enforcement) (`tests/unit/test_correlation.py`)  
- [ ] T096 US1 Unit tests for identifier mapping (unmapped logging, schema compliance) (`tests/unit/test_mapping.py`)  
- [ ] T017 US1 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; write `results/mapping_warnings_<species>.log` for unmapped genes  
- [ ] T017a Unit test for identifier mapping correctness and logging of unmapped genes (`tests/unit/test_mapping.py`)  
- [ ] T018 US1 Write edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`)  
- [ ] T097 US1 Unit tests for edge‑list exporter (format, warnings) (`tests/unit/test_exporter.py`)  
- [ ] T020a Integration test `tests/integration/test_end_to_end_us1.py` that runs `make all` on a tiny mock dataset and checks edge‑list header and **header‑only OR ≥ 10 000 edges** via T042  

## Phase 3 – User Story 3 – Functional Enrichment of Predicted Interactome (US‑3)

- [ ] T200 US2 Mock edge‑list generator `scripts/generate_mock_edge_list.py` producing `results/predicted_ppi_mock.tsv` for independent US‑2 testing  
- [ ] T200c Unit test confirming mock edge list format and size suitability (`tests/unit/test_mock_edge_list.py`)  
- [ ] T021 US2 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – downloads high‑confidence set (combined score ≥ 700) and explicitly filters out the co‑expression evidence channel  
- [ ] T021b US2 Unit test to verify that the downloaded STRING file excludes the co‑expression evidence channel (`tests/unit/test_string_download.py`)  
- [ ] T022 US2 Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges **from the mock file `results/predicted_ppi_mock.tsv` for unit testing (or the real file when available)**, (b) loads STRING high‑confidence interactions (filtered), (c) computes AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json`  
- [ ] T022a Compute AUROC/AUPRC on the **full**, imbalanced correlation set before any thresholding (fulfills FR‑006)  
- [ ] T023 US2 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC using the same mock edge list input  
- [ ] T023c Validate baseline graph preserves node degree distribution and compute permutation‑test p‑value (`baseline_p`)  
- [ ] T091 US2 Implement balanced negative‑sampling module `src/pipeline/negative_sampling.py` that draws N=10 independent balanced negative sets (size = positive set) from the complement of STRING (excluding co‑expression channel), using the global random seed (FR‑032) – operates on the mock edge list for independent testing  
- [ ] T091c Assert each negative set is true complement of STRING high‑confidence set (`tests/unit/test_negative_sampling.py`)  
- [ ] T091d Verify negative‑sampling uses global seed and size equals positive set (`tests/unit/test_negative_sampling.py`)  
- [ ] T092 US2 Implement median aggregation `src/pipeline/aggregate_metrics.py` to compute median AUROC/AUPRC across the 10 negative sets generated by T091  
- [ ] T102 US2 Unit test for balanced negative‑sampling (size, seed reproducibility) (`tests/unit/test_negative_sampling.py`)  
- [ ] T024 US2 Extend `src/cli/run_pipeline.py` to expose `evaluate` sub‑command and pass seed/threshold flags  
- [ ] T025 US2 Add unit tests `tests/unit/test_evaluate.py` and `test_baseline.py` (mock small graph, check metric calculation)  
- [ ] T045c Verify evaluation metrics: CI step that parses `results/evaluation_metrics.json` and asserts AUROC ≥ 0.70 and AUPRC ≥ 0.65 (passes on mock data)  
- [ ] T026 US2 Integration test `tests/integration/test_end_to_end_us2.py` that runs `make evaluate` on the mock data from US‑1 (or mock edge list) and asserts metric thresholds are met (uses pre‑computed expected values)  
- [ ] T114 US2 Integration test that runs `make evaluate` on a representative subset of real data and checks that evaluation respects FR‑045 & FR‑046  

## Phase 4 – Sensitivity Analysis & Supporting Tasks

- [ ] T201 US3 Mock prediction artifact generator `scripts/generate_mock_predictions.py` that creates minimal `results/predicted_ppi_mock.tsv` and `results/evaluation_metrics.json` for enrichment testing  
- [ ] T201c Unit test confirming mock prediction files meet schema (`tests/unit/test_mock_predictions.py`)  
- [ ] T027 US3 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology dated 2023‑12‑01) with Fisher’s exact test and Benjamini–Hochberg correction; reads the **mock** prediction file and outputs `results/go_enrichment_<species>.tsv`  
- [ ] T028 US3 Add CLI flag `--go-ontology` (default points to cached 2023‑12‑01 file) and integrate into `run_pipeline.py` as `enrich` sub‑command  
- [ ] T029 US3 Write unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation (uses mock predictions)  
- [ ] T044 US3 Verify GO‑enrichment FDR: CI step that parses `results/go_enrichment_<species>.tsv` and asserts at least one term has adjusted p < 0.05; if none, pipeline records “No significant enrichment” but CI passes only when file is correctly formatted (operates on mock data)  
- [ ] T044c Integration test ensuring pipeline continues without error when only “No significant enrichment” line is present (`tests/integration/test_no_enrichment.py`)  
- [ ] T030 US3 Integration test `tests/integration/test_end_to_edge_us3.py` that runs `make enrich` after US‑1 & US‑2 (or using the mock predictions from T201) and validates presence of at least one significant term (or graceful handling)  

## Phase 6 – Polish & Cross‑Cutting Concerns

- [ ] T085 US1/US2 Perform correlation‑threshold sensitivity analysis: loop over thresholds 0.80, 0.85, 0.90; for each threshold, re‑run T016a, T083, T016b, and T022. Write results to `results/threshold_sensitivity_<species>.tsv` (FR‑023)  
- [ ] T085p Record outputs of sensitivity analysis for downstream reporting (produces `results/threshold_sensitivity_<species>.tsv`)  
- [ ] T085c Unit test confirming sensitivity output contains rows for each threshold with required columns and respects global seed (`tests/unit/test_sensitivity.py`)  
- [ ] T086 Schema validation for `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml` (FR‑030)  
- [ ] T087 Unit test for sensitivity analysis output (correct columns, monotonic behavior) (`tests/unit/test_sensitivity.py`)  

## Phase 7 – Removed Tasks (Scope Creep / External Calibration)

- [ ] T128 US1 Generate construct‑validity citation block: retrieve, verify, and insert specific literature citations (Zhang et al., Lee et al.) into a text block `results/citation_block.txt` as required by FR‑026 (APA style)  
- [ ] T128c Unit test that `citation_block.txt` contains required citations in correct format (`tests/unit/test_citation_block.py`)  
- [ ] T126 US1 Generate per‑species summary report `summary_<species>.txt` that includes edge count, evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC, precision@1000), top GO terms, threshold‑sensitivity results, and a construct‑validity justification using the citation block from T128 (FR‑026)  
- [ ] T126c Unit test ensuring per‑species summary contains all required fields (`tests/unit/test_summary.py`)  
- [ ] T126d Unit test verifying top enriched GO terms are correctly extracted and ordered (`tests/unit/test_summary.py`)  
- [ ] T127 US1 Aggregate all per‑species summaries into `final_report.txt`, presenting overall performance statistics and restating the construct‑validity justification for the entire study (FR‑028)  
- [ ] T127c Integration test that `final_report.txt` correctly aggregates per‑species sections (`tests/integration/test_final_report.py`)  

## Phase 8 – Additional Supporting Tasks

- [ ] T036 [P] Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions, including the new validation‑set calibration sections  
- [ ] T108b [P] Documentation update (renamed from duplicate T064) – ensures no ID conflict  
- [ ] T046 Measure pipeline runtime (`scripts/measure_runtime.py`) and write to `results/benchmark_report.txt` (used by T037)  
- [ ] T046c CI step that fails if benchmark runtime exceeds a reasonable maximum duration. (`benchmark-runtime-check` job)  
- [ ] T037 Run performance benchmark script `scripts/benchmark.sh` to measure end‑to‑end runtime; assert runtime ≤ 6 h and write results to `results/benchmark_report.txt`  
- [ ] T037c CI step that fails if benchmark runtime exceeds 6 h (`benchmark-runtime-check` job)  
- [ ] T063 Automate check that the benchmark script (T037) reports runtime ≤ 6 h; CI fails otherwise (implemented via T125)  
- [ ] T125 CI step that reads `results/benchmark_report.txt` and fails if runtime > 6 h (replaces missing T046)  
- [ ] T038 Run CI step to enforce reproducibility: re‑run the pipeline with the same `--seed`, `git diff --exit-code` all result files, and fail on any mismatch (covers SC‑004)  
- [ ] T038c CI step that re‑runs pipeline with same seed and diffs outputs, failing on any mismatch  
- [ ] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`)  
- [ ] T122 CI step that runs `ruff`/`mypy` and writes `lint_report.txt` (verifies T039)  
- [ ] T040 Security hardening: verify that all external URLs are fetched over HTTPS and that each download includes a SHA‑256 checksum verification  
- [ ] T111 CI test that runs `scripts/audit_urls.py` to ensure all URLs are HTTPS and checksummed  
- [ ] T041 Documentation: Add a ‘Reproducibility Statement’ to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map  
- [ ] T123 Unit test that `docs/README.md` contains the reproducibility statement (`tests/unit/test_readme_reproducibility.py`)  
- [ ] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI (ensured by T100)  
- [ ] T050 [P] Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset  
- [ ] T051 CI test that executes the quickstart steps (`make quickstart-test`) and asserts successful completion and correct output file generation (`tests/integration/test_quickstart.py`)  
- [ ] T054 [P] CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.75 (per FR‑004)  
- [ ] T056 Extend `validate.py` (T011) to assert presence and parsability of **all** required output files (`predicted_ppi_*.tsv`, `evaluation_metrics.json`, `go_enrichment_*.tsv`, `pipeline.log`) after each target  
- [ ] T124 CI step that runs the extended `validate.py` after each Make target (ensures T056 is exercised)  
- [ ] T062 Verify false‑positive analysis output: unit test that ensures `fp_analysis.py` produces a non‑empty report with expected numeric fields (`tests/unit/test_fp_analysis.py`)  

## Phase 8 – False‑Positive Burden Analysis & Validation Set

- [ ] T129 [P] US1 Implement false‑positive burden estimator `src/pipeline/fp_burden.py` that uses a Poisson approximation to compute the expected number of spurious edges given the total number of gene‑pair tests, correlation threshold, and BH‑adjusted p‑value cutoff; outputs `results/fp_burden_<species>.txt`  
- [ ] T130 US1 Unit test `tests/unit/test_fp_burden.py` validating the Poisson calculation on a toy dataset (e.g., 1 000 genes, threshold 0.80, p‑value 1e‑4 → expected false positives are anticipated to be low.)  
- [ ] T131 US1 Write documentation `docs/false_positives.md` describing the theoretical false‑positive burden, the Poisson model, and mitigation strategies (e.g., stricter thresholds, multiple‑testing correction, validation set usage)  
- [ ] T132 US1 Implement validation‑set downloader `src/pipeline/download_validation_set.py` that fetches experimentally confirmed PPIs for each species from BioGRID (or an equivalent curated source), verifies SHA‑256 checksums, and stores them as `data/validation/<species>_validated.tsv`  
- [ ] T133 US1 Extend evaluation script (`src/pipeline/evaluate.py`) to optionally incorporate the validation set for calibration: compute calibration curves, adjust threshold recommendations, and record a `validation_calibration_<species>.json` artifact  
- [ ] T134 [P] CI step `make fp-analysis` that runs `src/pipeline/fp_burden.py` for all species and asserts the generated report exists and contains a numeric expected‑false‑positive count  
- [ ] T135c CI check that `docs/false_positives.md` includes the explicit Poisson formula string `λ = N * p` and a reference to the Dyson‑style discussion; fails otherwise  