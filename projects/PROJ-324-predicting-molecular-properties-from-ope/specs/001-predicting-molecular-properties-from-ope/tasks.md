# Tasks: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Inputs**: `spec.md`, `plan.md`, existing artifacts under `code/`, `data/`, `tests/`, and the reviewer/verifier feedback above.

**Context**: The foundational pipeline (download, preprocessing, MaxMin sampling, split, fingerprints, baseline, RF nested CV, Wilcoxon test, SHAP computation, LNAI, audits) has been implemented and verified. The verifier rejected five tasks whose *deliverable artifacts* were never materialized (T015, T027, T029, T033, T058) and flagged duplicate task identities (T033, T057, T058 appeared twice). This revision re-opens only the affected requirements as consolidated, individually verifiable tasks that each produce a real file with deterministic content. No completed requirement is dropped; no new study scope is added.

## Completed (verified — preserved)

- [ ] T001–T003 Project skeleton, `requirements.txt`, lint/format configuration.
- [X] T004, T008–T011.5 Data download (PubChem, fail-loudly), preprocessing, missing-covariate logging, MaxMin diverse sampling, dataset metadata (`data/raw/dataset_metadata.json`), 80/20 stratified split (`data/derived/train_set.csv`, `data/derived/test_set.csv`).
- [ ] T012–T014b Contract/unit tests; Crippen baseline features and undefined-atom imputation in `code/models/baseline.py`.
- [ ] T016.1–T016.2 Baseline failure magnitude log and report (`data/derived/additive_failure_log.txt`, `additive_failure_report.md`).
- [ ] T017–T020.1 Fingerprint generation via `obabel` subprocess (`data/processed/{full,train,test}_fingerprints.csv`), nested-CV RF training (`data/models/final_model.pkl`), test-set predictions (`data/derived/rf_test_predictions.csv`).
- [X] T021a–T023, T036 Wilcoxon test pipeline, comparison plots, runtime monitor, performance configuration.
- [X] T024–T026, T029.1 SHAP interaction values computed via `shap.TreeExplainer` in `code/analysis/explainability.py`; interaction-zone map report.
- [X] T030, T030.2 Steric descriptor cross-referencing and Local Non-Additivity Index.
- [X] T031, T037–T042, T057, T059 SMARTS rules file, docstrings, docs, security scan, test/format pass, validation audit, physical-vs-statistical analysis.

## Phase 1: Re-materialize rejected baseline artifacts

- [ ] T101 [US1] **Produce baseline metrics and residual plot (re-do of T015)**: Extend `code/analysis/stats.py` with a `compute_baseline_metrics()` function that (1) reads `data/derived/baseline_test_predictions.csv`, (2) computes MAE and RMSE per property (logP, solubility, boiling_point) with `pandas`/`numpy`, (3) writes the metric table to `data/derived/baseline_metrics.csv` with columns `property,mae,rmse,n`, and (4) renders a residual-distribution figure (matplotlib histogram of residuals per property, 3 panels) saved as `data/derived/baseline_residuals.png` (≥200×200 px, non-empty file). Add a focused test in `tests/unit/test_baseline_metrics.py` asserting the CSV row count equals 3 and that MAE ≥ 0. **Verification**: both files exist, CSV parses with the exact schema, PNG opens via `PIL.Image.open` without error. **Requirement**: FR-005 prerequisite (baseline side of the paired comparison), spec Validation Protocol metrics.
    - Command: `python -m code.analysis.stats --baseline-metrics` (or `python code/analysis/stats.py --baseline-metrics`).
    - Dependency: `baseline_test_predictions.csv` from completed T014.5 (already present).

## Phase 2: Re-materialize rejected explainability artifacts

- [ ] T102 [US3] **Produce SHAP interaction heatmap (re-do of T027)**: Add `plot_shap_interactions()` to `code/analysis/explainability.py` that (1) loads the trained model `data/models/final_model.pkl` and `data/processed/test_fingerprints.csv`, (2) computes SHAP interaction values with `shap.TreeExplainer(model).shap_interaction_values(X)` on the MACCS feature block, (3) persists the full interaction matrix to `data/derived/shap_interaction.npy` (per plan T027.1, which was also never materialized), and (4) renders a top-N (N ≥ 20) bit-pair interaction heatmap with `matplotlib.pyplot.imshow` + colorbar, saved as `data/derived/shap_interactions.png`. **Verification**: `.npy` loads with `np.load` and has shape (n_test, n_bits, n_bits) or the aggregated (n_bits, n_bits); PNG exists and is non-empty. **Requirement**: FR-006.
    - Command: `python code/analysis/explainability.py --shap-heatmap`.
    - Dependency: completed T026 (model + fingerprints already present). Sequential to T101 only for reporting consistency, not data.

