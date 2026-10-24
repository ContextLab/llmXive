# Tasks: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and any existing code/tests.  
All result artifacts must live under the project‑owned directories `data/`, `code/`, `results/`, or `specs/`.  
The pipeline is organized into three research phases; tasks are ordered to respect data flow and the functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑004).

---

## Phase 1 – Setup and first end‑to‑end analysis  

*Goal*: Verify that a minimal real‑data run works before scaling to the full cohort.

- [ ] **T001** [US1] Implement the Reference‑Validator and robust dataset download module.   <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 -->
  *File*: `code/verify_references.py` (functions `verify_dataset_id()`, `verify_conditions()`, `verify_citations()`) and `code/download.py`.  
  - `verify_dataset_id()` checks that the requested OpenNeuro ID equals **ds004510** and that the URL resolves; on mismatch it raises a `DatasetIDError` with a clear message (FR‑012 (1)).  
  - `download.py` invokes `verify_dataset_id()`, then streams the full OpenNeuro ds004510 BIDS files via `curl`/`wget` (FR‑001). It writes each file under `data/raw/` and computes a SHA‑256 checksum, storing the mapping in `data/raw/checksums.json`.  
  - After a successful download, the script **updates the project state file** `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` with a top‑level `artifact_hashes` map (file path → checksum) and an `updated_at` timestamp, thereby satisfying FR‑013.  
  - The download command accepts an optional `--subjects N` flag for the minimal end‑to‑end run; when omitted it downloads **all** subjects. Errors (network failure, missing files) raise exceptions that terminate the run; no synthetic fallback is provided.  
  - After download of the selected subset, `verify_conditions()` parses each subject’s `events.tsv` to confirm that both `simple` and `complex` values appear in the `condition_label` column; if `complex` is missing the script raises `DatasetConditionError` and halts with the exact FR‑008 message.  
  - `verify_citations()` (stub for later) records verified citation status in `data/results/citation_verification.json`.  
  - **Check**: `python code/verify_references.py --stage dataset` returns 0 for the correct ID; `python code/download.py --subjects 2` returns 0, creates `data/raw/` BIDS files, `data/raw/checksums.json`, and updates the state YAML; condition verification passes.

- [ ] **T002** [US1] Implement the preprocessing pipeline.  
  *File*: `code/preprocess.py`.  
  - Load each subject’s raw EEG (`mne.io.read_raw_*`) from `data/raw/`.  
  - Apply a **1–40 Hz FIR zero‑phase band‑pass filter** (FR‑002).  
  - Perform ICA (`n_components=0.99`, `random_state=42`), automatically detect EOG/ECG components via `mne.preprocessing.find_bads_eog`/`find_bads_ecg`, reject any component explaining > 99 % variance, and reconstruct the signal (FR‑002).  
  - Re‑reference to the average of mastoid electrodes `TP9`/`TP10`.  
  - Interpolate missing channels if < 10 % of the cap is absent (spherical splines).  
  - Epoch the continuous data from **‑200 ms to 500 ms** around stimulus onsets, baseline‑correct using the pre‑stimulus interval (‑200 ms → 0 ms) (FR‑003).  
  - Label epochs by `condition_label` (simple / complex) and `stimulus_type` (standard / deviant) from `events.tsv`.  
  - Exclude any subject with > 50 % rejected epochs; log exclusions to `data/processed/exclusions.csv`.  
  - Hard‑stop if any NaNs remain (`np.isnan(epochs.get_data()).any()` → abort).  
  - Save per‑subject preprocessed epochs to `data/processed/sub-XX_epochs.fif`.  
  - **Check**: Running on the T001 subset creates epoch files with the correct time window, no NaNs, and an updated exclusions log.

- [ ] **T003** [US1][US2] Compute per‑subject MMN metrics and define a per‑subject schema.  
  *Files*: `code/analysis.py` (per‑subject mode) and `specs/001-neural-correlates-of-temporal-prediction/contracts/metrics_per_subject.schema.yaml`.  
  - For each subject, each fronto‑central electrode (`Fz, FCz, Cz, F3, F4, FC3, FC4`) compute:  
    * **Amplitude difference** = mean voltage (deviant − standard) within **150–250 ms**.  
    * **Latency difference** = time of maximal difference within the same window.  
    * **Noise floor** = **standard deviation** of the pre‑stimulus baseline (‑200 ms → 0 ms).  
    * **SNR** = |amplitude| / baseline SD; `signal_validity = SNR ≥ 3.0` (FR‑011, SC‑001).  
  - Output a CSV `data/results/metrics_per_subject.csv` with columns: `subject_id, condition_label, electrode, amplitude_diff, latency_diff, snr_ratio, signal_validity`.  
  - Create `metrics_per_subject.schema.yaml` that enforces: required fields `subject_id, condition_label, electrode, amplitude_diff, latency_diff, snr_ratio, signal_validity`; enums for `condition_label`; boolean for `signal_validity`; numeric constraints (finite, non‑NaN).  
  - **Check**: The CSV contains real numbers (no placeholders), all rows pass validation against the new schema, and the script runs on the T001/T002 subset.

