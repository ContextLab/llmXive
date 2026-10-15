# Tasks: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Input**: Design documents from `specs/001-network-centrality-sleep-synchrony/` (spec.md, plan.md, data‑model.md, contracts/)  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

## Task format
`- [ ] T### [P?] [USx?] description with exact artifact paths`  
- **[P]** – can run in parallel (different files, no data dependencies)  
- **[USx]** – user‑story label (US1, US2, US3)  

All tasks respect the data‑flow ordering indicated by the indentation and by the “Depends on” table below.

---

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P] [US1] Establish project layout, configuration, and verified data acquisition from PhysioNet (FR‑001)   <!-- FAILED-IN-EXECUTION: code/download.py exit=1 -->
  - Update `specs/001-investigating-the-impact-of-network-cent/contracts/analysis.schema.yaml` to replace all references to "FDR-corrected" with "Bonferroni-corrected" to align with Constitution Principle VII.  
  - Write `code/config.yaml` with all signal‑processing parameters: bandpass 0.5–45 Hz, ICA kurtosis > 5.0, high‑frequency power > 3 × baseline, theta 4–8 Hz, alpha 8–13 Hz, epoch length 30 s, random seed, `N_MIN` = 30, VIF threshold 5.0, α = 0.05.  
  - Write `code/requirements.txt` with pinned versions of `mne`, `statsmodels`, `networkx`, `scipy`, `pandas`, `numpy`, `pyedflib`.  
  - Implement `code/download.py::download_sleep_edf(output_dir='data/raw/', n_subjects=…)` using MNE‑Python’s PhysioNet Sleep‑EDF fetch (`mne.datasets.sleep_physionet.fetch_data`). The fetch **must raise** on any download failure; no synthetic fallback. Verify file integrity via SHA‑256 checksums recorded in `data/raw/download_log.txt`. Corrupted `.edf` files are logged and **skipped** without halting the job (edge‑case: Data Corruption).  
  - **Verification**: `python -c "import mne,statsmodels,networkx,scipy,pandas,numpy,pyedflib"` succeeds; `data/raw/` contains ≥ 30 subjects; `data/raw/download_log.txt` lists checksum‑verified files; `analysis.schema.yaml` specifies Bonferroni.

- [ ] T002 [US1] Implement EEG preprocessing: filtering, ICA artifact removal, epoching, night‑ID extraction (FR‑002, FR‑011)  
  - `code/preprocess.py::apply_bandpass_filter(raw, low=0.5, high=45.0)` – unit test in `code/tests/test_preprocess.py` verifies a 10 Hz sinusoid passes while 0.1 Hz and 100 Hz components are attenuated.  
  - `code/preprocess.py::remove_ica_artifacts(filtered, kurtosis_thr=5.0, power_ratio_thr=3.0)` – flags/removes components with kurtosis > 5.0 **or** high‑frequency power > 3 × baseline; unit test flags a synthetic high‑kurtosis component.  
  - `code/preprocess.py::epoch_by_sleep_stage(cleaned, annotations, epoch_sec=30)` – produces 30‑second epochs labeled Wake/N1/N2/N3/REM; extracts `waking_night_id` and `sleep_night_id` from recording metadata. Outputs `data/processed/epochs_{subject_id}.npz` and `data/processed/metadata_{subject_id}.json`.  
  - `code/preprocess.py::validate_no_nans(arr)` – raises on any NaN; status logged to `data/processed/validation_log.txt`.  
  - Missing sleep stages for a subject are recorded (no imputation, no crash – edge‑case: Missing Sleep Stages).  
  - **Verification**: Run on a real 3‑subject subset; epochs have correct shape, correct labels, and contain no NaNs.

