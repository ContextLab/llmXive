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
- [ ] T001c Verify repository skeleton directories exist after T001 execution (CI test) — Add `tests/integration/test_skeleton_ci.py::test_directories_exist`
- [ ] T001d CI step that fails if any skeleton directory is missing — Implemented as `tests/integration/test_skeleton_ci.py` and CI job `skeleton-ci`
- [ ] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)
- [ ] T002c Verify `pyproject.toml` and `requirements.txt` are created and dependencies are pinned (unit test)
- [ ] T003_new Verify Bioconductor packages (`org.At.tair.db`, `DESeq2`, `limma`) are installable and importable via `rpy2` in the Python environment (replaces T003 series)
- [~] T003c_new Unit test confirming `rpy2` integration works and required packages are available (`tests/unit/test_rpy2_integration.py`)
- [~] T004 Add linting/formatting configuration (`.ruff.toml`, `pyproject.toml` sections for `ruff`, `black`, `styler`)
- [~] T004a **Add linting configuration test** `tests/unit/test_lint_config.py` to verify `.ruff.toml` exists and is syntactically valid (covers lint config delivery) (SC‑006)
- [~] T004c Verify linting config files (`.ruff.toml`, `pyproject.toml` sections) exist and runnable (unit test) — Implemented as `tests/unit/test_lint_config.py`
- [~] T005 Add CI workflow file `.github/workflows/ci.yml` with required jobs (validate, runtime‑check, reproducibility, renv-ci, skeleton-ci, lint, post-validate-ci, benchmark-runtime-check) (fulfills missing artifact) (SC‑004)
- [~] T005a **Add CI workflow file creation task** – generate `.github/workflows/ci.yml` with jobs `validate`, `runtime-check`, `reproducibility`, `renv-ci`, `skeleton-ci`, `lint`, `post-validate-ci`, `benchmark-runtime-check`
- [~] T005c Verify CI workflow file exists and contains a `validate` job (unit test) — Implemented as `tests/unit/test_ci_workflow.py`
- [~] T005d CI step that validates the workflow file structure (`scripts/validate_ci_workflow.py` + test `tests/unit/test_ci_workflow_structure.py`)
- [~] T005e CI job `ci-workflow-validation` runs the above script on each push
- [~] T005f CI job `ci-workflow-validation` added to the workflow file
- [~] T006 Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log` (FR‑010)
- [~] T006a **Implement logger file** `src/utils/logger.py` with JSON‑Line output, including fields `timestamp`, `level`, `message`, `schema_version`, `command`, `versions`, `seed` (fulfills FR‑010 & FR‑035)
- [~] T006c Unit test ensuring logger writes JSON‑Line entries with required fields (`timestamp`, `level`, `message`, `schema_version`) and conforms to `contracts/pipeline_log.schema.yaml` (`tests/unit/test_logger_fields.py`)
- [~] T006d Extend logger to record the exact command‑line invocation, software versions, and random seed in `pipeline.log` (FR‑035) — completed above
- [~] T006e Unit test confirming logger entries contain `command`, `versions`, and `seed` fields per schema (`tests/unit/test_logger_extension.py`)
- [~] T007 Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.)
- [~] T007c Unit test for CLI entry point execution and argument parsing (`tests/unit/test_cli_entrypoint.py`)
- [~] T008 Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check` (calls appropriate Python/R scripts)
- [~] T008c Integration test that all Makefile targets execute without error on a tiny mock dataset (`tests/integration/test_makefile_targets.py`)
- [~] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (default threshold set to a high confidence level, using a standard random seed)
- [~] T009a **Add concrete configuration files** `src/config/species.yaml` and `src/config/parameters.yaml` with required keys (`species`, `geo_accessions`, `threshold`, `seed`, `held_out_series`) (fulfills FR‑001, FR‑002, FR‑048)
- [~] T009c Verify `species.yaml` and `parameters.yaml` are present (unit test) — Implemented as `tests/unit/test_config_files.py`
- [ ] T009c_u Unit test confirming configuration files contain required keys and defaults (`tests/unit/test_config_content.py`)
- [ ] T009d CI step that aborts the run if total wall‑clock time exceeds a predefined maximum duration (hard failure) — Implemented via `scripts/record_runtime.py` and CI job `runtime-check`
- [~] T009e CI job `runtime-check` enforces a predefined multi‑hour wall‑clock limit.
- [~] T010 Implement schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`, `threshold_sensitivity.schema.yaml`, `pipeline_log.schema.yaml`)
- [~] T010a **Create `contracts/pipeline_log.schema.yaml`** defining the JSON‑Line logger schema (required for T006c) (FR‑010)
- [ ] T010c Verify all schema files are syntactically valid YAML/JSON (unit test) — Implemented as `tests/unit/test_schema_syntax.py`
- [~] T010g Create `contracts/pipeline_log.schema.yaml` (JSON‑Line schema for logging) (already created by T010a)
- [~] T010h Validate `results/predicted_ppi_*.tsv` against `contracts/predicted_ppi.schema.yaml` after generation (unit test) — Implemented as `tests/unit/test_predicted_edge_schema.py`
- [~] T010h_c CI step that runs the above validation after each edge‑list creation (ensures FR‑013)
- [~] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)
- [~] T011c Run verification script after every Make target (FR‑017) — Implemented via Makefile `post-validate` target and CI job `post-validate-ci`
- [~] T011c2 Hook validation script after every Make target (CI step) — Implemented and marked completed.
- [~] T011c_c Unit test confirming the post‑validate hook is executed for each target (`tests/unit/test_post_validate_hook.py`)
- [~] T012 Implement CLI argument validator in `src/cli/validator.py` that enforces `--threshold` ≥ 0.75 (per FR‑004)
- [~] T012c Unit test for CLI validator rejecting thresholds < 0.75 (`tests/unit/test_cli_threshold.py`)
- [~] T012d Global seed propagation: ensure `--seed` is passed to all stochastic modules (correlation, baseline, negative sampling, sensitivity)
- [~] T012e Unit test for seed propagation (`tests/unit/test_seed_propagation.py`)
- [~] T013 Implement citation verification step as pre‑commit hook `scripts/run_reference_validator.sh` and CI job that runs the Reference‑Validator Agent, failing on mismatches
- [~] T013c CI job `reference-validator-ci` invoking the above script and failing on non‑zero exit
- [~] T013d Unit test enforcing title‑token overlap ≥ 0.7 (`tests/unit/test_citation_overlap.py`)
- [~] T038 Reproducibility check: re‑run pipeline with same `--seed` and diff all result files; fail on any mismatch (covers SC‑004)
- [~] T038c CI step that runs the reproducibility check and fails on output differences
- [~] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`)
- [~] T039c Unit test confirming dead imports removed and type‑hints complete (unit test)
- [~] T122 CI step that runs `ruff`/`mypy` and writes `lint_report.txt` (verifies T039)
- [~] T040 Security hardening: verify that all external URLs are fetched over HTTPS and that each download includes a SHA‑256 checksum verification
- [~] T040c Unit test ensuring all URLs are HTTPS and checksummed (`tests/unit/test_url_security.py`)
- [~] T111 CI test that runs `scripts/audit_urls.py` to ensure all URLs are HTTPS and checksummed
- [~] T041 Documentation: Add a ‘Reproducibility Statement’ to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map
- [~] T041c Verify reproducibility statement presence and correct referencing (`tests/unit/test_repro_statement.py`)

