# Tasks: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Input**: `specs/001-visual-search-emotional-faces/spec.md`, `plan.md`, existing project structure.  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md`, contracts/, and any previously‑checked infrastructure tasks.

## Phase 0 – Project scaffolding (already completed)

- [~] T001 Establish the project directory layout (`projects/PROJ-290-the-impact-of-visual-search-strategies-o/`) and create core files (`code/__init__.py`, `requirements.txt`, `pyproject.toml`, `README.md`, `code/config.py`).  
- [X] T002 Set up logging infrastructure (`code/utils/logging.py`) with file handlers for `logs/`.  
- [~] T003 Implement `code/utils/hash_artifacts.py` to generate SHA‑256 hashes for all files under `data/` and `code/` (Constitution Principle V).  
- [~] T035 Implement `code/validation/reference_validator.py` to enforce citation‑title overlap ≥ 0.7.  

---

## Phase 1 – Data acquisition & verification (User Story 1 – P1)

- [ ] T010 [US1] **Download eye‑tracking dataset**   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->
  *Implement `code/data/download.py` to search HuggingFace Datasets for a dataset containing `gaze_coordinates`, `response_times`, `emotion_labels` (e.g., `eyetracking-emotion-face-search`).*  
  • Apply retry logic with exponential back‑off (1 s, 2 s, 4 s) and abort after 3 attempts (FR‑002).  
  • Save the raw archive under `data/raw/` and write a SHA‑256 checksum to `data/raw/checksum.txt`.  
  • **Verification**: Run the script; it must exit with status 0 and produce both the dataset directory and the checksum file.

- [ ] T013 [US1] **Implement Generic ROI Fallback (3 × 3 grid)**  
  *Add fallback logic to `code/features/extraction.py`.*  
  • When `roi_annotations` are missing, define eye ROI as the top‑center cell and mouth ROI as the bottom‑center cell of a 3 × 3 grid over the face image.  
  • Document the fallback in `data/processed/roi_fallback_used.txt`.  
  • **Verification**: Unit test `tests/unit/test_roi_fallback.py` confirms that the generated masks correspond to the expected grid cells.

- [ ] T011 [US1] **Validate dataset & apply generic ROI fallback**  
  *Implement `code/data/validate.py`.*  
  • Verify presence of critical variables (`gaze_coordinates`, `response_times`, `emotion_labels`, `roi_annotations`). If any are missing, HALT with a clear error (FR‑009).  
  • If `roi_annotations` are absent, invoke the Generic ROI Fallback implemented in T013.  
  • Exclude participants with > 20 % missing gaze coordinates; log the exclusion rate (must be ≤ 10 %).  
  • Compute the **record‑completeness percentage** (records with non‑null gaze coordinates and response times). **Assert that this percentage ≥ 95 %**; if not, fail with an informative error (fulfills SC‑001).  
  • Write a validation report to `data/validation_report.json` that includes the completeness percentage and exclusion rate.  
  • Write `data/processed/roi_fallback_used.txt` when the fallback is triggered.  
  • **Verification**: The script produces the JSON report, logs the exclusion rate, asserts the 95 % threshold, and creates the ROI‑fallback flag file when appropriate.

- [ ] T028 **Verify dataset completeness report**  
  *Implement `code/data/verify_completeness.py`.*  
  • Load `data/validation_report.json` and assert that `record_completeness >= 0.95`.  
  • If the assertion passes, write a pass flag file `data/validation_pass.txt`; otherwise, raise an error.  
  • **Verification**: The script exits with status 0 only when the completeness requirement is satisfied.

- [ ] T026 **Pin random seeds for reproducibility**  
  *Create `code/utils/seed.py` that sets `numpy.random.seed`, `random.seed`, and `sklearn.utils.check_random_state` to a fixed value (e.g., 42) and logs the action.*  
  • Ensure this script is imported/run before any stochastic operation (k‑means, bootstrapping, CV splits, model fitting).  
  • **Verification**: Unit test `tests/unit/test_seed.py` checks that the seeds are set to the expected value and that subsequent random draws are deterministic.

---

## Phase 2 – Feature extraction & strategy classification (User Story 2 – P2)

