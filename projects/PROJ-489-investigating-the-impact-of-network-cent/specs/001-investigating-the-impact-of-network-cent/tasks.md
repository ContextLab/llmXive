# Tasks: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Input**: Design documents from `/specs/001-network-centrality-sleep-synchrony/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

## Task format
`- [ ] T### [P?] [USx?] description with exact artifact paths`  
- **[P]** – can run in parallel (different files, no data dependencies)  
- **[USx]** – user‑story label (US1, US2, US3)  

Each task lists its scientific requirement, concrete output, and an observable check. Indented continuation lines give additional detail.

---

### Phase 1: Project Foundations  

- [ ] T001 [P] Create project skeleton, environment, and logging infrastructure  
  - Create directories: `code/`, `data/raw/`, `data/processed/`, `data/metrics/`, `data/results/`, `tests/unit/`, `tests/integration/`, `reports/`.  
  - Write `code/requirements.txt` (pinned versions of `mne`, `statsmodels`, `networkx`, `scipy`, `pandas`, `numpy`, `pyedflib`).  
  - Add `code/config.yaml` with signal‑processing parameters (bandpass 0.5–45 Hz, ICA kurtosis > 5.0, theta 4–8 Hz, alpha 8–13 Hz, random‑seed).  
  - Implement `code/__init__.py` and a basic logger in `code/main.py`.  
  - Verify by running `python -c "import mne,statsmodels,networkx,scipy,pandas,numpy,pyedflib; print('OK')"` and checking that all directories exist.  

### Phase 2: User Story 1 – Data Acquisition & Pre‑processing (Priority P1)  

- [ ] T002 [US1] Implement end‑to‑end acquisition & preprocessing pipeline  
  - **Download**: `code/download.py::download_sleep_edf(output_dir='data/raw/')` using MNE‑Python’s `mne.datasets.sleep_physionet.fetch_data()`. Verify ≥30 subjects, store files in `data/raw/`, write checksum log `data/raw/download_log.txt`. On corrupted `.edf` log error, skip file (edge‑case handling).  
  - **Band‑pass filter**: `code/preprocess.py::apply_bandpass_filter(raw_signal, low=0.5, high=45.0)` → filtered arrays. Unit test verifies 10 Hz signal passes, 0.1 Hz & 100 Hz attenuated.  
  - **ICA artifact removal**: `code/preprocess.py::remove_ica_artifacts(filtered_signal, kurtosis_thr=5.0, power_ratio_thr=3.0)` → cleaned arrays. Unit test flags synthetic high‑kurtosis component.  
  - **Epoching**: `code/preprocess.py::epoch_by_sleep_stage(cleaned_signal, annotations, epoch_sec=30)` → `data/processed/epochs_{subject_id}.npz` and `data/processed/metadata_{subject_id}.json` (stage labels, night IDs). Unit test checks epoch shape and correct label mapping.  
  - **NaN validation**: `code/preprocess.py::validate_no_nans(signal_array)` → raises if any NaNs; logs status to `data/processed/validation_log.txt`.  
  - **Orchestration**: integrate steps in `code/main.py` (download → filter → ICA → epoch → validate). Run on a real 3‑subject subset; produce `data/processed/preprocessing_complete.txt` summarising subject count and NaN status. Integration test confirms all expected files exist.  

### Phase 3: User Story 2 – Metric Computation (Priority P2)  

- [ ] T003 [US2] Compute connectivity, centrality, synchrony, VIF, and aggregate per‑subject metrics  
  - **Connectivity**: `code/metrics.py::compute_connectivity_matrix(waking_signal, bands={'theta':(4,8),'alpha':(8,13)})` → symmetric matrices (values 0–1) saved as `data/processed/connectivity_{subject_id}_{band}.npy`. Unit test checks symmetry & range.  
  - **Centrality**: `code/metrics.py::compute_centrality_metrics(matrix)` → degree, betweenness, eigenvector arrays; validate on a synthetic star graph (tolerance 1e‑6).  
  - **Phase‑Lag Index**: `code/metrics.py::compute_pli(epoch_signal)` → mean global PLI per sleep stage (0–1). Unit test on synthetic phase‑locked signals.  
  - **VIF**: `code/metrics.py::compute_vif(centrality_dict)` → VIF values, flag >5.0; output `data/metrics/vif_report.json`. Unit test on correlated synthetic data.  
  - **Aggregation**: `code/metrics.py::aggregate_subject_metrics(...)` → one row per subject per stage, handling missing stages by omission. Output `data/metrics/SubjectMetrics.csv` conforming to `SubjectMetricsSchema`. Integration test loads CSV, verifies schema, numeric ranges, and that no required column is missing.  

