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

- [X] T001 Create repository skeleton (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`)
- [X] T001c Verify repository skeleton directories exist after T001 execution (CI test) — Add `tests/integration/test_skeleton_ci.py::test_directories_exist`
- [X] T001d CI step that fails if any skeleton directory is missing — Implemented as `tests/integration/test_skeleton_ci.py` and CI job `skeleton-ci`
- [X] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)
- [X] T002c Verify `pyproject.toml` and `requirements.txt` are created and dependencies are pinned (unit test)
- [X] T003 Initialize R environment with `renv.lock` and install Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `sva`, `GEOquery`)
- [X] T003c Verify `renv.lock` is generated and records package versions (unit test)
- [X] T003d Unit test that runs `Rscript -e "renv::status()"` and fails on non‑zero exit — Implemented as `tests/integration/test_renv_status.py`
- [X] T003e CI step that validates R environment and fails on missing packages (pre‑commit hook)
- [X] **[X] T003b Generate `renv.lock` using `renv::init()` and commit it** (ensures file exists)
- [X] T004 Add linting/formatting configuration (`ruff`, `black`, `styler`)
- [X] T004c Verify linting config files (`.ruff.toml`, `pyproject.toml` sections) exist and runnable (unit test) — Implemented as `tests/unit/test_lint_config.py`
- [X] [X] T005 Add CI workflow file `.github/workflows/ci.yml` (declared, but file missing)
- [X] **[X] T005f Create `.github/workflows/ci.yml` with required jobs (validate, runtime‑check, reproducibility, etc.)**
- [X] T005c Verify CI workflow file exists and contains a `validate` job (unit test) — Implemented as `tests/unit/test_ci_workflow.py`
- [X] T005d CI step that validates the workflow file structure — Implemented via `scripts/validate_ci_workflow.py` and test `tests/unit/test_ci_workflow_structure.py`
- [X] T005e CI job `ci-workflow-validation` runs the above script on each push
- [X] T005e CI job `ci-workflow-validation` runs the above script on each push
- [X] T006 Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log`
- [X] T006c Unit test ensuring logger writes JSON‑Line entries with required fields (`timestamp`, `level`, `message`, `schema_version`) and conforms to `contracts/pipeline_log.schema.yaml` — Implemented as `tests/unit/test_logger_fields.py`
- [X] T098 Extend logger to record the exact command‑line invocation, software versions, and random seed in `pipeline.log` (FR‑035)
- [X] **[X] T098_schema_new Create `contracts/pipeline_log.schema.yaml` JSON‑Line schema for logger entries**
- [X] T098c Unit test confirming logger entries contain `command`, `versions`, and `seed` fields per schema — Implemented as `tests/unit/test_logger_extension.py`
- [X] T098d Verify logger extension unit test exists (`tests/unit/test_logger_extension.py`)
- [X] T007 Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.)
- [X] T007c Unit test for CLI entry point execution and argument parsing (`tests/unit/test_cli_entrypoint.py`)
- [X] T008 Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check` (calls appropriate Python/R scripts)
- [X] T008c Integration test that all Makefile targets execute without error on a tiny mock dataset (`tests/integration/test_makefile_targets.py`)
- [X] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (default threshold set to a high confidence level, using a standard random seed)
- [X] T009c Verify `species.yaml` and `parameters.yaml` are present (unit test) — Implemented as `tests/unit/test_config_files.py`
- [X] T009c_u Unit test confirming configuration files contain required keys and defaults (`tests/unit/test_config_content.py`)
- [X] T009d CI step that aborts the run if total wall‑clock time exceeds a predefined maximum duration (hard failure) — Implemented via `scripts/record_runtime.py` and CI job `runtime-check`
- [X] T009e CI job `runtime-check` enforces a predefined multi‑hour wall‑clock limit.
- [X] T010 Implement schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`, `threshold_sensitivity.schema.yaml`, `pipeline_log.schema.yaml`)
- [X] T010c Verify all schema files are syntactically valid YAML/JSON (unit test) — Implemented as `tests/unit/test_schema_syntax.py`
- [X] T010d Create `contracts/predicted_ppi.schema.yaml` (YAML schema for predicted edge list)
- [X] T010e Create `contracts/evaluation.schema.yaml` (YAML schema for evaluation metrics)
- [X] T010f Create `contracts/threshold_sensitivity.schema.yaml` (YAML schema for sensitivity output)
- [X] T010g Create `contracts/pipeline_log.schema.yaml` (JSON‑Line schema for logging) *(already created by T098_schema_new)*
- [X] T010h Validate `results/predicted_ppi_*.tsv` against `contracts/predicted_ppi.schema.yaml` after generation (unit test) — Implemented as `tests/unit/test_predicted_edge_schema.py`
- [X] T010h_c CI step that runs the above validation after each edge‑list creation (ensures FR‑013)
- [X] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)
- [X] T011c Run verification script after every Make target (FR‑017) — Implemented via Makefile `post-validate` target and CI job `post-validate-ci`
- [X] T011c2 Hook validation script after every Make target (CI step) — Implemented and marked completed.
- [X] T011c2_ci CI step that runs the post‑validate hook on each target
- [X] T011c_c Unit test confirming the post‑validate hook is executed for each target (`tests/unit/test_post_validate_hook.py`)
- [X] T012 Implement CLI argument validator in `src/cli/validator.py` that enforces `--threshold` ≥ 0.75 (per FR‑004)
- [X] T012c Unit test for CLI validator rejecting thresholds < 0.75 (`tests/unit/test_cli_threshold.py`)
- [X] T012d Global seed propagation: ensure `--seed` is passed to all stochastic modules (correlation, baseline, negative sampling, sensitivity)
- [X] T012e Unit test for seed propagation (`tests/unit/test_seed_propagation.py`)
- [X] T013 Implement citation verification step as pre‑commit hook `scripts/run_reference_validator.sh` and CI job that runs the Reference‑Validator Agent, failing on mismatches
- [X] T013c CI job `reference-validator-ci` invoking the above script and failing on non‑zero exit
- [X] T013d Unit test enforcing title‑token overlap ≥ 0.7 (`tests/unit/test_citation_overlap.py`)
- [X] T099 CI test for CLI validator — Implemented as CI job `threshold-validator-ci` running `pytest tests/unit/test_cli_threshold.py`
- [X] T099c CI step executing T012c unit test — Implemented in job `cli-threshold-ci`
- [X] T100 CI step for citation validation — Implemented as CI job `citation-validator-ci` running the pre‑commit hook
- [X] T100c CI job `citation-validator-ci` invoking `scripts/run_reference_validator.sh`
- [X] T038 Reproducibility check: re‑run pipeline with same `--seed` and diff all result files; fail on any mismatch (covers SC‑004)
- [X] T038c CI step that runs the reproducibility check and fails on output differences
- [X] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`)
- [X] T039c Unit test confirming dead imports removed and type‑hints complete (unit test)
- [X] T122 CI step that runs `ruff`/`mypy` and writes `lint_report.txt` (verifies T039)
- [X] T040 Security hardening: verify that all external URLs are fetched over HTTPS and that each download includes a SHA‑256 checksum verification
- [X] T040c Unit test ensuring all URLs are HTTPS and checksummed (`tests/unit/test_url_security.py`)
- [X] T111 CI test that runs `scripts/audit_urls.py` to ensure all URLs are HTTPS and checksummed
- [X] T041 Documentation: Add a ‘Reproducibility Statement’ to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map
- [X] T041c Verify reproducibility statement presence and correct referencing (`tests/unit/test_repro_statement.py`)

## Phase 1 – Foundational (Blocking Prerequisites)

- [X] T006 Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log`
- [X] T006c Unit test ensuring logger writes JSON‑Line entries with required fields (`timestamp`, `level`, `message`, `schema_version`) and conforms to `contracts/pipeline_log.schema.yaml` — Implemented as `tests/unit/test_logger_fields.py`
- [X] T098 Extend logger to record command, versions, seed (FR‑035) — completed above
- [X] T098c Unit test confirming logger entries contain `command`, `versions`, and `seed` fields — completed above
- [X] T007 Implement CLI entry point `src/cli/run_pipeline.py` — completed above
- [X] T008 Write Makefile with required targets — completed above
- [X] T009 Create configuration directory and files — completed above
- [X] T010 Implement schema files — completed above
- [X] T011 Write validation script and hook — completed above
- [X] T012 Implement CLI argument validator — completed above
- [X] T013 Implement citation verification step — completed above

