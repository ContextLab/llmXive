# Tasks: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contracts, and existing artifacts.
All paths are relative to the project directory. All computation is CPU-only (2 cores, ~7 GB RAM, ~14 GB disk, ≤6 h); no synthetic or placeholder data are ever generated — every metric derives from the real OpenNeuro `ds000030` recordings and event timings.

**Metric note (reconciling spec/constitution)**: Per Constitution Principle VII and `contracts/connectivity.schema.yaml`, the **primary** outcome is the **mean absolute correlation** across the six unique ROI‑pair edges (FR‑005). The sign‑preserving mean correlation is retained as a descriptive secondary metric.

**Note on ROI edge count**: The original plan referenced three ROI‑pair edges, but the specification (FR‑003) defines four DMN ROIs (PCC, mPFC, left and right angular gyrus), which yields six unique ROI‑pair edges. All tasks below reflect this correct six‑edge configuration; the plan should be updated accordingly.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Implement the dataset ingestion module `code/data_loader.py` that downloads the verified Cyberball dataset `ds000030` from `https://openneuro.org/datasets/ds000030` using the OpenNeuro API (e.g. `openneuro` Python package / `https://openneuro.org/crn/datasets/ds000030/subjects/{sub}?type=func` endpoints), streaming files one subject at a time so peak disk stays within ~14 GB and RAM within ~7 GB.
  - Implement retry with exponential backoff (1 s → 2 s → 4 s, 3 attempts) per FR‑013; on final failure raise `DataUnavailableError` (`ERR_DATA_UNAVAILABLE`). The loader must FAIL LOUDLY on fetch failure — never fall back to synthetic, mock, or bundled data.
  - Verify file integrity (downloaded NIfTI files open with `nibabel`, sizes > 0) per FR‑001.
  - Parse each subject's `events.tsv` and `*_confounds.tsv`; verify both "Inclusion" and "Exclusion" trial types exist, else abort with error code `101897695` per FR‑010.
  - Write the BIDS tree to `data/raw/ds000030/` and a manifest `data/processed/dataset_manifest.json` listing subject IDs, run IDs, TR (from BIDS JSON side‑cars), and available conditions.
  - Update `specs/001-neural-correlates-of-simulated-social-ex/quickstart.md` with the exact runnable command (`python code/data_loader.py --dataset ds000030 --output data/raw`).
  - Tests in `code/tests/test_data_loader.py`: missing‑marker events file triggers 101897695; corrupt/empty download raises rather than silently continuing.

- [ ] T002 [US1] Implement motion QC in `code/qc.py`: compute mean framewise displacement per subject from the BIDS `*_confounds.tsv` (Power FD definition using motion derivatives; use precomputed `framewise_displacement` column when present) and flag subjects with mean FD > 0.2 mm (FR‑002).
  - Output initial `data/processed/subjects_metadata.json` (fields per `contracts/subject.schema.yaml`: `subject_id`, `motion_mean`, `qc_status`, `conditions`).
  - Tests in `code/tests/test_qc.py`: a subject with mean FD > 0.2 mm is flagged `failed`; boundary FD = 0.2 mm retains the subject.

- [ ] T003 [US1] Implement ROI extraction and optional confound regression in `code/preprocess.py` + `code/roi_extractor.py` for each subject passing motion QC:
  - **Step 1 – Raw extraction:** Load the 4‑D BOLD NIfTI with `nibabel` (`mmap=True`, streaming) and **extract the mean BOLD time‑series for the four Harvard‑Oxford DMN ROIs (PCC, mPFC, L_ANG, R_ANG) before any nuisance regression**. Save these raw series to `data/processed/raw_timeseries_{subject_id}_{condition}.csv` (columns: `timepoint`, `PCC`, `mPFC`, `L_ANG`, `R_ANG`). This satisfies FR‑004’s requirement to use “raw time‑series” for connectivity.
  - **Step 2 – Confound regression (optional):** Load the same 4‑D data and regress out the six motion parameters + derivatives, WM/CSF CompCor signals, and global signal (FR‑019) using `nilearn.maskers.NiftiLabelsMasker` with `standardize=True` and a confounds DataFrame. Save the cleaned series (e.g., `cleaned_timeseries_…`) for any downstream analyses that may require denoised data.
  - Segment the **raw** time‑series into Inclusion and Exclusion conditions using the verified `events.tsv` onsets/durations aligned to TR.
  - Validate each record against `contracts/timeseries.schema.yaml`; subjects missing any required ROI column or with zero‑variance ROI are flagged for exclusion.
  - **Final Cohort Validation:** Exclude subjects missing valid time‑series for either condition or any required DMN ROI (FR‑011, FR‑014). Update `data/processed/subjects_metadata.json` and write `data/processed/qc_report.json` containing the final retention rate (SC‑001).
  - **Pipeline Guard:** Halt with error `101897696` if the final retained N < 10 (FR‑009).
  - Test in `code/tests/test_roi_extractor.py`: on one real retained subject, four ROI columns of equal length matching the condition's TR count; zero‑variance ROI triggers exclusion.

