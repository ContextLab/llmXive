# Tasks: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Input**: Design documents from `specs/001-network-centrality-sleep-synchrony/` (spec.md, plan.md, data-model.md, contracts/)
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

## Task format
`- [ ] T### [P?] [USx?] description with exact artifact paths`
- **[P]** – can run in parallel (different files, no data dependencies)
- **[USx]** – user-story label (US1, US2, US3)

**Methodological note**: Per `plan.md` and the active `contracts/analysis.schema.yaml`, the statistical method is **Linear Mixed-Effects (LME) models with FDR (Benjamini–Hochberg) correction**, replacing the spec's original Bonferroni/simple-correlation wording (dependent sleep-stage hypotheses; subject-level non-independence). The schema fixes `method: "lme"` and `p_value_corrected` as FDR-corrected. Tasks below implement that contract.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] Establish project layout, configuration, and verified data acquisition from PhysioNet (FR-001)
  - Write `code/config.yaml` with all signal-processing parameters: bandpass 0.5–45 Hz, ICA kurtosis threshold 5.0, high-frequency power ratio threshold 3.0, theta 4–8 Hz, alpha 8–13 Hz, epoch length 30 s, pinned random seed, N_MIN = 30, VIF threshold 5.0, alpha level 0.05.
  - Write `code/requirements.txt` with pinned versions of `mne`, `statsmodels`, `networkx`, `scipy`, `pandas`, `numpy`, `pyedflib`.
  - Implement `code/download.py::download_sleep_edf(output_dir='data/raw/', n_subjects=...)` using MNE-Python's PhysioNet Sleep-EDF access (`mne.datasets.sleep_physionet.fetch_data`). The fetch MUST fail loudly on download failure (raise; never fall back to synthetic or bundled data). Verify file integrity via checksums recorded in `data/raw/download_log.txt`. Corrupted `.edf` files are logged and skipped without halting the job (spec edge case: Data Corruption).
  - Verify: `python -c "import mne,statsmodels,networkx,scipy,pandas,numpy,pyedflib"` succeeds; `data/raw/` contains real Sleep-EDF recordings for ≥ 30 subjects and `data/raw/download_log.txt` lists checksum-verified files.

- [ ] T002 [US1] Implement EEG preprocessing: filtering, ICA artifact removal, epoching, night-ID extraction (FR-002, FR-011)
  - `code/preprocess.py::apply_bandpass_filter(raw, low=0.5, high=45.0)` — unit test in `code/tests/test_preprocess.py` verifies a 10 Hz sinusoid passes while 0.1 Hz and 100 Hz components are attenuated.
  - `code/preprocess.py::remove_ica_artifacts(filtered, kurtosis_thr=5.0, power_ratio_thr=3.0)` — flags/removes components with kurtosis > 5.0 or high-frequency power > 3× baseline; unit test flags a synthetic high-kurtosis component.
  - `code/preprocess.py::epoch_by_sleep_stage(cleaned, annotations, epoch_sec=30)` — produces 30-second epochs labeled Wake/N1/N2/N3/REM; extracts `waking_night_id` and `sleep_night_id` from recording metadata. Outputs `data/processed/epochs_{subject_id}.npz` and `data/processed/metadata_{subject_id}.json`.
  - `code/preprocess.py::validate_no_nans(arr)` — raises on any NaN; status logged to `data/processed/validation_log.txt`.
  - Missing sleep stages for a subject are recorded (no imputation, no crash — spec edge case: Missing Sleep Stages).
  - Verify: run on a real 3-subject subset; epochs have correct 30 s shape, labels match the annotation file, no NaNs remain.