- [ ] T103 [US3] **Produce MACCS bit→substructure mapping CSV (re-do of T029)**: Add `map_bits_to_substructures()` to `code/analysis/explainability.py` that (1) loads the SMARTS rules from `code/data/rules.py` (list of dicts with `name`, `smarts`, `description`), (2) for each MACCS bit index among the top-K SHAP-interaction bits (K ≥ 30, ranked by mean |interaction value| from `data/derived/shap_interaction.npy` produced in T102), matches the bit's SMARTS pattern against each molecule in `data/derived/test_set.csv` using `rdkit.Chem.MolFromSmiles` + `GetSubstructMatches`, (3) when a bit maps to multiple SMARTS, selects the one with the highest aggregate SHAP magnitude; unmatched bits are labeled `unmapped`, and hashed ECFP4/FP2 bits are reported as `uninterpretable` per plan, (4) writes `data/derived/deviation_contexts.csv` with columns `smiles,bit_index,matched_substructure,interaction_strength` conforming to `specs/.../contracts/interaction_context.schema.yaml` field names. Add `tests/unit/test_bit_mapping.py` asserting the CSV exists, has the exact header, and contains no empty `matched_substructure` cells (must be a SMARTS name or `unmapped`/`uninterpretable`). **Requirement**: FR-007.
    - Command: `python code/analysis/explainability.py --map-bits`.
    - Dependency: T102 (interaction matrix must exist first — data-flow order).

## Phase 3: Re-materialize rejected audit artifacts

- [ ] T104 [US3] **Produce conformational-limitations CSV (re-do of T033, deduplicated)**: Add `flag_conformational_limits()` to `code/analysis/explainability.py` that (1) reads `data/derived/test_set.csv`, (2) computes `NumRotatableBonds` and TPSA per molecule with `rdkit.Chem.rdMolDescriptors.CalcNumRotatableBonds` and `CalcTPSA`, (3) flags molecules with `NumRotatableBonds > 10` as conformationally limited (2D fingerprints likely miss solution-phase conformational ensembles — per reviewer concern on static vs. dynamic structures, addressed as a stated topological limitation, not a physical claim), (4) joins each flagged molecule with its RF residual magnitude from `data/derived/rf_test_predictions.csv`, and (5) writes `data/derived/conformational_limitations.csv` with columns `smiles,num_rotatable_bonds,tpsa,deviation_magnitude`. **Verification**: CSV exists, parses, header exact, every row has `num_rotatable_bonds > 10`. **Requirement**: plan T033; reviewer concern on conformational ensembles.
    - Command: `python code/analysis/explainability.py --conformational-audit`.
    - Dependency: completed T020.1 (rf predictions). Independent of T101–T103.