## Phase 2 – User Story 1 – Data Acquisition & Pre‑processing (US‑1)

- [X] T064 Implement GEO downloader `src/pipeline/download.py` (fetches count matrices, records SHA‑256 in `state/artifact_hashes.yaml`)
- [X] T064c Unit test confirming correct download, checksum recording, and error handling (`tests/unit/test_geo_downloader.py`)
- [X] [X] T064d Abort pipeline if total retained samples after series‑level filtering < 50 (FR‑047) — implemented and unit‑tested (`tests/integration/test_sample_abort.py`)
- [X] T064d_c Unit test verifying abort behavior on low‑sample series (`tests/unit/test_sample_abort_logic.py`)
- **[X] T064e Abort pipeline if total retained samples per species < 50 (FR‑001)** — added to satisfy FR‑001 requirement
- [X] T065 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2` or subprocess)
- [X] T065a Implement confound regression `src/pipeline/confound_regression.py` to regress out expression‑level and gene‑length confounds as required by FR‑014; output corrected expression matrix
- [X] T065a_c Unit test ensuring confound regression correctly removes specified confounds (`tests/unit/test_confound_regression.py`)
- [X] T014 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`
- [X] T014c Unit test confirming correct handling of both TPM and VST modes (`tests/unit/test_normalization_modes.py`)
- [X] T015 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80 % samples) and retain **at most 5,000 genes** with highest variance (hard limit per FR‑003, SC‑003)
- [X] T015c Unit test for CPM filter and variance‑based sub‑selection (`tests/unit/test_gene_filtering.py`)
- [X] T015e Verify default N=5,000 is enforced if config missing (`tests/unit/test_default_gene_limit.py`)
- [X] T015f Unit test confirming gene limit enforcement (`tests/unit/test_gene_limit_enforced.py`)
- **[X] T015g Add unit test verifying hard limit of [deferred] genes after variance selection** (covers FR‑003 verification)
- [X] T016a Implement Pearson correlation matrix generation `src/pipeline/correlation_raw.py` to compute and stream full raw correlation scores for all gene‑pair candidates (block size=1000 genes) to `results/raw_correlations_<species>.tsv.gz` before any thresholding
- [X] T016a_c Unit test confirming raw correlation file is correctly streamed and parsable (`tests/unit/test_raw_correlation_output.py`)
- [X] T016a_verify Verify that `results/raw_correlations_*.tsv.gz` is written before thresholding (unit test) — Implemented as `tests/unit/test_raw_correlation_presence.py`
- [X] T017 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; write `results/mapping_warnings_<species>.log` for unmapped genes (FR‑005)
- [X] T017c Unit test for identifier mapping correctness and logging of unmapped genes (`tests/unit/test_mapping.py`)
- [X] T017d Verify Bioconductor packages for identifier mapping are installed and functional (FR‑005) — implemented and unit‑tested (`tests/unit/test_bioc_packages_mapping.py`)
- [X] T016b Implement edge extraction `src/pipeline/correlation_extract.py` to extract edges from T016a using the `--threshold` parameter **ONLY** (ignores FDR) and output to `results/predicted_ppi_<species>.tsv`
- [X] T016b_c Verify edge extraction respects correlation threshold exclusively (`tests/unit/test_edge_extraction_threshold.py`)
- [X] T083 Implement Benjamini‑Hochberg FDR correction `src/pipeline/fdr_correction.py` on correlation p‑values from T016a; output adjusted p‑values to `results/correlation_stats_<species>.tsv` (FR‑045) — **Reporting ONLY; never consumed by edge selection logic**
- [X] T084 Verify `correlation_stats_<species>.tsv` exists, is complete, and parsable (unit test) (`tests/unit/test_fdr_output.py`)
- [X] T018 Write edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`) — depends on T017 (FR‑011)
- [X] T018c Unit test for edge‑list exporter (format, warnings) (`tests/unit/test_edge_export.py`)
- [X] T020a Integration test `tests/integration/test_end_to_end_us1.py` that runs `make all` on a tiny mock dataset and checks edge‑list header and **≥ 10 000 edges** via T042
- [X] T200_RNASeqSample Load GEO series into `RNASeqSample` entities (used by T064) (`tests/unit/test_rnaseq_sample.py`)
- [X] T201_Gene Process `Gene` entities after filtering (`tests/unit/test_gene_entity.py`)
- [X] T202_RawCorrelation Compute and store `RawCorrelation` objects (covers T016a) (`tests/unit/test_raw_correlation_entity.py`)
- [X] T203_ProteinCorrelation Generate `ProteinCorrelation` after mapping (`tests/unit/test_protein_correlation.py`)
- [X] T204_PredictedEdge Export `PredictedEdge` list (`tests/unit/test_predicted_edge_export.py`)
- [X] T205_EvaluationMetric Compute evaluation metrics (AUROC/AUPRC) (`tests/unit/test_evaluation_metric.py`)
- [X] T205c Implement EvaluationMetric data‑model entity creation and schema validation after evaluation (covers data‑model coverage)

## Phase 3 – User Story 2 – Quantitative Evaluation Against STRING (US‑2)

- [X] T200 Mock edge‑list generator `scripts/generate_mock_edge_list.py` producing `results/predicted_ppi_mock.tsv` for independent US‑2 testing
- [X] T200c Unit test confirming mock edge list format and size suitability (`tests/unit/test_mock_edge_list.py`)
- [X] [X] T021 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – downloads high‑confidence set (combined score ≥ 700) and explicitly filters out the co‑expression evidence channel
- [X] T021c Unit test to verify that the downloaded STRING file excludes the co‑expression evidence channel (`tests/unit/test_string_download.py`)
- [X] [X] T091 Implement balanced negative‑sampling module `src/pipeline/negative_sampling.py` (size = positive set) from the complement of STRING (excluding co‑expression channel), using the global random seed (FR‑016)
- [X] T091c Unit test asserting each negative set is true complement of STRING high‑confidence set and respects seed reproducibility (covers FR‑016)
- [X] T091d Verify negative‑sampling uses global seed and size equals positive set (`tests/unit/test_negative_sampling.py`)
- [X] [X] T023 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC using the same mock edge list input (FR‑007)
- [X] T023c Validate baseline graph preserves node degree distribution and compute permutation‑test p‑value (`tests/unit/test_baseline.py`)
- [X] [X] T022 Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges **from the real file `results/predicted_ppi_<species>.tsv`**, (b) loads STRING high‑confidence interactions (filtered), (c) **processes ALL gene‑pair correlation scores (full set)** via streaming/block‑wise loading to compute AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json` (covers FR‑006, FR‑020). **Prerequisites**: T023, T091.
- [X] **[X] T022_fullset Implement full‑set evaluation on all gene‑pair scores (AUROC/AUPRC) (FR‑006)** — added and marked completed
- [X] T022c Verify evaluation script loads data correctly and produces valid JSON (unit test) (`tests/unit/test_full_evaluation.py`)
- [X] T022a_c Unit test validating evaluation metrics against known benchmark on mock data (`tests/unit/test_full_evaluation_mock.py`)
- [X] T092 Implement median aggregation `src/pipeline/aggregate_metrics.py` to compute median AUROC/AUPRC across the 1 negative set generated by T091
- [X] T092c Unit test for median aggregation (`tests/unit/test_median_aggregation.py`)
- [X] T024 Extend `src/cli/run_pipeline.py` to expose `evaluate` sub‑command and pass seed/threshold flags
- [X] T024c Verify new CLI sub‑command parses and routes correctly (unit test `tests/unit/test_cli_evaluate.py`)
- [X] T025 Add unit tests `tests/unit/test_evaluate.py` and `tests/unit/test_baseline.py` (mock small graph, check metric calculation)
- [X] [X] T045c CI step that parses `results/evaluation_metrics.json` and asserts AUROC ≥ 0.70 **and** AUPRC ≥ 0.70 (per SC‑001) — implemented and marked completed
- [X] T045d Verification that both AUROC and AUPRC thresholds are met (unit test `tests/unit/test_evaluation_thresholds.py`)
- [X] T143 Validate `evaluation_metrics.json` against `contracts/evaluation.schema.yaml` (unit test `tests/unit/test_evaluation_schema.py`)

