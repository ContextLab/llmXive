# Tasks: Extending “In‑Context World Modeling for Robotic Control”

**Inputs**: `spec.md`, `plan.md`, existing code under `src/`, data‑model contracts, and any verifier feedback.  
All scripts live under `src/pipeline/`; all outputs follow the plan’s data‑model under `data/`, `results/`, `reports/`, `figures/`, and `model/`. The “ICWM policy” evaluation must be a real simulated rollout in **robosuite** (CPU‑only), never a heuristic proxy.

---

## User Story 1 – Automated Latent Statistic Extraction (US‑1)

- [ ] T001 [P1] [US1] **Document project layout & quick‑start command**  
  - Creates `quickstart.md` that explains the single command `python -m src.pipeline.run_all --subset 50`.  
  - *Verification*: CI runs the command on a fresh checkout; it must finish without error, produce `data/processed/descriptors.csv` (50 rows), and the command listed in `quickstart.md` must match the executed command **exactly**. Additionally, the generated `descriptors.csv` is validated against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml`.

- [ ] T002 [P1] [US1] **Generate a small dataset of interaction clips**  
  - `src/pipeline/generate_clips.py` creates 50 reproducible clips (`data/raw/clip_<id>.npz`) containing the three arrays `states`, `actions`, `observations`.  
  - *Verification*: `ls data/raw | wc -l` equals 50 **and** each `.npz` file loads successfully and contains the required three arrays.

- [ ] T003 [P1] [US1] **Extract latent statistical descriptors**  
  - `src/pipeline/extract_descriptors.py` runs the CPU‑only ICWM encoder, computes **variance**, **lag‑1 autocorrelation**, and **Welch spectral density** for every clip, handling the near‑zero‑variance edge case (sets autocorr = 0, spectral = 0).  
  - Writes `data/processed/descriptors.csv` and validates it against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml`.  
  - *Verification*: pytest `tests/test_descriptor_schema.py` passes; a sanity check asserts `variance_high > 2 × variance_low` for a known high‑ vs low‑variance pair.

- [ ] T004 [P1] [US1] **Run minimal end‑to‑end pipeline on 50 clips**  
  - Executes `python -m src.pipeline.run_all --subset 50`.  
  - Produces a 50‑row summary table (printed to stdout) and writes `data/processed/descriptors_subset.csv`.  
  - *Verification*: `logs/run_end_to_end.log` contains the full printed table; the SHA‑256 checksum of the table matches that of `descriptors_subset.csv`. Additionally, the run asserts that `data/processed/descriptors.csv` exists and passes schema validation.

- [ ] T018 [P1] [US1] **Verify end‑to‑end summary checksum**  
  - Computes SHA‑256 of the printed 50‑row table and compares it to the checksum recorded for `data/processed/descriptors_subset.csv`.  
  - *Verification*: CI fails if the two checksums differ.

- [ ] T007 [P1] [US1] **Compute the independent task‑complexity metric**  
  - `src/pipeline/compute_complexity.py` reads each clip’s environment `task_metadata.yaml`, counts distinct `subgoal` entries, writes `data/processed/task_complexity.csv`.  
  - Also writes `reports/complexity_summary.txt` containing the Pearson correlation (r, p) between **latent variance** (from `descriptors.csv`) and **subgoal_count**.  
  - *Verification*: `data/processed/task_complexity.csv` validates against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/complexity.schema.yaml`; `reports/complexity_summary.txt` must report |r| > 0.5 and p < 0.05 (SC‑001).

---

## User Story 2 – Hyperparameter Mapping Model Training (US‑2)

*All artifacts required for this story are generated within the story itself, ensuring independent shippability.*

- [ ] T020 [P2] [US2] **Generate training interaction clips**  
  - Re‑uses `src/pipeline/generate_clips.py` to create 200 training clips (`data/raw/clip_<id>.npz`).  
  - *Verification*: 200 files exist; each loads correctly.

- [ ] T021 [P2] [US2] **Extract descriptors & compute task‑complexity for training set**  
  - Runs `src/pipeline/extract_descriptors.py` on the training clips to produce `data/processed/descriptors.csv`.  
  - Runs `src/pipeline/compute_complexity.py` to produce `data/processed/task_complexity.csv`.  
  - *Verification*: Both CSVs pass their respective schema validations.

- [ ] T005 [P2] [US2] **Real grid‑search labeling (5 episodes per combo)**  
  - `src/pipeline/grid_search_labels.py` maps each **training** clip to its configuration ID, evaluates the ICWM‑conditioned policy for every grid pair **τ ∈ {0.5, 1.0, 1.5}**, **k ∈ {16, 32, 64}** (6 combos).  
  - For each pair runs **5 episodes** (fixed seeds), records binary success, computes a success rate, and selects the optimal pair using the deterministic tie‑breaker (lowest τ, then lowest k).  
  - Writes `data/processed/labels.csv` and validates it against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/label.schema.yaml`.  
  - *Verification*: pytest `tests/test_grid_search_schema.py` passes; a spot‑check confirms the tie‑breaker rule on a deliberately tied configuration.

