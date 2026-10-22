# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/` for feature `001-visual-salience-moral-judgments`

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully‑executable pipeline on a small real subset to prove that all downstream steps can be triggered without error. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T001** [US‑001] **Ingest and filter raw images** – `code/01_ingest_and_filter.py`   <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 -->
  - Stream the **Open Images V6** dataset (`datasets.load_dataset("open_images", "v6", split="train", streaming=True)`).  
  - Filter records that contain the tags `conflict` **or** `social` and have a downloadable image URL.  
  - Limit to the first **200** matching records (fixed seed 42) so RAM < 2 GB.  
  - For each kept record, download the image into `data/raw/` and compute a SHA‑256 checksum stored in `data/raw/checksums.json`.  
  - Write `data/processed/candidates_filtered.csv` conforming to `contracts/dataset.schema.yaml`.  
  - **Verification**: `python code/01_ingest_and_filter.py` exits 0, the CSV contains ≥ 1 row, each `original_image_path` points to an existing file under `data/raw/`, and unit test `tests/unit/test_data_loader.py` asserts that a simulated fetch failure raises `DataFetchError`.

- [ ] **T002** [US‑001] **Acquire human ambiguity annotations** – `code/02_acquire_annotations.py`  
  - Create a folder `data/raw/human_coding/`.  
  - Provide a CLI that, given a list of `scenario_id`s from `candidates_filtered.csv`, generates a **template CSV** (`annotations_template_<annotator_id>.csv`) for external crowdsourcing (e.g., Prolific).  
  - After manual collection, the script validates that **≥ 3** annotation files exist and that each scenario has **≥ 3** ratings; otherwise it raises `InsufficientAnnotatorsError`.  
  - **Verification**: unit test `tests/unit/test_annotation_acquisition.py` checks file count and per‑scenario rating counts.

- [ ] **T003** [US‑001] **Process human coding and select ambiguous scenarios** – `code/03_process_human_coding.py`  
  - Load all annotation CSVs produced by **T002**.  
  - Compute per‑scenario mean ambiguity score (1‑5 Likert) and Cohen’s κ.  
  - Retain scenarios with mean ≥ 3.5 **and** κ ≥ 0.6.  
  - Cross‑reference retained IDs against the external MoralD benchmark; write matches to `data/processed/ground_truth_match.csv`.  
  - Output `data/processed/valid_scenarios.csv` (schema `contracts/dataset.schema.yaml`).  
  - **Verification**: unit test `tests/unit/test_human_coding.py` validates `calculate_cohens_kappa` on a hand‑computed example and checks the filter logic; script aborts loudly if any required file is missing.

- [ ] **T015** **Provide a thin wrapper for the moral‑intent model** – `code/bert_moral_intent.py`  
  - Download the `bert‑moral‑intent` checkpoint from Hugging Face (`transformers.AutoModelForSequenceClassification`).  
  - Verify checksum (SHA‑256) against the published hash.  
  - Run the Reference‑Validator Agent on the model citation to ensure verified accuracy (Constitution II).  
  - Expose `compute_preservation_score(original_image, manipulated_image)` that extracts image captions via a pretrained caption model, encodes them with BERT, and returns Pearson correlation with reference moral‑intent scores (must be ≥ 0.90 on a sanity‑check image).  
  - **Verification**: unit test `tests/unit/test_bert_moral_intent.py` checks the checksum, runs the sanity inference, and asserts the correlation threshold.

- [ ] **T004** [US‑001] **Generate salience‑manipulated stimulus variants** – `code/04_manipulate_stimuli.py`  
  - Read manipulation parameters from `config/manipulation.yaml` (contrast & brightness levels for low/medium/high).  
  - For each valid scenario (from **T003**) detect the ROI using Sobel edge detection; apply the three contrast/brightness settings, saving PNGs under `data/processed/stimuli/` with filenames `<scenario_id>_low.png`, etc.  
  - Validate each variant:  
    * RMS contrast change in ROI ≥ 15 % (computed with `numpy`).  
    * CLIP image‑embedding cosine similarity ≥ 0.95 (CPU first; if `torch.cuda.is_available()` use GPU).  
    * Texture/edge‑density change < 0.05 (Laplacian variance).  
    * Moral‑intent preservation score ≥ 0.90 using the wrapper from **T015**.  
  - Log failures to `logs/manipulation_errors.log` and exclude those stimuli from downstream files.  
  - Write two **YAML** manifest files:  
    1. `data/processed/stimulus_manifest.yaml` (schema `contracts/stimuli_manifest.schema.yaml`).  
    2. `data/processed/stimulus_variants.yaml` (schema `contracts/stimulus.schema.yaml`).  
  - **Verification**: unit test `tests/unit/test_manipulation.py` checks that a real image produces ≥ 15 % RMS contrast change, CLIP ≥ 0.95, texture change < 0.05, and that both YAML manifests validate against their schemas.