- [ ] T004 [US2] Implement connectivity computation in `code/connectivity.py` and run it end‑to‑end on the final retained cohort:
  - **Static connectivity:** per subject and condition, compute the 4 × 4 Pearson correlation matrix **directly from the raw ROI time‑series saved in Step 1 of T003** (FR‑004). Derive `strength_absolute` (mean **absolute** correlation across the **six** unique ROI‑pair edges — **primary**, FR‑005) and `strength_signed` (descriptive secondary), plus per‑edge signed values.
  - **Note:** The original plan and research documents referenced three ROI‑pair edges (three ROIs). This implementation uses four ROIs, yielding six unique edges, and therefore conducts six edge‑wise tests with FDR correction. The expanded edge set is documented here to maintain transparency while still satisfying all FRs.
  - Write `data/processed/connectivity_{subject_id}_{condition}.json` validated against `contracts/connectivity.schema.yaml`, and a cohort table `data/results/strength_per_subject.csv` with columns `subject_id, inclusion_absolute, exclusion_absolute, difference_absolute, inclusion_signed, exclusion_signed, difference_signed` (SC‑004).
  - **Dynamic connectivity:** sliding‑window (30 s window, 5 s step, converted via TR) Pearson correlations producing a time‑resolved strength series per condition (FR‑018); write `data/processed/dynamic_{subject_id}_{condition}.csv` (`window_center_sec`, `strength_absolute`, `strength_signed`).
  - Tests in `code/tests/test_connectivity.py`: correlation of a real pair recomputed with `numpy.corrcoef` matches; window count equals `floor((T - 30s)/5s) + 1` for a series of length T; strength difference = exclusion − inclusion.
  - **Checkpoint:** `python code/main.py --stage connectivity --seed 42` runs on real data and produces the per‑subject CSV with N ≥ 10 rows.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US3] Implement the statistical testing module `code/stats.py`: non‑parametric paired permutation test (exactly 10 000 permutations) on per‑subject absolute strength differences (Exclusion − Inclusion), reporting a two‑tailed empirical p‑value, Cohen's d, and a 95 % CI from the permutation distribution (FR‑006).
  - Accept an explicit `--seed` argument (FR‑016); run edge‑wise paired permutation tests for each of the **six** unique ROI edges with Benjamini–Hochberg FDR correction across edges (documented deviation from the plan’s three‑edge expectation).
  - Write `data/results/statistical_result.json` validating against `contracts/result_schema.schema.yaml` (authoritative contract). Pin the following fields: `metric` = `"mean_absolute_correlation"`, `condition_comparison` = `"Exclusion vs Inclusion"`, `is_associational: true`. Include `p_value`, `effect_size`, `confidence_interval`, `edge_p_values`, `edge_p_values_fdr`, `n_subjects`, and `motion_threshold`.
  - Report the power limitation honestly: with N ≈ 10–30 the test reliably detects only large effects (Cohen's d ≈ 0.8) at α = 0.05 (SC‑007).
  - Tests in `code/tests/test_stats.py`: permutation count is exactly 10 000; p‑value on swapped‑sign differences is symmetric; identical seed reproduces identical p‑value.

- [ ] T006 [US3] Implement visualization in `code/viz.py`, generating from the validated result artifacts (FR‑015, FR‑017):
  - `data/results/figures/null_distribution.png` — histogram of the permutation null distribution with the observed statistic marked;
  - `data/results/figures/strength_difference_bar.png` — bar plot of the observed mean difference with 95 % CI error bars;
  - `data/results/figures/heatmap_inclusion.png` and `heatmap_exclusion.png` — group‑mean ROI correlation‑matrix heatmaps with colorbars and axis labels (SC‑003, SC‑005);
  - `data/results/figures/dynamic_series.png` — group‑mean sliding‑window strength series per condition with ± SEM bands (SC‑006).
  - Test in `code/tests/test_viz.py`: all PNGs exist, are non‑empty, and matplotlib figures contain titles, axis labels, and colorbars.

- [ ] T007 [US2] Complete the dynamic‑connectivity summary and multiple‑comparison control: aggregate per‑subject sliding‑window series into `data/results/dynamic_summary.csv` (per subject and condition: mean and SD of windowed absolute strength, SC‑006).
  - For each window, compute the raw p‑value of the condition difference across subjects using a paired t‑test; apply Benjamini–Hochberg FDR correction across all windows and store corrected p‑values in `data/results/dynamic_fdr.csv` (SC‑008).
  - Test in `code/tests/test_dynamic_summary.py`: row count = 2 × N_retained; FDR‑corrected p‑values are monotonically ≥ raw p‑values.

- [ ] T008 Implement the sensitivity analysis in `code/sensitivity_analysis.py`: re‑apply the QC filter at motion thresholds [0.2, 0.3, 0.4, 0.5] mm (reusing already‑extracted time‑series, no re‑download), recompute the primary permutation test at each threshold (10 000 permutations, fixed seed), and record `{threshold, n_retained, p_value, effect_size}` rows in `data/results/sensitivity_curve.csv` plus a line plot `data/results/figures/sensitivity_curve.png` (p‑value vs. threshold).
  - Halt any threshold arm whose retained N < 10 and record it as `insufficient_n` in the CSV rather than fabricating a result.
  - Test in `code/tests/test_sensitivity.py`: CSV has four threshold rows in ascending order; each row's n_retained is non‑decreasing with threshold.

- [ ] T009 [US3] Implement the full orchestrator `code/main.py` wiring download → QC → ROI extraction (raw & cleaned) → static + dynamic connectivity → statistics → figures, with `--seed` propagated end‑to‑end and error codes (`101897695`, `101897696`, `ERR_DATA_UNAVAILABLE`) surfaced as non‑zero exits. Run the complete pipeline on the full retained cohort; all artifacts land under `data/processed/`, `data/results/`, and `data/results/figures/`.
  - Integration test in `code/tests/test_integration.py`: re‑running the stats stage with the same seed reproduces `data/results/statistical_result.json` byte‑identically (excluding timestamps); re‑running with 5 different seeds yields p‑value SD ≤ 0.01 (SC‑002).

## Phase 3: Reproducible results and paper handoff

- [ ] T010 Write `data/results/report.md`: a concise methods‑and‑results account generated from the actual result artifacts, stating the exact retained N, retention rate, motion threshold, primary p‑value, Cohen's d, 95 % CI, FDR‑corrected edge‑wise p‑values, dynamic‑series summary, sensitivity curve, and the power limitation (N‑dependent detectable effect size). Frame all findings as **associational** and report negative/null results honestly. Link every figure and table to its file under `data/results/`.
  - Verification: Implement a verification script `code/verify_report.py` that extracts numeric literals from `report.md` and asserts they match the values in `statistical_result.json`, `sensitivity_curve.csv`, or `dynamic_summary.csv`.

- [ ] T011 Re‑run the documented workflow from its declared inputs (`python code/main.py --seed 42` per `quickstart.md`), confirm all unit and integration tests pass (`pytest code/tests/`), confirm every contract‑validating check passes against the schemas in `specs/001-neural-correlates-of-simulated-social-ex/contracts/`, and document the paper‑stage handoff: the tables (`strength_per_subject.csv`, `dynamic_summary.csv`, `sensitivity_curve.csv`), figures (all PNGs under `data/results/figures/`), statistical summary (`statistical_result.json`), and report (`report.md`) are packaged for downstream manuscript preparation — formatting, references, and submission belong to the paper pipeline.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR‑001, FR‑013, FR‑010 (ingest, retry, markers) | T001 | `python code/data_loader.py --dataset ds000030 --output data/raw` |
| FR‑002, FR‑009, FR‑011, FR‑014 (QC, N ≥ 10) | T002, T003 | `pytest code/tests/test_qc.py` |
| FR‑003, FR‑019 (confounds, ROI extraction) | T003 | `pytest code/tests/test_roi_extractor.py` |
| FR‑004, FR‑005, FR‑018 (static + dynamic connectivity) | T004, T007 | `python code/main.py --stage connectivity --seed 42` |
| FR‑006, FR‑016 (permutation test, seed) | T005, T009 | `python code/main.py --seed 42` |
| FR‑015, FR‑017 (figures) | T006 | `pytest code/tests/test_viz.py` |
| SC‑001–SC‑008 | T002, T003, T004–T009 | integration tests + artifact checks |
| Paper handoff | T010, T011 | `data/results/report.md` exists and validates |

Execution order: T001 → T002 → T003 → T004 → (T005, T006, T007, T008 after T004/T005) → T009 → T010 → T011. No task writes to `state/` or `.github/`; the platform derives artifact hashes at verification time.