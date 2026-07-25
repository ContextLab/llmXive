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

- [X] T001 Create repository skeleton (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`) with README and initial .gitignore.
- [X] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)
- [X] T003 Initialize R environment with `renv.lock` and install Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `sva`, `GEOquery`)
- [X] T004 Add linting/formatting configuration (`ruff`, `black`, `styler`) and corresponding config files.
- [X] T005 Add CI workflow file `.github/workflows/ci.yml` that runs `make validate` on a fresh runner and includes steps for runtime, reproducibility, and citation checks.
- [X] T006 Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log` (no [P] flag – writes to a shared file). (covers FR‑009)
- [X] T007 [P] Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.) (covers FR‑012)
- [X] T008 [P] Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check`. **Must enforce that the verification script (T011) is invoked as a prerequisite for EVERY target** to satisfy FR-017.
- [X] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (A default threshold is established., seed 42)
- [X] T010 Create schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`, `threshold_sensitivity.schema.yaml`, `pipeline_log.schema.yaml`) (covers FR‑013, FR‑019, FR‑030, FR‑034)
- [X] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)
- [X] T012 Implement CLI argument validator (part of `run_pipeline.py`) that enforces `--threshold` ≥ 0.75 **AND sets the default value to 0.80** (per FR‑004).
- [X] T012b Implement `--seed` CLI flag handling and propagation to all stochastic components (per FR‑012)
- [X] T012c Add unit test verifying that the The default threshold is set to a high value to ensure strict filtering criteria. in `parameters.yaml` and CLI help text (per FR-004).
- [X] T012d Add unit test verifying that the CLI validator correctly defaults to 0.80 when no `--threshold` is provided.
- [X] T012e Add unit test verifying that the configuration file `parameters.yaml` explicitly sets the default threshold to 0.80.
- [X] T013 Implement citation verification step that invokes the Reference‑Validator Agent on all markdown and code files during CI
- [X] T098 Extend logger to record the exact command‑line invocation, software versions, and random seed in `pipeline.log` (FR‑035)
- [X] T098a Extend logger to also capture software version (`pip freeze` snapshot) and the random seed used for the run (ensuring FR‑035 completeness).
- [X] T098b Add unit‑test verifying that `pipeline.log` entries contain the new fields (`command_line`, `software_versions`, `seed`). (addresses executability‑a53c135b)
- [X] T098c Add integration test that runs the full pipeline (`make all`) and asserts the presence of those fields in `pipeline.log`. (addresses executability‑5fbab9b1)
- [X] T010a Add unit‑test verifying that `pipeline.log` entries conform to `pipeline_log.schema.yaml`.
- [X] T010b Add unit‑test that all schema files created by T010 load without syntax errors (schema‑validation test).
- [X] T014a Add unit‑test confirming that both TPM and VST normalization produce correctly shaped output matrices and respect the `--norm-method` flag. *(now pending)*
- [ ] T014 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`. Must produce correctly shaped matrices for both methods and respect the method flag. (addresses FR‑002)
- [ ] T014b Add integration test that runs the full pipeline (`make all`) and verifies that the normalized matrices have expected dimensions and that the `--norm-method` flag is honoured throughout the workflow. (addresses executability‑35c0579c)
- [ ] T015 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80% samples) and **retain at most 5,000 genes** with highest variance (configurable, but capped at [deferred]). Must log filtering statistics and the final gene count. (addresses FR‑003)
- [X] T065 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2`). Runs on normalized data.
- [X] T065a Implement confound regression `src/pipeline/confound_regression.py` to regress out expression‑level and gene‑length confounds; outputs corrected expression matrix.
- [X] T065b Implement SVA fallback when metadata are incomplete (detects missing batch info and runs `sva::svaseq`).
- [X] T065c Add SVA fallback implementation details and unit‑test verifying fallback activation when batch metadata are missing.
- [X] T065_test Add unit‑test verifying batch‑effect correction correctly handles multiple GEO series and produces expected corrected data.
- [X] T065a_test Add unit‑test confirming confound regression removes specified covariates and logs the operation.
- [X] T065b_test Add unit‑test verifying SVA fallback activation and output shape.
- [X] T065c_test Add unit‑test verifying SVA fallback produces biologically plausible corrected data.
- [X] T065d_test Add unit‑test verifying batch‑effect correction when only a single GEO series is present (no‑op case). *(renamed to resolve duplicate ID)*
- [X] T065_test_test Add unit‑test verifying batch‑effect correction correctly handles multiple GEO series and produces expected corrected data. *(original retained, ID adjusted)*
- [ ] T016a [P] Implement Pearson correlation matrix generation `src/pipeline/correlation_raw.py` to compute and stream full raw correlation scores for all gene‑pair candidates to `results/raw_correlations_<species>.tsv.gz` before any thresholding. Must support optional Spearman mode. (addresses FR‑004)
- [X] T016a-test Add unit‑test verifying Pearson vs. Spearman computation and correct handling of NaNs. *(now pending)*
- [X] T016a_perf Add performance test confirming block‑wise streaming stays within memory limits and completes within the ‑hour budget on a realistic mock dataset. (addresses executability‑667b973b)
- [X] T083 Implement Benjamini‑Hochberg FDR correction `src/pipeline/fdr_correction.py` on correlation p‑values from T016a; output adjusted p‑values (FR‑045).
- [ ] T016b Implement edge extraction `src/pipeline/correlation_extract.py` to extract edges from T016a. **Must apply Benjamini-Hochberg FDR correction (adjusted p-value ≤ 0.05) as a mandatory filter** AND the `--threshold` parameter (must be ≥ 0.75). Output to `results/predicted_ppi_<species>.tsv`. (addresses FR‑004, FR‑045)
- [ ] T016b-test Add unit‑test confirming that edge extraction respects the threshold and that the output schema is satisfied. *(now pending)*
- [ ] T016b_int Add integration test that runs the full pipeline and checks that edge extraction respects the `--threshold` flag, applies FDR filtering, and produces a schema‑valid `predicted_ppi_<species>.tsv`. (addresses executability‑56ad172c)
- [X] T095 Unit tests for correlation module (`Pearson/Spearman`, threshold enforcement) (`tests/unit/test_correlation_raw.py::test_pearson_vs_spearman`).
- [X] T096 Unit tests for identifier mapping (unmapped logging, schema compliance) (`tests/unit/test_mapping.py::test_unmapped_logging`).
- [ ] T017 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; writes `results/mapping_warnings_<species>.log` for unmapped genes. Must produce a complete mapping for all genes used in the edge list. (addresses FR‑005)
- [ ] T017a Add unit‑test confirming that all genes are successfully mapped or properly logged as unmapped. *(now pending)*
- [ ] T017b Add integration test that runs mapping followed by edge‑list generation, verifies that all edges contain mapped STRING IDs and that unmapped‑gene warnings stay within tolerance. (addresses executability‑0fa5e638)
- [ ] T018 Implement edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`). **(No orthogonal filtering)**. *(now pending)*
- [X] T097 Unit tests for edge‑list exporter (format, warnings) (`tests/unit/test_exporter.py::test_tsv_format`).
- [ ] T018b Add integration test that runs `make all` and confirms the final `predicted_ppi_<species>.tsv` exists, has correct header, and meets the edge‑count requirement (≥ 10 000 or header‑only). (addresses executability‑47123b45)
- [X] T020 Integration test `tests/integration/test_end_to_end_us1.py::test_edge_list` runs `make all` on a tiny mock dataset and checks edge‑list header and edge count (≥ 10 000 or header‑only). *(now pending)*
- [X] T095 US1 Unit tests for correlation module (Pearson/Spearman, threshold enforcement) (`tests/unit/test_correlation_raw.py::test_pearson_vs_spearman`).

## Phase 2 – User Story 2 – Quantitative Evaluation Against STRING (US‑2)

- [X] T021 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – downloads high‑confidence set (combined ≥ 700) and explicitly filters out the co‑expression evidence channel.
- [X] T021b Unit test to verify that the downloaded STRING file excludes the co‑expression evidence channel (`tests/unit/test_download_string.py::test_no_coexpression_channel`).
- [X] T022 Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges, (b) loads STRING high‑confidence interactions (filtered), (c) computes AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json`.
- [X] T022b Add validation task to ensure `evaluation_metrics.json` contains the required `baseline_p` field per FR‑018. (addresses constraint_preservation‑1531f6d3)
- [X] T023 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC.
- [X] T018a Add validation task to ensure `evaluation_metrics.json` contains the required `baseline_p` field (FR‑018).
- [X] T091 Implement balanced negative‑sampling module `src/pipeline/negative_sampling.py` that draws N=10 independent balanced negative sets (size = positive set) from the complement of STRING (excluding co‑expression channel), using the global random seed (FR‑032).
- [X] T092 Implement median aggregation `src/pipeline/aggregate_metrics.py` to compute median AUROC/AUPRC across the 10 negative sets generated by T091.
- [X] T102 Unit test for balanced negative‑sampling (size, seed reproducibility) (`tests/unit/test_negative_sampling.py::test_seed_reproducibility`).
- [X] T024 Extend `src/cli/run_pipeline.py` to expose `evaluate` sub‑command and pass seed/threshold flags.
- [X] T025 Add unit tests `tests/unit/test_evaluate.py` and `tests/unit/test_baseline.py` (mock small graph, check metric calculation).
- [X] T045 Modify CI step `scripts/ci_check_evaluation_metrics.sh` to assert AUROC ≥ 0.70 **and** AUPRC ≥ 0.70 for each species, removing the previous 0.65 threshold and deleting the reference to non‑existent FR‑046. (addresses constraint_preservation‑c69b7406 and‑906290cb)
- [X] T026 Integration test `tests/integration/test_end_to_end_us2.py` runs `make evaluate` on the mock data from US1 and asserts metric thresholds are met.
- [X] T114 US2 Integration test that runs `make evaluate` on a representative subset of real data and checks that the same metric thresholds hold (addresses FR‑045). *(reference to FR‑046 removed)*
- [X] T115 CI step that runs schema‑validation tests for the updated `evaluation.schema.yaml` (including `precision_at_1000` field).

