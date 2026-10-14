# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/` for feature `001-visual-salience-moral-judgments`
**Re-plan note**: Consolidates the prior task list (which contained a duplicate T022 identity and many non-verifiable micro-tasks) into a smaller set of substantive, deterministically verifiable research tasks. All scientific requirements (FR-001–FR-008) are preserved. Synthetic/mock data generation, polling-wait tasks, and platform scaffolding are removed: every analysis task must consume REAL data from a REAL fetch, and any failed fetch must raise (fail loudly).

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Establish the runnable pipeline entry point and verified data ingestion in `code/01_ingest_and_filter.py`.
  - Fetch real image data from the canonical Hugging Face source (e.g., `datasets.load_dataset("visual_genome", ...)` or the MoralD dataset if a verified source is injected via the `VERIFIED_DATA_SOURCE` environment variable — in that case use that exact recipe as the single source).
  - Stream or sample a real subset (fixed seed 42, first N image records with `social`/`conflict`-style metadata tags; state the exact sampling rule in the script docstring) so the run fits ≤7 GB RAM; the loader MUST raise `DataFetchError` on any fetch failure — no synthetic fallback of any kind.
  - Output candidate scenario rows to `data/processed/candidates_filtered.csv` conforming to `contracts/dataset.schema.yaml`, with per-image SHA-256 checksums in `data/raw/sample_metadata.json`.
  - Document the runnable command in the feature's `quickstart.md`.
  - Verification: `python code/01_ingest_and_filter.py` exits 0 and produces `data/processed/candidates_filtered.csv` with ≥1 real row whose `original_image_path` points to an existing downloaded image file under `data/raw/`; unit test `tests/unit/test_data_loader.py` simulates a fetch failure and asserts `DataFetchError` is raised.

- [ ] T002 [US1] Implement moral-ambiguity identification in `code/02_human_coding.py` (FR-008).
  - Ingest ≥3 real annotator rating files (5-point Likert ambiguity ratings) from `data/raw/human_coding/`; raise `InsufficientAnnotatorsError` if fewer than 3 distinct annotator files are present — never generate mock or simulated annotations.
  - Compute per-scenario mean ambiguity score and Cohen's κ; retain scenarios with mean ≥ 3.5 AND κ ≥ 0.6 (majority vote resolves disagreements); cross-reference retained scenarios against an external pre-validated resource (e.g., MoralD) and log the match in `data/processed/ground_truth_match.csv`.
  - Output `data/processed/valid_scenarios.csv` conforming to `contracts/dataset.schema.yaml`.
  - Verification: unit test `tests/unit/test_human_coding.py` validates `calculate_cohens_kappa` on hand-computed example ratings and the retention filter logic; the script raises loudly when annotator files are absent.

- [ ] T003 [US1] Implement salience manipulation and semantic-integrity verification in `code/03_manipulate_stimuli.py` (FR-001).
  - Read versioned parameters from `config/manipulation.yaml` (fields: `version`, `seed`, `luminance_levels`, `target_region`, `output_path`); generate low/medium/high luminance-contrast/brightness variants of the ROI (bounding-box defined) of each valid scenario's real image into `data/processed/stimuli/`.
  - Verify each variant: RMS contrast change ≥ 15% in the ROI, CLIP cosine similarity ≥ 0.95 between original and manipulated image (CPU-tractable CLIP with `torch.no_grad()` and batching; if CUDA is available use `device="cuda"`), texture/edge-density change < 0.05 (Laplacian variance), and non-target-region SSIM recorded.
  - Log and exclude failures (edge case: target-object detection failure → logged, excluded); write the stimulus manifest `data/processed/stimulus_manifest.json` with entries conforming to `contracts/stimuli_manifest.schema.yaml` and `contracts/stimulus.schema.yaml` (including `clip_similarity`, `rms_contrast_change`, `moral_intent_preservation_score`, `semantic_integrity`).
  - Verification: unit test `tests/unit/test_manipulation.py` checks that a manipulated variant of a real image shows ≥15% ROI RMS contrast change and that the manifest validates against the contract schema; a first end-to-end run on the real candidate subset produces real stimulus files and manifest rows under `data/processed/`.

**Checkpoint**: The documented command chain (`01` → `02` → `03`) executes on real downloaded images and produces verifiable real stimulus artifacts. No report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Implement the within-subject survey randomization engine and response logging in `code/04_survey_deployment.py` (FR-002, FR-003).
  - Generate per-participant presentation sequences from the real stimulus manifest respecting: no two identical scenarios in a row, balanced salience order across participants (Latin-square style), and each participant sees each scenario at exactly one salience level per block, never the same variant twice.
  - Present the real manipulated images, collect 1–7 blame ratings (1=Not at all blameworthy, 7=Extremely blameworthy), and log each response with `response_id`, `participant_id`/`user_id`, `stimulus_id`/`variant_id`, salience level, blame rating, ISO-8601 timestamp, attention-check pass, and completion status to `data/processed/responses.csv`, conforming to `contracts/response.schema.yaml` and `contracts/survey_responses.schema.yaml`.
  - The deployment MUST abort with `DataIntegrityError` if the stimulus manifest's `source_type` is `synthetic` (no synthetic stand-ins are permitted anywhere).
  - Verification: unit test `tests/unit/test_survey_logic.py` verifies the randomization constraints on generated sequences; unit test `tests/unit/test_data_schema.py` validates logged rows against the response contract; integration test `tests/integration/test_survey_flow.py` runs a full pilot session end-to-end and confirms complete logging with no truncation.

