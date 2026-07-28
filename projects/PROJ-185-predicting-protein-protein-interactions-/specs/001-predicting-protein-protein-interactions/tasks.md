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
- [X] T001c Verify repository skeleton directories exist after T001 execution (CI test) — Add `tests/integration/test_skeleton_ci.py::test_directories_exist`
- [X] T001d CI step that fails if any skeleton directory is missing — Implemented as `tests/integration/test_skeleton_ci.py` and CI job `skeleton-ci`
- [X] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)
- [X] T002c Verify `pyproject.toml` and `requirements.txt` are created and dependencies are pinned (unit test)
- [ ] T003 Initialize R environment with `renv.lock` and install Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `sva`, `GEOquery`)
- [ ] T003c Verify `renv.lock` is generated and records package versions (unit test)
- [ ] T003d Unit test that runs `Rscript -e "renv::status()"` and fails on non‑zero exit — Implemented as `tests/integration/test_renv_status.py`
- [ ] T004 Add linting/formatting configuration (`ruff`, `black`, `styler`)
- [ ] T004c Verify linting config files (`.ruff.toml`, `pyproject.toml` sections) exist and runnable (unit test) — Implemented as `tests/unit/test_lint_config.py`
- [ ] T005 Add CI workflow file `.github/workflows/ci.yml` that runs `make validate` on fresh runner
- [X] T005c Verify CI workflow file exists and contains a `validate` job (unit test) — Implemented as `tests/unit/test_ci_workflow.py`
- [ ] T005d CI step that validates the workflow file structure — Implemented via `scripts/validate_ci_workflow.py` and test `tests/unit/test_ci_workflow_structure.py`
- [ ] T005e CI job `ci-workflow-validation` runs the above script on each push

## Phase 1 – Foundational (Blocking Prerequisites)

- [ ] T006 Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log`
- [ ] T006c Unit test ensuring logger writes JSON‑Line entries with required fields (`timestamp`, `level`, `message`, `schema_version`) and conforms to `contracts/pipeline_log.schema.yaml` — Implemented as `tests/unit/test_logger_fields.py`
- [ ] T098 Extend logger to record the exact command‑line invocation, software versions, and random seed in `pipeline.log` (FR‑035)
- [ ] T098_schema Update `contracts/pipeline_log.schema.yaml` to include `command`, `versions`, and `seed` fields (prerequisite for T098)
- [X] T098c Unit test confirming logger entries contain `command`, `versions`, and `seed` fields per schema — Implemented as `tests/unit/test_logger_extension.py`
- [X] T098d Verify logger extension unit test exists (`tests/unit/test_logger_extension.py`)
- [X] T007 Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.)
- [X] T008 Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check` (calls appropriate Python/R scripts)
- [ ] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (default threshold set to a high confidence level, using a standard random seed)
- [ ] T009c Verify `species.yaml` and `parameters.yaml` are present (unit test) — Implemented as `tests/unit/test_config_files.py`
- [ ] T009d CI step that aborts the run if total wall‑clock time exceeds a predefined maximum duration (hard failure) — Implemented via `scripts/record_runtime.py` and CI job `runtime-check`
- [ ] T009e CI job `runtime-check` enforces a predefined multi‑hour wall‑clock limit.
- [ ] T010 Implement schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`, `threshold_sensitivity.schema.yaml`, `pipeline_log.schema.yaml`)
- [ ] T010c Verify all schema files are syntactically valid YAML/JSON (unit test) — Implemented as `tests/unit/test_schema_syntax.py`
- [ ] T010d Create `contracts/predicted_ppi.schema.yaml` (YAML schema for predicted edge list)
- [ ] T010e Create `contracts/evaluation.schema.yaml` (YAML schema for evaluation metrics)
- [ ] T010f Create `contracts/threshold_sensitivity.schema.yaml` (YAML schema for sensitivity output)
- [ ] T010g Create `contracts/pipeline_log.schema.yaml` (JSON‑Line schema for logging)
- [ ] T010h Validate `results/predicted_ppi_*.tsv` against `contracts/predicted_ppi.schema.yaml` after generation (unit test) — Implemented as `tests/unit/test_predicted_edge_schema.py`
- [ ] T010h_c CI step that runs the above validation after each edge‑list creation (ensures FR‑013)
- [ ] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)
- [ ] T011c Run verification script after every Make target (FR‑017) — Implemented via Makefile `post-validate` target and CI job `post-validate-ci`
- [ ] T011c_c Unit test confirming the post‑validate hook is executed for each target (`tests/unit/test_post_validate_hook.py`)
- [ ] T012 Implement CLI argument validator in `src/cli/validator.py` that enforces `--threshold` ≥ 0.75 (per FR‑004)
- [ ] T012c Unit test for CLI validator rejecting thresholds < 0.75 (`tests/unit/test_cli_threshold.py`)
- [ ] T012d Global seed propagation: ensure `--seed` is passed to all stochastic modules (correlation, baseline, negative sampling, sensitivity)
- [ ] T012e Unit test for seed propagation (`tests/unit/test_seed_propagation.py`)
- [X] T013 Implement citation verification step as pre‑commit hook `scripts/run_reference_validator.sh` and CI job that runs the Reference‑Validator Agent, failing on mismatches
- [ ] T013c CI job `reference-validator-ci` invoking the above script and failing on non‑zero exit
- [ ] T013d Unit test enforcing title‑token overlap ≥ 0.7 (`tests/unit/test_citation_overlap.py`)

- [ ] T099 CI test for CLI validator — Implemented as CI job `threshold-validator-ci` running `pytest tests/unit/test_cli_threshold.py`
- [ ] T099c CI step executing T012c unit test — Implemented in job `cli-threshold-ci`

- [ ] T100 CI step for citation validation — Implemented as CI job `citation-validator-ci` running the pre‑commit hook
- [ ] T100c CI job `citation-validator-ci` invoking `scripts/run_reference_validator.sh`

- [ ] T038 Reproducibility check: re‑run pipeline with same `--seed` and diff all result files; fail on any mismatch (covers SC‑004)
- [ ] T038c CI step that runs the reproducibility check and fails on output differences

- [ ] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`)
- [ ] T039c Unit test confirming dead imports removed and type‑hints complete (unit test)
- [ ] T122 CI step that runs `ruff`/`mypy` and writes `lint_report.txt` (verifies T039)