- [ ] T003 [US2] Compute connectivity, centrality, PLI, VIF, and aggregate subject-level metrics (FR-003, FR-004, FR-005, FR-009)
  - `code/metrics.py::compute_connectivity_matrix(waking_signal, bands={'theta':(4,8),'alpha':(8,13)})` — symmetric coherence matrices with values strictly in (0,1), saved as `data/processed/connectivity_{subject_id}_{band}.npy`; also compute `global_coherence_mean` (covariate). Unit test checks symmetry and range.
  - `code/metrics.py::compute_centrality_metrics(matrix)` — degree, betweenness, eigenvector centrality via NetworkX; validated on a synthetic star graph against pre-calculated reference values within 1e-6 (US-2 acceptance scenario 2).
  - `code/metrics.py::compute_pli(epoch_signal)` — Phase Lag Index across electrode pairs per epoch, aggregated to a mean global synchrony score per sleep stage (single float in [0,1]); unit test on synthetic phase-locked signals.
  - `code/metrics.py::compute_vif(centrality_df)` — VIF per centrality metric, flags > 5.0; output `data/metrics/vif_report.json`; unit test on correlated synthetic data.
  - `code/metrics.py::aggregate_subject_metrics(...)` — one row per subject per stage (missing stage-subject pairs excluded, not zero-imputed) into `data/metrics/SubjectMetrics.csv` conforming to `specs/.../contracts/dataset.schema.yaml` (columns: subject_id, stage_label, mean_pli, n_epochs, centrality_degree_mean, centrality_betweenness_mean, centrality_eigenvector_mean, waking_night_id, sleep_night_id, temporal_proximity).
  - Verify: integration test loads `SubjectMetrics.csv`, validates schema, numeric ranges, and no missing required columns.

- [ ] T004 [US3] Run a thin end-to-end analysis on the real subset and produce first result rows
  - Wire `code/main.py` (download → preprocess → metrics → analysis) with runtime and peak-memory logging (SC-002, SC-003).
  - Run the full chain on the real 3-subject subset; produce a preliminary `data/results/analysis_results.json` with real (not expected or invented) LME entries conforming to `contracts/analysis.schema.yaml`.
  - Verify: the documented command executes; JSON entries have all required fields (`metric_name`, `stage_label`, `band`, `correlation_coefficient`, `p_value_raw`, `p_value_corrected`, `significant`, `method: "lme"`, `global_connectivity_coefficient`, `covariate_used`).

**Checkpoint**: The documented command executes end-to-end on real data and its numerical outputs can be checked against the schema. Do not proceed to reporting from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US1] [US2] Run the complete dataset through preprocessing and metric computation (FR-001–FR-005, SC-001)
  - Process all downloaded subjects (subject-by-subject to stay < 4 GB RAM); compute processed-subject percentage against total downloaded (SC-001) recorded in `data/processed/preprocessing_complete.txt`.
  - Regenerate the full `data/metrics/SubjectMetrics.csv` and `data/metrics/vif_report.json` on the complete dataset.
  - Verify: distinct `subject_id` count ≥ 30 in `SubjectMetrics.csv`; all rows schema-valid.

- [ ] T006 [US3] Implement the statistical analysis: sample-size gate, normality diagnostics, LME models, FDR correction (FR-006, FR-007, FR-010, FR-012)
  - `code/analysis.py::check_sample_size(df, n_min=30)` — if N < 30, log an "Insufficient Sample Size" warning to `data/results/sample_size_warning.txt` and proceed with effect-size/CI estimation flagged as underpowered (per plan.md deviation from spec halt-behavior; documented limitation). Unit test covers the N = 20 path.
  - `code/analysis.py::shapiro_diagnostics(df)` — Shapiro-Wilk on model variables/residuals per metric-stage-band; results recorded in `data/results/method_selection.csv` (diagnostic record).
  - `code/analysis.py::fit_lme(df)` — for each centrality metric × stage × band (3 × 4 × 2 = 24 models): LME with mean PLI as outcome, centrality metric and global coherence covariate as fixed effects, subject-level random intercept `(1|Subject)` via `statsmodels.MixedLM`. Extract fixed-effect coefficient and raw p-value.
  - `code/analysis.py::fdr_correct(pvals)` — Benjamini–Hochberg across the family of 24 tests; verify corrected p ≥ raw p monotonically and flag `significant = corrected < 0.05`.
  - Unit tests: MixedLM converges on synthetic clustered data; FDR correction returns valid, monotone adjusted p-values.
  - Verify: `data/results/analysis_results.json` contains 24 schema-conformant entries with real coefficients and corrected p-values.

