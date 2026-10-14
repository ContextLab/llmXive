# Tasks: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics  

**Input**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, contracts, and existing artifacts.  
All paths are relative to the repository root.

---

## Phase 1 – Project scaffolding (already completed)

- [ ] T001 Create the required directory hierarchy  
  `data/raw/`, `data/processed/`, `data/results/`, `code/`, `tests/`.

- [ ] T002 Add a runnable **quickstart** guide (`specs/001‑neural‑correlates‑of‑simulated‑social‑ex/quickstart.md`) that documents the end‑to‑end command line.

- [ ] T003 Publish the immutable data‑model (`specs/001‑neural‑correlates‑of‑simulated‑social‑ex/data‑model.md`).

---

## Phase 2 – Core utilities & configuration (foundational)

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
| - | - | - | All tasks in this phase must be finished before any user‑story work can start. |

- [ ] T004 Implement `code/exceptions.py` defining `DataUnavailableError` and `InsufficientSubjectsError` (used throughout the pipeline).

- [ ] T005 **[P]** `code/utils.py` – utility library.  
  - `load_config(config_path: str) → dict` – loads a YAML file.  
  - `get_seed(key: str = "default") → int` – returns a reproducible seed (default = 42).  
  - `ensure_dir(path: str) → None` – creates missing directories.  

- [ ] T006 **[P]** `config.yaml` – central configuration (project‑wide). Must contain:  
  ```yaml
  motion_threshold: 0.2          # mm, per FR‑002 & spec
  dmn_rois:
    - PCC
    - mPFC
    - L_ANG
    - R_ANG
  sliding_window:
    length_sec: 30
    step_sec: 5
  permutation:
    n_iter: 10000
  random_seed: 42
  ```  

- [ ] T007 **[P]** `code/integrity.py` – checksum utility that computes a SHA‑256 hash for any file and writes it to `state/projects/PROJ‑474‑neural‑correlates‑social‑ex.yaml` under `artifact_hashes`. All artifact‑creation tasks must call this function after writing a file.

- [ ] T008 **[P]** `tests/conftest.py` – pytest configuration that pins the global random seed (`config.yaml → random_seed`) for reproducible test runs.

---

## Phase 3 – User Story 1: Data ingestion & quality control (US‑1)

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
| - | - | - | These tasks consume the raw OpenNeuro dataset and produce a vetted subject list. |

- [ ] T009 **[P]** `code/data_loader.py` – download the **verified** Cyberball dataset `ds000030` from `https://openneuro.org/datasets/ds000030`. Implements exponential back‑off (1 s → 2 s → 4 s) with up to three attempts; on permanent failure raises `DataUnavailableError` with code `ERR_DATA_UNAVAILABLE`. Writes the extracted BIDS tree to `data/raw/ds000030/`.

- [ ] T010 **[P]** `code/qc.py` – compute mean framewise displacement (FD) for each subject from the standard BIDS `*_confounds.tsv`. Writes per‑subject CSV files `data/processed/fd_{subject_id}.csv`.

- [ ] T011 **[P]** `code/qc.py` – verify that each subject’s `events.tsv` contains **both** “Inclusion” and “Exclusion” trial types. If a subject is missing either, record an error and raise `DataUnavailableError` with code `101897695`.

- [ ] T012 **[P]** `code/qc.py` – filter subjects: keep only those with `mean FD ≤ 0.2 mm` **and** with valid event markers.  
  - Output `data/processed/subjects_metadata.json` (list of retained subjects with fields `subject_id`, `motion_mean`, `condition_status`, `retained`).  
  - Output `data/processed/qc_report.json` (summary counts of retained vs. excluded).  
  - If the retained count **< 10**, raise `InsufficientSubjectsError` with error code `101897696`.  

- [ ] T013 **[P]** `code/main_us1.py` – orchestrator that runs T009 → T010 → T011 → T012 in order, handling exceptions and exiting with the appropriate error codes. Produces the final QC artifacts described above.

