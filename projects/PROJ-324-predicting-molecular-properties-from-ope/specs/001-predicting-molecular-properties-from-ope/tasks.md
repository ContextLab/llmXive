# Tasks: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Inputs**: `spec.md`, `plan.md`, existing artifacts under `code/`, `data/`, `tests/`, verifier rejections of T015/T027/T029/T033/T058, and reviewer feedback (experimental validation evidence, conformational-ensemble limitations, topological-vs-physical framing).

**Context**: The core pipeline is implemented and verified: PubChem download with fail-loudly behavior, preprocessing with missing-covariate logging, MaxMin diverse sampling, 80/20 stratified split, Open Babel fingerprint generation, Crippen/linear baselines, nested-CV Random Forest, Wilcoxon comparison, SHAP interaction computation, LNAI, SMARTS rules, and the validation audit. The verifier rejected five deliverables whose output files were never materialized, and the previous task list had duplicate IDs (T033, T057, T058). This revision reopens only the rejected deliverables as individually verifiable tasks with unique IDs; all verified requirements are preserved. No completed requirement is dropped; no new scope is added.

## Verified (preserved — do not redo)

- Data download (PubChem, fail-loudly), preprocessing, missing-covariate logging, MaxMin diverse sampling, dataset metadata (`data/raw/dataset_metadata.json`), 80/20 stratified split (`data/derived/train_set.csv`, `data/derived/test_set.csv`) — FR-001, FR-002, FR-008.
- Open Babel CLI fingerprint generation (`data/processed/{full,train,test}_fingerprints.csv`) — FR-003.
- Nested-CV Random Forest training (`data/models/final_model.pkl`) and test-set predictions (`data/derived/rf_test_predictions.csv`) — FR-004.
- Wilcoxon signed-rank pipeline with Bonferroni correction (`data/derived/statistical_test_report.md`), comparison plots, runtime monitoring — FR-005 (statistical machinery).
- SHAP interaction computation in `code/analysis/explainability.py`, interaction-zone map report, LNAI with BH-FDR (`data/derived/lna_index.csv`), SMARTS rules file, validation audit, physical-vs-statistical analysis.

## Phase 1: Re-materialize rejected baseline deliverable

- [ ] T101 [US1] **Baseline metrics table and residual plot (re-do of rejected T015)**: Extend `code/analysis/stats.py` with `compute_baseline_metrics()` that (1) reads `data/derived/baseline_test_predictions.csv`, (2) computes MAE and RMSE per property (logP, solubility, boiling_point) with `pandas`/`numpy`, (3) writes `data/derived/baseline_metrics.csv` with columns `property,mae,rmse,n` (exactly 3 rows), and (4) renders a 3-panel matplotlib histogram of residuals per property saved as `data/derived/baseline_residuals.png` (non-empty, ≥200×200 px). Add `tests/unit/test_baseline_metrics.py` asserting the CSV has 3 rows, the exact header, and MAE ≥ 0. **Verification**: both files exist, CSV parses with the exact schema, PNG opens via `PIL.Image.open` without error. **Requirement**: FR-005 (baseline side of the paired comparison), spec Validation Protocol metrics.
    - Command: `python -m code.analysis.stats --baseline-metrics`.
    - Dependency: `baseline_test_predictions.csv` (already present from verified baseline work).

## Phase 2: Re-materialize rejected explainability deliverables

- [ ] T102 [US3] **SHAP interaction heatmap and persisted matrix (re-do of rejected T027, absorbing T027.1)**: Add `plot_shap_interactions()` to `code/analysis/explainability.py` that (1) loads `data/models/final_model.pkl` and `data/processed/test_fingerprints.csv`, (2) computes SHAP interaction values with `shap.TreeExplainer(model).shap_interaction_values(X)` on the MACCS feature block, (3) persists the interaction matrix to `data/derived/shap_interaction.npy` (per-molecule tensor or mean-aggregated square matrix — state which in the script), and (4) renders a top-N (N ≥ 20) bit-pair heatmap via `matplotlib.pyplot.imshow` with colorbar, saved as `data/derived/shap_interactions.png`. **Verification**: `.npy` loads with `np.load` with shape `(n_test, n_bits, n_bits)` or `(n_bits, n_bits)`; PNG exists and is non-empty. **Requirement**: FR-006. <!-- FAILED-IN-EXECUTION: code/analysis/explainability.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/analysis/explainability.py exit=1 -->
    - Command: `python -m code.analysis.explainability --shap-heatmap`.
    - Dependency: verified model + fingerprints. Data-independent of T101.