- [ ] T006 [P2] [US2] **Train a lightweight regressor that beats the temperature‑only baseline (SC‑006)**  
  - `src/pipeline/train_regressor.py` standardises the three descriptors plus `task_complexity` covariate, performs 5‑fold CV over hidden sizes `{16, 32, 64}` and L2 regularisation `{1e‑4, 1e‑3, 1e‑2}`, and trains a single‑hidden‑layer MLP (≤ 64 units) to predict **both τ and k** (joint MSE).  
  - Computes baseline joint MSE by always predicting the global mean τ and k; asserts `model_joint_mse < 0.9 × baseline_joint_mse`.  
  - Saves `model/regressor.pt` and `data/metrics.json` containing `train_mse`, `val_mse`, `baseline_mse`, `meets_sc006`.  
  - *Verification*: `tests/test_train_regressor_metrics.py` checks the JSON fields and that `meets_sc006` is `true`. The pipeline aborts if the assertion fails.

- [ ] T016 [P2] [US2] **Descriptor‑schema contract test (CI hook added)**  
  - `tests/test_descriptor_schema.py` imports the schema from `specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml` and validates `data/processed/descriptors.csv`.  
  - *Verification*: The CI configuration includes this test; `pytest -q tests/test_descriptor_schema.py` must exit with 0 failures.

- [ ] T017 [P2] [US2] **Validation‑results schema contract test (CI hook added)**  
  - `tests/test_validation_results_schema.py` validates `results/validation_results.csv` against `specs/001-llmxive-follow-up-extending-in-context-w/contracts/validation_results.schema.yaml`.  
  - *Verification*: The test is part of CI; it must pass.

---

## User Story 3 – Zero‑Shot Validation and Statistical Evaluation (US‑3)

*All required artifacts are produced within this story, making it independently shippable.*

- [ ] T022 [P3] [US3] **Generate training interaction clips (re‑run for independence)**  
  - Executes `src/pipeline/generate_clips.py` to create a fresh set of 200 training clips (`data/raw/clip_<id>.npz`).  
  - *Verification*: 200 files exist and load correctly.

- [ ] T023 [P3] [US3] **Run grid‑search labeling & train regressor (re‑run for independence)**  
  - Runs the same pipeline steps as T005 and T006 (5 episodes per combo, same deterministic tie‑breaker) to produce `data/processed/labels.csv` and `model/regressor.pt`.  
  - *Verification*: Files exist and pass their schema / metric checks as in US‑2.

- [ ] T013 [P3] **Generate and encode novel interaction clips**  
  - `src/pipeline/generate_novel_clips.py` creates 200 unseen configuration clips (`data/raw_novel/clip_<id>.npz`) with a different random seed.  
  - `src/pipeline/extract_descriptors_novel.py` encodes them, applies the same edge‑case handling, writes `data/processed/descriptors_novel.csv` (validated against the descriptor schema) and logs any encoder failures to `data/logs/encoder_failures.txt`.  
  - *Verification*: Clip count = 200; CSV validates; failure log exists if any OOD clips were skipped.

- [ ] T008 [P3] **Zero‑shot validation pipeline (5 episodes per clip)**  
  - `src/pipeline/validate_autocwm.py` loads `model/regressor.pt`, predicts (τ, k) for each novel clip (clamped to allowed ranges), runs **5 episodes** per clip with the predicted hyperparameters **and** with the fixed baseline (τ = 1.0, k = 32) using identical episode seeds.  
  - Records `auto_success_rate`, `baseline_success_rate`, and `success_diff` (∈ {-1, 0, 1}) per clip, writing `results/validation_results.csv` validated against the validation‑results schema.  
  - *Verification*: The CSV passes schema validation; rates are in [0, 1].

- [ ] T009 [P3] **Statistical significance, lift, and SC‑002 enforcement**  
  - `src/pipeline/stats_test.py` reads `results/validation_results.csv`, performs a **paired t‑test** and a **Wilcoxon signed‑rank test** (α = 0.05, no Bonferroni correction), plus a **McNemar exact test** on the binary outcomes.  
  - Computes absolute success‑rate lift (`auto – baseline`).  
  - Writes `reports/stats_report.txt` (test statistics, p‑values) and `reports/lift_report.txt` containing `lift_ok = True/False` and the numeric lift.  
  - *Verification*: `lift_ok` is `True` only when lift ≥ 0.05 **and** the primary paired t‑test p < 0.05.