- **Tests** (optional but recommended)  
  - `tests/unit/test_qc_motion.py` – asserts that a subject with mean FD > 0.2 mm is excluded.  
  - `tests/unit/test_qc_events.py` – asserts that missing “Inclusion” or “Exclusion” markers trigger error 101897695.  
  - `tests/unit/test_qc_subject_count.py` – asserts that < 10 retained subjects raise error 101897696.

---

## Phase 4 – Confound regression (new step required by the plan)

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
| - | - | - | Nuisance regression must be applied before any ROI extraction. |

- [ ] T014 **[P]** `code/confound_regression.py` – for each retained subject:  
  1. Load the raw 4‑D NIfTI (`data/raw/ds000030/sub‑*/func/*_bold.nii.gz`) with `nibabel` `mmap=True`.  
  2. Load motion parameters and their first‑order derivatives from `*_confounds.tsv`.  
  3. Extract WM and CSF signals using masks derived from the Harvard‑Oxford atlas (via `nilearn`).  
  4. Perform linear regression of the six motion parameters + derivatives + WM + CSF + global signal from the voxel‑wise time‑series.  
  5. Write the cleaned 4‑D image to `data/processed/preprocessed_{subject_id}.nii.gz` and invoke `code/integrity.py` to record its checksum.

---

## Phase 5 – ROI time‑series extraction (part of US‑1 & US‑2)

- [ ] T015 **[P]** `code/roi_extractor.py` – using the Harvard‑Oxford cortical atlas, extract mean BOLD signals for the four DMN ROIs (`PCC`, `mPFC`, `L_ANG`, `R_ANG`) from the **preprocessed** images produced by T014.  
  - Output per‑subject, per‑condition CSV files: `data/processed/timeseries_{subject_id}_{condition}.csv` (columns: `timepoint`, `PCC`, `mPFC`, `L_ANG`, `R_ANG`).  

- **Test** `tests/unit/test_roi_extractor.py` – checks that the extractor returns four columns with matching lengths to the original TR count.

---

## Phase 6 – Connectivity metric computation (US‑2)

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
| - | - | - | Static and dynamic functional connectivity are derived from the ROI time‑series. |

- [ ] T016 **[P]** `code/connectivity_static.py` – for each subject and condition:  
  1. Load the corresponding time‑series CSV (from T015).  
  2. Compute a 4 × 4 Pearson correlation matrix (including self‑correlations).  
  3. Store the matrix as JSON `data/processed/connectivity_{subject_id}_{condition}.json`.  

- [ ] T017 **[P]** `code/connectivity_strength.py` – compute the **mean absolute correlation** across the three unique ROI‑pair edges (PCC‑mPFC, PCC‑L_ANG, PCC‑R_ANG, mPFC‑L_ANG, mPFC‑R_ANG, L_ANG‑R_ANG → 6 edges, but the spec defines three ROI‑pair edges; we follow the spec’s “three edges” by averaging the three *unique* pairs among the four nodes).  
  - Output per‑subject strength JSON `data/processed/strength_{subject_id}.json` with fields `inclusion`, `exclusion`, and `difference` (exclusion – inclusion).  

- [ ] T018 **[P]** `code/dynamic_connectivity.py` – sliding‑window analysis (30 s window, 5 s step):  
  1. Convert window length and step from seconds to TRs using the subject’s `tr` value (from the BIDS JSON side‑car).  
  2. For each window, compute the Pearson correlation matrix and then the mean absolute correlation across the three edges.  
  3. Produce a time‑resolved series CSV `data/processed/dynamic_{subject_id}_{condition}.csv` (columns: `window_center_sec`, `strength`).  
  4. Apply Benjamini‑Hochberg FDR correction across all windows **within a subject** and store corrected p‑values in the same CSV (`fdr_corrected_p`).  

- **Tests**  
  - `tests/unit/test_connectivity_static.py` – verifies that a synthetic time‑series with known correlation yields the expected matrix.  
  - `tests/unit/test_dynamic_connectivity.py` – checks windowing logic and that the number of windows matches the expected count for a given TR series length.