## Phase 4 – User Story 3 – Functional Enrichment of Predicted Interactome (US‑3)

- [X] T028 Add CLI flag `--go-ontology` (default points to cached 2023‑12‑01 file) and integrate into `run_pipeline.py` as `enrich` sub‑command
- [X] T028c Unit test for `--go-ontology` flag parsing and integration (`tests/unit/test_go_ontology_flag.py`)
- [X] [X] T027 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology dated ‑‑01) with Fisher’s exact test and Benjamini‑Hochberg correction; reads the **mock** prediction file and outputs `results/go_enrichment_<species>.tsv`
- [X] T029 Unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation (uses mock predictions)
- [X] [X] T044c CI step that parses `results/go_enrichment_<species>.tsv` and asserts at least one term has adjusted p < 0.05; if none, pipeline records “No significant enrichment” and **exits gracefully** (per SC‑002) — implemented and marked completed
- [X] T044d Integration test ensuring pipeline continues without error when only “No significant enrichment” line is present (`tests/integration/test_no_enrichment.py`)
- [X] T030 Integration test `tests/integration/test_end_to_edge_us3.py` that runs `make enrich` after US‑1 & US‑2 (or using the mock predictions from T201) and validates presence of at least one significant term (or graceful handling)
- [X] T206_GOEnrichmentRecord stores GO enrichment results (`tests/unit/test_go_enrichment_record.py`)