- [ ] T003 [US2] Compute connectivity, centrality, PLI, VIF, and aggregate subject‑level metrics (FR‑003, FR‑004, FR‑005, FR‑009)  
  - `code/metrics.py::compute_connectivity_matrix(waking_signal, bands={'theta':(4,8),'alpha':(8,13)})` – symmetric coherence matrices with values strictly in (0, 1); saved as `data/processed/connectivity_{subject_id}_{band}.npy`; also compute `global_coherence_mean` (covariate). Unit test checks symmetry and range.  
  - `code/metrics.py::compute_centrality_metrics(matrix)` – degree, betweenness, eigenvector centrality via NetworkX; validated on a synthetic star graph against reference values within 1e‑6 (US‑2 acceptance scenario 2).  
  - `code/metrics.py::compute_pli(epoch_signal)` – Phase Lag Index across electrode pairs per epoch, aggregated to a mean global synchrony score per sleep stage (single float in [0, 1]); unit test on synthetic phase‑locked signals.  
  - `code/metrics.py::compute_vif(centrality_df)` – VIF per centrality metric, flags > 5.0; output `data/metrics/vif_report.json`; unit test on correlated synthetic data.  
  - `code/metrics.py::aggregate_subject_metrics(...)` – one row per subject per stage (missing stage‑subject pairs excluded, not zero‑imputed) into `data/metrics/SubjectMetrics.csv` conforming to `specs/.../contracts/dataset.schema.yaml`. Columns: `subject_id, stage_label, mean_pli, n_epochs, centrality_degree_mean, centrality_betweenness_mean, centrality_eigenvector_mean, waking_night_id, sleep_night_id, temporal_proximity`.  
  - **Verification**: Integration test loads `SubjectMetrics.csv`, validates schema, numeric ranges, and presence of all required columns.

- [ ] T004 [US3] Run a thin end‑to‑end analysis on the real subset and produce first result rows (FR‑006, FR‑007, SC‑002, SC‑003)  
  - Wire `code/main.py` (download → preprocess → metrics → analysis) with runtime and peak‑memory logging.  
  - Execute the full chain on the real 3‑subject subset; compute Shapiro‑Wilk normality on each centrality‑PLI pair, then select Pearson (if normal) or Spearman (if non‑normal) correlation.  
  - Apply **Bonferroni** correction to the resulting raw p‑values (multiply by the number of tests, cap at 1.0).  
  - Produce a preliminary `data/results/analysis_results.json` containing entries that conform to the *updated* `contracts/analysis.schema.yaml` (Bonferroni-corrected).  
  - **Verification**: The documented command executes; JSON entries contain all required fields (`metric_name`, `stage_label`, `band`, `correlation_coefficient`, `p_value_raw`, `p_value_corrected`, `significant`, `method:"pearson"` or `"spearman"`, `global_connectivity_coefficient` set to `null`, `covariate_used:false`).

---

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US1] [US2] Run the complete dataset through preprocessing and metric computation (FR‑001–FR‑005, SC‑001)  
  - Process all downloaded subjects subject‑by‑subject to stay < 4 GB RAM; compute processed‑subject percentage against total downloaded (SC‑001) recorded in `data/processed/preprocessing_complete.txt`.  
  - Regenerate the full `data/metrics/SubjectMetrics.csv` and `data/metrics/vif_report.json` on the complete dataset.  
  - **Verification**: Distinct `subject_id` count ≥ 30 in `SubjectMetrics.csv`; all rows schema‑valid.

- [ ] T006 [US3] Implement the full statistical analysis respecting FR‑010, FR‑012, and **Bonferroni** correction (FR‑006, FR‑007)  
  - `code/analysis.py::check_sample_size(df, n_min=30)` – logs a **warning** if N < 30 and skips the correlation step (continues pipeline).  
  - `code/analysis.py::shapiro_and_select(df)` – runs Shapiro‑Wilk on each predictor/response pair, selects Pearson if p ≥ 0.05 else Spearman; records diagnostics in `data/results/method_selection.csv`.  
  - `code/analysis.py::compute_correlations(df)` – for each centrality metric × stage × band, computes the selected correlation coefficient and raw p‑value.  
  - `code/analysis.py::bonferroni_correct(pvals, n_tests=24)` – applies Bonferroni correction (multiply by 24, cap at 1.0).  
  - Assemble results into `data/results/analysis_results.json` matching the updated schema (p‑value fields now Bonferroni‑corrected, `method` set to `"pearson"` or `"spearman"`).  
  - **Verification**: JSON contains 24 entries, all fields present, corrected p‑values ≥ raw p‑values and ≤ 1.0, `significant` flag correct.

