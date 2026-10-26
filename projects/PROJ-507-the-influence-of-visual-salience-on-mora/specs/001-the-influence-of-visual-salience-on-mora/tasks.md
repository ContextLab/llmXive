# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/` for feature `001-visual-salience-moral-judgments`

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully‑executable pipeline on a small real subset to prove that all downstream steps can be triggered without error. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T001** [US‑001] **Ingest and filter raw images from Visual Genome** – `code/01_ingest_and_filter.py`   <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/01_ingest_and_filter.py exit=-1 (TIMEOUT) -->
  - Stream the **Visual Genome** image dataset with `datasets.load_dataset("visual_genome", "images", split="train", streaming=True)`.  
  - Keep records whose `metadata.tags` contain **“conflict”** or **“social”** and that have a downloadable image URL.  
  - Limit to the first **200** matching records (fixed seed 42) so RAM < 2 GB.  
  - **Determinism**: set `random.seed(42)` and `np.random.seed(42)` at script start.  
  - Create `data/raw/images/` if it does not exist; download each image there and compute a SHA‑256 checksum stored in `data/raw/checksums.json`.  
  - Write `data/processed/candidates_filtered.csv` conforming to `contracts/dataset.schema.yaml`.  
  - **Verification**:  
    - Running `python code/01_ingest_and_filter.py` exits 0.  
    - The CSV contains ≥ 1 row and every `original_image_path` points to an existing file under `data/raw/images/`.  
    - Unit test `tests/unit/test_data_loader.py` asserts that a simulated fetch failure raises a `DataFetchError`.

- [ ] **T002** [US‑001] **Create human‑coding directory and template** – `code/02_prepare_human_coding_dir.py`  
  - Create the folder `data/raw/human_coding/` (must exist after execution).  
  - Generate a **template CSV** `data/raw/human_coding/annotations_template.csv` that lists all `scenario_id`s from `candidates_filtered.csv` and provides columns for three independent annotators to record a 1‑5 ambiguity rating.  
  - Include a short README in the same folder describing the annotation procedure and required number of raters.  
  - **Verification**:  
    - After script execution the folder and template file are present.  
    - Integration test `tests/integration/test_human_coding_dir.py` checks that the file count matches the number of scenarios and that the header columns are correct.

- [ ] **T003** [US‑001] **Process human‑coding annotations and select ambiguous scenarios** – `code/03_process_human_coding.py`  
  - Load all annotation CSVs placed in `data/raw/human_coding/` (at least three per scenario).  
  - Compute for each scenario:  
    1. **Mean ambiguity score** (1‑5 Likert).  
    2. **Cohen’s κ** across the three annotators.  
  - Retain scenarios where **mean ≥ 3.5** **and** **κ ≥ 0.6**.  
  - Cross‑reference retained IDs against the external **MoralD** benchmark (provided via `datasets.load_dataset("moral_d")`). Write matches to `data/processed/ground_truth_match.csv`.  
  - Output `data/processed/valid_scenarios.csv` conforming to `contracts/dataset.schema.yaml`.  
  - **Verification**:  
    - Unit test `tests/unit/test_human_coding.py` validates `calculate_cohens_kappa` on a hand‑computed example and checks that the filtering logic keeps only scenarios meeting both thresholds.  
    - The script aborts loudly (`raise RuntimeError`) if any required annotation file is missing.

- [ ] **T015** **Provide a thin wrapper for the moral‑intent model** – `code/bert_moral_intent.py`  
  - Download the `bert-base-uncased` checkpoint fine‑tuned on MoralD from Hugging Face (`transformers.AutoModelForSequenceClassification`).  
  - Verify the file checksum (SHA‑256) against the published hash.  
  - Expose `compute_preservation_score(original_image_path, manipulated_image_path)` that:  
    1. Generates captions for both images using a pretrained caption model.  
    2. Encodes captions with BERT and returns the Pearson correlation with a reference moral‑intent vector.  
    3. Must return ≥ 0.90 on a sanity‑check image.  
  - **Verification**: Unit test `tests/unit/test_bert_moral_intent.py` checks checksum, runs the sanity inference, and asserts the correlation threshold.