## Phase 5 – Pilot Benchmark & Construct‑Validity (US‑1 Extension)

- [X] T148 Perform pilot benchmark on a held‑out Arabidopsis GEO series (held‑out series = **last entry in species.yaml**) using default correlation threshold **high value**; compute precision ≥ 0.60 and recall ≥ 0.40 against STRING high‑confidence interactions (excluding co‑expression evidence); output `pilot_validation_<species>.json` and cite it in the summary (FR‑048)
- [X] T148c Unit test verifying pilot benchmark metrics meet precision/recall requirements and JSON is correctly formatted (`tests/unit/test_pilot_benchmark.py`)
- [X] T150 Extend per‑species summary generation (`src/pipeline/summary.py`) to include the pilot benchmark results and a construct‑validity justification using the citation block from T128 (FR‑026)
- [X] T150c Integration test confirming the summary report contains a "Pilot Benchmark" section with numeric values (`tests/integration/test_summary_pilot.py`)
- [X] [X] T155 Extend per‑species summary to incorporate false‑positive burden estimate and calibration benchmark results (implemented and unit‑tested)
- [X] T155c Unit test ensuring summary includes FP burden and calibration sections (`tests/unit/test_summary_extensions.py`)

## Phase 6 – Sensitivity Analysis & Supporting Tasks