- [ ] T040 Security hardening: verify that all external URLs are fetched over HTTPS and that each download includes a SHA‑256 checksum verification
- [ ] T040c Unit test ensuring all URLs are HTTPS and checksummed (`tests/unit/test_url_security.py`)
- [ ] T111 CI test that runs `scripts/audit_urls.py` to ensure all URLs are HTTPS and checksummed

- [ ] T041 Documentation: Add a ‘Reproducibility Statement’ to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map
- [ ] T041c Verify reproducibility statement presence and correct referencing (`tests/unit/test_repro_statement.py`)

## Phase 2 – User Story 1 – Data Acquisition & Pre‑processing (US‑1)

- [ ] T064 Implement GEO downloader `src/pipeline/download.py` (fetches count matrices, records SHA‑256 in `state/artifact_hashes.yaml`)
- [ ] T064c Unit test confirming correct download, checksum recording, and error handling (`tests/unit/test_geo_downloader.py`)
- [ ] T064d Abort pipeline if total retained samples after series‑level filtering < 50 (FR‑047) — Implemented in `src/pipeline/download.py` and tested via `tests/integration/test_sample_abort.py`
- [ ] T065 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2` or subprocess)
- [ ] T065a Implement confound regression `src/pipeline/confound_regression.py` to regress out expression‑level and gene‑length confounds as required by FR‑014; output corrected expression matrix
- [ ] T065c After batch correction, compute residual batch variance; log warning if > 5% (FR‑014) — Unit test `tests/unit/test_batch_variance_warning.py`
- [ ] T014 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`
- [ ] T014c Unit test confirming correct handling of both TPM and VST modes (`tests/unit/test_normalization_modes.py`)
- [ ] T015 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80 % samples) and retain **at most 5,000 genes** with highest variance (hard limit per FR‑003, SC‑003)
- [ ] T015c Unit test for CPM filter and variance‑based sub‑selection (`tests/unit/test_gene_filtering.py`)
- [ ] T015e Verify default N=5,000 is enforced if config missing (`tests/unit/test_default_gene_limit.py`)
- [ ] T016a Implement Pearson correlation matrix generation `src/pipeline/correlation_raw.py` to compute and stream full raw correlation scores for all gene‑pair candidates (block size=1000 genes) to `results/raw_correlations_<species>.tsv.gz` before any thresholding
- [ ] T016a_c Unit test confirming raw correlation file is correctly streamed and parsable (`tests/unit/test_raw_correlation_output.py`)
- [ ] T016a_verify Verify that `results/raw_correlations_*.tsv.gz` is written before thresholding (unit test) — Implemented as `tests/unit/test_raw_correlation_presence.py`
- [ ] T017 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; write `results/mapping_warnings_<species>.log` for unmapped genes (FR‑005)
- [ ] T017c Unit test for identifier mapping correctness and logging of unmapped genes (`tests/unit/test_mapping.py`)
- [ ] T016b Implement edge extraction `src/pipeline/correlation_extract.py` to extract edges from T016a using the `--threshold` parameter **ONLY** (no p‑value filtering; **IGNORES FDR output** per FR‑045); output to `results/predicted_ppi_<species>.tsv` (requires T017 for protein IDs)
- [ ] T016b_c Verify edge extraction respects correlation threshold exclusively (`tests/unit/test_edge_extraction_threshold.py`)
- [ ] T083 Implement Benjamini‑Hochberg FDR correction `src/pipeline/fdr_correction.py` on correlation p‑values from T016a; output adjusted p‑values to `results/correlation_stats_<species>.tsv` (FR‑045) — **Reporting ONLY; never consumed by edge selection logic**
- [ ] T084 Verify `correlation_stats_<species>.tsv` exists, is complete, and parsable (unit test) (`tests/unit/test_fdr_output.py`)
- [ ] T018 Write edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`) — depends on T017 (FR‑011)
- [ ] T018c Unit test for edge‑list exporter (format, warnings) (`tests/unit/test_edge_export.py`)
- [ ] T020a Integration test `tests/integration/test_end_to_end_us1.py` that runs `make all` on a tiny mock dataset and checks edge‑list header and **header‑only OR ≥ 10 000 edges** via T042

- **Data‑model entity tasks**
- [ ] T200_RNASeqSample Load GEO series into `RNASeqSample` entities (used by T064) (`tests/unit/test_rnaseq_sample.py`)
- [ ] T201_Gene Process `Gene` entities after filtering (`tests/unit/test_gene_entity.py`)
- [ ] T202_RawCorrelation Compute and store `RawCorrelation` objects (covers T016a) (`tests/unit/test_raw_correlation_entity.py`)
- [ ] T203_ProteinCorrelation Generate `ProteinCorrelation` after mapping (`tests/unit/test_protein_correlation.py`)
- [ ] T204_PredictedEdge Export `PredictedEdge` list (`tests/unit/test_predicted_edge_export.py`)
- [ ] T205_EvaluationMetric Compute evaluation metrics (AUROC/AUPRC) (`tests/unit/test_evaluation_metric.py`)
- [ ] T205c Implement EvaluationMetric data‑model entity creation and schema validation after evaluation (covers data‑model coverage)

## Phase 3 – User Story 2 – Quantitative Evaluation Against STRING (US‑2)

- [ ] T200 Mock edge‑list generator `scripts/generate_mock_edge_list.py` producing `results/predicted_ppi_mock.tsv` for independent US‑2 testing
- [ ] T200c Unit test confirming mock edge list format and size suitability (`tests/unit/test_mock_edge_list.py`)
- [ ] T021 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – downloads high‑confidence set (combined score ≥ 700) and explicitly filters out the co‑expression evidence channel
- [ ] T021c Unit test to verify that the downloaded STRING file excludes the co‑expression evidence channel (`tests/unit/test_string_download.py`)
- [ ] T091 Implement balanced negative‑sampling module `src/pipeline/negative_sampling.py` that {{claim:c_6ffc1bf5}} ({{claim:c_41a5b477}}, https://oeis.org/A331313) (size = positive set) from the complement of STRING (excluding co‑expression channel), using the global random seed (FR‑016)
- [ ] T091c Unit test asserting each negative set is true complement of STRING high‑confidence set and respects seed reproducibility (covers FR‑016)
- [ ] T091d Verify negative‑sampling uses global seed and size equals positive set (`tests/unit/test_negative_sampling.py`)
- [ ] T023 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC using the same mock edge list input (FR‑007)
- [ ] T023c Validate baseline graph preserves node degree distribution and compute permutation‑test p‑value (`tests/unit/test_baseline.py`)
- [ ] T022a Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges **from the real file `results/predicted_ppi_<species>.tsv`**, (b) loads STRING high‑confidence interactions (filtered), (c) **processes ALL gene-pair correlation scores (full set)** via streaming/block-wise loading to compute AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json` (covers FR‑006, FR‑020). **Prerequisites**: T023 (baseline graph), T091 (negative set).
- [ ] T022c Verify evaluation script loads data correctly and produces valid JSON (unit test) (`tests/unit/test_full_evaluation.py`)
- [ ] T022a_c Validate metric values against a known benchmark on mock data (`tests/unit/test_full_evaluation_mock.py`)
- [ ] T092 Implement median aggregation `src/pipeline/aggregate_metrics.py` to compute median AUROC/AUPRC across the 1 negative set generated by T091
- [ ] T102 Unit test for balanced negative‑sampling (size, seed reproducibility) (`tests/unit/test_negative_sampling.py`)
- [ ] T024 Extend `src/cli/run_pipeline.py` to expose `evaluate` sub‑command and pass seed/threshold flags
- [ ] T024c Verify new CLI sub‑command parses and routes correctly (unit test `tests/unit/test_cli_evaluate.py`)
- [ ] T025 Add unit tests `tests/unit/test_evaluate.py` and `tests/unit/test_baseline.py` (mock small graph, check metric calculation)
- [ ] T045c CI step that parses `results/evaluation_metrics.json` and asserts AUROC ≥ 0.70 **and** AUPRC ≥ 0.70 (per SC‑001)
- [ ] T045d Verification that both AUROC and AUPRC thresholds are met (unit test `tests/unit/test_evaluation_thresholds.py`)
- [ ] T143 Validate `evaluation_metrics.json` against `contracts/evaluation.schema.yaml` (unit test `tests/unit/test_evaluation_schema.py`)