- [ ] **T004** [US‑001] **Generate salience‑manipulated stimulus variants** – `code/04_manipulate_stimuli.py`  
  - Read manipulation parameters from `config/manipulation.yaml` (contrast & brightness levels for low/medium/high).  
  - For each valid scenario (from **T003**) detect the ROI using Sobel edge detection, then create three variants by adjusting contrast/brightness as specified.  
  - Save PNGs under `data/processed/stimuli/` with filenames `<scenario_id>_low.png`, `<scenario_id>_medium.png`, `<scenario_id>_high.png`.  
  - Validate each variant:  
    * **RMS contrast change** in ROI ≥ 15 %.  
    * **CLIP cosine similarity** ≥ 0.95 (CPU first; fallback to GPU if `torch.cuda.is_available()`).  
    * **Texture/edge‑density change** < 0.05 (Laplacian variance).  
    * **Moral‑intent preservation score** ≥ 0.90 using the wrapper from **T015**.  
  - Log any failures to `logs/manipulation_errors.log` and exclude those stimuli from downstream files.  
  - Write `data/processed/stimuli_manifest.csv` (schema `contracts/stimuli_manifest.schema.yaml`) listing one row per variant with all validation metrics.  
  - **Verification**:  
    - Unit test `tests/unit/test_manipulation.py` checks that a real image produces ≥ 15 % RMS contrast change, CLIP ≥ 0.95, texture change < 0.05, and that the CSV validates against its schema.

- [ ] **T005** [US‑001] **Automated pilot human manipulation check** – `code/05_human_manipulation_check.py`  
  - Use a pre‑collected pilot‑check dataset (`data/processed/pilot_human_check.csv`) containing binary judgments from ≥ 5 coders on 20 randomly sampled manipulated images.  
  - Compute the proportion of “preserved” responses; require **≥ 80 %** agreement.  
  - Append a boolean column `human_narrative_preserved` to each row in `stimuli_manifest.csv`.  
  - Summarize results in `data/processed/human_check_report.md`.  
  - **Verification**: Unit test `tests/unit/test_human_check.py` loads the pilot file, validates the agreement calculation, and aborts if the threshold is not met.

- [ ] **T016** **A‑priori power analysis for target sample size** – `code/00_pilot_power_analysis.py`  
  - Perform a simulation‑based power analysis (or invoke G*Power) targeting a medium effect (odds ratio ≈ 1.5) with α = 0.05 (Bonferroni‑adjusted for three pairwise tests), participant ICC = 0.10, scenario ICC = 0.05.  
  - Determine the required total N (≈ 600) and participants per scenario.  
  - Write results to `config/pre_registration.yaml` under `required_sample_size` and store the full simulation output in `data/processed/power_analysis_a_priori.json`.  
  - **Verification**: Unit test `tests/unit/test_power_a_priori.py` checks that the computed N meets the specification and that the JSON contains the expected fields.

---

## Phase 2 – Complete study, validation, and analysis  

- [ ] **T006** [US‑002] **Deploy within‑subject survey (simulated participants)** – `code/06_survey_deployment.py`  
  - Load `stimuli_manifest.csv` and generate a **Latin‑square** schedule ensuring:  
    1. No identical scenario appears consecutively for a participant.  
    2. Salience order is balanced across participants.  
    3. Each participant sees each scenario at exactly one salience level per block.  
  - For automated CI runs, use a **simulated participant pool** (`data/processed/mock_participants.csv`) generated from the a‑priori power analysis.  
  - Interface with the recruitment API only in a manual “real‑deployment” mode (outside CI).  
  - Present each stimulus image, record a 1‑7 blame rating, and write two files per run:  
    * `data/processed/responses_raw.csv` (schema `contracts/response.schema.yaml`).  
    * `data/processed/responses_survey_raw.csv` (schema `contracts/survey_responses.schema.yaml`).  
  - Abort with `DataIntegrityError` if the manifest’s `source_type` is `synthetic`.  
  - **Verification**: Unit test `tests/unit/test_survey_logic.py` checks randomisation constraints; integration test `tests/integration/test_survey_flow.py` runs a pilot session using the mock participants, confirms the required number of participants logged, and validates both CSVs against their schemas.