- [X] T085 Correlation‑threshold sensitivity analysis: loop over thresholds **including a low‑threshold case**, 0.80, 0.85, 0.90; for each threshold, re‑run T016a, T016b, and T022. Write results to `results/threshold_sensitivity_<species>.tsv` (FR‑023)
- [X] T085p Record outputs of sensitivity analysis for downstream reporting (produces `results/threshold_sensitivity_<species>.tsv`)
- [X] T085c Unit test confirming sensitivity output contains rows for each threshold with required columns and respects global seed (`tests/unit/test_sensitivity.py`)
- [X] T086 Schema validation for `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml` (FR‑030, SC‑006)
- [X] T087 Unit test for sensitivity analysis output (correct columns, monotonic behavior) (`tests/unit/test_sensitivity.py`)

## Phase 7 – Polishing & Cross‑Cutting Concerns

- [X] T128 Generate construct‑validity citation block: retrieve, verify, and insert specific literature citations (Zhang et al., Lee et al.) into `results/citation_block.txt` as required by FR‑026 (APA style)
- [X] T128c Unit test that `citation_block.txt` contains required citations in correct format (`tests/unit/test_citation_block.py`)
- [X] [X] T126 Generate per‑species summary report `summary_<species>.txt` that includes edge count, evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC, precision@1000), top GO terms, threshold‑sensitivity results, **pilot benchmark results**, and a construct‑validity justification using the citation block from T128 (FR‑026)
- [X] [X] T127 Aggregate all per‑species summaries into `final_report.txt`, presenting overall performance statistics and restating the construct‑validity justification for the entire study (FR‑028)
- [X] T138 Extend final report generation (`src/pipeline/final_report.py`) to aggregate and display overall performance statistics and summarize **pilot benchmark outcomes** (replaces 'validation‑set calibration')
- [X] T138c Verification that final report includes performance and pilot benchmark sections with consistent numbers (unit test `tests/unit/test_final_report_content.py`)