- [ ] **T005** [US‑001] **Pilot human manipulation check** – `code/05_human_manipulation_check.py`  
  - Recruit a separate coder panel (≥ 5 coders) and present a random sample of 20 manipulated images (mixed salience levels).  
  - Collect binary judgments on whether the original moral narrative is preserved.  
  - Compute proportion of “preserved” responses; require **≥ 80 %** agreement.  
  - Append a boolean field `human_narrative_preserved` to each entry in `stimulus_variants.yaml`.  
  - Log summary to `data/processed/human_check_report.md`.  
  - **Verification**: unit test `tests/unit/test_human_check.py` validates the agreement calculation and aborts if the threshold is not met.

- [ ] **T016** **A‑priori power analysis for target sample size** – `code/00_pilot_power_analysis.py`  
  - Perform a simulation‑based power analysis (or invoke G*Power via command‑line) targeting a medium effect (odds ratio ≈ 1.5) with α = 0.05 (Bonferroni‑adjusted for three pairwise tests), participant ICC = 0.10, scenario ICC = 0.05.  
  - Determine the required total N (≈ 600) and participants per scenario.  
  - Write results to `config/pre_registration.yaml` under `required_sample_size` and store the full simulation output in `data/processed/power_analysis_a_priori.json`.  
  - **Verification**: unit test `tests/unit/test_power_a_priori.py` checks that the computed N meets the specification and that the JSON conforms to `contracts/analysis_schema.yaml` (partial).

- [ ] **T006** [US‑002] **Deploy within‑subject survey** – `code/06_survey_deployment.py`  
  - Load `stimulus_manifest.yaml` and generate a Latin‑square schedule ensuring: (a) no identical scenario appears consecutively for a participant, (b) salience order is balanced across participants, (c) each participant sees each scenario at exactly one salience level per block.  
  - Interface with the platform’s recruitment API to obtain **the number of participants indicated by T016** (≈ 600). Store anonymised IDs in `data/processed/participants.csv`.  
  - Present each stimulus image, record a 1‑7 blame rating, and write two files per run:  
    * `data/processed/responses_variant.csv` (schema `contracts/response.schema.yaml`).  
    * `data/processed/responses_survey.csv` (schema `contracts/survey_responses.schema.yaml`).  
  - Abort with `DataIntegrityError` if the manifest’s `source_type` is `synthetic`.  
  - **Verification**: unit test `tests/unit/test_survey_logic.py` checks randomisation constraints; integration test `tests/integration/test_survey_flow.py` runs a pilot session end‑to‑end, confirms the required number of participants logged, and validates both CSVs against their schemas.

---

## Phase 2 – Complete study, validation, and analysis  

- [ ] **T007** [US‑003] **Clean raw responses and exclude straight‑liners** – `code/07_data_cleaning.py`  
  - Load `responses_variant.csv`.  
  - For each participant compute rating variance; flag exclusion if variance < 0.1 **or** > 90 % identical ratings.  
  - Also flag participants who fail the embedded attention check in `responses_survey.csv`.  
  - Write `data/processed/cleaned_responses.csv` (adds a `valid` flag per response) and `data/processed/participants_excluded.csv` (schema `contracts/participant.schema.yaml`).  
  - **Verification**: unit test `tests/unit/test_data_cleaning.py` runs on a synthetic dataset with known straight‑liners and asserts correct exclusion; script prints the actual exclusion rate.

- [ ] **T008** [US‑003] **Fit CLMM with robust fallback and report power/precision** – `code/08_analysis_clmm.py`  
  - Load `cleaned_responses.csv`.  
  - Fit a Cumulative Link Mixed Model: `blame_rating ~ salience + (1|participant) + (1|scenario)`.  
  - If the optimizer fails to converge, automatically switch to a Linear Mixed Model with bootstrapped (10 000) robust SEs; set `fallback_method` accordingly.  
  - Perform Bonferroni‑adjusted pairwise contrasts (low‑vs‑medium, medium‑vs‑high, low‑vs‑high).  
  - Compute odds‑ratio effect size with 95 % CI, Type III Sums of Squares, and store under `effect_size`.  
  - Run a post‑hoc power simulation using the observed odds‑ratio; flag `power_flag` if observed power < 0.80.  
  - Verify the CI width against the pre‑registered precision threshold (0.30) and set `precision_flag`.  
  - Write `data/processed/results.json` conforming to `contracts/analysis_schema.schema.yaml`.  
  - **Verification**: unit test `tests/unit/test_analysis.py` runs the pipeline on a synthetic dataset with injected β = 0.5 and checks that the recovered effect meets the tolerance, that correction and fallback logic work, and that the JSON validates; integration test `tests/integration/test_analysis_pipeline.py` runs on the real cleaned data and asserts schema compliance.

