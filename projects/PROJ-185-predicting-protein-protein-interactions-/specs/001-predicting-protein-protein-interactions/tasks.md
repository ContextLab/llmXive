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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create repository skeleton (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`)  
- [ ] T002 Initialize Python project with `pyproject.toml` and pin dependencies in `requirements.txt` (numpy, pandas, networkx, goatools, scikit‑learn, tqdm, requests)  
- [ ] T003 Initialize R environment with `renv.lock` and install Bioconductor packages (`DESeq2`, `org.At.tair.db`, `biomaRt`, `sva`, `GEOquery`)  
- [ ] T004 Add linting/formatting configuration (`ruff`, `black`, `styler`)  
- [ ] T005 Add CI workflow file `.github/workflows/ci.yml` that runs `make validate` on fresh runner  

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can be implemented  

- [ ] T006 [P] Create central logger module `src/utils/logger.py` that writes ISO‑8601 timestamps to `pipeline.log`  
- [ ] T007 [P] Implement CLI entry point `src/cli/run_pipeline.py` with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`, etc.)  
- [ ] T008 [P] Write Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `sensitivity`, `reproducibility-check` (calls appropriate Python/R scripts)  
- [ ] T009 Create configuration directory `src/config/` with `species.yaml` (default Arabidopsis GEO list) and `parameters.yaml` (default threshold 0.8, seed 42)  
- [ ] T010 Implement schema files in `contracts/` (`predicted_ppi.schema.yaml`, `evaluation.schema.yaml`)  
- [ ] T011 Write validation script `src/pipeline/validate.py` that checks result files against the contracts **and** verifies existence and parsability of all required output files after each Makefile target (covers SC‑005)  
- [ ] T012 Implement CLI argument validator (part of `run_pipeline.py`) that enforces `--threshold` ≥ 0.8 (cannot be lowered)  
- [ ] T013 [P] Implement citation verification step that invokes the Reference‑Validator Agent on all markdown and code files during CI  

**Checkpoint**: Foundations ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 – Build & Export Co‑expression‑based PPI Predictions (Priority: P1)

**Goal**: Produce reproducible edge‑list files `predicted_ppi_<species>.tsv` for each species.

**Independent Test**: Run `make all` on a fresh runner and verify that for each species a non‑empty (or header‑only) `predicted_ppi_<species>.tsv` exists **and** contains ≥ 10 000 edges when data are sufficient.

### Implementation Tasks

- [ ] T064 US1 Implement GEO downloader `src/pipeline/download.py` (fetches count matrices, records SHA‑256 in `state/artifact_hashes.yaml`)  
- [ ] T065 US1 Implement batch‑effect correction wrapper `src/pipeline/batch_correct.py` using ComBat (R via `rpy2` or subprocess)  
- [ ] T014 US1 Implement normalization script `src/pipeline/normalize.py` supporting `TPM` (default) and `VST` (R) with CLI flag `--norm-method`  
- [ ] T015 US1 Implement gene‑filtering `src/pipeline/filter.py` (CPM < 1 in > 80 % samples) and write provenance JSON (`results/provenance_<species>.json`)  
- [ ] T016 US1 Implement Pearson correlation matrix and edge extraction `src/pipeline/correlation.py` (threshold `--threshold`, default 0.8, enforce ≥ 0.8)  
- [ ] T017 US1 Implement identifier mapping `src/pipeline/mapping.py` using `org.At.tair.db` with fallback to Ensembl BioMart; write `results/mapping_warnings_<species>.log` for unmapped genes  
- [ ] T018 US1 Write edge‑list exporter that creates `results/predicted_ppi_<species>.tsv` (STRING protein IDs, correlation) and logs warnings (`results/pipeline.log`)  
- [ ] [ ] T019 US1 Add unit tests in `tests/unit/test_download.py`, `test_normalize.py`, `test_correlation.py` that assert file creation and basic sanity checks (fail before implementation)  
- [ ] [ ] T020 US1 Add integration test `tests/integration/test_end_to_end_us1.py` that runs `make all` on a tiny mock dataset and checks edge‑list header, **edge‑count ≥ 10 000** (or header‑only) via task T042  
- [ ] [ ] T042 US1 Verify edge‑list size: unit/integration test that asserts `predicted_ppi_<species>.tsv` contains ≥ 10 000 edges (or is header‑only) and fails otherwise  
- [ ] [ ] T043 US1 Abort on insufficient GEO samples: modify downloader to check sample count; if `< 20` abort that series, log `Insufficient sample count (<20)` in `pipeline.log` and continue with remaining series  
- [ ] [ ] T069 US1 Add unit test to verify abort behavior for GEO series with < 20 samples (ensures proper logging and graceful continuation)  
- [ ] [ ] T031 US1 Add quantitative false‑positive analysis module `src/pipeline/fp_analysis.py` that (a) computes total number of tested gene pairs, (b) estimates expected false positives for a given correlation threshold using a Poisson approximation, (c) writes a brief report `results/false_positive_estimate_<species>.txt`  
- [ ] [ ] T032 US1 Extend the pipeline documentation (`docs/false_positives.md`) with the Poisson derivation, expected spurious link count, and discussion of mitigation (high threshold, baseline comparison) – referenced from Dyson’s comment.  
- [ ] [ ] T072 US1 Add CI documentation lint test `scripts/lint_docs.py` that verifies `docs/false_positives.md` exists and contains the required sections (Poisson derivation, mitigation).  