- **Data‑model entity tasks**
- [ ] T205_EvaluationMetric (see above) creates `EvaluationMetric` records

## Phase 4 – User Story 3 – Functional Enrichment of Predicted Interactome (US‑3)

- [ ] T028 Add CLI flag `--go-ontology` (default points to cached 2023‑12‑01 file) and integrate into `run_pipeline.py` as `enrich` sub‑command
- [ ] T027 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology dated ‑‑01) with Fisher’s exact test and Benjamini‑Hochberg correction; reads the **mock** prediction file and outputs `results/go_enrichment_<species>.tsv`
- [ ] T029 Unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation (uses mock predictions)
- [ ] T044c Unit test for the 'no enrichment' case: verify that the enrichment logic correctly identifies no significant terms and prepares the 'No significant enrichment' record (`tests/unit/test_enrichment_no_terms.py`)
- [ ] T044d Integration test ensuring pipeline continues without error when only “No significant enrichment” line is present (`tests/integration/test_no_enrichment.py`)
- [ ] T044 CI step that parses `results/go_enrichment_<species>.tsv` and asserts at least one term has adjusted p < 0.05; if none, pipeline records “No significant enrichment” and **exits gracefully** (per SC‑002)
- [ ] T030 Integration test `tests/integration/test_end_to_edge_us3.py` that runs `make enrich` after US‑1 & US‑2 (or using the mock predictions from T201) and validates presence of at least one significant term (or graceful handling)