---

## Phase 2 – Complete the study and validate its evidence  

*Goal*: Process the full cohort, perform group‑level statistics, and verify all contracts.

- [ ] **T004** [US2] Scale the pipeline to the full ds004510 cohort and generate the canonical MMN topography template (leave‑one‑out).  
  *Files*: `code/download.py` (full‑cohort mode), `code/preprocess.py` (iterative), `code/analysis.py` (template mode).  
  - Download **all** subjects iteratively (memory‑mapped, one subject at a time) into `data/raw/`.  
  - Preprocess each subject as in T002, saving epochs to `data/processed/`.  
  - For every subject, compute the **deviant − standard** topography (average voltage across the 150–250 ms window) for the **simple** condition.  
  - Build a **leave‑one‑out (LOO) canonical template** by averaging these topographies across *all other* subjects; save the resulting vector to `data/templates/canonical_mmn_loo.npy` and the corresponding channel order to `data/templates/canonical_mmn_channels.json`.  
  - Append the full‑cohort rows to `data/results/metrics_per_subject.csv`.  
  - **Check**: The CSV now contains entries for every non‑excluded subject; the LOO template file exists, its length matches the number of channels in the montage, and the channel‑order JSON is present.

- [ ] **T005a** [US2] Perform group‑level statistical testing (paired t‑tests, FDR, effect size).  
  *File*: `code/analysis.py` (group mode).  
  - Load `metrics_per_subject.csv`.  
  - For each electrode, conduct a **paired t‑test** comparing MMN amplitude between the simple and complex conditions (FR‑005).  
  - Apply **Benjamini‑Hochberg FDR** correction across the electrode set (SC‑002).  
  - Compute **Cohen’s d** for the paired differences.  
  - Load the literature benchmark from `data/benchmarks/mmn_effect_sizes.json` (which contains `{ "medium_effect_d": 0.5 }`) and flag `practical_significance = (d ≥ 0.5)` (FR‑010, SC‑003).  
  - Write an intermediate results file `data/results/stats_intermediate.csv` containing per‑electrode `t_statistic, p_value, p_value_fdr, cohen_d, benchmark_reference, practical_significance, significant`.  
  - Additionally compute the **mean latency difference** across subjects for each electrode and include it as `latency_diff` for later aggregation.  
  - **Check**: The CSV contains real statistics (no NaNs), FDR‑corrected p‑values, and the practical‑significance flag.

- [ ] **T005b** [US2] Compute topographic validation, enforce SC‑004, and produce the final cohort‑level output files that fully comply with `contracts/output.schema.yaml`.  
  *Files*: `code/analysis.py` (final mode) and `data/results/metrics.csv`, `data/results/stats.json`.  
  - Load the LOO canonical template (`canonical_mmn_loo.npy` + channel order).  
  - For each subject and each condition, compute the Pearson **r** between the observed MMN topography (deviant − standard, 150–250 ms) and the LOO template.  
    * Tag `validation_type = "consistency_simple"` for the simple condition and `validation_type = "validity_complex"` for the complex condition.  
    * **Enforce**: if any `r < 0.8` the script logs the subject ID, condition, and r‑value and raises a `TopographyThresholdError`, causing the pipeline to abort (fulfills SC‑004).  
  - Aggregate per‑subject metrics to group‑level values: for each electrode compute the mean `amplitude_diff`, mean `latency_diff`, mean `snr_ratio`, and import the group‑level `t_statistic`, `p_value_fdr`, `cohen_d` from T005a.  
  - Populate **all required fields** for the output schema:  
    `metric_id` (UUID), `condition_label`, `electrode`, `amplitude_diff`, `latency_diff`, `window_start` (150), `window_end` (250), `snr_ratio`, `signal_validity`, `t_statistic`, `p_value`, `p_value_fdr`, `cohen_d`, `benchmark_reference` (`data/benchmarks/mmn_effect_sizes.json`), `practical_significance`, `validation_type`, `topographic_correlation`, `significant`.  
  - Write `data/results/metrics.csv` (CSV) and `data/results/stats.json` (JSON array) such that every row validates against `contracts/output.schema.yaml`.  
  - **Check**: both files pass `jsonschema` validation; any topographic r‑value below 0.8 aborts the run.