## Phase 2 – User Story 1 – Data Acquisition & Pre‑processing (US‑1)

- [~] T064 Implement GEO downloader `src/pipeline/download.py` (fetches count matrices, records SHA‑256 in `state/artifact_hashes.yaml`)
- [~] T064c Unit test confirming correct download, checksum recording, and error handling (`tests/unit/test_geo_downloader.py`)
- [ ] T064d Abort pipeline if total retained samples after series‑level filtering < 50 (FR‑047) — implemented and unit‑tested (`tests/integration/test_sample_abort.py`)
- [~] T064d_c Unit test verifying abort behavior on low‑sample series (`tests/unit/test_sample_abort_logic.py`)
- [~] T064e Abort pipeline if total retained samples per species < 50 (FR‑001) — added
- [ ] T014 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`
- [~] T014c Unit test confirming correct handling of both TPM and VST modes (`tests/unit/test_normalization_modes.py`)
- [ ] T065 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2` or subprocess) **after** normalization
- [ ] T065a Implement confound regression `src/pipeline/confound_regression.py` to regress out expression‑level and gene‑length confounds as required by FR‑014; output corrected expression matrix
- [~] T065a_c Unit test ensuring confound regression correctly removes specified confounds (`tests/unit/test_confound_regression.py`)
- [ ] T015 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80 % samples) and retain **at most 5,000 genes** with highest variance (hard limit per FR‑003, SC‑003)
- [~] T015c Unit test for CPM filter and variance‑based sub‑selection (`tests/unit/test_gene_filtering.py`)
- [~] T015e Verify default N=5,000 is enforced if config missing (`tests/unit/test_default_gene_limit.py`)
- [~] T015f Unit test confirming gene limit enforcement (`tests/unit/test_gene_limit_enforced.py`)
- [~] T015g Add unit test verifying hard limit of genes after variance selection (covers FR‑003 verification)
- [ ] T016a [P] Implement Pearson correlation matrix generation `src/pipeline/correlation_raw.py` to compute and stream full raw correlation scores for all gene‑pair candidates using **block-wise processing** (block size=1000 genes) to fit within 7GB RAM, outputting to `results/raw_correlations_<species>.tsv.gz` before any thresholding
- [~] T016a_c Unit test confirming raw correlation file is correctly streamed and parsable (`tests/unit/test_raw_correlation_output.py`)
- [ ] T016a_stream Unit test verifying that correlation computation processes data in blocks and does not load the full matrix into memory (`tests/unit/test_correlation_streaming.py`)
- [ ] T016a_verify Verify that `results/raw_correlations_*.tsv.gz` is written before thresholding (unit test) — Implemented as `tests/unit/test_raw_correlation_presence.py`
- [ ] T017 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; write `results/mapping_warnings_<species>.log` for unmapped genes (FR‑005)
- [~] T017c Unit test for identifier mapping correctness and logging of unmapped genes (`tests/unit/test_mapping.py`)
- [ ] T017d Verify Bioconductor packages for identifier mapping are installed and functional (FR‑005) — implemented and unit‑tested (`tests/unit/test_bioc_packages_mapping.py`)
- [ ] T016b Implement edge extraction `src/pipeline/correlation_extract.py` to extract edges from T016a using the `--threshold` parameter **ONLY** (ignores FDR) and output to `results/predicted_ppi_<species>.tsv`
- [~] T016b_c Verify edge extraction respects correlation threshold exclusively (`tests/unit/test_edge_extraction_threshold.py`)
- [ ] T083 [P] Implement Benjamini‑Hochberg FDR correction `src/pipeline/fdr_correction.py` on correlation p‑values from T016a; output adjusted p‑values to `results/correlation_stats_<species>.tsv` (FR‑045) — **Reporting ONLY; never consumed by edge selection logic**
- [~] T084 Verify `correlation_stats_<species>.tsv` exists, is complete, and parsable (unit test) (`tests/unit/test_fdr_output.py`)
- [ ] T018 Write edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`) — depends on T017 (FR‑011)
- [ ] T018c Unit test for edge‑list exporter (format, warnings) (`tests/unit/test_edge_export.py`)
- [~] T020a Integration test `tests/integration/test_end_to_end_us1.py` that runs `make all` on a tiny mock dataset and checks edge‑list header and **valid format** (edge count may be zero or low)
- [~] T042 Integration test verifying edge‑list contains valid header and format (edge count may be zero or low, no minimum requirement) (`tests/integration/test_edge_count_valid.py`)
- [ ] T042_low Integration test verifying that the pipeline produces a valid header-only file (or low count) when the threshold yields few edges, and continues execution (`tests/integration/test_low_edge_scenario.py`)

## Phase 3 – User Story 2 – Quantitative Evaluation Against STRING (US‑2)

- [ ] T200 Mock edge‑list generator `scripts/generate_mock_edge_list.py` producing `results/predicted_ppi_mock.tsv` for independent US‑2 testing
- [~] T200c Unit test confirming mock edge list format and size suitability (`tests/unit/test_mock_edge_list.py`)
- [ ] T021 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – downloads high‑confidence set (combined score ≥ 700) and explicitly filters out the co‑expression evidence channel
- [~] T021c Unit test to verify that the downloaded STRING file excludes the co‑expression evidence channel (`tests/unit/test_string_download.py`)
- [ ] T022_split Implement data splitting logic `src/pipeline/split_data.py` to separate samples into training (for network construction) and test (for evaluation) sets, preserving species stratification and ensuring no overlap
- [ ] T022_split_c Unit test verifying correct train/test split and no data leakage (`tests/unit/test_data_splitting.py`)
- [~] T022_split_impl Implement the train/test split workflow: split data per species, compute correlations on the **training set** for network construction, and reserve the **test set** for evaluation (FR‑006, Plan Phase 6)
- [ ] T022_split_impl_c Unit test verifying that correlations are computed only on the training set and evaluation uses the test set (`tests/unit/test_split_workflow.py`)
- [ ] T022_eval_impl Implement the evaluation workflow: load predicted edges from `results/predicted_ppi_<species>.tsv`, load STRING high‑confidence interactions, compute AUROC/AUPRC using **ALL gene-pair correlation scores from the TEST SET ONLY** (streaming/block-wise), and write to `results/evaluation_metrics.json` (FR‑006, FR‑020)
- [~] T022_eval_impl_c Unit test validating evaluation metrics against known benchmark on mock data with strict test-set separation (`tests/unit/test_full_evaluation_mock.py`)
- [ ] T091 Implement balanced negative‑sampling module `src/pipeline/negative_sampling.py` (size = positive set) from the complement of STRING (excluding co‑expression channel), using the global random seed (FR‑016)
- [~] T091c Unit test asserting each negative set is true complement of STRING high‑confidence set and respects seed reproducibility (covers FR‑016)
- [~] T091d Verify negative‑sampling uses global seed and size equals positive set (`tests/unit/test_negative_sampling.py`)
- [ ] T023 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC using the same mock edge list input (FR‑007)
- [ ] T023c Validate baseline graph preserves node degree distribution and compute permutation‑test p‑value (`tests/unit/test_baseline.py`)
- [~] T022 Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges **from the real file `results/predicted_ppi_<species>.tsv`**, (b) loads STRING high‑confidence interactions (filtered), (c) **processes ALL gene‑pair correlation scores from the TEST SET ONLY** (via streaming/block‑wise loading) to compute AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json` (covers FR‑006, FR‑020). **Prerequisites**: T022_split, T023, T091, T022_split_impl, T022_eval_impl.
- [~] T022_fullset Implement full-set evaluation on all gene-pair scores from the test set (AUROC/AUPRC) (FR-006) — added and marked completed
- [ ] T022c Verify evaluation script loads data correctly and produces valid JSON (unit test) (`tests/unit/test_full_evaluation.py`)
- [ ] T045c CI step that parses `results/evaluation_metrics.json` and asserts AUROC ≥ 0.70 **and** AUPRC ≥ 0.70 (per SC‑001) — implemented and marked completed
- [~] T045d Verification that both AUROC and AUPRC thresholds are met (unit test `tests/unit/test_evaluation_thresholds.py`)
- [~] T143 Validate `evaluation_metrics.json` against `contracts/evaluation.schema.yaml` (unit test `tests/unit/test_evaluation_schema.py`)