- [ ] T005 [US3] Implement data cleaning in `code/05_data_cleaning.py` (FR-007).
  - Read the real responses from `data/processed/responses.csv`; exclude straight-lining participants (rating variance < 0.1 OR > 90% identical ratings); flag excluded participants with reason per `contracts/participant.schema.yaml`.
  - Output `data/processed/cleaned_responses.csv` with a `valid` flag per response and a per-participant summary including exclusion rate.
  - Verification: unit test `tests/unit/test_data_cleaning.py` checks the straight-lining detection rule on constructed rating vectors (the rule test uses fixed input vectors, not fabricated study data); the script runs on the real response file and reports the actual exclusion rate.

- [ ] T006 [US3] Implement the CLMM analysis with convergence fallback, corrections, and effect sizes in `code/06_analysis_clmm.py` (FR-004, FR-005, FR-006).
  - Fit `blame_rating ~ salience + (1|participant) + (1|scenario)` as a Cumulative Link Mixed Model on the cleaned real responses; check convergence and, on failure, switch to a robust alternative (LMM with robust SE or Wilcoxon signed-rank with Bonferroni), recording `convergence_status` and `fallback_method`.
  - Perform post-hoc pairwise comparisons (low vs medium, medium vs high, low vs high) with Tukey adjustment (Bonferroni for the fallback); compute odds ratios and 95% CIs for the salience fixed effect.
  - Perform post-hoc power analysis with the observed effect size and flag if power < 0.80; load the precision threshold from `config/pre_registration.yaml` (raise `PreRegistrationError` if missing or `verification_status: UNVERIFIED`) and record CI width against it.
  - Write results to `data/results/results.json` conforming to `contracts/analysis_schema.schema.yaml` (including `post_hoc_tests`, `exclusion_rate`, `sample_size`, `power_analysis`, `convergence_status`).
  - Verification: unit test `tests/unit/test_analysis.py` runs the pipeline on a constructed calibration dataset with a known injected coefficient (β=0.5) and verifies the recovered effect within an acceptable margin, correct correction application, and fallback logic; integration test `tests/integration/test_analysis_pipeline.py` runs the full analysis on the real cleaned data and checks `results.json` validates against the contract schema.

- [ ] T007 Generate the specified tables and figures directly from the validated outputs.
  - From `data/results/results.json` and `data/processed/cleaned_responses.csv`, produce: a fixed-effects/odds-ratio table with CIs, a post-hoc comparison table, a power/precision summary, and figures (rating distributions by salience level, estimated marginal effects with CI bands, exclusion-flow summary) into `data/results/` and `figures/`.
  - All values must be read programmatically from the result artifacts — no hand-typed numbers.
  - Verification: a check script asserts every number in the tables appears in `results.json` or `cleaned_responses.csv`, and every figure file exists and is non-empty.

## Phase 3: Reproducible results and paper handoff

- [ ] T008 Write a concise methods/results account in `data/results/report.md` linked to the actual output cells and figure files.
  - Describe the sampling rule and its representativeness limitation (streamed/sampled subset of the real dataset, exact N stated), the manipulation validation outcomes (CLIP similarity, RMS contrast change, exclusions), the cleaning exclusion rate, model convergence status, effect sizes with CIs, corrected p-values, power and precision flags, and any negative findings or failures honestly (including the edge-case handling: undersized sample → reduced-power warning; failed manipulations → logged exclusions).
  - Verification: every claim in `report.md` references a concrete artifact path (`data/results/...`, `figures/...`).

- [ ] T009 Re-run the documented workflow end-to-end from its declared inputs and document the paper-stage handoff.
  - Re-execute `code/01` → `code/06` per `quickstart.md` with pinned seeds; confirm all unit/integration tests pass (`pytest tests/`) and that re-running reproduces identical result artifacts (checksummed into `data/checksums.txt`).
  - Record in `data/results/handoff.md` the paper-stage requirements preserved for the subsequent pipeline: CLMM tables with effect sizes and CIs, figures, power/precision statements, limitations section, and the pre-registered threshold source (`config/pre_registration.yaml`).
  - Verification: the re-run produces byte-identical `results.json` (modulo timestamps) and `pytest` exits 0.

## Dependencies and requirement coverage

| Requirement | Tasks | Demonstrating command |
|---|---|---|
| FR-001 (ingest + salience manipulation, CLIP ≥ 0.95, RMS ≥ 15%, texture < 0.05) | T001, T003 | `python code/03_manipulate_stimuli.py` |
| FR-002 (randomized within-subject survey) | T004 | `pytest tests/unit/test_survey_logic.py` |
| FR-003 (1–7 blame ratings, structured logging) | T004 | `pytest tests/unit/test_data_schema.py` |
| FR-004 (CLMM, random intercepts, convergence fallback) | T006 | `python code/06_analysis_clmm.py` |
| FR-005 (Tukey/Bonferroni corrections) | T006 | `pytest tests/unit/test_analysis.py` |
| FR-006 (odds ratios, CIs) | T006, T007 | `data/results/results.json` |
| FR-007 (straight-liner exclusion) | T005 | `python code/05_data_cleaning.py` |
| FR-008 (two-stage ambiguity identification, κ ≥ 0.6, external cross-reference) | T002 | `python code/02_human_coding.py` |

Execution order: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009. T002 depends on T001 (candidates); T003 depends on T002 (valid scenarios); T004 depends on T003 (stimulus manifest); T005–T009 depend on their predecessors per data flow.

## Revision behavior

Prior working artifacts and verified requirements are preserved in intent; the malformed duplicate task identity (`T022` appearing as both randomization engine and unit test) and non-verifiable micro-tasks (directory creation, config-file boilerplate, polling-wait tasks, synthetic-data generation, linting/refactoring/profiling chores) are consolidated into the nine substantive tasks above. No test or constraint was weakened; no synthetic or mock data path remains in any task.
