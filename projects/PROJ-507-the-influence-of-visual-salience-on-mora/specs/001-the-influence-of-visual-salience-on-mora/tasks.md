# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/` for feature `001-visual-salience-moral-judgments`

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Establish the runnable pipeline entry point and verified data ingestion in `code/01_ingest_and_filter.py`. <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 -->
  - Fetch real image data from the canonical Hugging Face source (e.g., `datasets.load_dataset("visual_genome", ...)` or the MoralD dataset if a verified source is injected via the `VERIFIED_DATA_SOURCE` environment variable — in that case use that exact recipe as the single source).
  - Stream or sample a real subset (fixed seed 42, first N image records with `social`/`conflict`‑style metadata tags; state the exact sampling rule in the script docstring) so the run fits ≤7 GB RAM; the loader **must raise** `DataFetchError` on any fetch failure — no synthetic fallback of any kind.
  - Output candidate scenario rows to `data/processed/candidates_filtered.csv` conforming to `contracts/dataset.schema.yaml`, with per‑image SHA‑256 checksums in `data/raw/sample_metadata.json`.
  - Document the runnable command in the feature's `quickstart.md`.
  - Verification: `python code/01_ingest_and_filter.py` exits 0 and produces `data/processed/candidates_filtered.csv` with ≥1 real row whose `original_image_path` points to an existing downloaded image file under `data/raw/`; unit test `tests/unit/test_data_loader.py` simulates a fetch failure and asserts `DataFetchError` is raised.

- [ ] T010 [US1] Acquire real human ambiguity annotation files for FR‑008.
  - Use a crowdsourcing platform (e.g., Prolific) to collect 5‑point Likert ambiguity ratings from **at least three independent annotators** per scenario.
  - Store raw CSVs under `data/raw/human_coding/annotations_<annotator_id>.csv`.
  - Verify that ≥3 distinct annotator files exist **and** that each scenario has ≥3 ratings; raise `InsufficientAnnotatorsError` otherwise.
  - Verification: unit test `tests/unit/test_annotation_acquisition.py` checks file count and per‑scenario rating counts.

- [ ] T002 [US1] Process human ambiguity annotations and identify morally ambiguous scenarios in `code/02_human_coding.py`.
  - Ingest the annotation CSVs produced by **T010**.
  - Compute per‑scenario mean ambiguity score and Cohen’s κ; retain scenarios with mean ≥ 3.5 **and** κ ≥ 0.6 (majority‑vote resolution for ties).
  - Cross‑reference retained scenarios against an external pre‑validated resource (e.g., MoralD) and log the match in `data/processed/ground_truth_match.csv`.
  - Output `data/processed/valid_scenarios.csv` conforming to `contracts/dataset.schema.yaml`.
  - Verification: unit test `tests/unit/test_human_coding.py` validates `calculate_cohens_kappa` on a hand‑computed example and the retention filter logic; the script raises loudly when annotator files are absent.

- [ ] T011 [US1] Validate and load configuration files required by downstream tasks.
  - Ensure `config/manipulation.yaml` exists and contains required fields (`version`, `seed`, `luminance_levels`, `target_region`, `output_path`).
  - Ensure `config/pre_registration.yaml` exists, is marked `verification_status: VERIFIED`, and contains `precision_threshold` and `threshold_source`.
  - Raise `ConfigError` if any check fails.

- [ ] T015 [US1] Build, validate, and expose the `bert‑moral‑intent` model.
  - Download the pre‑trained `bert‑moral‑intent` checkpoint from the official Hugging Face repository.
  - Verify model integrity via checksum and a sanity‑check inference on a known sentence (expected correlation ≥0.90 with reference scores).
  - Provide a thin wrapper `code/bert_moral_intent.py` exposing a `compute_preservation_score(original_image, manipulated_image)` function that returns the required correlation metric.
  - Verification: unit test `tests/unit/test_bert_moral_intent.py` checks checksum, runs the sanity inference, and asserts the correlation threshold.