- [ ] T012 [US2] **Extract fixation metrics & compute continuous ratio**  
  *Implement `code/features/extraction.py`.*  
  • For each trial compute eye‑region duration, mouth‑region duration, saccade amplitude, and dispersion (FR‑003).  
  • Calculate the **continuous fixation ratio** = eye_duration / mouth_duration for each participant (primary predictor).  
  • Persist all rows to `data/processed/features.csv` adhering to `output.schema.yaml`.  
  • **Verification**: The CSV file exists, contains the required columns, and passes schema validation (`python -m jsonschema -i data/processed/features.csv contracts/output.schema.yaml`).

- [ ] T023 **Calculate variance inflation factors (VIF) for collinearity**  
  *Implement `code/diagnostics/vif.py`.*  
  • Load `data/processed/features.csv`, compute VIF for all predictor pairs (including the continuous fixation ratio).  
  • Flag any predictor with VIF ≥ 5 and write a VIF report to `results/vif_report.csv`.  
  • **Verification**: The CSV exists, contains columns `predictor` and `VIF`; the task fails if any VIF ≥ 5 (meeting FR‑005).

- [ ] T014 [US2] **Classify participants via k‑means (k = 2) – exploratory**  
  *Implement `code/features/classification.py`.*  
  • Apply k‑means clustering on the fixation‑distribution features (eye / mouth ratio, saccade amplitude, dispersion).  
  • Compute silhouette score; if mean silhouette < 0.25 **or** either cluster contains < 5 participants, log a warning and skip clustering (proceed with descriptive statistics only) (FR‑004).  
  • Write cluster labels to `data/processed/labels_k2.csv` (columns: `participant_id`, `processing_strategy_label`).  
  • **Verification**: The CSV is present when clustering succeeds; the log contains the warning when criteria are not met.

- [ ] T024 **Derive processing‑strategy labels with 5‑fold cross‑validation**  
  *Implement `code/features/cv_labeling.py`.*  
  • Perform stratified 5‑fold cross‑validation on the participant set; in each fold train k‑means (k=2) on the training split and assign labels to the held‑out participants.  
  • Aggregate per‑fold labels into a final label file `data/processed/labels_cv5.csv`.  
  • Report cross‑validation stability metrics (e.g., adjusted Rand index across folds) in `results/cv_stability_report.yaml`.  
  • **Verification**: The CSV and YAML files exist; unit test `tests/unit/test_cv_labeling.py` checks that each participant receives exactly one label and that stability metrics are computed.

---

## Phase 3 – Statistical analysis & power validation (User Story 3 – P3)

- [ ] T016 [US3] **Fit primary Linear Mixed‑Effects Model (continuous ratio)**  
  *Implement `code/analysis/lmm_continuous.py`.*  
  • Use `statsmodels` to fit an LMM with detection time as outcome, `continuous_fixation_ratio` as fixed effect, and participant as random intercept (FR‑006).  
  • Enforce max 500 iterations, tolerance 1e‑6; **assert convergence** by checking the model’s `converged` attribute and logging a flag.  
  • Write model summary to `results/lmm_continuous.csv`.  
  • **Verification**: The CSV exists, contains columns `estimate`, `SE`, `t`, `p`; the script exits with non‑zero status if convergence flag is false.

- [ ] T017 [US3] **Fit exploratory LMM with processing‑strategy label**  
  *Implement `code/analysis/lmm_cluster.py`.*  
  • Same specifications as T016 but using `processing_strategy_label` as the fixed effect (FR‑006, exploratory).  
  • If the model fails to converge within 500 iterations, automatically fall back to a simple linear regression with the same predictor and log the fallback.  
  • Output to `results/lmm_cluster.csv`.  
  • **Verification**: The CSV is produced; the log indicates whether the fallback was used and the fallback output conforms to the same schema.

- [ ] T018 [US3] **Permutation test for primary model**  
  *Implement `code/analysis/permutation_test.py`.*  
  • Permute detection‑time values 1 000 times, refit the primary LMM each time, and record the distribution of the fixed‑effect coefficient.  
  • Save the null distribution and empirical p‑value to `results/permutation_test.json`.  
  • **Verification**: The JSON file contains keys `null_distribution` (list of 1000 floats) and `empirical_p`.