- **Data‑model entity tasks**
- [ ] T206_GOEnrichmentRecord stores GO enrichment results (`tests/unit/test_go_enrichment_record.py`)

## Phase 5 – Pilot Benchmark & Construct‑Validity (US‑1 Extension)

- [ ] T148 Perform pilot benchmark on a held‑out Arabidopsis GEO series (held‑out series = **last entry in species.yaml**) using default correlation threshold **high value**; compute precision ≥ 0.60 and recall ≥ 0.40 against STRING high‑confidence interactions (excluding co‑expression evidence); output `pilot_validation_<species>.json` and cite it in the summary (FR‑048)
- [ ] T148c Unit test verifying pilot benchmark metrics meet precision/recall requirements and JSON is correctly formatted (`tests/unit/test_pilot_benchmark.py`)
- [ ] T150 Extend per‑species summary generation (`src/pipeline/summary.py`) to include the pilot benchmark results and a construct‑validity justification using the citation block from T128 (FR‑026)
- [ ] T150c Integration test confirming the summary report contains a "Pilot Benchmark" section with numeric values (`tests/integration/test_summary_pilot.py`)

## Phase 6 – Sensitivity Analysis & Supporting Tasks

- [ ] T085 Correlation‑threshold sensitivity analysis: loop over thresholds **including a low‑threshold case**, 0.80, 0.85, 0.90; for each threshold, re‑run T016a, T016b, and T022. Write results to `results/threshold_sensitivity_<species>.tsv` (FR‑023)
- [ ] T085p Record outputs of sensitivity analysis for downstream reporting (produces `results/threshold_sensitivity_<species>.tsv`)
- [ ] T085c Unit test confirming sensitivity output contains rows for each threshold with required columns and respects global seed (`tests/unit/test_sensitivity.py`)
- [ ] T086 Schema validation for `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml` (FR‑030, SC‑006)
- [ ] T087 Unit test for sensitivity analysis output (correct columns, monotonic behavior) (`tests/unit/test_sensitivity.py`)

