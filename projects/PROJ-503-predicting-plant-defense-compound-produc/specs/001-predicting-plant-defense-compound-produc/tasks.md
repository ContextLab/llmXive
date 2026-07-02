# Tasks: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Input**: Design documents from `/specs/001-predict-plant-defense/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: User story tests are REQUIRED per spec.md Independent Test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0 – Data Discovery (MANDATORY BLOCKER)

**Purpose**: Verify dataset availability and define search criteria BEFORE any project structure or code is built.

**⚠️ ABORT CRITERIA**: If no verified plant omics datasets with ≥95% pairing and n≥28, project halts with E‑DATASET.

- [ ] T001 [P] [US1] Define search criteria (GEO herbivore‑stress keywords, Metabolomics Workbench metabolite keywords) and draft `projects/PROJ-503-predict-plant-defense-compound-produc/data/sources.yaml`. Verify YAML syntax.
- [ ] T002 [P] [US1] Search GEO for *Arabidopsis* herbivore‑stress series; output IDs to `projects/PROJ-503-predict-plant-defense-compound-produc/data/raw/geo_arabidopsis_search.json`.
- [ ] T003 [P] [US1] Search GEO for *Solanum* herbivore‑stress series; output IDs to `projects/PROJ-503-predict-plant-defense-compound-produc/data/raw/geo_solanum_search.json`.
- [ ] T004 [P] [US1] Search Metabolomics Workbench for defense‑metabolite experiments; output IDs to `projects/PROJ-503-predict-plant-defense-compound-produc/data/raw/mw_search.json`. Verify at least one accession is returned. <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 4, column 21:
 def search_geo(query: str) -> List[Dict[str, Any]]:
 ^) -->
- [ ] T005 [P] Create configurable power‑analysis utility `projects/PROJ-503-predict-plant-defense-compound-produc/code/utils/power_analysis.py` (default power = 0.8, α = 0.05, target r = 0.5). Include unit test.
- [ ] T006 [P] Run power analysis (using T005) and write result to `projects/PROJ-503-predict-plant-defense-compound-produc/logs/power_analysis.log`. If n < 28, log a warning and halt **modeling** (do not abort the entire pipeline); document the power deficiency in `logs/power_analysis.log`.
- [~] T007 [P] Verify sample‑level pairing feasibility (≥95% match) by comparing biosample identifiers from GEO and Metabolomics metadata; write report to `projects/PROJ-503-predict-plant-defense-compound-produc/data/paired/pairing_report.json` and log details to `projects/PROJ-503-predict-plant-defense-compound-produc/logs/data_pairing.json`.
- [~] T008a [P] If pairing rate < 95%, attempt **condition‑level aggregation** (averaging replicates within the same experimental condition) using `projects/PROJ-503-predict-plant-defense-compound-produc/code/data_aggregation.py`. Output aggregated matrices to `projects/PROJ-503-predict-plant-defense-compound-produc/data/processed/aggregated_expression.csv` and `aggregated_metabolite.csv`. Update `pairing_report.json` with fallback status.
- [ ] T008b [P] After fallback attempt, if pairing rate remains < 95%, abort pipeline with error code **E‑PAIRING** and record reason in `projects/PROJ-503-predict-plant-defense-compound-produc/logs/data_pairing.json`.
- [ ] T009 [P] Document verified dataset sources (accession IDs, download dates, checksums) in `projects/PROJ-503-predict-plant-defense-compound-produc/data/sources.yaml`.
- [ ] T010 [P] Create `research.md` summarizing dataset citations and availability status.

## Phase 1 – Setup (Shared Infrastructure)