- [ ] T007 [US3] Add independent correctness, sensitivity, and runtime checks and record actual outcomes (SC-002, SC-003, SC-004, SC-005)
  - Sensitivity check: re-fit the LME family excluding subjects with `temporal_proximity == true`; compare coefficient signs/significance in `data/results/sensitivity_temporal.json`.
  - Collinearity check: confirm `data/metrics/vif_report.json` flags VIF > 5.0 and that highly collinear metrics are reported descriptively, not as independent effects (spec edge case: Collinearity).
  - Runtime/memory check: assert full pipeline runtime < 4 h and peak RAM < 4 GB from `main.py` logs; record in `data/results/pipeline_complete.txt`.
  - Schema validation test: `data/results/analysis_results.json` validates against `contracts/analysis.schema.yaml`; all significant entries have corrected p < 0.05 (SC-004).

- [ ] T008 [US3] Generate result tables and figures directly from validated outputs (FR-008, FR-011)
  - `code/report.py` builds from `data/results/analysis_results.json`, `data/metrics/vif_report.json`, and `data/metrics/SubjectMetrics.csv` (no hand-typed numbers):
    - `data/results/correlation_table.csv` — coefficient, raw p, FDR-corrected p, significance flag per metric-stage-band.
    - `figures/centrality_pli_scatter.png` — scatter plots of each centrality metric vs. mean PLI per stage with LME fit lines.
    - `figures/synchrony_by_stage.png` — mean PLI distribution per sleep stage.
  - "Confounding Limitation" section content generated whenever any subject has `temporal_proximity == true` (FR-011).
  - Verify: every number in the tables/figures traces programmatically to `data/results/` and `data/metrics/` artifacts.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [P] [US3] Write the human-readable report (FR-008, FR-011)
  - Generate `reports/final_report.md` containing: sample-size summary and any underpowered warning; results table (coefficients, raw and FDR-corrected p-values, significance flags); VIF table with > 5.0 flags; "Confounding Limitation" paragraph for temporal proximity; normality/LME diagnostic note; explicit "Significant"/"Non-Significant" labeling; associational (non-causal) framing per spec Assumption 2.
  - Verify: unit test asserts all required sections appear and significance flags render correctly.

- [ ] T010 [P] Write the methods/results account and quick-start, and document the paper-stage handoff
  - Populate `specs/001-network-centrality-sleep-synchrony/quickstart.md` with the exact runnable commands (install, `python code/main.py`), expected outputs (`SubjectMetrics.csv`, `analysis_results.json`, `final_report.md`), and measured runtime/memory from `data/results/pipeline_complete.txt`.
  - Write a concise methods/results account in `specs/001-network-centrality-sleep-synchrony/methods.md`: data source (Sleep-EDF via PhysioNet/MNE), preprocessing, coherence/centrality/PLI computation, LME + FDR methodology (noting the documented Bonferroni→FDR/LME deviation and its rationale), VIF diagnostics, temporal-proximity limitation, and honest reporting of negative or non-significant findings.
  - Re-run the documented workflow from `data/raw/` inputs; confirm tests and artifact checks pass; capture outcome in `data/results/reproducibility_check.txt`.
  - Document the paper-stage handoff: paper layout, PDF compilation, and publication requirements are deferred to the subsequent paper pipeline; this study hands over `data/results/analysis_results.json`, `data/results/correlation_table.csv`, `figures/*.png`, and `reports/final_report.md`.

---

## Dependencies and requirement coverage

| Task | Depends on | Requirements covered |
|------|------------|----------------------|
| T001 | – | FR-001 |
| T002 | T001 | FR-002, FR-011 (night-ID extraction) |
| T003 | T002 | FR-003, FR-004, FR-005, FR-009 |
| T004 | T003 | FR-006/FR-007 (thin end-to-end), SC-002/SC-003 (logging) |
| T005 | T004 | FR-001–FR-005 at full scale, SC-001 |
| T006 | T005 | FR-006, FR-007, FR-010, FR-012 |
| T007 | T006 | SC-002, SC-003, SC-004, SC-005, collinearity edge case |
| T008 | T007 | FR-008, FR-011 |
| T009 | T008 | FR-008, FR-011 |
| T010 | T008 | Reproducibility, documentation, paper handoff |

T009 and T010 are parallelizable ([P]) once T008 completes. All data-flow orderings are respected: verification tasks run after the computations they verify.

**Compute note**: All methods (MNE filtering/ICA, NetworkX, MixedLM) are CPU-tractable on the default free runner (2 vCPU, ~7 GB RAM, ≤ 6 h); data is processed subject-by-subject to stay under 4 GB RAM. No synthetic data fallbacks exist anywhere in the pipeline — a failed real fetch raises and fails the run.