## Phase 7 – Polishing & Cross‑Cutting Concerns

- [ ] T128 Generate construct‑validity citation block: retrieve, verify, and insert specific literature citations (Zhang et al., Lee et al.) into `results/citation_block.txt` as required by FR‑026 (APA style)
- [ ] T128c Unit test that `citation_block.txt` contains required citations in correct format (`tests/unit/test_citation_block.py`)
- [ ] T126 Generate per‑species summary report `summary_<species>.txt` that includes edge count, evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC, precision@1000), top GO terms, threshold‑sensitivity results, **pilot benchmark results**, and a construct‑validity justification using the citation block from T128 (FR‑026)
- [ ] T126c Unit test ensuring per‑species summary contains all required fields (`tests/unit/test_summary.py`)
- [ ] T126d Unit test verifying top enriched GO terms are correctly extracted and ordered (`tests/unit/test_summary.py`)
- [ ] T127 Aggregate all per‑species summaries into `final_report.txt`, presenting overall performance statistics and restating the construct‑validity justification for the entire study (FR‑028)
- [ ] T127c Integration test that `final_report.txt` correctly aggregates per‑species sections (`tests/integration/test_final_report.py`)
- [ ] T138 Extend final report generation (`src/pipeline/final_report.py`) to aggregate and display overall performance statistics and summarize **pilot benchmark outcomes** (replaces 'validation-set calibration')
- [ ] T138c Verification that final report includes performance and pilot benchmark sections with consistent numbers (unit test `tests/unit/test_final_report_content.py`)

## Phase 8 – Additional Supporting Tasks

- [ ] T036 Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions, including the new pilot benchmark sections
- [ ] T036c Verify documentation builds and usage instructions are accurate (unit test `tests/unit/test_docs_build.py`)
- [ ] T108b Update documentation (renamed from duplicate T064) – ensures no ID conflict
- [ ] T046 Measure pipeline runtime (`scripts/measure_runtime.py`) and write to `results/benchmark_report.txt` (used by T037)
- [ ] T046c Verify benchmark script records runtime correctly (unit test `tests/unit/test_measure_runtime.py`)
- [ ] T037 Run performance benchmark script `scripts/benchmark.sh` to measure end‑to‑end runtime; record results to `results/benchmark_report.txt` (warn if >6h, do not fail)
- [ ] T037c CI step that warns if benchmark runtime exceeds a predefined maximum duration (`benchmark-runtime-check` job)
- [ ] T063 Automate check that the benchmark script (T037) reports runtime ≤ 6 h; CI warns otherwise (implemented via job `benchmark-runtime-check`)
- [ ] T125 CI step that reads `results/benchmark_report.txt` and warns if runtime > 6 h (replaces missing T046)
- [ ] T038 (see Phase 1) ensures reproducibility with identical seed
- [ ] T039 Code cleanup (see Phase 1)
- [ ] T040 Security hardening (see Phase 1)
- [ ] T041 Documentation reproducibility statement (see Phase 1)
- [ ] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI (ensured by T100)
- [ ] T050 Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset
- [ ] T150_quickstart_run Execute `make all` as described in quickstart Step 5 (CI test `tests/integration/test_quickstart_run.py`)
- [ ] T151_quickstart_verify Run `make verify` as described in quickstart Step 6 (CI test `tests/integration/test_quickstart_verify.py`)
- [ ] T054 CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.75 (per FR‑004)
- [ ] T056 Extend `validate.py` (T011) to assert presence and parsability of **all** required output files after each target
- [ ] T056c CI step that runs the extended `validate.py` after each Make target (ensures T056 is exercised)
- [ ] T062 Verify false‑positive analysis output (`tests/unit/test_fp_burden.py`)