- [ ] T010a [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/code/`.
- [ ] T010b [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/data/raw/`.
- [ ] T010c [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/data/processed/`.
- [ ] T010d [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/data/paired/`.
- [ ] T010e [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/logs/`.
- [ ] T010f [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/outputs/models/`.
- [ ] T010g [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/docs/`.
- [ ] T010h [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/tests/contract/`.
- [ ] T010i [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/tests/integration/`.
- [ ] T010j [P] Create directory `projects/PROJ-503-predict-plant-defense-compound-produc/tests/unit/`.
- [ ] T011 [P] Initialize git repository and add `.gitignore`.
- [ ] T012 [P] Create `requirements.txt` with exact version pins for all dependencies.
- [ ] T013 [P] Create `.flake8` and `pyproject.toml` with Black configuration.

## Phase 2 – Foundational (Blocking Prerequisites)

- [ ] T019 [P] Create logging infrastructure:
 - Define JSON schema `projects/PROJ-503-predict-plant-defense-compound-produc/logs/data_pairing_schema.json`.
 - Define CSV schema `projects/PROJ-503-predict-plant-defense-compound-produc/logs/feature_filtering_schema.csv`.
- [ ] T020a [P] Implement `ExpressionMatrix` class in `projects/PROJ-503-predict-plant-defense-compound-produc/code/models/expression.py`.
- [ ] T020b [P] Implement `MetaboliteMatrix` class in `projects/PROJ-503-predict-plant-defense-compound-produc/code/models/metabolite.py`.
- [ ] T020c [P] Implement `FeatureSet` and `ModelArtifact` classes in `projects/PROJ-503-predict-plant-defense-compound-produc/code/models/artifact.py`.
- [ ] T021 [P] Implement error‑handling framework with defined error codes (`E‑DATASET`, `E‑PAIRING`, `E‑POWER`, `E‑TIMEOUT`, `E‑CHECKSUM`, `E‑FEATURE`) in `projects/PROJ-503-predict-plant-defense-compound-produc/code/errors.py`.
- [ ] T022 [P] Implement runtime timer in `projects/PROJ-503-predict-plant-defense-compound-produc/code/main.py` that logs to `projects/PROJ-503-predict-plant-defense-compound-produc/logs/runtime.log` and raises `E‑TIMEOUT` if CPU time > 4 h.
- [ ] T023 [P] Add pip‑audit step to CI workflow; write findings to `projects/PROJ-503-predict-plant-defense-compound-produc/docs/security_report.md`.

## Phase 3 – User Story 1 – End‑to‑end data acquisition & pairing (Priority: P1) 🎯 MVP

- [ ] T023a [P] Implement GEO downloader function `download_geo_series(series_id)` in `projects/PROJ-503-predict-plant-defense-compound-produc/code/data_download.py`. Store raw files under `projects/PROJ-503-predict-plant-defense-compound-produc/data/raw/`.
- [ ] T023b [P] Unit test for GEO downloader (`tests/unit/test_geo_download.py`).
- [ ] T024a [P] Implement Metabolomics Workbench downloader `download_mw_experiment(exp_id)` in same module. Store raw files under `data/raw/`.
- [ ] T024b [P] Unit test for MW downloader (`tests/unit/test_mw_download.py`).
- [ ] T025 [P] Verify SHA checksums of all downloaded files; write PASS/FAIL per file to `projects/PROJ-503-predict-plant-defense-compound-produc/logs/checksum_report.log`.
- [ ] T026 [P] Parse GEO sample metadata to extract biosample IDs; parse MW metadata similarly; store intermediate mappings in `data/processed/geo_metadata.csv` and `mw_metadata.csv`.
- [ ] T027 [P] Implement sample‑level pairing script `projects/PROJ-503-predict-plant-defense-compound-produc/code/pairing.py` that matches based on biosample_id; output paired index to `projects/PROJ-503-predict-plant-defense-compound-produc/data/paired/paired_index.csv`.
- [ ] T028 [P] Create expression matrix CSV (`projects/PROJ-503-predict-plant-defense-compound-produc/data/processed/expression_matrix.csv`) with TPM/FPKM values per sample.
- [ ] T029 [P] Create metabolite matrix CSV (`projects/PROJ-503-predict-plant-defense-compound-produc/data/processed/metabolite_matrix.csv`) with log‑transformed concentrations aligned to biosample IDs. **If sample-level pairing fails (<95%), this task must attempt condition-level aggregation as defined in T008a before finalizing the matrix.**
- [ ] T030 [P] Log any sample‑level mismatches to `projects/PROJ-503-predict-plant-defense-compound-produc/logs/data_pairing.json` (fields: `sample_id, expression_source, metabolite_source, reason`).
- [ ] T031 [P] Validate pairing rate (≥95%); if not satisfied after fallback (T008a/T029), abort with `E‑PAIRING` (handled in T008b).

## Phase 4 – User Story 2 – Feature selection & preprocessing (Priority: P2)

- [ ] T032a [P] Implement expression normalization to TPM/FPKM (`normalize_expression`) in `projects/PROJ-503-predict-plant-defense-compound-produc/code/preprocessing.py`; output to `data/processed/expression_normalized.csv`.
- [ ] T032b [P] Unit test for expression normalization (`tests/unit/test_expression_normalization.py`).
- [ ] T033a [P] Implement metabolite log‑transformation (`log_transform_metabolite`) in same module; output to `data/processed/metabolite_log.csv`.
- [ ] T033b [P] Unit test for metabolite transformation (`tests/unit/test_metabolite_log.py`).
- [ ] T034a [P] Implement zero‑variance gene filtering (variance < 1e‑10) on `expression_normalized.csv`; output filtered matrix to `data/processed/expression_filtered.csv`.
- [ ] T034b [P] Log removed genes to `projects/PROJ-503-predict-plant-defense-compound-produc/logs/feature_filtering.csv` (columns: `gene_id, variance, reason`).
- [ ] T035a [P] Retrieve KEGG pathway gene lists for terpenoid, alkaloid, phenylpropanoid pathways using `gseapy`; write combined gene list to `data/processed/defense_genes.txt`.
- [ ] T036a [P] Filter `expression_filtered.csv` to retain only genes present in `defense_genes.txt`; output to `data/processed/expression_defense.csv`. **Strictly map to the three specified defense-biosynthetic pathways; do not apply additional exclusions (e.g., regulatory genes) unless explicitly defined in a future spec amendment.**
- [ ] T036b [P] Ortholog fallback: for Solanum genes missing KEGG annotation, find Arabidopsis orthologs (≥60% identity) via Biopython; write substitutions to `docs/edge_cases.md` (markdown table) and update `expression_defense.csv` with substituted IDs.
- [ ] T037 [P] Verify ≥75% of known defense pathway genes retained per species; write summary to `logs/feature_retention.csv`. Abort with `E‑FEATURE` if threshold not met.
- [ ] T038a [P] Apply species‑specific z‑score normalization to `expression_defense.csv`; output to `data/processed/expression_zscore.csv`.
- [ ] T038b [P] Apply ComBat batch correction across species on `expression_zscore.csv`; output to `data/processed/expression_corrected.csv`.
- [ ] T039a [P] Conditional PCA: if number of features `p` > 2 × number of samples `n`, compute PCA retaining components that explain ≥95 % variance (or up to `min(p, n‑1)`); write transformed matrix to `data/processed/expression_pca.csv` and log summary to `logs/pca_summary.csv`. If condition not met, copy `expression_corrected.csv` to `expression_pca.csv` unchanged.
- [ ] T040 [P] Define final feature matrix path `data/processed/feature_matrix.csv` (alias of PCA output or corrected matrix) for downstream modeling.
- [ ] T041 [P] Final metabolite matrix path is `data/processed/metabolite_matrix.csv` (already created in US1).

## Phase 5 – User Story 3 – Predictive modelling & evaluation (Priority: P3)

- [ ] T042a [P] Implement Ridge regression training (`train_ridge`) in `projects/PROJ-503-predict-plant-defense-compound-produc/code/modeling.py`; perform inner CV to select alpha. Save species‑specific models to `outputs/models/ridge_species_A.pkl` and `ridge_species_S.pkl`.
- [ ] T042b [P] Unit test for Ridge training (`tests/unit/test_ridge_training.py`).
- [ ] T043a [P] Implement outer k-fold cross-validation. (`evaluate_cv`) that computes RMSE and Pearson r per metabolite; aggregate mean ± SD and write to `outputs/metrics/model_results.json`.
- [ ] T043b [P] Unit test for CV evaluation (`tests/unit/test_cv_evaluation.py`).
- [ ] T044a [P] Implement permutation test (1 000 iterations) in `projects/PROJ-503-predict-plant-defense-compound-produc/code/evaluation.py`; write raw p‑values to `outputs/metrics/permutation_pvalues.json`.
- [ ] T044b [P] Unit test for permutation test (`tests/unit/test_permutation.py`).
- [ ] T045a [P] Apply Bonferroni correction across metabolites; update `model_results.json` with corrected p‑values and also compute Benjamini‑Hochberg FDR (optional).
- [ ] T045b [P] Verify that the metabolite with highest Pearson r has r ≥ 0.5; log verification in `logs/verification.log`.
- [ ] T045c [P] Verify that the same metabolite has Bonferroni‑corrected p ≤ 0.05; log verification in `logs/verification.log`.
- [ ] T046a [P] Serialize `ModelArtifact` (coefficients, metrics) for each species model to `outputs/models/ridge_species_A_model.pkl` and `ridge_species_S_model.pkl`.
- [ ] T046b [P] Log serialization success to `logs/runtime.log`.
- [ ] T047a [P] Conditional cross‑species model: if total paired samples ≥ 50 (checked from `pairing_report.json`), train Ridge model on combined data and save to `outputs/models/cross_species_model.pkl`; otherwise log `E‑SAMPLESIZE` to `logs/runtime.log`. **Explicitly note that SC‑001 (r≥0.5) and SC‑002 (p≤0.05) do NOT apply to this exploratory model.**
- [ ] T047b [P] Unit test for cross‑species model creation (`tests/unit/test_cross_species_model.py`).
- [ ] T048a [P] Perform species‑holdout validation (train on Arabidopsis, test on Solanum and vice versa); write results to `outputs/metrics/species_holdout.json`.
- [ ] T048b [P] Unit test for species‑holdout validation (`tests/unit/test_species_holdout.py`).
- [ ] T049 [P] Compute VIF diagnostics on final feature matrix; write to `outputs/vif_diagnostics.csv`.

## Phase N – Polish & Cross‑Cutting Concerns

- [ ] T050a [P] Create `docs/quickstart.md` with end‑to‑end pipeline instructions.
- [ ] T050b [P] Validate `quickstart.md` on a fresh runner; record success in `docs/quickstart_validation.md`.
- [ ] T051a [P] Create `docs/data-model.md` describing schemas for ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact; reference files in `contracts/`.
- [ ] T051b [P] Populate `contracts/` directory with YAML schema files (`expression_matrix.schema.yaml`, `metabolite_matrix.schema.yaml`, `model_output.schema.yaml`).
- [ ] T052 [P] Run `black --check` and `flake8`; fix violations; document changes in `docs/refactoring_log.md`.
- [ ] T053a [P] Profile pipeline with `cProfile`; output to `logs/profiling_report.txt`.
- [ ] T053b [P] Optimize identified bottlenecks; ensure total runtime < 4 h; update integration test `tests/integration/test_e2e_runtime.py`.
- [ ] T054 [P] Run unit tests with coverage: `pytest --cov=code --cov-report=term-missing`; write coverage summary to `logs/coverage_report.txt`; enforce ≥ 80 % line coverage.
- [ ] T055 [P] Run `pip-audit`; write findings to `docs/security_report.md`.
- [ ] T056 [P] Verify all `[deferred]` citations in `spec.md` have resolved entries in `research.md`; produce `docs/assumption_resolution_log.md` (parse step writes temporary `logs/assumption_parsing.log` before final markdown).