- [ ] T003 [US1] Implement salience manipulation and semantic‑integrity verification in `code/03_manipulate_stimuli.py`.
  - Read versioned parameters from `config/manipulation.yaml`.
  - Generate low/medium/high luminance‑contrast/brightness variants of the ROI (bounding‑box defined) of each valid scenario's real image into `data/processed/stimuli/`.
  - Load the `bert‑moral‑intent` model via **T015** and compute `moral_intent_preservation_score` (correlation ≥ 0.90 required).
  - Verify each variant: RMS contrast change ≥ 15 % in the ROI, CLIP cosine similarity ≥ 0.95 (CPU‑tractable CLIP with `torch.no_grad()`; use GPU if available), texture/edge‑density change < 0.05 (Laplacian variance), and non‑target‑region SSIM recorded.
  - Log and exclude failures (e.g., target‑object detection failure → logged, excluded).
  - Write **two** manifest files:
    1. `data/processed/stimulus_manifest.json` conforming to `contracts/stimuli_manifest.schema.yaml`.
    2. `data/processed/stimulus_variants.json` conforming to `contracts/stimulus.schema.yaml`.
  - Verification: unit test `tests/unit/test_manipulation.py` checks that a manipulated variant of a real image shows ≥15 % ROI RMS contrast change and that both manifests validate against their respective schemas; an end‑to‑end run on the real candidate subset produces real stimulus files and manifest rows.

- [ ] T012 [US2] Recruit real participants and conduct the within‑subject survey in `code/04_survey_deployment.py`.
  - Use the platform’s API to recruit participants (minimum N ≥ 30) and store anonymised `participant_id`s.
  - Generate per‑participant presentation sequences from the real stimulus manifests respecting: no two identical scenarios in a row, balanced salience order across participants (Latin‑square style), and each participant sees each scenario at exactly one salience level per block.
  - Present the manipulated images, collect 1–7 blame ratings, and log each response **to two files**:
    * `data/processed/responses_variant.csv` – conforms to `contracts/response.schema.yaml` (fields `response_id`, `participant_id`, `variant_id`, `blame_rating`, `timestamp`, `valid`).
    * `data/processed/responses_survey.csv` – conforms to `contracts/survey_responses.schema.yaml` (fields `response_id`, `stimulus_id`, `user_id`, `blame_rating`, `timestamp`, `attention_check_pass`, `completion_status`).
  - Abort with `DataIntegrityError` if the stimulus manifest’s `source_type` is `synthetic`.
  - Verification: unit test `tests/unit/test_survey_logic.py` verifies randomisation constraints; integration test `tests/integration/test_survey_flow.py` runs a pilot session end‑to‑end and confirms complete logging with no truncation and that at least 30 participants are recorded.

- [ ] T004 [US3] Implement data cleaning and straight‑liner exclusion in `code/05_data_cleaning.py`.
  - Read the real responses from `data/processed/responses_variant.csv`.
  - Exclude participants whose rating variance < 0.1 **or** > 90 % identical ratings; flag excluded participants with reason per `contracts/participant.schema.yaml`.
  - Output `data/processed/cleaned_responses.csv` with a `valid` flag per response and a per‑participant summary including exclusion rate.
  - Verification: unit test `tests/unit/test_data_cleaning.py` checks the straight‑liner detection rule on constructed rating vectors; the script runs on the real response file and reports the actual exclusion rate.

- [ ] T005 [US3] Perform CLMM analysis with convergence fallback, corrections, effect‑size computation (including Type III SS), and power/precision reporting in `code/06_analysis_clmm.py`.
  - Fit `blame_rating ~ salience + (1|participant) + (1|scenario)` as a Cumulative Link Mixed Model on the cleaned real responses.
  - Check convergence; on failure switch to a robust alternative (LMM with robust SE or Wilcoxon signed‑rank with Bonferroni) and record `convergence_status` and `fallback_method`.
  - Perform post‑hoc pairwise comparisons (low vs medium, medium vs high, low vs high) with Tukey adjustment (Bonferroni for the fallback).
  - Compute odds ratios, 95 % CIs, **and** Type III Sums of Squares for the fixed effect (via `statsmodels` ANOVA) and store under `effect_size.typeIII_ss`.
  - **Family‑wise error rate measurement**: generate 10 000 null datasets, run the same test pipeline, and record the empirical FWER as `familywise_error_rate_measured`.
  - Perform post‑hoc power analysis using the observed effect size; flag if observed power < 0.80.
  - Load `config/pre_registration.yaml` (validated by **T011**) and verify the precision threshold; raise `PreRegistrationError` if missing or unverified.
  - Write results to `data/processed/results.json` conforming to `contracts/analysis_schema.schema.yaml` (including `post_hoc_tests`, `power_analysis`, `typeIII_ss`, and `familywise_error_rate_measured`).
  - Verification: unit test `tests/unit/test_analysis.py` runs the pipeline on a constructed calibration dataset with a known injected coefficient (β = 0.5) and verifies the recovered effect, correct correction, fallback logic, Type III SS, and FWER measurement; integration test `tests/integration/test_analysis_pipeline.py` runs the full analysis on the real cleaned data and checks `results.json` validates against the contract schema.