## Phase 3 – User Story 3 – Functional Enrichment of Predicted Interactome (US‑3)

- [X] T027 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology date from the most recent release) with Fisher's exact test and Benjamini‑Hochberg correction; output `results/go_enrichment_<species>.tsv`.
- [P] T028 Add CLI flag `--go-ontology` (default points to cached `-12-01` file) and integrate into `run_pipeline.py` as `enrich` sub‑command.
- [P] T029 Write unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation.
- [P] T044 Verify GO‑enrichment FDR: CI step that parses `go_enrichment_<species>.tsv` and asserts at least one term has adjusted p < 0.05; if none, the pipeline records “No significant enrichment” (file must be correctly formatted).
- [P] T030 Integration test `tests/integration/test_end_to_end_us3.py` runs `make enrich` after US1 & US2 and validates presence of at least one significant term (or graceful “No significant enrichment” handling).

## Phase 4 – Sensitivity Analysis & Supporting Tasks

- [X] T085 Perform correlation‑threshold sensitivity analysis: **loop over a range of high confidence thresholds**; for each threshold, re‑run T016a, T083, T016b, and T022; write results to `results/threshold_sensitivity_<species>.tsv` (FR‑023). **No external calibration or BioGRID usage. The task records metrics for each fixed threshold; it does not perform an optimization step to select a single threshold.**
- [P] T086 Schema validation for `threshold_sensitivity_<species>.tsv` against `contracts/threshold_sensitivity.schema.yaml` (FR‑030).
- [P] T087 Unit test for sensitivity analysis output (correct columns and monotonic behavior). *(description clarified to emphasize monotonicity verification)*
- [X] T085_monotonic_test (renamed from T087) ensures monotonic metric trends across thresholds.

