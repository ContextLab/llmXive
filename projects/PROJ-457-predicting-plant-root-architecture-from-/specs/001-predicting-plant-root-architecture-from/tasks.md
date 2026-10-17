# Tasks: Predicting Plant Root Architecture from Soil Nutrient Availability

**Input**: Design documents from `/specs/001-predict-root-architecture/` (spec.md, plan.md, research.md, data-model.md, contracts/)
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Status**: Preserving verified completed work; reopening the two verifier‑rejected contract tasks and consolidating all remaining pending work into canonical research tasks.

## Path Conventions

Paths are relative to the project directory. Source in `code/`, tests in `tests/`, results in `artifacts/` and `data/processed/`. Research scripts write only to project‑owned paths (`code/`, `data/`, `artifacts/`, `tests/`); the platform's `state/` files are **NOT** written by research tasks.

## Completed work (verified — preserved)

- [ ] T001 Project directory structure, logging, and repository initialization (`code/`, `tests/`, `data/raw`, `data/processed`, `artifacts/`, `logs/`).
- [X] T002a/T002b `code/requirements.txt` created and versions pinned.
- [ ] T003a–T003c Linting configuration and Black/Flake8 checks pass.
- [X] T004/T006/T007/T008 `code/config.py`, logging setup, base data models (`RootPhenotypeRecord`, `SoilNutrientRecord`), `config.yaml.template`.
- [X] T014a/T015g State file `artifacts/state.json` initialized; ISRIC verified‑source check performed — no verified ISRIC source exists; deviation logged, `is_isric_verified: false`.
- [X] T010/T012/T021/T022/T031 Unit and integration tests for preprocessing, species‑stratified splits, model pipeline, and file‑size constraint.
- [X] T013/T013b/T014/T014d/T015c–T015m/T035a–T035c Data ingestion from the verified HuggingFace merged‑dataset sources (fail‑loudly, no synthetic fallback), ISRIC‑unavailable path, P/N availability check, AM‑001 amendment record (`artifacts/sc_amendments.json`), FR‑012 observational filtering, missing‑nutrient exclusion per AM‑001, species‑count filtering (n≥20), species counts and SC‑001/SC‑005 metrics in `artifacts/reports/metrics.json` and `artifacts/reports/success_criteria_status.json`, deviation logs.
- [ ] T016 `code/preprocessing.py`: log‑transformation of root metrics (`log(x + 1e-6)`), global z‑score normalization of nutrients, conditional on `p_n_available`.
- [X] T023–T026b/T027 `code/modeling.py`: `GroupKFold` species‑stratified CV, Linear Mixed‑Effects Model (REML, Satterthwaite, species random intercept), Random Forest baseline (max_depth=5), F‑test, F‑test verification log, multiple‑comparison correction.
- [ ] T028a–T028c Literature range fetch/verification (`artifacts/literature_ranges.json`, `literature_verified` flag), sensitivity analysis (`artifacts/sensitivity/sensitivity_analysis.json`), literature comparison and plausibility verdict.
- [ ] T029a–T029d Final model metrics JSON (`artifacts/reports/model_metrics.json`) with adjusted R², RMSE, p‑values, CV mean R², `sc002_met` boolean.
- [X] T032/T033 `code/visualization.py`: partial dependence plots (5th–95th percentile range), PNG output with ≤100 MB enforcement.
- [X] T034a–T034e/T034d/T036 `code/reporting.py`: deviation logs read, metrics read, final report compiled with associational framing, causal‑language scan, report written to `artifacts/reports/final_report.md`, literature comparison table included.
- [X] T037a/T037/T038/T039 State file artifact hashes, README/docs update, quickstart validation.

## Phase 1: Repair rejected contract artifacts (verifier‑flagged)

- [ ] T101 Create `contracts/dataset.schema.yaml` and implement `test_merged_dataset_schema_validates_columns` in `tests/contract/test_schemas.py`.
    - Create a schema matching the active data‑model (required non‑null `species`, log‑transformed root metrics, nullable nutrient fields, `sample_size_per_species` integer; `additionalProperties: false`).
    - Implement a test that loads the schema with `pyyaml`, validates a representative row from `data/processed/merged_dataset.parquet`, and includes a negative case for missing `species`.
- [ ] T102 Create `contracts/output.schema.yaml` and implement `test_final_report_schema_validates_structure` in `tests/contract/test_schemas.py`.
    - Schema requires `report_file`, `plots` array, `total_plot_size_mb` ≤ 100, `associational_statement`, `deviations` array, and a `success_criteria` object with `sc_001_met` … `sc_006_met`; `additionalProperties: false`.
    - Test loads the schema, validates the JSON produced by `code/reporting.py`, asserts non‑empty associational statement and size constraint.

## Phase 2: Complete remaining scientific requirements

- [ ] T104 A priori power analysis (FR‑024, SC‑009) in `code/modeling.py`.
    - Compute required per‑species sample size for ≥80 % power to detect a standardized effect size f² = 0.15 at α = 0.05 using `statsmodels.stats.power.FTestPower`.
    - Record `required_n_per_species` and the achieved `power_achieved` (based on the minimum species count after the n ≥ 30 re‑filter) in `artifacts/reports/model_metrics.json` under `success_criteria`.
- [ ] T105 VIF collinearity check for all fixed predictors (FR‑008) in `code/modeling.py`.
    - Compute Variance Inflation Factors for phosphorus, nitrogen, soil_moisture, temperature, elevation; log a warning if any VIF > 5.
    - Output `vif` mapping and `vif_warning` boolean in `artifacts/reports/model_metrics.json`.