- [ ] **T007** [US‑003] **Clean raw responses and exclude straight‑liners** – `code/07_data_cleaning.py`  
  - Load `responses_raw.csv`.  
  - For each participant compute rating variance; flag exclusion if variance < 0.1 **or** > 90 % identical ratings.  
  - Also flag participants who fail the embedded attention check in `responses_survey_raw.csv`.  
  - Write `data/processed/responses_cleaned.csv` (adds a `valid` flag per response) and `data/processed/participants_excluded.csv` (schema `contracts/participant.schema.yaml`).  
  - **Verification**: Unit test `tests/unit/test_data_cleaning.py` runs on a synthetic dataset with known straight‑liners and asserts correct exclusion; script prints the actual exclusion rate.

- [ ] **T008** [US‑003] **Fit CLMM with robust fallback and report power/precision** – `code/08_analysis_clmm.py`  
  - Load `responses_cleaned.csv`.  
  - Fit a **Cumulative Link Mixed Model**: `blame_rating ~ salience_level + (1|participant_id) + (1|scenario_id)`.  
  - If the optimizer fails to converge, automatically switch to a **Linear Mixed Model** with 10 000 bootstrap robust SEs (preserving the ordinal outcome).  
  - Perform **Bonferroni‑adjusted** pairwise contrasts (low‑vs‑medium, medium‑vs‑high, low‑vs‑high).  
  - Compute odds‑ratio effect size with 95 % CI, Type III sums of squares, and store under `effect_size`.  
  - Run a post‑hoc power simulation using the observed odds‑ratio; set `power_flag` if observed power < 0.80.  
  - Verify CI width against the pre‑registered precision threshold (0.30) and set `precision_flag`.  
  - Write `data/processed/analysis_results.json` conforming to `contracts/analysis_schema.yaml`.  
  - **Verification**: Unit test `tests/unit/test_analysis.py` runs the pipeline on a synthetic dataset with injected β = 0.5 and checks that the recovered effect meets tolerance, that correction and fallback logic work, and that the JSON validates; integration test `tests/integration/test_analysis_pipeline.py` runs on the real cleaned data and asserts schema compliance.

- [ ] **T009** [US‑003] **Generate figures, tables, and verification script** – `code/09_generate_reports.py`  
  - From `analysis_results.json` and `responses_cleaned.csv` produce:  
    * `figures/odds_ratio_table.csv` (fixed‑effects odds‑ratio & CI).  
    * `figures/posthoc_table.csv` (pairwise contrast statistics, Bonferroni‑adjusted).  
    * `figures/power_summary.txt` (observed power, flags).  
    * `figures/rating_distribution.png` (histograms per salience level).  
    * `figures/marginal_effects.png` (predicted probability curves).  
    * `figures/exclusion_flow.png` (Sankey diagram of participant flow).  
  - Provide `tests/integration/test_report_verification.py` that loads each figure/table and asserts that every numeric entry appears in `analysis_results.json` or `responses_cleaned.csv`, and that each file is non‑empty.  
  - **Verification**: Running `pytest -q tests/integration/test_report_verification.py` must pass.

- [ ] **T010** [US‑003] **Write methods & results markdown with automated verification** – `data/results/report.md`  
  - Summarise:  
    1. Sampling rule for image ingestion.  
    2. Manipulation validation metrics (CLIP, RMS contrast, moral‑intent score, human‑check agreement).  
    3. Participant exclusion statistics.  
    4. Model convergence status and fallback used (if any).  
    5. Effect‑size tables with CIs, corrected p‑values.  
    6. Observed power & precision flags.  
    7. Limitations (e.g., reduced sample size).  
  - Every claim cites a concrete artifact path (e.g., `figures/odds_ratio_table.csv`, `data/processed/stimuli_manifest.csv`).  
  - **Automated verification**: Added `code/10_verify_report.py` and unit test `tests/unit/test_report_verification.py` which checks that all required sections are present, citations resolve to existing files, and no placeholder text remains.  