## Phase 5 – Reporting & Summary (Construct Validity & Final Report)

- [X] T128 Generate construct‑validity citation block: retrieve, verify, and insert specific literature citations (Zhang et al., Nat Commun. [Year]; Lee et al., Plant Cell) into `results/citation_block.txt` as required by FR‑026.
- [X] T126 Generate per‑species summary report `summary_<species>.txt` that includes edge count, evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC, precision@1000), top GO terms, threshold‑sensitivity results, and a construct‑validity justification using the citation block (FR‑026). **(No 'Dyson' branding or Poisson calculator)**.
- [X] T127 Aggregate all per‑species summaries into `final_report.txt`, presenting overall performance statistics and restating the construct‑validity justification for the entire study (FR‑028).
- [X] T133 Update the per‑species summary report to include false‑positive burden (derived from internal sensitivity analysis and literature) and sensitivity analysis results sections. *(new task - now strictly internal sensitivity results)*
- [X] T133_test Add test to verify the summary report correctly includes the new sections.
- [X] T131 (Removed - replaced by internal sensitivity analysis)
- [X] T131_test (Removed)
- [X] T132 (Removed - replaced by internal sensitivity analysis)
- [X] T134 (Removed - replaced by internal sensitivity analysis)
- [X] T134_doc_test (Removed)

## Phase 6 – Polish & Cross‑Cutting Concerns