## Phase 4 – User Story 3 – Functional Enrichment of Predicted Interactome (US‑3)

- [~] T028 Add CLI flag `--go-ontology` (default points to cached file) and integrate into `run_pipeline.py` as `enrich` sub‑command
- [~] T028c Unit test for `--go-ontology` flag parsing and integration (`tests/unit/test_go_ontology_flag.py`)
- [~] T027 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology dated early January) with Fisher’s exact test and Benjamini‑Hochberg correction; reads the **mock** prediction file and outputs `results/go_enrichment_<species>.tsv`
- [~] T029 Unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation (uses mock predictions)
- [ ] T044c [P] Unit test verifying that when no GO terms pass FDR < 0.05, the pipeline writes a file with the specific message "No significant enrichment" and exits with code 0 (replaces hard-failure) (`tests/unit/test_go_enrichment_graceful.py`)
- [~] T030 Integration test `tests/integration/test_end_to_edge_us3.py` that runs `make enrich` after US‑1 & US‑2 and validates presence of at least one significant term (or proper graceful exit/failure message).
- [~] T206 GOEnrichmentRecord stores GO enrichment results (`tests/unit/test_go_enrichment_record.py`)

## Phase 5 – Pilot Benchmark & Construct‑Validity (US‑1 Extension)