- [ ] T103 [US3] **MACCS bit→substructure mapping CSV (re-do of rejected T029)**: Add `map_bits_to_substructures()` to `code/analysis/explainability.py` that (1) loads SMARTS rules from `code/data/rules.py` (list of dicts with `name`, `smarts`, `description`), (2) ranks the top-K MACCS bits (K ≥ 30) by mean |interaction value| from `data/derived/shap_interaction.npy` produced by T102, (3) matches each bit's SMARTS against molecules in `data/derived/test_set.csv` using `rdkit.Chem.MolFromSmiles` + `GetSubstructMatches`, resolving multi-matches to the highest aggregate SHAP magnitude; unmatched bits labeled `unmapped`, hashed ECFP4/FP2 bits reported as `uninterpretable` per plan, and (4) writes `data/derived/deviation_contexts.csv` with columns `smiles,bit_index,matched_substructure,interaction_strength` conforming to `specs/.../contracts/interaction_context.schema.yaml` field names. Add `tests/unit/test_bit_mapping.py` asserting the CSV exists with the exact header and no empty `matched_substructure` cells. **Requirement**: FR-007.
    - Command: `python -m code.analysis.explainability --map-bits`.
    - Dependency: T102 (interaction matrix must exist first — data-flow order).

## Phase 3: Re-materialize rejected audit deliverables

- [ ] T104 [US3] **Conformational-limitations CSV (re-do of rejected T033, single deduplicated identity)**: Add `flag_conformational_limits()` to `code/analysis/explainability.py` that (1) reads `data/derived/test_set.csv`, (2) computes `CalcNumRotatableBonds` and `CalcTPSA` per molecule with RDKit, (3) flags molecules with `NumRotatableBonds > 10` as conformationally limited — framed as a stated topological limitation of 2D fingerprints (they cannot reflect solution-phase conformational ensembles), not a physical claim, per the reviewer's objection that fingerprints are topological abstractions, (4) joins each flagged molecule with its RF residual magnitude from `data/derived/rf_test_predictions.csv`, and (5) writes `data/derived/conformational_limitations.csv` with columns `smiles,num_rotatable_bonds,tpsa,deviation_magnitude`. **Verification**: CSV exists, parses, header exact, every row has `num_rotatable_bonds > 10`. **Requirement**: plan T033; reviewer concern on conformational ensembles. <!-- FAILED-IN-EXECUTION: code/analysis/explainability.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/analysis/explainability.py exit=1 -->
    - Command: `python -m code.analysis.explainability --conformational-audit`.
    - Dependency: verified `rf_test_predictions.csv`. Independent of T101–T103.

- [ ] T105 [US3] **Experimental validation protocol document (re-do of rejected T058, single deduplicated identity)**: Add `write_validation_protocol()` to `code/analysis/stats.py` generating `data/derived/experimental_validation_protocol.md` from real artifacts only — no invented values. The document must contain, as sections string-built from loaded data (not hand-written placeholders): (1) a provenance table listing each property's source record for the held-out test set, read from `data/raw/dataset_metadata.json` and `data/derived/test_set.csv`; (2) a measurement-uncertainty section reporting the exact status string from the metadata (`"Not Available in Source"` when absent — never fabricated numbers, per the reviewer's demand for direct measurement evidence); (3) an aggregation of missing covariates (pH, temperature) from `data/derived/data_quality_report.csv`; (4) a validation procedure describing how future wet-lab measurements (shake-flask logP, gravimetric solubility, distillation boiling point) would check the top-ranked interaction zones from `data/derived/lna_index.csv` and `data/derived/deviation_contexts.csv`; and (5) an explicit statistical-power limitation statement if the diverse subset is smaller than 5000 molecules. **Verification**: file exists, is valid Markdown ≥ 50 lines, contains the literal string `Not Available in Source` iff the metadata says so, and cites at least the four artifact filenames above. **Requirement**: plan T058; reviewer concern on experimental validation.
    - Command: `python -m code.analysis.stats --validation-protocol`.
    - Dependency: T103 (deviation contexts feed the ranked zones) plus verified LNAI and quality-report artifacts.