- [ ] T007 [US3] Add independent correctness, sensitivity, and runtime checks; record actual outcomes (SC‑002, SC‑003, SC‑004, SC‑005)  
  - Sensitivity check: re‑run `code/analysis.py` **excluding** subjects where `temporal_proximity == true`; compare coefficients in `data/results/sensitivity_temporal.json`.  
  - Collinearity check: confirm `data/metrics/vif_report.json` flags VIF > 5.0 and that highly collinear metrics are reported descriptively, not as independent effects (edge‑case: Collinearity).  
  - Runtime/memory check: assert full pipeline runtime < 4 h and peak RAM < 4 GB from `main.py` logs; record in `data/results/pipeline_complete.txt`.  
  - Schema validation test: `data/results/analysis_results.json` validates against `contracts/analysis.schema.yaml`; all significant entries have corrected p < 0.05 (SC‑004).  
  - **Verification**: All auxiliary JSON/TXT files exist and contain the expected diagnostic information.

- [ ] T008 [US3] Generate result tables and figures directly from validated outputs (FR‑008, FR‑011)  
  - `code/report.py` builds from `data/results/analysis_results.json`, `data/metrics/vif_report.json`, and `data/metrics/SubjectMetrics.csv` (no hand‑typed numbers):  
    - `data/results/correlation_table.csv` – coefficient, raw p, Bonferroni‑corrected p, significance flag per metric‑stage‑band.  
    - `figures/centrality_pli_scatter.png` – scatter plots of each centrality metric vs. mean PLI per stage with correlation fit lines.  
    - `figures/synchrony_by_stage.png` – mean PLI distribution per sleep stage.  
  - “Confounding Limitation” paragraph is auto‑generated whenever any subject has `temporal_proximity == true` (FR‑011).  
  - **Verification**: Every number in the tables/figures traces programmatically to `data/results/` or `data/metrics/` artifacts; files exist and are readable.

- [ ] T009 [P] [US3] Write the human‑readable final report (FR‑008, FR‑011)  
  - Generate `reports/final_report.md` containing:  
    - Sample‑size summary and any under‑powered warning (appears only if N < 30).  
    - Results table (coefficients, raw and Bonferroni‑corrected p‑values, significance flags).  
    - VIF table with any > 5.0 flags.  
    - “Confounding Limitation” paragraph for temporal proximity.  
    - Normality/Pearson/Spearman diagnostic note.  
    - Explicit “Significant” / “Non‑Significant” labeling.  
    - Associational (non‑causal) framing per spec Assumption 2.  
  - **Verification**: Unit test asserts presence of all required sections and correct rendering of significance flags.

- [ ] T010 [P] Write the methods/results account, quick‑start guide, and document the paper‑stage handoff (FR‑008, FR‑011)  
  - Populate `specs/001-network-centrality-sleep-synchrony/quickstart.md` with exact runnable commands (install, `python code/main.py`), expected outputs (`SubjectMetrics.csv`, `analysis_results.json`, `final_report.md`), and measured runtime/memory from `data/results/pipeline_complete.txt`.  
  - Write `specs/001-network-centrality-sleep-synchrony/methods.md` describing: data source (Sleep‑EDF via PhysioNet/MNE), preprocessing steps, theta/alpha coherence, centrality computation, PLI calculation, **Bonferroni‑corrected** Pearson/Spearman correlation methodology, VIF diagnostics, temporal‑proximity limitation, and honest reporting of null findings.  
  - Re‑run the documented workflow from `data/raw/` inputs; confirm all tests and artifact checks pass; capture outcome in `data/results/reproducibility_check.txt`.  
  - Document the paper‑stage handoff: list of artefacts handed to the paper pipeline (`analysis_results.json`, `correlation_table.csv`, `figures/*.png`, `final_report.md`).  
  - **Verification**: Re‑execution produces identical hashes for all listed artefacts; `reproducibility_check.txt` contains a success message.

