# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

**Inputs**: `spec.md`, `plan.md`, existing code skeleton under `src/`, data‑model contracts in `specs/001‑investigating‑the‑relationship‑between‑b/contracts/`.

The checklist below implements every functional requirement (FR‑001 – FR‑008) and success‑criteria (SC‑001 – SC‑004).  Tasks are ordered so that each downstream step has its inputs ready.  All artifacts are written under the project‑owned directories `data/`, `figures/`, `code/`, `tests/`, or `docs/`.

---

- [ ] **T001 [P1] [US1]** Download the verified OpenNeuro fMRI datasets (ds000246 and, if needed, ds001600) containing musical improvisation and scripted runs.   <!-- FAILED-IN-EXECUTION: code/download_openneuro.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_openneuro.py exit=1 -->
  *Artifact path*: `data/raw/openneuro/ds000246/` (and `data/raw/openneuro/ds001600/` if available).  
  *Verification*:  
  &nbsp;&nbsp;• After download, a `manifest.json` in the dataset folder lists all subject IDs and must contain the columns `subject_id`, `run_label`, `age`, `years_training`, `fd`.  
  &nbsp;&nbsp;• SHA‑256 checksums for every downloaded file are recorded in `data/raw/checksums.json`.  
  &nbsp;&nbsp;• `pytest tests/test_download.py` asserts that at least 20 subjects are present and that each subject has at least one “Improv” and one “Scripted” run.

- [ ] **T002 [P1] [US2]** Preprocess each subject’s fMRI volumes on a CPU‑only runner using Nipype wrappers for **FSL** (MCFLIRT, slicetimer, FLIRT) and **AFNI** (3dBandpass).  Extract Schaefer‑100 ROI time‑series with Nilearn.  
  *Artifact paths*:  
  &nbsp;&nbsp;• Preprocessed NIfTI → `data/preprocessed/nifti/<subject_id>_preproc.nii.gz`  
  &nbsp;&nbsp;• ROI time‑series CSV → `data/preprocessed/timeseries/<subject_id>_timeseries.csv`  
  *Verification*:  
  &nbsp;&nbsp;• Motion‑correction reduces mean frame‑wise displacement (FD) to < 0.5 mm for > 80 % of volumes; values are stored in `logs/motion_<subject_id>.txt`.  
  &nbsp;&nbsp;• Band‑pass filter (0.01–0.1 Hz) applied – frequency range logged.  
  &nbsp;&nbsp;• Each CSV has dimensions `(timepoints × 100)` and passes the `preprocessed_timeseries.schema.yaml` contract (`pytest tests/test_preprocess.py`).

- [ ] **T008 [P1] [US8]** Implement **quality‑control & exclusion logic**:  
  • Flag any subject with mean FD > 0.5 mm for > 20 % of volumes → exclude from all downstream analyses.  
  • Detect missing `run_label` entries; abort with a clear error message directing the user to provide manual labels or switch to the “years_training” proxy.  
  *Artifact path*: `logs/exclusion_log.txt` (lists excluded subject IDs and reasons).  
  *Verification*:  
  &nbsp;&nbsp;• The exclusion log is consulted by tasks T003–T005; unit test `tests/test_qc.py` confirms that excluded subjects do not appear in `data/metrics/` or `data/pca/`.

- [ ] **T003 [P2] [US3]** Compute sliding‑window functional connectivity for each subject using a rectangular window (default 45 s, step 10 s) with **Pearson correlation** followed by **Ledoit‑Wolf** shrinkage.  Derive per‑window graph metrics (global efficiency, modularity via Louvain, participation coefficient) with NetworkX.  
  *Artifact path*: `data/metrics/<subject_id>_metrics.csv` (conforms to `network_metrics.schema.yaml`).  
  *Verification*:  
  &nbsp;&nbsp;• Each row contains `subject_id`, `window_id`, `global_efficiency`, `modularity`, `participation_coefficient`.  
  &nbsp;&nbsp;• Minimum 30 time‑points per window is enforced; windows with fewer points are skipped and logged.  
  &nbsp;&nbsp;• `pytest tests/test_connectivity.py` validates metric ranges and schema compliance.

- [ ] **T004 [P2] [US4]** Perform **Principal Component Analysis** on the stacked metric matrix (all subjects × all windows).  Retain enough components to explain ≥ 80 % of variance and output per‑subject PC scores.  
  *Artifact path*: `data/pca/pca_scores.csv` (schema `pca_scores.schema.yaml`).  
  *Verification*:  
  &nbsp;&nbsp;• Cumulative variance explained column in `logs/pca_explained_variance.txt` meets the 80 % threshold.  
  &nbsp;&nbsp;• Scores file contains columns `subject_id`, `pc_1`, `pc_2`, … up to the retained component count.  
  &nbsp;&nbsp;• `pytest tests/test_pca.py` checks orthogonality and variance capture.

