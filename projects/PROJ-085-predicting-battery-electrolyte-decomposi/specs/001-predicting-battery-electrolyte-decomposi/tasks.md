# Tasks: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

**Inputs**: `specs/001-battery-electrolyte-decomposition/spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Re-plan note**: Consolidated prior 50+ tasks into 14 substantive tasks; repaired duplicate task ID `T045` (one instance was a US-1 integration test, the other a US-3 reporting task — both are folded into the consolidated tasks below). Previously verified work is preserved as checked. All paths are relative to the project root.

## Phase 1: Setup and first end-to-end analysis

**Goal**: A runnable ingestion → descriptor → target‑calculation path on a small real subset, producing real result rows.

- [ ] T001 [US1] Initialize project constants and reaction lookup infrastructure in `code/utils/constants.py`: Faraday constant `FARADAY_C = 96485.33212`, potential list `PHI_VALUES = [0.0, 2.0, 4.0]`, potential bins (low: 0–2 V, high: 3–5 V mapped to the 4 V data point), and `code/utils/reactions.yaml` schema with keys `molecule_id, potential_v, reactants, products, n_electrons, energy_products, energy_reactants`, populated with the 3 hardcoded reference rows (EC‑0V → CO₂ + C₂H₄, n=2; DMC‑2V → CH₃OH + CO₂, n=1; LiPF₆‑4V → LiF + PF₅, n=1) used for schema validation and unit tests only. Also implement `code/utils/models.py` dataclasses (`ElectrolyteMolecule`, `DecompositionEvent`), seed configuration, and checksum logic for `data/raw`, `data/processed`, `data/validation`. (FR‑002, FR‑008)

- [ ] T002 [P] [US3] Implement external‑data verification in `code/data/external_search.py`: query NOMAD API, Materials Project, and PubChem for experimental electrolyte onset potentials (keywords: 'electrolyte', 'onset potential', 'cyclic voltammetry'; check DOIs in `research.md`). Write `data/validation/data_status.json` with `external_data_available: false` if none found and generate `code/reports/limitations.md` documenting the search. **Do not generate synthetic data.** Update `research.md` with the final status. (FR‑006 precondition)

- [ ] T003 [US1] Implement `code/data/ingestion.py` to fetch and filter real DFT data **from Materials Project, NOMAD, and the verified HuggingFace dataset** (streaming with `datasets.load_dataset(..., streaming=True)` if needed). Filter for EC, DMC, LiPF₆ species; deduplicate on (molecule ID, potential). On fetch failure raise `DataNotFoundError` — **no synthetic fallback**. Verify coverage of all three species and raise `CoverageError` if any is missing. Include unit test `tests/unit/test_ingestion.py` for deduplication and filter logic on a fixed small subset. (FR‑001)

- [ ] T004 [US1] Implement `code/data/descriptors.py` to extract HOMO, LUMO, band gap, and **≥5 geometric features** (max/min bond length, mean bond length, mean bond angle, max dihedral, **torsion count**) via `pymatgen`/`RDKit`; flag metallic (gap ≤ 0) and invalid‑geometry entries as `is_outlier` and exclude them; log warnings for missing geometric data without crashing. Include unit test `tests/unit/test_descriptors.py` for outlier flagging. (FR‑003)

- [ ] T005 [US1] Implement `code/data/target_calc.py` computing $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ for $\phi \in \{0, 2, 4\}$ V for all ingested molecules **using the hard‑coded `reactions.yaml` lookup table** (populated by T018). Molecules without a defined mechanism are excluded. Include unit test `tests/unit/test_target_calc.py` verifying the formula against a hand‑computed value within 0.01 eV. (FR‑002, FR‑008)

- [ ] T006 [US1] **Deprecated – split into finer‑grained tasks** (see T019‑T021). Previously built the processed feature matrix end‑to‑end; now responsibilities are distributed.

- [ ] T007 [US2] Implement `code/models/trainer.py`: Random Forest Regressor with GridSearchCV 5‑fold cross‑validation (`n_estimators=[100,200,500]`, `max_depth=[10,20,None]`), potential included as a feature, stratified by potential bin. If `high_bin_valid` is false, run single‑point mode (skip CV when n < 3) and log a warning. Include unit test `tests/unit/test_trainer.py`. (FR‑004)

- [ ] T008 [US2] Implement `code/models/evaluator.py` permutation‑importance analysis per potential bin (low vs high), identify descriptors entering the top 3 at high potential but absent at low, and save model artifacts, R², MAE, and importance maps conforming to `contracts/model_output.schema.yaml` (contract test `tests/contract/test_model_output.py`) to `data/processed/model_run.json`. If `high_bin_valid` is false, report "Insufficient data for high‑potential comparison" and flag the statistical‑power limitation in `bin_statistics.json` and `research.md`. (FR‑005)

- [ ] T009 [US2] Generate the feature‑importance heatmap (top 5 features, low vs high bins) with `seaborn`, saved to `figures/feature_importance_heatmap.png`; if the high bin is invalid, show only the low bin with an annotation of the missing bin. (FR‑005, SC‑002)

- [ ] T010 [US3] **Mandatory external validation**: read `data/validation/data_status.json`; if `external_data_available` is false, abort the pipeline with an error before any importance reporting (enforcing Principle VII). If data is present, compute MAE/R² against experimental onset potentials ($V_{onset}=E_{decomp}/nF$) and generate `data/validation/validation_report.md`. (FR‑006, SC‑003)

- [ ] T011 [US3] Implement the threshold sensitivity sweep in `code/models/evaluator.py`: sweep the decomposition‑energy stability cutoff over {0.45, 0.50, 0.55} eV, recompute top‑3 feature rankings at each threshold, verify maximum rank change ≤ 1 position, and write `data/validation/sensitivity_report.md` with the actual rank‑stability numbers. Include unit test `tests/unit/test_sensitivity.py`. (FR‑007, SC‑004)

- [ ] T012 [US1] Run the complete pipeline on the full ingested dataset (all molecules, all three potentials, both bins), executing the full parameter/data domain from the specification, and record actual R², MAE, importance rankings, and runtime in `data/results/` (JSON + CSV), tracing every metric to specific data rows. (SC‑001, SC‑005)

- [ ] T013 Write a concise methods/results account in `data/results/summary.md` linked to the actual output cells and figure files: dataset provenance and size, descriptor extraction method, reaction‑mechanism assumptions, model metrics, feature‑importance shift across bins, validation status (external vs internal fallback), threshold robustness, and honest limitations (single 4 V point for the high bin, missing experimental dataset, GCM‑based reaction energies, kinetic barriers ignored). (SC‑002, SC‑003, SC‑004)

- [ ] T014 Verify reproducibility and failure handling:
  1. Run a test suite that attempts to fetch from an intentionally unreachable endpoint and confirms a loud failure (fetch‑failure test).
  2. Then rerun the full pipeline using cached/checksummed raw data to confirm deterministic regeneration of all result artifacts. Document both outcomes in `research.md`. (SC‑005)

## New fine‑grained Phase 1 tasks

- [ ] T019 [US1] Run the end‑to‑end pipeline on a small real subset, producing intermediate CSVs: `data/raw/raw_ingested.csv`, `data/processed/descriptors.csv`, `data/processed/targets.csv`.

- [ ] T020 [US1] Validate the processed feature matrix against `contracts/dataset.schema.yaml`, checking for missing values and schema compliance; output a validation log `data/processed/validation_log.txt`.

- [ ] T021 [US1] Perform train/validation/hold‑out split and bin assignment, writing `data/processed/electrolyte_features.csv`, `data/processed/electrolyte_heldout.csv`, `data/processed/bins.csv`, and `data/validation/bin_statistics.json` (including `high_bin_valid` flag).

- [ ] T022 [US3] Generate a row‑level metrics report `data/results/metrics_by_row.csv` linking each `dft_id` and `potential_v` to predicted vs true decomposition energy, R² contribution, and feature values for full traceability.

## Additional supporting tasks

- [ ] T015 [US3] Enforce mandatory external experimental validation before any feature‑importance reporting; abort pipeline with a clear error if `external_data_available` is false (fulfills Principle VII and FR‑006).

- [ ] T017 [US2] Compute feature importance at 1 V (using available 0 V and 2 V data or interpolated values) and compare with 4 V importance, reporting any descriptor that enters the top 3 at 4 V but not at 1 V.

- [ ] T018 [US1] Populate a complete reaction lookup table (`code/utils/reactions.yaml`) for all ingested electrolyte molecules, providing `n_electrons`, product/reactant energies, and mechanism identifiers based on literature; this table is used by T005.

- [ ] T023 [US1] **Update dataset schema**: modify `contracts/dataset.schema.yaml` to add the missing geometric field `torsion_count` (type number, description “Number of torsional angles”). This aligns the contract with FR‑003’s ≥5 geometric features requirement.

## Dependencies and requirement coverage

- T001–T002 (done) → T003 → T004 → T005 → T006 (now split into T019‑T021) → T007 → T008/T009 → T010 (blocked until T015 passes) → T011 → T012 → T013 → T014

- All tasks respect data flow; each consumer runs after its producer.