- [ ] T148 Perform pilot benchmark on a held‑out Arabidopsis GEO series **defined in `species.yaml` as `held_out_series`** (dynamic selection) using default correlation threshold **high value**, compute precision ≥ 0.60 and recall ≥ 0.40 against STRING high‑confidence interactions (excluding co‑expression evidence); output `pilot_validation_<species>.json` and cite it in the summary (FR‑048)
- [~] T148c Unit test verifying pilot benchmark metrics meet precision/recall requirements and JSON is correctly formatted (`tests/unit/test_pilot_benchmark.py`)
- [ ] T150 Extend per‑species summary generation (`src/pipeline/summary.py`) to include the pilot benchmark results and a construct‑validity justification using the citation block from T128 (FR‑026)
- [~] T150c Integration test confirming the summary report contains a "Pilot Benchmark" section with numeric values (`tests/integration/test_summary_pilot.py`)
- [~] T155 Extend per‑species summary to incorporate false‑positive burden estimate and calibration benchmark results (implemented and unit‑tested)
- [~] T155c Unit test ensuring summary includes FP burden and calibration sections (`tests/unit/test_summary_extensions.py`)

## Phase 6 – Sensitivity Analysis & Supporting Tasks

- [~] T085 Correlation‑threshold sensitivity analysis: loop over thresholds **including a low‑threshold case**,, 0.90; for each threshold, re‑run T016a, T016b, and T022. Write results to `results/threshold_sensitivity_<species>.tsv` (FR‑023)
- [~] T085p Record outputs of sensitivity analysis for downstream reporting (produces `results/threshold_sensitivity_<species>.tsv`)
- [ ] T085c Unit test confirming sensitivity output contains rows for each threshold with required columns and respects global seed (`tests/unit/test_sensitivity.py`)
- [~] T086 Schema validation for `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml` (FR‑030, SC‑006)
- [ ] T087 Unit test for sensitivity analysis output (correct columns, monotonic behavior) (`tests/unit/test_sensitivity.py`)