- [ ] T106 Leave‑one‑species‑out bias assessment (FR‑027, SC‑008) in `code/modeling.py`.
    - Iteratively refit the LMM excluding each species, compute maximum absolute relative change in any nutrient coefficient versus the full fit, flag if > 5 %.
    - Record `loso_max_coeff_change` and `sc008_met` in `artifacts/reports/model_metrics.json`.
- [ ] T107 Imputation/exclusion bias assessment (FR‑025) in `code/preprocessing.py`.
    - Compare pre‑ and post‑filtering summary statistics (mean, SD) for nutrients and root traits; log the bias metric.
    - Store `imputation_bias` block in `artifacts/reports/metrics.json`.

## Phase 3: Report verification and end‑to‑end validation

- [ ] T108 Report verification step (FR‑029, FR‑022, SC‑007, SC‑011) in `code/reporting.py`.
    - After compiling `final_report.md`, run a causal‑keyword lint using word‑boundary regex `\\b(cause|leads to|effect of|driven by)\\b`.
    - Verify the exact associational statement *“All findings are presented as associational relationships; no causal inference is claimed.”* is present.
    - Output `artifacts/reports/report_verification.json` with `associational_statement_present`, `causal_violations` list, `sc007_met`, `sc011_met`.
- [ ] T103 Validate `artifacts/reports/model_metrics.json` against `contracts/model_results.schema.yaml` in `tests/contract/test_schemas.py`.
    - This test now runs after the metrics JSON is produced (see ordering change).
- [ ] T109 Compile consolidated SC‑001–SC‑011 summary and final report refresh in `code/reporting.py`.
    - Merge all metric sources (`metrics.json`, `model_metrics.json`, `sensitivity/sensitivity_analysis.json`, `report_verification.json`) into an SC table in the final report.
    - Include a concrete test `tests/contract/test_report_sc_table.py` that asserts **each value in the SC table string‑matches the corresponding field in its source JSON artifact**, guaranteeing mechanical verification.
- [ ] T110 Run the full documented workflow end‑to‑end and validate all contract tests.
    - Execute `python code/ingestion.py && python code/preprocessing.py && python code/modeling.py && python code/visualization.py && python code/reporting.py`.
    - Then run `pytest tests/contract/test_schemas.py && pytest tests/contract/test_report_sc_table.py`.
    - Verify that all stages complete without error on the real HuggingFace merged dataset, and that all three contract tests (T101‑T103) pass.
- [ ] T111 Document the paper‑stage handoff in `artifacts/reports/final_report.md` and `quickstart.md`.
    - Add a handoff section naming the final report PDF, metrics SSoT, plot files, associational statement, causal‑lint requirements, and the AM‑001 deviation record.

## New tasks added to close gaps

- [ ] T112 Implement ISRIC merge with 10 km nearest‑neighbor interpolation (FR‑002) in `code/data_ingestion.py`.
    - Use geographic coordinates to locate nearest ISRIC soil sample within a 10 km radius; if none, log exclusion.
- [ ] T113 Implement k‑NN imputation (k=5, Euclidean distance, mean fallback) for missing phosphorus/nitrogen (FR‑003) in `code/preprocessing.py`.
    - Apply after log‑transformation; fallback to column mean when fewer than 5 neighbors exist.
- [ ] T114 Compute merge_success_rate (SC‑001) against RootReader and PlantPheno datasets in `code/metrics.py`.
    - Record `merge_success_rate` (≥ 0.90) in `artifacts/reports/metrics.json`.
- [ ] T115 Extend `contracts/model_results.schema.yaml` to include `required_n_per_species` (number) and `sc009_met` (boolean) under `success_criteria`.
    - Update the schema file accordingly.
- [ ] T116 Re‑filter species to n ≥ 30 (FR‑024) after initial ingestion; enforce the threshold and record compliance in `artifacts/reports/sampling_report.json`.
- [ ] T117 Perform power analysis after T116 and write `required_n_per_species` and `sc009_met` (SC‑009) into `model_metrics.json` (uses output of T116).
- [ ] T118 Record SHA‑256 checksums of all raw data files in `data/checksums.json` (Constitution III/V).
    - Compute checksums during ingestion and store them alongside the raw files.
- [ ] T119 Retrieve literature effect‑size values from `plantphysio/nutrient_ranges` (FR‑021) and verify citations per Constitution II.
    - Store verified ranges in `artifacts/literature_ranges.json` and set `literature_verified` flag.
- [ ] T120 Adjust sensitivity analysis fallback to ±15 % variation (FR‑028) in `code/sensitivity.py`.
    - Ensure the fallback matches the spec’s ±15 % range.
- [ ] T121 Align script naming: rename ingestion entry point to `code/ingestion.py`; update all task references (including T110) and quickstart documentation.
- [ ] T122 Generate final PDF report (`final_report.pdf`) from `final_report.md` using Pandoc (or LaTeX) and store under `artifacts/reports/`.
- [ ] T123 Update T108 keyword matching to use word‑boundary regex to avoid false positives (e.g., “because”).
- [ ] T124 Implement concrete verification of the SC table in the final report (`tests/contract/test_report_sc_table.py`).
- [ ] T125 Remove parallel `[P]` tags from T101‑T103 and serialize their execution to avoid write conflicts.

## Dependencies and requirement coverage

- **Order**: T101–T102 → T112/T113 → T014/T015 → T116 → T104 → T115 → T117 → T105/T106/T107 → T108 → T103 → T109 → T110 → T111 → T122 (PDF generation).  
- **FR coverage**: All functional requirements (FR‑001 … FR‑028) now have explicit covering tasks.  
- **SC coverage**: All success criteria (SC‑001 … SC‑011) are measured, recorded, and validated by dedicated tasks.  
- **Constitution compliance**: Checksums recorded under `data/`, no research script writes to `state/`; citation verification task satisfies Principle II.  