### Phase 4: User Story 3 – Statistical Analysis & Reporting (Priority P3)  

- [ ] T004 [US3] Validate subject count (FR‑010)  
  - Load `data/metrics/SubjectMetrics.csv`; count distinct `subject_id`.  
  - If **N ≥ 30** → proceed; else **log warning** to `data/results/sample_size_warning.txt` **and abort further analysis** (no downstream files produced).  
  - Unit test confirms abort behaviour when N = 20.  

- [ ] T005 [US3] Normality testing & method selection (FR‑012)  
  - For each centrality metric × sleep‑stage × band pair, perform Shapiro‑Wilk test on the paired vectors (centrality values vs. PLI scores) using `scipy.stats.shapiro`.  
  - Record chosen method (`pearson` if p ≥ 0.05, else `spearman`) in `data/results/method_selection.csv`.  
  - Unit test validates correct method choice on synthetic normal and non‑normal data.  

- [ ] T006 [US3] Correlation computation (FR‑006)  
  - Using the method from T005, compute the correlation coefficient and raw two‑tailed p‑value for every metric‑stage‑band combination (3 metrics × 4 stages × 2 bands = 24 tests).  
  - Store results in `data/results/correlation_raw.csv` with columns: `metric_name, stage_label, band, method, correlation, p_value_raw`.  
  - Unit test checks that Pearson on perfectly correlated data yields 1.0 and p ≈ 0.  

- [ ] T007 [US3] Bonferroni correction (FR‑007)  
  - Apply Bonferroni correction across all 24 raw p‑values: `p_corrected = min(p_raw * 24, 1.0)`.  
  - Append `p_value_corrected` and `significant` (true if corrected < 0.05) to `data/results/correlation_corrected.csv`.  
  - Verify that every corrected p ≥ raw p and that the file contains the expected columns.  

- [ ] T008 [US3] JSON results report (FR‑008)  
  - Combine `correlation_corrected.csv`, `vif_report.json`, and the sample‑size flag into a single JSON document `data/results/analysis_report.json` matching `AnalysisResultSchema` (one entry per metric‑stage‑band).  
  - Include `global_connectivity_coefficient` set to the mean coherence value per subject (computed earlier in T003) and `covariate_used: true`.  
  - Unit test validates JSON against the schema.  

- [ ] T009 [US3] Human‑readable Markdown report (FR‑008)  
  - Generate `reports/final_report.md` containing:  
    * Sample size summary and any N < 30 warning.  
    * Table of correlation coefficients, raw & Bonferroni‑corrected p‑values, significance flags.  
    * VIF table highlighting any metric with VIF > 5.0.  
    * “Confounding Limitation” paragraph if any subject has `temporal_proximity == true` (from `SubjectMetrics.csv`).  
    * Diagnostic note that normality was assessed per pair (referencing `method_selection.csv`).  
  - Unit test checks that all required sections appear and that the significance flag is correctly rendered.  

- [ ] T010 [US3] Full pipeline execution & verification (Phase 4 end‑to‑end)  
  - Run `python code/main.py` on the **complete** pre‑processed dataset.  
  - Verify creation of: `data/metrics/SubjectMetrics.csv`, `data/results/correlation_corrected.csv`, `data/results/analysis_report.json`, `reports/final_report.md`, and `data/results/pipeline_complete.txt` (contains timestamp, runtime, and memory summary).  
  - Integration test asserts that runtime ≤ 4 h and peak RAM ≤ 4 GB on the CI runner.  

### Phase 5: Validation, Documentation & Handoff  