- [ ] T006 [US3] Conduct a pilot **human manipulation check** for stimulus validity in `code/07_human_manipulation_check.py`.
  - Recruit a separate coder panel (≥ 5 coders) to rate whether the moral narrative is preserved after salience manipulation.
  - Compute the proportion of coders indicating preservation; require **≥ 80 %** agreement.
  - Log the outcome to `data/processed/human_check_report.md` and add a boolean flag `human_narrative_preserved` to each entry in `data/processed/stimulus_variants.json`.
  - Verification: unit test `tests/unit/test_human_check.py` validates the agreement calculation and aborts if the threshold is not met.

- [ ] T014 [US3] Measure empirical family‑wise error rate (FWER) for the correction procedure.
  - Simulate 10 000 null datasets matching the real study’s structure (same sample size, random salience assignments, no true effect).
  - Run the full analysis pipeline (including post‑hoc tests and correction) on each simulated dataset.
  - Calculate the proportion of simulations where any family‑wise error occurs; store this empirical FWER in `data/processed/fwer_measurement.json`.
  - Verification: unit test `tests/unit/test_fwer_measurement.py` checks that the simulation loop runs and that the resulting FWER value is a number between 0 and 1.

- [ ] T007 [US3] Generate tables, figures, and a verification script in `code/07_generate_reports.py`.
  - Produce:
    * Fixed‑effects odds‑ratio table → `figures/odds_ratio_table.csv`.
    * Post‑hoc comparison table → `figures/posthoc_table.csv`.
    * Power/precision summary → `figures/power_summary.txt`.
    * Rating‑distribution plots → `figures/rating_distribution.png`.
    * Estimated marginal‑effects plot → `figures/marginal_effects.png`.
    * Exclusion‑flow diagram → `figures/exclusion_flow.png`.
  - Provide verification script `tests/integration/test_report_verification.py` that asserts every numeric entry in the tables appears in `data/processed/results.json` or `data/processed/cleaned_responses.csv` and that each figure file exists and is non‑empty.

- [ ] T008 [US4] Write a concise methods/results account in `data/results/report.md`.
  - Describe sampling rule, manipulation validation outcomes (CLIP similarity, RMS contrast change, moral‑intent preservation, human‑check agreement), cleaning exclusion rate, model convergence status, effect sizes with CIs, corrected p‑values, power and precision flags, and any negative findings (e.g., reduced power, failed manipulations).
  - Every claim references a concrete artifact path (`data/...` or `figures/...`).

- [ ] T009 [US4] Re‑run the documented workflow end‑to‑end and record the paper‑stage handoff in `data/results/handoff.md`.
  - Re‑execute tasks T001 → T008 per `quickstart.md` with pinned seeds.
  - Confirm all unit/integration tests pass (`pytest tests/`) and that the re‑run produces **byte‑identical** `data/processed/results.json` (the file contains no timestamp fields).
  - Record in `handoff.md` the artifacts required by the subsequent paper pipeline: CLMM tables, figures, power/precision statements, limitation discussion, and the pre‑registration source (`config/pre_registration.yaml`).

- [ ] T013 [US1] Create and pin `code/requirements.txt` listing all dependencies with exact versions, then verify its existence with `code/10_verify_requirements.py`.
  - Verification: unit test `tests/unit/test_requirements.py` asserts the file exists and matches the environment’s installed package list.