---

## Phase 3: Alignment with Specification & Contracts

- [ ] T011 [P] Perform a final audit of the analysis contract and all generated results to ensure absolute alignment with Bonferroni requirements (FR‑007)  
  - Verify that `specs/001-investigating-the-impact-of-network-cent/contracts/analysis.schema.yaml` explicitly describes "Bonferroni-corrected p-value".  
  - Cross-reference `data/results/analysis_results.json` against the schema to ensure no "FDR" terminology persists in descriptions or values.  
  - **Verification**: Audit log confirms 100% alignment between Constitution VII, Spec FR-007, and the final schema.

- [ ] T012 [P] Ensure the implementation of `code/analysis.py` uses the Bonferroni correction defined in the updated schema (FR‑007)  
  - Replace any remaining reference to FDR in the code with a call to `bonferroni_correct`.  
  - Add a unit test confirming that for a known set of raw p‑values the Bonferroni‑adjusted values match the expected calculation (p_adj = p * n_tests).  
  - **Verification**: Unit test passes; static analysis shows no remaining FDR function calls.

- [ ] T013 [P] Align the sample‑size check with FR‑010 (halt with warning, not error)  
  - Confirm that `code/analysis.py::check_sample_size` logs a warning when `N < 30` and **skips** correlation computation while allowing the pipeline to continue to later steps (e.g., reporting the warning).  
  - Add an integration test that feeds a dataset with 20 subjects and expects the pipeline to emit the warning and produce no analysis results rather than raising an exception.  
  - **Verification**: Integration test passes; pipeline aborts analysis but completes without error when sample size is insufficient.

---

## Dependencies and requirement coverage

| Task | Depends on | Requirements covered |
|------|------------|----------------------|
| T001 | – | FR‑001, Constitution VII (Contract) |
| T002 | T001 | FR‑002, FR‑011 |
| T003 | T002 | FR‑003, FR‑004, FR‑005, FR‑009 |
| T004 | T003 | FR‑006, FR‑007 (Bonferroni), SC‑002, SC‑003 |
| T005 | T003 | FR‑001–FR‑005 at full scale, SC‑001 |
| T006 | T005 | FR‑006, FR‑007 (Bonferroni), FR‑010, FR‑012 |
| T007 | T006 | SC‑002, SC‑003, SC‑004, SC‑005, edge‑case collinearity |
| T008 | T007 | FR‑008, FR‑011 |
| T009 | T008 | FR‑008, FR‑011 |
| T010 | T008 | Reproducibility, documentation, paper handoff |
| T011 | T006 | FR‑007 (Final Audit) |
| T012 | T011 | FR‑007 (Implementation Alignment) |
| T013 | – | FR‑010 (Warning‑only behavior) |

Tasks T011‑T013 are parallelizable ([P]) once the core pipeline (T001‑T010) is in place. All data‑flow orderings are respected: verification tasks run after the computations they verify.  

**Compute note**: All methods (MNE filtering/ICA, NetworkX centrality, Pearson/Spearman correlation) are CPU‑tractable on the default free runner (2 vCPU, ≈ 7 GB RAM, ≤ 6 h). Data are processed subject‑by‑subject to keep peak memory < 4 GB. No synthetic data fallbacks are used; any real‑data fetch failure raises an exception, allowing the platform to retry on a verified source.