- [ ] **T005 [P2] [US5]** Run the primary **regression / correlation analysis**:  
  `PC_score ~ task_condition + years_training + age + fd` (task_condition is Improvisation vs Scripted).  
  Use **5 000 permutations** to generate raw p‑values, then apply **FDR correction** across all tested PCs.  
  *Artifact path*: `data/results/regression_results.csv` (schema `regression_results.schema.yaml`).  
  *Verification*:  
  &nbsp;&nbsp;• Each row includes `pc`, `coefficient`, `raw_p`, `fdr_p`, `significance`.  
  &nbsp;&nbsp;• At least one PC with `significance == true` and `fdr_p < 0.05` satisfies **SC‑001**; if none, the null‑result flag is recorded and still passes verification.  
  &nbsp;&nbsp;• `pytest tests/test_regression.py` confirms that permutation distribution is correctly built and that the FDR procedure uses the Benjamini‑Yekutieli method.

- [ ] **T006 [P3] [US6]** Conduct a **sensitivity analysis** sweeping sliding‑window size over {30 s, 45 s, 60 s} and step size over {5 s, 10 s}.  For each parameter pair, repeat tasks T003–T005 and record the resulting regression coefficient for the primary PC.  
  *Artifact path*: `data/sensitivity/sensitivity_summary.csv` (columns: `window_sec`, `step_sec`, `pc`, `coefficient`, `fdr_p`).  
  *Verification*:  
  &nbsp;&nbsp;• The summary table contains exactly 6 rows (3 window × 2 step).  
  &nbsp;&nbsp;• Variation (range) of the primary coefficient is reported in `logs/sensitivity_variation.txt`.  
  &nbsp;&nbsp;• `pytest tests/test_sensitivity.py` asserts that every run completed without error and that all intermediate metric files were cleaned up after aggregation.

- [ ] **T007 [P3] [US7]** Generate **network topology visualizations** comparing high‑skill (top 33 % years_training) vs. low‑skill (bottom 33 % years_training) groups.  Build mean adjacency matrices per group, threshold at the 75th percentile, and plot graphs with **NetworkX** (edge‑weight colormap) and **Matplotlib**.  
  *Artifact paths*:  
  &nbsp;&nbsp;• Figure of high‑skill graph → `figures/network_high_skill.png`  
  &nbsp;&nbsp;• Figure of low‑skill graph → `figures/network_low_skill.png`  
  &nbsp;&nbsp;• Supporting data → `data/visualization/mean_adj_high.npy`, `data/visualization/mean_adj_low.npy`  
  *Verification*:  
  &nbsp;&nbsp;• Both PNGs load without error and contain a legend indicating edge weight.  
  &nbsp;&nbsp;• `pytest tests/test_visualization.py` checks that the adjacency matrices have shape (100, 100) and that node labels correspond to the Schaefer atlas.

- [ ] **T009 [P?] [US9]** Create a **reproducible end‑to‑end command** and document it in `docs/quickstart.md`.  The command runs the full pipeline on a single subject (e.g., `sub-01`) and produces the minimal set of outputs (`timeseries`, `metrics`, `pca_scores`, `regression_results`).  
  *Artifact path*: `docs/quickstart.md` (includes exact CLI invocation).  
  *Verification*:  
  &nbsp;&nbsp;• Running the documented command on the CI runner completes in **< 30 min** and produces the expected files under `data/quickstart/`.  
  &nbsp;&nbsp;• `pytest tests/test_quickstart.py` asserts that the command returns exit code 0, that `regression_results.csv` is present, and that the measured wall‑clock time (recorded in `logs/quickstart_runtime.txt`) is < 30 min.

- [ ] **T010 [P?] [US10]** Add **automated test suite** covering download, preprocessing, connectivity, PCA, regression, sensitivity, visualization, and QC.  Place tests under `tests/` and ensure they are executed by the CI workflow.  
  *Artifact path*: `tests/` (Python `pytest` modules).  
  *Verification*:  
  &nbsp;&nbsp;• CI run reports **all** tests passing (`0 failures`).  
  &nbsp;&nbsp;• Coverage report (`pytest --cov=code`) shows ≥ 85 % line coverage across `code/` modules.

- [ ] **T011 [P?] [US11]** **Performance monitoring**: run the full pipeline on a representative subset (e.g., 5 subjects) and record total wall‑clock time and peak RAM usage. Verify that total runtime ≤ 6 h and peak memory ≤ 7 GB, satisfying **SC‑004**.  
  *Artifact path*: `logs/performance_metrics.txt` (records `runtime_seconds` and `peak_ram_gb`).  
  *Verification*:  
  &nbsp;&nbsp;• A CI step parses `performance_metrics.txt` and fails if `runtime_seconds` > 21600 or `peak_ram_gb` > 7.0.  
  &nbsp;&nbsp;• `pytest tests/test_performance.py` checks that the file exists and that the recorded metrics are within the specified limits.

---

### Dependency & Requirement Mapping

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001 | T001 |
| FR‑002 | T002 |
| FR‑003 | T003 |
| FR‑004 | T005 |
| FR‑005 | T005 |
| FR‑006 | T006 |
| FR‑007 | T007 |
| FR‑008 | T004 |
| SC‑001 | T005 (FDR‑corrected p < 0.05) |
| SC‑002 | T006 (robustness across windows/steps) |
| SC‑003 | T005 (FDR control) |
| SC‑004 | T011 (runtime & RAM verification) |

All tasks are unchecked (`[ ]`) pending implementation.  Once a task is completed and its verification passes, the CI will automatically check the box.  This checklist provides the smallest complete study that fulfills the specification while remaining feasible on the free‑tier GitHub Actions runner.