## Phase 7 – Polishing & Cross‑Cutting Concerns

- [ ] T128 Generate construct‑validity citation block: retrieve, verify, and insert specific literature citations (Zhang et al., Lee et al.) into `results/citation_block.txt` as required by FR‑026 (APA style)
- [~] T128c Unit test that `citation_block.txt` contains required citations in correct format (`tests/unit/test_citation_block.py`)
- [~] T126 Generate per‑species summary report `summary_<species>.txt` that includes edge count, evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC, precision@), top GO terms, threshold‑sensitivity results, **pilot benchmark results**, and a construct‑validity justification using the citation block from T128 (FR‑026)
- [~] T127 Aggregate all per‑species summaries into `master_results.json` (Single Source of Truth) and then into `final_report.txt`, presenting overall performance statistics and restating the construct‑validity justification for the entire study (FR‑028)
- [~] T127c Unit test validating `master_results.json` schema compliance (`tests/unit/test_master_results_schema.py`) and existence.
- [~] T127d **Validate `master_results.json`** against `contracts/master_results.schema.yaml` (new schema) to guarantee SSoT integrity (fulfills Constitution Principle IV) (SC‑001)
- [ ] T138 Extend final report generation (`src/pipeline/final_report.py`) to aggregate and display overall performance statistics and summarize **pilot benchmark** outcomes (replaces 'validation‑set calibration')
- [~] T138c Verification that final report includes performance and pilot benchmark sections with consistent numbers (unit test `tests/unit/test_final_report_content.py`)