- [ ] **T011** [US‑003] **Paper‑stage handoff** – `data/results/handoff.md`  
  - Re‑run the full workflow from **T001** through **T010** using the exact commands listed in `quickstart.md` (pinned seeds, deterministic RNG).  
  - Confirm that all unit/integration tests pass (`pytest`).  
  - Verify that `data/processed/analysis_results.json` is byte‑identical between runs (no timestamps).  
  - List the artifacts required by the downstream paper pipeline: CLMM results JSON, all figures, tables, and the pre‑registration file (`config/pre_registration.yaml`).  
  - **Verification**: Script `code/10_verify_handoff.py` computes SHA‑256 of `analysis_results.json` before and after a fresh run and asserts equality.

---

## Phase 3 – Reproducibility scaffolding  

- [ ] **T012** [P] **Create `quickstart.md` with a reproducible entry‑point** – `docs/quickstart.md`  
  - Provide a step‑by‑step command list (environment setup, `pip install -r code/requirements.txt`, `python -m llmxive_toolkit.paths && python code/01_ingest_and_filter.py`, …, `python code/09_generate_reports.py`).  
  - Include the exact seed values and environment variables required for deterministic execution.  
  - **Verification**: Running the commands on a fresh clone reproduces the end‑to‑end results and all tests pass.

- [ ] **T013** [P] **Pin exact dependencies** – `code/requirements.txt` & verification script `code/10_verify_requirements.py`  
  - List all packages with exact version numbers (e.g., `torch==2.2.0`, `datasets==2.18.0`, `statsmodels==0.14.0`, etc.).  
  - `code/10_verify_requirements.py` compares the file against the current Python environment (`pip freeze`) and exits 0 only if they match.  
  - **Verification**: Unit test `tests/unit/test_requirements.py` asserts existence of the file and that the script returns exit 0 in the CI environment.

- [ ] **T014** [P] **Validate configuration files** – `code/11_validate_configs.py`  
  - Ensure `config/manipulation.yaml`, `config/pre_registration.yaml`, and `config/analysis.yaml` exist, contain all required keys, and that `pre_registration.yaml` has `verification_status: VERIFIED`.  
  - Raise `ConfigError` with a clear message for any missing key or mismatched status.  
  - **Verification**: Unit test `tests/unit/test_config_validation.py` loads each YAML and checks schema compliance.

- [ ] **T017** **Validate generated artifacts against contract schemas** – `code/12_validate_contracts.py`  
  - For every data file produced in Phases 1‑2 (CSV, YAML, JSON), run JSON/YAML schema validation against the corresponding schema in `contracts/`.  
  - Abort with `ContractValidationError` if any artifact fails.  
  - **Verification**: Unit test `tests/unit/test_contract_validation.py` loads a sample artifact and confirms successful validation.

---  

### Dependency & Requirement Mapping  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| **FR‑001** (salience manipulation) | T004, T005, T015 |
| **FR‑002** (survey randomisation) | T006 |
| **FR‑003** (blame rating collection) | T006 |
| **FR‑004** (CLMM with fallback) | T008 |
| **FR‑005** (Bonferroni / Tukey) | T008 |
| **FR‑006** (effect size reporting) | T008 |
| **FR‑007** (straight‑liner exclusion) | T007 |
| **FR‑008** (ambiguous scenario identification) | T001, T002, T003 |
| **FR‑009** (a‑priori power analysis) | T016 |
| **SC‑001** (stimulus integrity metrics) | T004, T005 |
| **SC‑002** (effect size detection) | T008 |
| **SC‑003** (family‑wise error control) | T008 |
| **SC‑004** (valid participant proportion) | T007 |
| **SC‑005** (CI width precision) | T008 |

All tasks are ordered to respect data flow: ingestion → human coding → moral‑intent wrapper → stimulus creation → pilot checks → power analysis → survey → cleaning → analysis → reporting → handoff.  