- [ ] T014 [P3] **Correlation analysis with strict Pearson requirement**  
  - `src/pipeline/correlation_analysis.py` computes:  
    1. Pearson correlation between **latent variance** and **subgoal_count**.  
    2. Partial Pearson correlations between **variance** and the optimal **τ** and **k**, controlling for `subgoal_count`.  
    3. Diagnostic tests (Shapiro‑Wilk, Breusch‑Pagan, Cook’s distance).  
    4. **If any Pearson assumption fails, the task aborts and reports failure** (no Spearman fallback).  
  - Generates `reports/correlation_report.md` and figures `figures/variance_vs_complexity.png`, `figures/residuals.png`.  
  - *Verification*: The report must state |r| > 0.5 with p < 0.05 for the variance‑complexity correlation (SC‑001) and must include all diagnostic outcomes.

- [ ] T015 [P3] **Power analysis & stratified sampling documentation**  
  - `src/pipeline/power_analysis.py` performs a post‑hoc power analysis for the variance‑complexity correlation (α = 0.05, target power = 0.8) using the actual sample size and observed effect size.  
  - Documents the stratified train/validation split by `task_complexity` bins.  
  - Writes `reports/power_analysis.txt`.  
  - *Verification*: The file contains the calculated achieved power (must be ≥ 0.8) and a clear description of the binning strategy that matches the actual splits.

- [ ] T010 [P3] **Resource‑budget monitoring (FR‑006, SC‑004, SC‑005)**  
  - `src/pipeline/monitor_resources.py` wraps the full pipeline (tasks T022 → T023 → T013 → T008 → T009 → T014). It records wall‑clock time (`time.perf_counter`) and peak RSS via `psutil`.  
  - Asserts runtime ≤ 4 h, peak RSS ≤ 7 GB, and `torch.cuda.is_available()` is `False`.  
  - Writes `data/logs/resource_usage.json` and `reports/resource_report.txt`.  
  - *Verification*: JSON fields `runtime_seconds`, `peak_rss_gb`, `gpu_available` must satisfy the limits; CI fails otherwise.

- [ ] T011 [P3] **Methods & results summary (paper‑stage handoff)**  
  - `docs/methods.md` describes every pipeline stage, links to the exact artifacts (`descriptors.csv`, `labels.csv`, `model/regressor.pt`, `validation_results.csv`, `stats_report.txt`, `lift_report.txt`, `correlation_report.md`, `resource_report.txt`, `power_analysis.txt`).  
  - Reports measured values for SC‑001 – SC‑006, including any negative findings, limitations, and the computational budget numbers.  
  - Ends with a “Paper handoff” section that lists figure filenames, table locations, and the expected PDF compilation entry point.  
  - *Verification*: A CI script parses the markdown, confirms all referenced files exist, and checks that quoted numbers match the source CSV/JSON values.

- [ ] T012 [P3] **Full reproducibility script**  
  - `run_all.sh` (executable, idempotent) runs the tasks in strict order:  
    `T020 → T021 → T005 → T006 → T022 → T023 → T013 → T008 → T009 → T014 → T015 → T010 → T011`.  
  - After successful completion it creates a SHA‑256 manifest of **all** generated artifacts (including logs, intermediate CSVs, figures, model checkpoint) and writes it to `state/projects/PROJ-971-llmxive-follow-up-extending-in-context-w.yaml` (as required by the constitution) **and** copies it to `reports/hash_manifest.txt`.  
  - *Verification*: Executing `bash run_all.sh` twice yields identical `hash_manifest.txt` (diff empty); the manifest lists entries for every file under `data/`, `results/`, `reports/`, `figures/`, and `model/`.

---

## Cross‑cutting & General Requirements

| Requirement | Satisfying task(s) |
|-------------|--------------------|
| FR‑001 (descriptor extraction) | T003, T004, T018, T007, T020, T021 |
| FR‑002 (grid‑search labeling) | T005, T022 |
| FR‑003 (regressor training) | T006, T023 |
| FR‑004 (zero‑shot validation) | T008 |
| FR‑005 (statistical test) | T009 |
| FR‑006 (resource budget) | T010 |
| FR‑007 (task‑complexity metric) | T007, T021 |
| FR‑008 (partial correlation) | T014 |
| SC‑001 (variance‑complexity correlation) | T014 |
| SC‑002 (auto‑ICWM lift) | T009 |
| SC‑003 (paired t‑test) | T009 |
| SC‑004 (wall‑clock budget) | T010 |
| SC‑005 (peak RAM) | T010 |
| SC‑006 (MSE improvement) | T006 |

All tasks respect the CPU‑only constraint, write only to project‑owned paths, and follow the required data‑flow ordering.

---  

**Execution order (canonical)**  

1. **US‑1**: T001 → T002 → T003 → T004 → T018 → T007  
2. **US‑2**: T020 → T021 → T005 → T006 → T016 → T017  
3. **US‑3**: T022 → T023 → T013 → T008 → T009 → T014 → T015 → T010 → T011 → T012  

---  

*End of tasks.md*===