## Phase 4: Consolidated verification, reproducibility, and handoff

- [ ] T106 **End-to-end re-run and artifact inventory check**: Add `tests/integration/test_artifact_inventory.py` (driven by `code/main.py::verify_artifacts()`) asserting existence, non-emptiness, and basic schema of every deliverable promised by the spec's Data Model: `data/raw/pubchem_raw.csv`; `data/derived/{data_quality_report,diverse_subset,train_set,test_set,baseline_test_predictions,baseline_metrics,rf_test_predictions,statistical_test_report,deviation_contexts,lna_index,conformational_limitations}.csv`; `data/derived/{baseline_residuals,shap_interactions,model_comparison}.png`; `data/derived/shap_interaction.npy`; `data/derived/{validation_audit.md,experimental_validation_protocol.md,interaction_zone_map.md,physical_vs_statistical_analysis.md}`; and `data/models/final_model.pkl`. Re-run the full documented workflow from `data/raw/` inputs in one command, recording start/end timestamps (runtime guard, NFR-003/NFR-004). **Verification**: `python -m pytest tests/integration/test_artifact_inventory.py` passes; every listed path exists with the expected header/shape.
    - Dependency: T101–T105 (all artifacts must exist first).

- [ ] T107 **Methods/results account and paper-stage handoff**: Write `paper/methods_results.md` (create `paper/` on demand via the toolkit `paths` helper) summarizing: dataset size and experimental/computed ratio; baseline vs. RF MAE/RMSE per property (from `baseline_metrics.csv` and RF metrics); Wilcoxon p-values with Bonferroni correction; top interaction zones with their SMARTS descriptions and LNAI scores; the conformational-limitation subset size; and an honest limitations section (topological proxies are not physical mechanisms; missing pH/temperature covariates; any negative findings reported as found). End with a **paper-stage handoff** section listing the figures (`baseline_residuals.png`, `shap_interactions.png`, `model_comparison.png`), tables, and contracts to carry into the paper pipeline — PDF compilation and publication remain subsequent stages and are not tasked here. **Verification**: document exists, every number cited traces to a named artifact file, no bracket-style attribution markers.
    - Dependency: T106.

## Dependencies and requirement coverage

| Requirement | Task(s) | Command / artifact |
|---|---|---|
| FR-001/FR-002/FR-008 | verified download/preprocess work | `data/raw/pubchem_raw.csv`, `data_quality_report.csv` |
| FR-003 | verified fingerprint work | `data/processed/*_fingerprints.csv` |
| FR-004 | verified nested-CV work | `data/models/final_model.pkl`, `rf_test_predictions.csv` |
| FR-005 | verified Wilcoxon + T101 | `statistical_test_report.md`, `baseline_metrics.csv`, `baseline_residuals.png` |
| FR-006 | verified SHAP + T102 | `shap_interaction.npy`, `shap_interactions.png` |
| FR-007 | T103 | `deviation_contexts.csv` |
| Conformational audit (plan T033) | T104 | `conformational_limitations.csv` |
| Experimental protocol (plan T058) | T105 | `experimental_validation_protocol.md` |
| Reproducibility (NFR-004) | T106 | integration test + full re-run |
| Paper handoff | T107 | `paper/methods_results.md` |

Execution order: T101, T102, T104 (data-independent of each other) → T103 → T105 → T106 → T107. The five re-opened deliverables each produce one deterministically checkable file; the duplicate-ID malformation (old T033/T057/T058 double-entries) is resolved by assigning each requirement exactly one unique task ID, with the audit content of T057 already verified and preserved.

## Revision behavior

All previously verified tasks remain complete with their artifact identities intact. Only the verifier-rejected deliverables (T015, T027, T029, T033, T058) were reopened, renumbered T101–T105 to eliminate the duplicate-ID malformation, and rewritten so each promises exactly one real, schema-checkable output file with a concrete command. Reviewer concerns (experimental validation evidence, conformational-ensemble limitations, topological-vs-physical framing) are addressed inside T104, T105, and T107 without duplicating the already-verified validation-audit and physical-vs-statistical analyses.