---

## Phase 7 – Statistical hypothesis testing & visualisation (US‑3)

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
| - | - | - | All statistical inference must obey FR‑006, FR‑016 and produce the required figures. |

- [ ] T019 **[P]** `code/stats.py` – paired permutation test (10 000 permutations) on the per‑subject **strength difference** values from T017. Returns: two‑tailed p‑value, Cohen’s d, 95 % confidence interval, and the full null‑distribution array. Also runs **edge‑wise** paired permutation tests for each of the three ROI edges and applies Benjamini‑Hochberg FDR correction (q ≤ 0.05). Outputs a consolidated JSON `results/statistical_result.json` matching `contracts/result_schema.schema.yaml`.

- [ ] T020 **[P]** `code/visualization.py` – generate the following PNGs in `results/figures/`:  
  1. `null_distribution.png` – histogram of the permutation null distribution (global MAC test).  
  2. `strength_difference_bar.png` – bar plot of the observed mean difference with 95 % CI error bars.  
  3. `heatmap_inclusion.png` & `heatmap_exclusion.png` – ROI‑wise correlation‑matrix heatmaps (colorbars, axis labels).  

- [ ] T021 **[P]** `code/main_us3.py` – orchestrator that loads `strength_{subject_id}.json`, runs T019, calls T020, and writes a human‑readable markdown report `results/report.md` summarising: number of subjects, motion threshold used, p‑value, effect size, CI, edge‑wise corrected p‑values, and embeds the generated figures. The report must contain the literal word **“associational”** (per FR‑016).

- **Test** `tests/integration/test_full_analysis.py` – runs the entire pipeline on a tiny synthetic subset (e.g., two subjects with 10 TRs) and checks that `results/statistical_result.json` contains the required fields and that `results/report.md` mentions “associational”.

---

## Phase 8 – Sensitivity analysis across motion thresholds (SC‑005)

- [ ] T022 **[P]** `code/sensitivity_analysis.py` – loop over motion thresholds `[0.2, 0.3, 0.4, 0.5]` mm:  
  1. Re‑apply the QC filter from T012 using the current threshold (no re‑download).  
  2. For each threshold, recompute static strength metrics (reuse T016–T017) and run a **paired permutation test** (5 000 permutations for speed).  
  3. Record `{threshold, n_retained, p_value, effect_size}` rows in `results/sensitivity_curve.csv`.  
  4. Produce a line plot `results/figures/sensitivity_curve.png` (p‑value vs. motion threshold).  

- **Test** `tests/unit/test_sensitivity_analysis.py` – verifies that the CSV contains four rows and that thresholds are correctly ordered.

---

## Phase 9 – Paper‑stage handoff

- [ ] T023 **[P]** `results/methods_and_results.md` – concise methods & results narrative automatically generated from the JSON/CSV artifacts (uses Jinja2 templating). Links to all figures and reports the exact number of retained subjects, motion threshold, and the “associational” framing.

---

## Dependency & Execution Order Summary

| Phase | Must finish before |
|-------|--------------------|
| 1 – Scaffolding | – |
| 2 – Utilities & config | Phase 1 |
| 3 – US‑1 (download → QC) | Phase 2 |
| 4 – Confound regression | Phase 3 (needs retained subjects) |
| 5 – ROI extraction | Phase 4 |
| 6 – Connectivity (static + dynamic) | Phase 5 |
| 7 – Statistics & visualisation | Phase 6 |
| 8 – Sensitivity analysis | Phase 7 (uses same code, can run in parallel after stats are verified) |
| 9 – Paper handoff | Phase 8 (final artefacts ready) |

All tasks marked **[P]** can be executed in parallel **once their declared dependencies are satisfied**. Tasks without the **[P]** flag must run sequentially as listed.

---  

*All scientific requirements from `spec.md` and `plan.md` are covered, the motion‑threshold is correctly set to **0.2 mm**, real OpenNeuro data are used, and every step is CPU‑only and streaming‑friendly.*