- [ ] **T006** [P] Implement comprehensive contract tests.  
  *File*: `code/tests/test_contracts.py`.  
  - Use `jsonschema` to validate:  
    1. Each row of `data/results/metrics_per_subject.csv` against `metrics_per_subject.schema.yaml`.  
    2. Each row of `data/results/metrics.csv` and each object in `data/results/stats.json` against `output.schema.yaml`.  
    3. The dataset metadata (subject‑level JSON generated from BIDS) against `dataset.schema.yaml`.  
  - Extend tests to verify that every row in `metrics.csv` contains the required fields `latency_diff`, `window_start`, `window_end`, `t_statistic`, `p_value`, `cohen_d` (in addition to previously checked fields).  
  - Include focused unit tests for:  
    * Correct MMN window extraction (150–250 ms).  
    * SD‑based SNR computation.  
    * Benjamini‑Hochberg FDR implementation.  
  - **Check**: `pytest -q code/tests/` exits with 0; any schema violation or logical error fails the suite.

- [ ] **T007** [US3] Generate publication‑quality visualizations.  
  *File*: `code/visualize.py`.  
  - **ERP plot**: average standard and deviant waveforms for each condition, overlay the 150–250 ms MMN window, save as `data/results/figures/erp_simple.png` and `erp_complex.png` (PNG + SVG).  
  - **Scalp topography maps**: for the 150–250 ms window, plot the MMN difference topography for simple and complex conditions; save as `topography_simple.png` and `topography_complex.png`.  
  - **Significance heatmap**: electrode‑wise FDR‑corrected p‑values and Cohen’s d visualized on a scalp map; save as `significance.png`.  
  - All figures must be generated from the real data files (`metrics_per_subject.csv`, `metrics.csv`, `stats.json`) with no synthetic curves.  
  - **Check**: All PNG/SVG files exist, open without error, and visually reflect the underlying data.

---

## Phase 3 – Reproducible results, verification gates, and paper handoff  

*Goal*: Provide a single, documented entry point, verify all gates, and prepare the research report.

- [ ] **T008** [US2] Write the orchestration script and update the quick‑start guide.  
  *File*: `code/main.py` and `quickstart.md`.  
  - `main.py` sequentially calls: `verify_references --stage dataset`, `download`, `verify_references --stage conditions`, `preprocess`, `analysis` (full‑cohort), `visualize`, `verify_references --stage citations`.  
  - Pin dependencies in `code/requirements.txt` (`mne>=1.7.0`, `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `jsonschema`, `pytest`).  
  - Add a reproducible random seed (`numpy.random.seed(42)`, ICA `random_state=42`).  
  - Update `quickstart.md` with the single command:  

    ```bash
    python code/main.py
    ```

  - **Check**: On a fresh runner, executing `python code/main.py` reproduces all result files, and `pytest` passes.

- [ ] **T009** [US3] Write the methods‑results report linked to real artifacts.  
  *File*: `specs/001-neural-correlates-of-temporal-prediction/research.md`.  
  - Summarize the preprocessing pipeline, MMN quantification, statistical tests, topographic validation, and effect‑size benchmarking.  
  - Cite only sources that passed `verify_references --stage citations` (listed in `data/results/citation_verification.json`).  
  - Report the observed **SNR**, **p‑values (FDR‑corrected)**, **Cohen’s d**, and **Pearson r** values, noting whether each met its respective success criterion (SC‑001 – SC‑004).  
  - Document any exclusions (subjects with > 50 % bad epochs) and limitations (single dataset, sample size).  
  - Include a “paper‑stage handoff” section that lists the exact artifact paths (`data/results/metrics.csv`, `data/results/stats.json`, `data/results/figures/*`) that the downstream paper pipeline should consume.  
  - **Check**: Running `python code/verify_references.py --stage citations` returns 0; every numeric claim in `research.md` can be traced to a row in the CSV/JSON or a figure file.

- [ ] **T010** [US2] Harden and re‑run all Reference‑Validator gates after the full pipeline is in place.  
  *File*: `code/verify_references.py` (already created).  
  - Add unit tests in `code/tests/test_verify.py` that deliberately supply:  
    1. An incorrect dataset ID → expect non‑zero exit and clear error.  
    2. A metadata file missing the `complex` label → expect FR‑008 halt.  
    3. An unreachable citation URL → expect citation‑verification failure.  
  - Execute `python code/verify_references.py --stage all` after the full run; it must exit 0 on the correct dataset, and each negative case must exit non‑zero with a descriptive message.  
  - **Check**: All three negative unit tests fail as intended, and the positive “all” run succeeds, confirming the gates are reliable.