- [ ] T105 [US3] **Produce experimental validation protocol document (re-do of T058, deduplicated)**: Add `write_validation_protocol()` to `code/analysis/stats.py` that generates `data/derived/experimental_validation_protocol.md` from real artifacts only — no invented values. The document must contain, as generated sections (string-built from loaded data, not hand-written placeholders): (1) a provenance table listing each property's source record for the held-out test set, read from `data/raw/dataset_metadata.json` and `data/derived/test_set.csv`; (2) a measurement-uncertainty section that reports the exact status string from `dataset_metadata.json` (`"Not Available in Source"` when absent — never fabricated numbers, per the reviewer's demand for direct measurement); (3) an aggregation of missing covariates (pH, temperature) from `data/derived/data_quality_report.csv`; (4) a validation procedure describing how future wet-lab measurements (shake-flask logP, gravimetric solubility, distillation boiling point) would check the top-ranked interaction zones from `data/derived/lna_index.csv` and `deviation_contexts.csv`; (5) an explicit statement of statistical-power limitations if the diverse subset is smaller than 5000 molecules. **Verification**: file exists, is valid Markdown ≥ 50 lines, contains the literal string `Not Available in Source` iff the metadata says so, and cites at least the four artifact filenames above. **Requirement**: plan T058; reviewer concern on experimental validation of predictions.
    - Command: `python code/analysis/stats.py --validation-protocol`.
    - Dependency: T103 (deviation contexts feed the protocol's ranked zones) and completed T030.2/T009 artifacts.

## Phase 4: Consolidated verification and reproducibility pass

- [ ] T106 **End-to-end re-run and artifact inventory check**: Add `code/main.py::verify_artifacts()` (or a `tests/integration/test_artifact_inventory.py`) that asserts the existence, non-emptiness, and basic schema of every deliverable promised by the spec's Data Model: `data/raw/pubchem_raw.csv`, `data/derived/{data_quality_report,diverse_subset,train_set,test_set,baseline_test_predictions,baseline_metrics,rf_test_predictions,statistical_test_report,deviation_contexts,lna_index,conformational_limitations}.csv`, `data/derived/{baseline_residuals,shap_interactions,model_comparison}.png`, `data/derived/shap_interaction.npy`, `data/derived/{validation_audit.md,experimental_validation_protocol.md,interaction_zone_map.md,physical_vs_statistical_analysis.md}`, and `data/models/final_model.pkl`. Run the full documented workflow from `data/raw/` inputs in one command and record start/end timestamps. **Verification**: `python -m pytest tests/integration/test_artifact_inventory.py` passes; every listed path exists with the expected header/shape.
    - Dependency: T101–T105 (all artifacts must exist first).

- [ ] T107 **Methods/results account and paper-stage handoff**: Write `paper/methods_results.md` (create `paper/` on demand via the toolkit `paths` helper) summarizing: dataset size and experimental/computed ratio, baseline vs. RF MAE/RMSE per property (from `baseline_metrics.csv` and the RF metrics), Wilcoxon p-values with Bonferroni correction, top interaction zones with their SMARTS descriptions and LNAI scores, the conformational-limitation subset size, and an honest limitations section (topological proxies not physical mechanisms; missing pH/temperature covariates; any negative findings reported as found). End with a **paper-stage handoff** section listing the figures (`baseline_residuals.png`, `shap_interactions.png`, `model_comparison.png`), tables, and contracts to carry into the paper pipeline — PDF compilation and publication remain subsequent stages and are not tasked here. **Verification**: document exists, every number cited traces to a named artifact file, no bracket-style attribution markers.
    - Dependency: T106.

## Dependencies and requirement coverage

| Requirement | Task(s) | Command / artifact |
|---|---|---|
| FR-001/FR-002/FR-008 | completed T008–T011.5 | `data/raw/pubchem_raw.csv`, `data_quality_report.csv` |
| FR-003 | completed T019/T019.1 | `data/processed/*_fingerprints.csv` |
| FR-004 | completed T020/T020.1 | `data/models/final_model.pkl`, `rf_test_predictions.csv` |
| FR-005 | completed T021.1 + T101 | `statistical_test_report.md`, `baseline_metrics.csv`, `baseline_residuals.png` |
| FR-006 | completed T026 + T102 | `shap_interaction.npy`, `shap_interactions.png` |
| FR-007 | T103 | `deviation_contexts.csv` |
| Conformational audit (plan T033) | T104 | `conformational_limitations.csv` |
| Experimental protocol (plan T058) | T105 | `experimental_validation_protocol.md` |
| Reproducibility (NFR-004) | T106 | integration test + full re-run |
| Paper handoff | T107 | `paper/methods_results.md` |

Execution order: T101 → (T102 → T103) and T104 in parallel → T105 → T106 → T107. The five re-opened tasks each produce one deterministically checkable file, resolving the earlier unverifiable-artifact failures; the duplicate identities (old T033/T057/T058 double-entries) are collapsed into single tasks T104/T105 with the audit content of T057 already verified and preserved.

## Revision behavior

All previously verified tasks remain checked above with their artifact identities intact. Only the verifier-rejected deliverables (T015, T027, T029, T033, T058) were re-opened, renumbered (T101–T105) to eliminate the duplicate-ID malformation, and rewritten so each promises exactly one real, schema-checkable output file. Reviewer concerns (experimental validation evidence, conformational-ensemble limitations, topological-vs-physical framing) are addressed inside T104, T105, and T107 without duplicating the already-verified T057/T059 analyses.