---

## Phase 4: User Story 2 – Quantitative Evaluation Against STRING (Priority: P2)

**Goal**: Compute AUROC and AUPRC for each species and produce a degree‑preserving random‑graph baseline.

**Independent Test**: Run `make evaluate` and verify `results/evaluation_metrics.json` contains AUROC > 0.70, AUPRC ≥ 0.65, and baseline AUROC ≤ 0.55 for each species.

### Implementation Tasks

- [ ] T021 US2 Implement STRING downloader `src/pipeline/download_string.py` (fixed URL, checksum verification) – provides **full high‑confidence set** (combined score ≥ 700) without evidence‑type restriction  
- [ ] T022 US2 Implement evaluation script `src/pipeline/evaluate.py` that (a) loads predicted edges, (b) loads STRING high‑confidence interactions, (c) computes AUROC/AUPRC with `sklearn.metrics`, (d) writes per‑species entries to `results/evaluation_metrics.json`  
- [ ] T023 US2 Implement baseline generator `src/pipeline/baseline.py` that creates a degree‑preserving random graph via NetworkX `double_edge_swap` (controlled by `--seed`) and computes baseline AUROC/AUPRC  
- [ ] T024 US2 Extend `src/cli/run_pipeline.py` to expose `evaluate` sub‑command and pass seed/threshold flags  
- [ ] T025 US2 Add unit tests `tests/unit/test_evaluate.py` and `test_baseline.py` (mock small graph, check metric calculation)  
- [ ] T026 US2 Add integration test `tests/integration/test_end_to_end_us2.py` that runs `make evaluate` on the mock data from US1 and asserts metric thresholds are met (uses pre‑computed expected values)  
- [ ] T045 US2 Verify evaluation metrics: CI step that parses `evaluation_metrics.json` and asserts AUROC > 0.70, AUPRC ≥ 0.65, and baseline AUROC ≤ 0.55 for each species; fails the pipeline otherwise  
- [ ] T046 US2 Enforce runtime limit: wrapper script that measures total wall‑clock time of `make all`/`make evaluate` and aborts with error if > 6 h (benchmark task T037 logs the time; T046 enforces)  
- [ ] T047 US2 Seed propagation test: unit test ensuring that stochastic functions in `baseline.py` and any tie‑breaking in `correlation.py` respect the global `--seed` flag, yielding identical outputs on repeated runs  
- [ ] T065 US2 Real‑data evaluation integration test: runs the full default dataset (or a representative subset) and checks that AUROC > 0.70 and AUPRC ≥ 0.65, confirming compliance on real data  
- [ ] T070 US2 Verify baseline AUROC ceiling: CI step that asserts baseline AUROC ≤ 0.55 (as required by acceptance scenario)  

---

## Phase 5: User Story 3 – Functional Enrichment of Predicted Interactome (Priority: P3)

**Goal**: Perform GO term enrichment on genes participating in predicted PPIs and report adjusted p‑values.

**Independent Test**: Run `make enrich` and verify that `results/go_enrichment_<species>.tsv` contains at least one GO term with adjusted p < 0.05, or a “No significant enrichment” line.

### Implementation Tasks

- [ ] T027 US3 Implement GO enrichment script `src/pipeline/enrichment.py` using GOATOOLS (ontology 2023‑12‑01) with Fisher’s exact test and Benjamini–Hochberg correction; output `results/go_enrichment_<species>.tsv`  
- [ ] T028 US3 Add CLI flag `--go-ontology` (default points to cached 2023‑12‑01 file) and integrate into `run_pipeline.py` as `enrich` sub‑command  
- [ ] T029 US3 Write unit test `tests/unit/test_enrichment.py` that runs enrichment on a tiny gene set with a known GO term and checks adjusted p‑value calculation  
- [ ] T030 US3 Write integration test `tests/integration/test_end_to_end_us3.py` that runs `make enrich` after US1 & US2 and validates presence of at least one significant term (or graceful “No significant enrichment” handling)  
- [ ] T044 US3 Verify GO‑enrichment FDR: CI step that parses `go_enrichment_<species>.tsv` and asserts at least one term has adjusted p < 0.05; if none, the pipeline records “No significant enrichment” but the check passes only when the file is correctly formatted  