## Phase 8 – Additional Supporting Tasks

- [~] T036 Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions, including the new pilot benchmark sections
- [ ] T036c Verify documentation builds and usage instructions are accurate (unit test `tests/unit/test_docs_build.py`)
- [ ] T046 Measure pipeline runtime (`scripts/measure_runtime.py`) and write to `results/benchmark_report.txt` (used by T037)
- [~] T046c Verify benchmark script records runtime correctly (unit test `tests/unit/test_measure_runtime.py`)
- [~] T037 Run performance benchmark script `scripts/benchmark.sh` to measure end‑to‑end runtime; record results to `results/benchmark_report.txt` (warn if >6h, do not fail)
- [~] T037c CI step that warns if benchmark runtime exceeds a predefined maximum duration (`benchmark-runtime-check` job)
- [~] T063 Automate check that the benchmark script (T037) reports runtime ≤ 6 h; CI warns otherwise (implemented via job `benchmark-runtime-check`)
- [~] T125 CI step that reads `results/benchmark_report.txt` and warns if runtime > 6 h (replaces missing T046)
- [~] T038 (see Phase 1) ensures reproducibility with identical seed
- [~] T039 Code cleanup (see Phase 1)
- [~] T040 Security hardening (see Phase 1)
- [~] T041 Documentation reproducibility statement (see Phase 1)
- [~] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI (ensured by T100)
- [ ] T050 Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset
- [~] T050c Unit test for quickstart end‑to‑end run (`tests/unit/test_quickstart_run.py`) — completed
- [~] T051 Verify quickstart documentation correctness (`tests/unit/test_quickstart_content.py`)
- [~] T054 CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.75 (per FR‑004)
- [~] T056 Extend `validate.py` (T011) to assert presence and parsability of **all** required output files after each target
- [~] T056c CI step that runs the extended `validate.py` after each Make target (ensures T056 is exercised)
- [~] T056c Unit test confirming extended validation logic works (`tests/unit/test_extended_validation.py`)

## Phase 9 – False‑Positive Burden & Calibration (US‑1 Extension)

- [ ] T300 Compute theoretical false‑positive expectation using a Poisson approximation for each species and write `results/false_positive_burden_<species>.tsv` (columns: `species`, `threshold`, `expected_fp_count`, `expected_fp_rate`) (file path `src/pipeline/false_positive_burden.py`)
- [~] T300c Unit test verifying Poisson calculation correctness and schema compliance (`tests/unit/test_false_positive_burden.py`)
- [ ] T301 Extend per‑species summary generation (`src/pipeline/summary.py`) to include false‑positive burden metrics from `false_positive_burden_<species>.tsv` and reference the Poisson calculation in the report (file path `src/pipeline/summary.py`)
- [~] T301c Integration test ensuring summary incorporates false‑positive burden metrics (`tests/integration/test_summary_fp_burden.py`)
- [~] T302 Documentation update: add a "False‑Positive Burden" section to `docs/README.md` describing the Poisson model, its assumptions, and how the calibration pilot benchmark (T148) informs real‑world FP rates (file path `docs/README.md`)
- [ ] T302c Doc‑build unit test confirming the new section appears in rendered README (`tests/unit/test_readme_fp_section.py`)
- [ ] T303 Documentation update: extend `docs/quickstart.md` to mention the false‑positive analysis step and how to interpret its output (file path `docs/quickstart.md`)
- [ ] T303c Doc‑build unit test ensuring quickstart reflects false‑positive analysis (`tests/unit/test_quickstart_fp_section.py`)
- [ ] T305 Implement calibration assessment script `src/pipeline/calibration.py` that bins correlation scores, computes observed true‑positive rates against STRING high‑confidence interactions, and writes `results/calibration_<species>.tsv`
- [ ] T305c Unit test confirming calibration bins are correctly generated and that observed TP rates align with expectations on a mock dataset (`tests/unit/test_calibration.py`)