- [ ] T011 [P] Write reproducible quick‑start guide and perform reproducibility check  
  - Create `specs/001-network-centrality-sleep-synchrony/quickstart.md` with step‑by‑step commands to clone the repo, install requirements, and run the pipeline (`python code/main.py`).  
  - In a fresh temporary environment, execute the quick‑start; capture success/failure in `data/results/reproducibility_check.txt`.  
  - Ensure the guide lists expected outputs (`SubjectMetrics.csv`, `analysis_report.json`, `final_report.md`) and the estimated runtime/memory (matching SC‑002 & SC‑003).  

- [ ] T012 [P] Consolidate methods documentation  
  - Populate `specs/001-network-centrality-sleep-synchrony/methods.md` with a concise description of: data source (Sleep‑EDF via PhysioNet), preprocessing steps, connectivity & centrality calculations, PLI computation, normality testing, correlation approach, Bonferroni correction, VIF diagnostics, and temporal‑proximity limitation.  
  - Include citations to MNE‑Python, NetworkX, and the statistical textbooks used.  
  - Link to the actual code files and output artefacts for traceability.  

- [ ] T013 [P] Archive data‑model summary  
  - Ensure `specs/001-network-centrality-sleep-synchrony/data-model.md` accurately reflects all entities (`Subject`, `WakingNetwork`, `SleepStageEpoch`, `SubjectMetrics`, `AnalysisResult`) and matches the schemas in `contracts/`.  
  - Add a short diagram (ASCII or mermaid) showing data flow from raw EDF → processed epochs → metrics CSV → analysis JSON.  

---

## Dependencies & Execution Order  

| ID   | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T002 |
| T004 | T003 |
| T005 | T004 |
| T006 | T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T009 |
| T011 | T010 |
| T012 | T011 |
| T013 | T012 |

Parallel opportunities are indicated by the **[P]** flag (e.g., environment setup vs. data download). All data‑flow dependencies are respected so that each downstream task receives the artefacts produced by its prerequisites.

--- 

### Success‑Criteria Verification Table  

| Task | Requirement | Observable Check | Output |
|------|-------------|------------------|--------|
| T001 | Project skeleton (FR‑001 provenance) | All directories exist; `requirements.txt` imports succeed | – |
| T002 | Download & preprocessing (FR‑001‑FR‑002) | ≥30 subjects in `data/raw/`; no NaNs; epoch counts reasonable | `data/processed/preprocessing_complete.txt` |
| T003 | Metric computation (FR‑003‑FR‑005‑FR‑009) | `SubjectMetrics.csv` with ≥3 rows, all numeric columns populated, values in expected ranges | `data/metrics/SubjectMetrics.csv` |
| T004 | Sample‑size rule (FR‑010) | Warning file created and pipeline aborts when N < 30 | `data/results/sample_size_warning.txt` |
| T006 | Correlation (FR‑006) | CSV with 24 rows, coefficients & raw p‑values present | `data/results/correlation_raw.csv` |
| T007 | Bonferroni (FR‑007) | Corrected p‑values ≥ raw, significance flag added | `data/results/correlation_corrected.csv` |
| T008 | JSON report (FR‑008) | JSON validates against `AnalysisResultSchema` | `data/results/analysis_report.json` |
| T009 | Markdown report (FR‑008) | Sections for sample size, table of results, VIF, limitation, diagnostics present | `reports/final_report.md` |
| T010 | Full pipeline (SC‑002‑SC‑003) | Runtime < 4 h, RAM < 4 GB, all final artefacts created | `data/results/pipeline_complete.txt` |
| T011 | Quick‑start reproducibility (SC‑004) | Fresh run succeeds, `reproducibility_check.txt` logs success | `data/results/reproducibility_check.txt` |

--- 

**Note**: All tasks are designed to run on the default CPU‑only CI runner (2 vCPU, ~7 GB RAM, ≤6 h). No GPU resources are required. Real Sleep‑EDF data is fetched directly from PhysioNet; no synthetic fall‑backs are used. Edge‑case handling (missing sleep stages, corrupted files, collinearity) is explicitly coded and tested.
