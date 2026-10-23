# Tasks: Extending “ACE‑Ego‑0” with a CPU‑only static visual proxy

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001‑llmxive‑follow‑up‑extending‑ace‑ego‑0‑un/contracts/`.

The following checklist implements the smallest complete study that satisfies **all functional requirements (FR‑001 – FR‑007)** and **success criteria (SC‑001 – SC‑005)**.  
Tasks are ordered so that each produces the inputs required by the next.  
All file paths are relative to the project root and live under `data/`, `code/`, `figures/`, or `results/`.

---

- [ ] **T001** [P] [US0] Download verified source datasets.   <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 -->
  *Download the **ACE‑Ego‑0** dataset archive, the dynamic‑reliability heuristic script, and the RoboCasa & RoboTwin benchmark archives into `data/raw/`.*  
  *Verification:*  
    • Compute SHA‑256 checksums and compare to the values listed in `plan.md`.  
    • Write `data/raw/download_log.txt` with timestamps and any checksum mismatches.  

- [ ] **T002** [P] [US1] Extract static visual features per video segment **with imputation**.  
  *Using OpenCV (CPU) extract frames at 1 fps, then compute per‑frame entropy, YOLOv8 hand‑detection confidence, lighting (mean & std of grayscale intensity), and camera metadata (timestamp, exposure, focal length). Aggregate per‑segment statistics (mean ± std). If any feature is missing for a frame, impute it with the **dataset‑wide mean** of that feature; if imputation fails (e.g., NaN after mean substitution), **exclude the entire segment** and log its ID. Persist the final table as `data/static_features.csv`.*  
  *Verification:*  
    • Validate `data/static_features.csv` against `specs/001‑llmxive‑follow‑up‑extending‑ace‑ego‑0‑un/contracts/static_features.schema.yaml` with the provided JSON‑schema test.  
    • Log the number of processed segments, number of imputed values, and number of excluded segments in `code/logs/static_extraction.log`.  

- [ ] **T003** [P] [US1] Compute ground‑truth dynamic reliability scores.  
  *Run the official ACE‑Ego‑0 temporal heuristic (CPU‑only) on each segment and store `segment_id, dynamic_reliability` in `data/dynamic_reliability.csv`.*  
  *Verification:*  
    • Ensure every `segment_id` present in `static_features.csv` appears exactly once in `dynamic_reliability.csv`.  
    • Record the mean and std of the reliability distribution in `code/logs/dynamic_scores.txt`.  

- [ ] **T004** [P] [US1] Train static‑only regression model.  
  *Train a Random Forest regressor (scikit‑learn, `random_state=42`) on `static_features.csv` to predict `dynamic_reliability`. Perform 5‑fold cross‑validation, compute cross‑validated **R²** and a 95 % bootstrap confidence interval. Save the fitted model to `data/models/static_rf.pkl` and predictions to `data/static_predictions.csv` (including per‑tree std as `prediction_std`).*  
  *Verification:*  
    • Assert that the CV R² ≥ 0.0 and write the value and CI to `results/static_model_metrics.txt`.  
    • Check that `static_predictions.csv` contains the columns `segment_id, predicted_reliability, prediction_std`.  

- [ ] **T005** [P] [US1] Residual analysis & orthogonality check.  
  *Compute residuals = `predicted_reliability − dynamic_reliability` and store in `data/static_residuals.csv`. Additionally, calculate Pearson correlation between each static feature and the dynamic reliability; write a summary table to `results/feature_correlations.csv`.*  
  *Verification:*  
    • Verify that every `segment_id` from `static_predictions.csv` appears in `static_residuals.csv`.  
    • Flag any feature with |r| > 0.8 (potential leakage) in `results/orthogonality_warnings.txt`.  

- [ ] **T006** [P] [US2] Extract temporal‑window optical‑flow features.  
  *For each segment, compute optical‑flow magnitude statistics (mean, std) and an 8‑bin direction histogram for **four** window lengths: 1 s, 3 s, 5 s, 10 s (using `torchvision` CPU optical‑flow). Save each window’s CSV as `data/temporal_features_{W}s.csv` (e.g., `temporal_features_3s.csv`).*  
  *Verification:*  
    • Confirm that each CSV contains `segment_id, window_sec, flow_mag_mean, flow_mag_std, flow_dir_hist_0 … flow_dir_hist_7`.  
    • Log any segment that fails due to insufficient frames in `code/logs/temporal_extraction.log`.  

- [ ] **T007** [P] [US2] Temporal‑augmented regression and diminishing‑return analysis.  
  *For each window CSV, merge its columns with `static_features.csv`, retrain a Random Forest (same hyper‑parameters as T004), and record the new cross‑validated R² in `results/temporal_r2.csv` (columns: `window_sec, r2`). Identify the smallest window where the incremental gain ΔR² < 0.01 per added second; write that “elbow” window to `results/diminishing_return.txt`.*  
  *Verification:*  
    • Ensure `temporal_r2.csv` has exactly four rows (1, 3, 5, 10).  
    • Assert that the elbow detection script runs without error and produces a numeric window length.  

- [ ] **T008** [P] [US3] Define high‑reliability filter.  
  *Using `static_predictions.csv`, create a whitelist of `segment_id`s that satisfy **both**: (a) `predicted_reliability ≥ 0.4` **and** (b) `prediction_std ≤ 0.2`. Write the IDs to `data/high_reliability_ids.txt`.*  
  *Verification:*  
    • Report the retained‑segment count and exclusion count in `results/filter_summary.txt`.  
    • Verify that every ID in the whitelist exists in `static_features.csv`.  

- [ ] **T009** [P] [US3] Assemble three VLA training manifests.  
  *Create plain‑text manifest files listing the video segment paths for: (a) **dynamic baseline** (all segments), (b) **uniform weighting** (same list, but a weight column set to 1.0 for all), and (c) **static‑proxy filtered** (only IDs from `high_reliability_ids.txt`). Store as `data/vla_manifest_dynamic.txt`, `data/vla_manifest_uniform.txt`, `data/vla_manifest_static.txt`.*  
  *Verification:*  
    • Check that the filtered manifest contains ≤ the number of segments in the baseline manifest.  
    • Log the manifest sizes in `results/manifest_overview.txt`.  

- [ ] **T010** [P] [US3] Train small OpenVLA variants on each manifest.  
  *Using the provided `code/models/openvla_small.py` (CPU‑only), train three models (max 5 000 segments each) with identical hyper‑parameters and 5 random seeds. Save checkpoints to `data/vla_models/{variant}_seed{N}.pth` (e.g., `static_proxy_seed3.pth`).*  
  *Verification:*  
    • Ensure each training run finishes within **2 h** wall‑clock time (recorded in `code/logs/vla_train_{variant}_seed{N}.log`).  
    • Confirm that exactly 5 checkpoint files exist per variant.  

- [ ] **T011** [P] [US3] Benchmark VLA models on RoboCasa & RoboTwin.  
  *Run the evaluation script `code/evaluation/benchmarks.py` for each checkpoint on **≥ 100 shared episodes** per benchmark. Output CSVs `results/vla_{variant}_robocasa.csv` and `results/vla_{variant}_robotwin.csv` containing `episode_id, success`.*  
  *Verification:*  
    • Compute and store the success rate (percentage of `success=True`) in `results/vla_success_summary.csv` (columns: `variant, benchmark, success_rate`).  
    • Assert that each CSV has at least 100 rows.  

- [ ] **T012** [P] [US3] Statistical comparison of static‑proxy vs. dynamic baseline.  
  *For each benchmark, perform a paired t‑test across the 5 seeds comparing the success rates of the **dynamic baseline** and **static‑proxy** models (using `statsmodels`). Write the p‑value, mean difference, and 95 % CI to `results/statistical_summary.txt`. Also note whether the p‑value satisfies the SC‑004 threshold (p < 0.05).*  
  *Verification:*  
    • The summary file must contain a line `p_value = ...` and `significant = True/False`.  

- [ ] **T013** [P] [SC‑005] Profile computational cost (raw metrics).  
  *Instrument the static‑feature extraction (T002) and VLA training (T010) to record total CPU seconds and peak RAM (using `psutil`). Write the aggregated metrics to `results/performance_metrics.txt` and assert the absolute constraints: ≤ 2 min CPU per hour of video for extraction, ≤ 6 GB peak RAM for the whole pipeline.*  
  *Verification:*  
    • The file must contain the fields `cpu_minutes_per_hour_video`, `peak_ram_gb`, and a boolean `constraints_met`.  

- [ ] **T016** [P] [SC‑005] Compute and record speed‑up relative to ACE‑Ego‑0 baseline.  
  *Read the `cpu_minutes_per_hour_video` value from `results/performance_metrics.txt`, compute the percentage speed‑up compared to the ACE‑Ego‑0 baseline of 5 min CPU per hour (i.e., `speedup = (5 - observed) / 5 * 100`). Append a line `speedup_vs_ace_ego0_percent = <value>` to the same `results/performance_metrics.txt` file.*  
  *Verification:*  
    • Ensure the speed‑up line is present and the computed value is a non‑negative number; if the observed time exceeds 5 min, the speed‑up will be negative, which is still recorded for transparency.  

- [ ] **T014** [P] Generate figures & tables for the paper handoff.  
  *Create: (a) a line plot of R² vs. temporal window length (`figures/r2_vs_window.png`), (b) a histogram of residuals (`figures/residual_hist.png`), (c) a bar chart of benchmark success rates per variant (`figures/benchmark_success.png`), and (d) a table summarizing all numeric results (`figures/results_table.tex`).*  
  *Verification:*  
    • Each figure file must exist and be > 0 KB.  
    • The LaTeX table compiles without errors (checked by `pdflatex -interaction=nonstopmode`).  

- [ ] **T015** [P] Write the research report linking all artifacts.  
  *Produce `docs/research_report.md` that (i) restates the research question, (ii) describes the methodology, (iii) reports SC‑001 – SC‑005 outcomes with explicit references to the CSV/figure files generated above, and (iv) discusses limitations and next steps.*  
  *Verification:*  
    • Run `markdownlint` to ensure the file is well‑formed.  
    • Confirm that every cited artifact (e.g., `data/static_features.csv`, `figures/r2_vs_window.png`) is hyperlinked and exists.  

---  

**Dependency mapping**

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001 – FR‑003, SC‑001 | T002, T003, T004, T005 |
| FR‑004, SC‑002 | T006, T007 |
| FR‑005 – FR‑007, SC‑003, SC‑004 | T008‑T012 |
| SC‑005 (absolute & speed‑up) | T013, T016 |
| All reporting & handoff | T014, T015 |

All tasks are unchecked; the CI runner will mark them as completed when the corresponding scripts succeed and the verification steps pass.  