- [X] T036 [P] Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions.
- [X] T108a Documentation update (renamed from duplicate T064) – ensures no ID conflict; updates docs to reflect new pipeline steps.
- [X] T038 Run CI step to enforce reproducibility: after a successful run, re‑run the pipeline with the same `--seed` and `git diff` the resulting `evaluation_metrics.json` and all `go_enrichment_*.tsv` files; fail if any differences are detected (FR‑012).
- [X] T121 CI step that executes the reproducibility‑check (`make reproducibility-check`) and diffs outputs (ensures T038 is actually executed).
- [X] T121a Add explicit diff script (`src/utils/repro_check.py`) that runs the pipeline twice and uses `deepdiff` to compare all output artifacts, exiting with non‑zero status on any mismatch.
- [X] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`).
- [X] T122 CI step that runs `ruff`/`mypy` and writes `lint_report.txt` (verifies T039).
- [X] T040 Verify all external URLs are fetched over HTTPS and that each download includes a SHA‑256 checksum verification.
- [X] T040_test Add CI test that scans the codebase for URLs, asserts HTTPS scheme, and checks that a corresponding SHA‑256 checksum entry exists in the download script or metadata file. (addresses executability‑98ba966f)
- [X] T041 Documentation: Add a ‘Reproducibility Statement’ to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map.
- [X] T123 Unit test that checks `docs/README.md` contains the reproducibility statement.
- [X] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI (ensured by T100).
- [X] T050 [P] Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset.
- [X] T051 CI test that executes the quickstart steps (`make quickstart-test`) and asserts successful completion and correct output file generation.
- [X] T054 [P] CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.75 (per FR‑004).
- [X] T056 Extend `validate.py` (T011) to assert presence and parsability of **all** required output files (`predicted_ppi_*.tsv`, `evaluation_metrics.json`, `go_enrichment_*.tsv`, `pipeline.log`) after each target.
- [X] T124 CI step that runs the extended `validate.py` after each Make target (ensures T056 is exercised).
- [X] T062 Verify false‑positive analysis output: unit test that ensures `fp_analysis.py` produces a non‑empty report with expected numeric fields (already covered by T107).
- [X] T107 Unit test for false‑positive analysis module.
- [X] T108 Documentation lint test that verifies `docs/false_positives.md` contains required sections (construct validity justification, sensitivity results). **Removed 'Poisson derivation' and 'Dyson' references.**

## Phase 7 – Removed Tasks (Scope Creep / External Calibration)

- [ ] T129 (REMOVED - BioGRID false-positive burden)
- [ ] T130 (REMOVED - BioGRID false-positive test)
- [ ] T131 (REMOVED - BioGRID calibration)
- [ ] T131_test (REMOVED)
- [ ] T132 (REMOVED)
- [ ] T133 (REMOVED)
- [ ] T133_test (REMOVED)
- [ ] T134 (REMOVED)
- [ ] T134_doc_test (REMOVED)
- [ ] T135 (REMOVED)
- [ ] T136 (REMOVED)
- [ ] T137 (REMOVED - BioGRID calibration)
- [ ] T138 (REMOVED - BioGRID calibration test)
- [ ] T139 (REMOVED)
- [ ] T140 (REMOVED)
- [ ] T140_ci_test (REMOVED)
- [ ] T141 (REMOVED - Dyson Poisson calculator)
- [ ] T141_test (REMOVED)
- [ ] T142 (REMOVED - Dyson branding)
- [ ] T143 (REMOVED - Dyson branding)

## Phase 8 – Additional Supporting Tasks

- [X] T200 Implement logging JSON‑Line schema file `contracts/pipeline_log.schema.yaml` (FR‑034) and ensure validation scripts reference it.
- [X] T202 Implement runtime‑tracking utility `src/utils/runtime_tracker.py` that records start/end timestamps for the whole pipeline; CI step asserts total wall‑clock time ≤ 6 hours (SC‑003).
- [X] T202c Add CI step that invokes `src/utils/runtime_tracker.py` after pipeline completion to enforce the runtime budget. (addresses executability‑8ac0ffbe)
- [X] T203 Implement reproducibility‑check script `src/utils/repro_check.py` that runs the pipeline twice with the same `--seed` and diffs all output artifacts; CI step fails on any mismatch (SC‑004).
- [X] T150 Add mock‑data generation script `src/utils/mock_data.py` and CI test to allow US‑2 evaluation to run independently of US‑1 outputs.
- [X] T112 Implement mapping‑warnings audit script `src/pipeline/audit_mapping_warnings.py` that scans `results/mapping_warnings_*.log` for unmapped entries and fails if any exceed a configurable tolerance (addresses executability concern).
- [X] T112a Add unit‑test `tests/unit/test_readme_repro_statement.py` that checks `docs/README.md` contains the required reproducibility statement (ensures documentation consistency).
- [X] T112b Add CI step that runs `src/pipeline/audit_mapping_warnings.py` after the mapping stage and aborts on excess unmapped genes.