---

## Phase 6: Address Prior Research‑Stage Review (Dyson)

**Goal**: Explicitly quantify expected false‑positive burden and provide a calibration validation set.

### Tasks

- [ ] T031 US1 Add quantitative false‑positive analysis module `src/pipeline/fp_analysis.py` that (a) computes total number of tested gene pairs, (b) estimates expected false positives for a given correlation threshold using a Poisson approximation, (c) writes a brief report `results/false_positive_estimate_<species>.txt`  
- [ ] T032 US1 Extend the pipeline documentation (`docs/false_positives.md`) with the Poisson derivation, expected spurious link count, and discussion of mitigation (high threshold, baseline comparison) – referenced from Dyson’s comment.  
- [ ] T072 US1 Add CI documentation lint test `scripts/lint_docs.py` that verifies `docs/false_positives.md` exists and contains the required sections (Poisson derivation, mitigation).  
- [ ] T067 US1 Run documentation linter (`mkdocs build` or equivalent) to ensure `false_positives.md` renders without errors.  
- [ ] T033 US2 Create a curated validation set `data/external/validation_string.tsv` containing experimentally confirmed Arabidopsis PPIs (downloaded from STRING with evidence type “exp”) and add a calibration step in `evaluate.py` that reports precision at top‑k edges (`k = 1000`) against this set.  
- [ ] T034 US2 Update `evaluation_metrics.json` schema to include `precision_at_1000` field and modify `contracts/evaluation.schema.yaml` accordingly.  
- [ ] T068 US2 Run schema‑validation tests after the schema update to ensure downstream code conforms.  
- [ ] T035 US2 Add unit test `tests/unit/test_validation_set.py` that checks the calibration metric against a tiny synthetic validation set.  
- [ ] T062 US1 Verify false‑positive analysis output: unit test that ensures `fp_analysis.py` produces a non‑empty report with expected numeric fields.  

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` and `docs/quickstart.md` with full end‑to‑end usage instructions, including the new false‑positive analysis and validation‑set calibration sections.  
- [ ] T037 [P] Run comprehensive performance benchmark script `scripts/benchmark.sh` to ensure total wall‑clock time ≤ 6 h on the GitHub Actions runner; log results in `results/benchmark_report.txt`. (Note: enforcement of the 6‑hour limit is performed by T046.)  
- [ ] T038 Run CI step to enforce reproducibility: after a successful run, re‑run the pipeline with the same `--seed` and `git diff` the resulting `evaluation_metrics.json` and all `go_enrichment_*.tsv` files; fail if any differences are detected.  
- [ ] T039 Code cleanup: remove dead imports, ensure full type‑hint coverage, and produce a linting report `lint_report.txt` (generated via `ruff` and `mypy`).  
- [ ] T040 Security hardening: verify that all external URLs are fetched over HTTPS and that each download includes SHA‑256 checksum verification; automated audit script `scripts/audit_urls.py` runs in CI.  
- [ ] T041 Documentation: Add a “Reproducibility Statement” section to `docs/README.md` citing the global `--seed` flag and the content‑hashed artifact map. Unit test `tests/unit/test_repro_statement.py` ensures the statement is present.  
- [ ] T048 Run Reference‑Validator Agent on all citation‑bearing files during CI to guarantee verified accuracy (Constitution II).  
- [ ] T050 [P] Create quickstart documentation (`docs/quickstart.md`) that walks a user through a minimal end‑to‑end run on a tiny mock dataset.  
- [ ] T051 CI test that executes the quickstart steps (`make quickstart-test`) and asserts successful completion and correct output file generation.  
- [ ] T054 [P] CLI argument validator (implemented in T012) ensures `--threshold` cannot be set below 0.8.  
- [ ] T056 [P] Extend `validate.py` (T011) to assert presence and parsability of **all** required output files (`predicted_ppi_*.tsv`, `evaluation_metrics.json`, `go_enrichment_*.tsv`, `pipeline.log`) after each target.  
- [ ] T059 [P] Add quickstart documentation creation (see T050) – consolidated under T050.  
- [ ] T060 CI test for quickstart (see T051) – consolidated under T051.  
- [ ] T062 Verify false‑positive analysis output (see above).  
- [ ] T063 Automated check that the benchmark script (T037) reports runtime ≤ 6 h; CI fails otherwise.  
- [ ] T064 [P] Documentation build verification: run `mkdocs build` (or equivalent) and ensure no errors, confirming that new sections render correctly.  