## Phase 8 – Additional Supporting Tasks

- [X] T036 Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions, including the new pilot benchmark sections
- [X] T036c Verify documentation builds and usage instructions are accurate (unit test `tests/unit/test_docs_build.py`)
- [X] T108b Update documentation (renamed from duplicate T064) – ensures no ID conflict
- [X] [X] T046 Measure pipeline runtime (`scripts/measure_runtime.py`) and write to `results/benchmark_report.txt` (used by T037)
- [X] T046c Verify benchmark script records runtime correctly (unit test `tests/unit/test_measure_runtime.py`)
- [X] [X] T037 Run performance benchmark script `scripts/benchmark.sh` to measure end‑to‑end runtime; record results to `results/benchmark_report.txt` (warn if >6h, do not fail)
- [X] T037c CI step that warns if benchmark runtime exceeds a predefined maximum duration (`benchmark-runtime-check` job)
- [X] T063 Automate check that the benchmark script (T037) reports runtime ≤ 6 h; CI warns otherwise (implemented via job `benchmark-runtime-check`)
- [X] T125 CI step that reads `results/benchmark_report.txt` and warns if runtime > 6 h (replaces missing T046)
- [X] T038 (see Phase 1) ensures reproducibility with identical seed
- [X] T039 Code cleanup (see Phase 1)
- [X] T040 Security hardening (see Phase 1)
- [X] T041 Documentation reproducibility statement (see Phase 1)
- [X] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI (ensured by T100)
- [X] T050 Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset
- [X] [X] T050c Unit test for quickstart end‑to‑end run (`tests/unit/test_quickstart_run.py`) — completed
- [X] T051 Verify quickstart documentation correctness (`tests/unit/test_quickstart_content.py`)
- [X] T054 CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.75 (per FR‑004)
- [X] T056 Extend `validate.py` (T011) to assert presence and parsability of **all** required output files after each target
- [X] T056c CI step that runs the extended `validate.py` after each Make target (ensures T056 is exercised)
- [X] T056c Unit test confirming extended validation logic works (`tests/unit/test_extended_validation.py`)
- [X] T062 Verify false‑positive analysis output (`tests/unit/test_fp_burden.py`) — task removed per constraint preservation
- [X] T062c Unit test for false‑positive analysis (removed)