- [ ] T019 [US3] **Multiple‑comparison correction & power analysis**  
  *Extend `code/analysis/power.py`.*  
  • Apply Bonferroni or Benjamini‑Hochberg correction (α = 0.05) to any family of tests performed (FR‑007).  
  • Perform a priori power analysis for effect size d = 0.5 (target ≥ 0.80) and post‑hoc power analysis for the observed sample size (FR‑008).  
  • Write results to `results/power_analysis.json`, including a flag `power_sufficient: true/false`.  
  • **Verification**: The JSON file reports both a priori and post‑hoc power values and the correction method used.

- [ ] T020 [US3] **Assemble statistical results table & generate figures**  
  *Implement `code/reporting/generate_outputs.py`.*  
  • Merge model summaries, corrected p‑values, and power metrics into `results/table.csv`.  
  • Produce publication‑ready figures:  
    – `results/figures/fixation_distribution.png` (distribution of continuous ratio)  
    – `results/figures/model_coefficients.png` (fixed‑effect estimates with confidence intervals)  
    – `results/figures/power_curve.png` (power vs. sample size).  
  • **Verification**: The CSV and all three PNG files exist and open without error.

- [ ] T021 [US3] **Generate final markdown report**  
  *Implement `code/reporting/report.py`.*  
  • Compile a reproducible report (`results/report.md`) that references every artifact produced above, includes the sensitivity report, tables, figures, and explicitly documents any limitations (e.g., power < 0.80, clustering warnings).  
  • **Include** a reproducibility statement that cites the random‑seed pinning task (T026).  
  • **Verification**: The markdown file renders without broken links and contains sections “Data”, “Methods”, “Results”, “Sensitivity”, “Limitations”, and a reproducibility statement.

- [ ] T015 [US2] **Bootstrap stability check & k‑sweep sensitivity analysis**  
  *Add `code/features/sensitivity.py`.*  
  • Perform 100 bootstrap resamples of the participant set, re‑run k‑means (k = 2) on each, and compute label stability (adjusted Rand index).  
  • Sweep `k` over {2, 3} and record cluster composition and downstream model coefficients using the **exploratory LMM** from T017.  
  • Output a consolidated YAML report to `results/sensitivity_report.yaml` (validated against `contracts/sensitivity_report.schema.yaml`) and, for k = 3, write `data/processed/labels_k3.csv`.  
  • **Verification**: The YAML file exists, contains entries for `k_value`, `cluster_composition`, and `model_coefficients`; a unit test validates its schema.

---

## Phase 4 – Cross‑cutting verification & provenance

- [ ] T027 **Create `state/` directory for provenance artifacts**  
  *Simple script to `mkdir -p state/` before any hashing occurs.*  
  • **Verification**: Directory existence check passes before T022 runs.

- [ ] T022 [P] **Update artifact hashes after all outputs**  
  *Run `code/utils/hash_artifacts.py`* to compute SHA‑256 hashes for every file under `data/`, `results/`, and `code/`.  
  • Write the manifest to `state/hashes.json`.  
  • **Verification**: The JSON file exists and contains a mapping from relative paths to hash strings; CI can compare it to the previous manifest.

### Execution order notes
1. Foundational tasks (T001‑T003, T035) must be complete before any user‑story work.  
2. **User Story 1** (T010, T013, T011, T028, T026) produces the raw dataset and validation artifacts.  
3. **User Story 2** (T012, T023, T014, T024) depends on validated data; T026 runs before any stochastic step.  
4. **User Story 3** (T016‑T021) runs after all feature files (`features.csv`, `labels_*.csv`, VIF report) are available.  
5. **Sensitivity analysis** (T015) runs after the exploratory LMM (T017) to use its downstream coefficients.  
6. **Cross‑cutting** (T027, T022) execute at the end to ensure provenance.

--- 

*All tasks are expressed as unchecked boxes (`- [ ]`) ready for implementation. Completed infrastructure tasks remain checked (`- [X]`).* 