- [ ] **T009** [US‑003] **Generate figures, tables, and verification script** – `code/09_generate_reports.py`  
  - From `results.json` and `cleaned_responses.csv` produce:  
    * `figures/odds_ratio_table.csv` (fixed‑effects odds‑ratio & CI).  
    * `figures/posthoc_table.csv` (pairwise contrast statistics).  
    * `figures/power_summary.txt` (observed power, flags).  
    * `figures/rating_distribution.png` (histograms per salience level).  
    * `figures/marginal_effects.png` (predicted probability curves).  
    * `figures/exclusion_flow.png` (Sankey diagram of participant flow).  
  - Provide `tests/integration/test_report_verification.py` that loads each figure/table and asserts that every numeric entry appears in `results.json` or `cleaned_responses.csv`, and that each file is non‑empty.  
  - **Verification**: run `pytest -q tests/integration/test_report_verification.py` – must pass.

- [ ] **T010** [US‑003] **Write methods & results markdown** – `data/results/report.md`  
  - Summarise: (a) sampling rule for image ingestion, (b) manipulation validation metrics (CLIP, RMS contrast, moral‑intent score, human‑check agreement), (c) participant exclusion statistics, (d) model convergence status, (e) effect‑size tables with CIs, (f) corrected p‑values, (g) power & precision flags, and (h) any limitations (e.g., reduced sample size).  
  - Every claim cites a concrete artifact path (e.g., `figures/odds_ratio_table.csv`, `data/processed/stimulus_variants.yaml`).  
  - **Verification**: manual reviewer check – no automated test required.

- [ ] **T011** [US‑003] **Paper‑stage handoff** – `data/results/handoff.md`  
  - Re‑run the full workflow from **T001** through **T010** using the exact commands listed in `quickstart.md` (pinned seeds, deterministic RNG).  
  - Confirm that all unit/integration tests pass (`pytest`).  
  - Verify that `data/processed/results.json` is byte‑identical between runs (no timestamps).  
  - List the artifacts required by the downstream paper pipeline: CLMM results JSON, all figures, tables, and the pre‑registration file (`config/pre_registration.yaml`).  
  - **Verification**: a simple script `code/10_verify_handoff.py` computes SHA‑256 of `results.json` before and after a fresh run and asserts equality.

---

## Phase 3 – Reproducibility scaffolding  

- [ ] **T012** [P] **Create `quickstart.md` with a reproducible entry‑point** – `docs/quickstart.md`  
  - Provide a step‑by‑step command list (environment setup, `pip install -r code/requirements.txt`, `python -m llmxive_toolkit.paths && python code/01_ingest_and_filter.py`, …, `python code/09_generate_reports.py`).  
  - Include the exact seed values and environment variables required for deterministic execution.  
  - **Verification**: running the commands on a fresh clone reproduces the end‑to‑end results and all tests pass.

- [ ] **T013** [P] **Pin exact dependencies** – `code/requirements.txt` & verification script `code/10_verify_requirements.py`  
  - List all packages with exact version numbers (e.g., `torch==2.2.0`, `datasets==2.18.0`, `statsmodels==0.14.0`, etc.).  
  - `code/10_verify_requirements.py` compares the file against the current Python environment (`pip freeze`) and exits 0 only if they match.  
  - **Verification**: unit test `tests/unit/test_requirements.py` asserts existence of the file and that the script returns exit 0 in the CI environment.

- [ ] **T014** [P] **Validate configuration files** – `code/11_validate_configs.py`  
  - Ensure `config/manipulation.yaml`, `config/pre_registration.yaml`, and `config/analysis.yaml` exist, contain all required keys, and that `pre_registration.yaml` has `verification_status: VERIFIED`.  
  - Raise `ConfigError` with a clear message for any missing key or mismatched status.  
  - **Verification**: unit test `tests/unit/test_config_validation.py` loads each YAML and checks schema compliance.

- [ ] **T017** **Validate generated artifacts against contract schemas** – `code/12_validate_contracts.py`  
  - For every data file produced in Phases 1‑2 (CSV, YAML, JSON), run JSON/YAML schema validation against the corresponding schema in `contracts/`.  
  - Abort with `ContractValidationError` if any artifact fails.  
  - **Verification**: unit test `tests/unit/test_contract_validation.py` loads a sample artifact and confirms successful validation.
