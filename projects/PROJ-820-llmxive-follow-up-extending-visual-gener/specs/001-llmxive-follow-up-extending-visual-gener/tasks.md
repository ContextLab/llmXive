# Tasks: llmXive follow-up: extending "Visual Generation in the New Era: An Evolution from Atomic Mapping to "

**Inputs**: Active `spec.md`, `plan.md`, data-model, contracts, and prior verification feedback.  
**Scope**: N=500 scenes per group (2 groups, 1000 total generations) on CPU‑only free runner; N=500 satisfies FR‑001/FR‑008 power requirement.

## Path conventions

Paths are relative to the project root (`projects/PROJ-820-llmxive-follow-up-extending-visual-gener/`). Code lives in `code/`, tests in `code/tests/`, results under `data/`. The platform's `llmxive_toolkit.paths` creates output folders on demand, so no standalone directory‑creation tasks exist.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Generate the full stimulus dataset (500 main scenes + 50 validation scenes) with deterministic script `code/data/make_scenes.py` (seed=42). The script writes `data/raw/scene_descriptions.csv` (500 rows) and `data/raw/validation_scenes.csv` (50 rows) using the predefined templates. **Verification**: both CSVs exist, are non‑empty, parse with pandas, contain ≥500 and ≥50 rows, and every description matches a template.

- [ ] T002 [US1] Implement `code/simulation/physics_engine.py` (pymunk, single CPU core). For each scene in `scene_descriptions.csv`, parse objects/relations, run a pymunk simulation, detect logical contradictions (e.g., cyclical “above” rules), and write a JSON file to `data/derived/physics_constraints/{scene_id}.json` that conforms **exclusively** to `specs/001-llmxive-follow-up-extending-visual-gener/contracts/physics-constraint.schema.yaml`. Contradictory scenes are excluded; a log `data/derived/physics_constraints/contradiction_log.json` records them and the overall contradiction **rate** (must be **< 5 %**). **Verification**: `pytest code/tests/unit/test_physics_logic.py` passes; schema validation succeeds; contradiction rate < 5 %.

- [ ] T003 [US1] Implement `code/generation/prompt_engine.py` to read the scene text and its physics JSON and write **two** prompt files per scene under `data/derived/prompts/`:
  * `{scene_id}_baseline.txt` – original text only.
  * `{scene_id}_experimental.txt` – text plus a deterministic natural‑language descriptor derived from the JSON `natural_language_descriptor`.  
  **Verification**: for every valid scene both files exist, are single‑line non‑empty strings, and the experimental descriptor is a pure function of the physics JSON (unit‑tested).

- [ ] T004 [US2] Implement deterministic seed locking:
  * `code/generation/seed_manifest.py` creates `data/derived/seed_manifest.json` mapping each scene to a shared integer seed used for baseline and experimental generations.
  * `code/generation/diffusion_runner.py` loads the distilled CPU‑optimized diffusion model `latent-consistency/lcm-lora-sdv1-5` (`device="cpu"`), reads prompts, and generates images at 512×512. If the model only approximates seed control, generate **N=5** candidates per prompt using the same seed, compute SSIM against the reference geometry (pymunk bounding boxes projected onto a 512×512 canvas), and select the best. Record the mode (`exact` vs `fallback`) and **verify** that the selected image’s bounding‑box deviation is **≤ 1 pixel**. Retries up to 3 times on failure; unrecoverable failures are logged to `data/derived/generated_images/generation_failure_log.json`. Images are saved to `data/derived/generated_images/{baseline,experimental}/{scene_id}.png`.  
  **Verification**: smoke run on 5 scenes produces 10 PNGs, no CUDA errors, `seed_lock_status.json` records mode, and the bounding-box deviation is verified to be ≤ 1 pixel.

- [ ] T005 Run the full generation: execute `code/main.py --phase gen` over all 500 valid scenes for both baseline and experimental groups, producing the complete image sets in `data/derived/generated_images/{baseline,experimental}/`. Produce `data/derived/generated_images/manifest.csv` (image_id, prompt_id, group, seed, status). Exclude any scenes listed in `generation_failure_log.json` from the statistical denominator.  
  **Verification**: image counts per group equal (500 – failures); manifest rows match files; no zero‑byte files.

- [ ] T018 Generate baseline and experimental images for the validation split (50 scenes) using the same seed‑locking mechanism, storing them under `data/derived/generated_images/validation/{baseline,experimental}/`. These images are required for detector quality assessment in T007.  
  **Verification**: 100 PNGs exist; manifest updated accordingly.

- [ ] T006 [US3] Implement `code/evaluation/detector.py`:
  * Load YOLOv8n on CPU.
  * Detect objects in each generated image, extract bounding boxes and confidences.
  * Compare against the scene’s physics JSON (projected to 512×512). Flag a violation if:
    - Any required support relation deviates > 5 px vertically, or
    - Any forbidden intersection has IoU ≥ 0.5, or
    - An expected object is missing or confidence < 0.7 (treated as a violation **and** set `manual_review_flag=true`).
  * Write a record per image to `data/derived/evaluation_results/{image_id}.json` conforming to the **extended** `evaluation-result.schema.yaml` (includes `manual_review_flag`).  
  **Verification**: contract tests (`code/tests/contract/test_schemas.py`) pass; a hand‑checked set of 20 images (`manual_labels.csv`) matches the automatically computed flags.

- [ ] T007 Compute detector quality:
  * Run the full pipeline on the validation split (T018 then T006) to obtain detections.
  * Calculate the False Negative Rate (FNR) as the proportion of ground‑truth objects missed with confidence ≥ 0.7.
  * Derive a threshold: `acceptable_fnr = 0.1 * (computed_fnr)` (i.e., 10 % of the observed FNR).  
  * Write `data/derived/evaluation_results/fnr_threshold.json` and a decision log `correction_factor_log.json` (apply conservative correction if observed FNR > acceptable_fnr).  
  **Verification**: both JSON artifacts exist and contain numeric values; decision log indicates whether correction was applied.

- [ ] T008 [US3] Implement `code/analysis/statistics.py`:
  * Load all evaluation records, apply exclusions (contradiction log, generation failures, and correction decisions from T007).
  * Compute per‑group **Prompt Adherence Rate** = 1 – violation_rate, with binomial 95 % confidence intervals.
  * Perform a power analysis targeting **≥ 0.8** power, using the effect size specified in the research parameters (as deferred in FR-008) and α = 0.05; abort with error if power < 0.8.
  * Choose statistical test: two‑proportion z‑test unless any expected cell count < 5, in which case use Fisher’s Exact Test (per FR-008).  
  * Apply any correction factor from T007 to the violation rates before testing.
  * Output `data/processed/power_analysis_report.json`, `data/processed/statistical_test_results.json`, `data/processed/exclusion_list.json`, and `data/processed/final_analysis.csv` (columns: group, total_count, violation_count, adherence_rate, ci_lower, ci_upper, p_value, significance).  
  **Verification**: unit tests (`code/tests/unit/test_statistics.py`) pass; all four artifacts are non‑empty and contain real numeric results.

- [ ] T009 Execute the complete pipeline end‑to‑end: `code/main.py --phase eval --phase analyze`. Verify that `final_analysis.csv` contains rows for baseline and experimental groups with adherence rates, confidence intervals, and a significant p‑value (p < 0.05) when appropriate.

- [ ] T010 Generate study figures and summary table:
  * `code/analysis/report.py` reads the processed CSV/JSON files and creates `figures/violation_rates_by_group.png` (bar chart with CIs) and `figures/detection_confidence_distribution.png` (histogram).  
  * Produce `data/processed/summary_table.md` summarizing key metrics.  
  **Verification**: figures and markdown exist and are reproducible from the same inputs.

- [ ] T011 Write `paper/research_summary.md`: concise methods and results linked to actual output cells in `final_analysis.csv` and figure files, explicitly labeling the metric as **Prompt Adherence Rate** and reporting any generation failures, detector FNR, and the N=500 scope limitation.

- [ ] T012 After each major phase (simulation, generation, evaluation, analysis) run `code/utils/update_state.py` to SHA‑256 hash all files under `data/derived/` and `data/processed/` and write the `artifact_hashes` map plus `updated_at` timestamp into `state/projects/PROJ-820-llmxive-follow-up-extending-visual-gener.yaml`. This satisfies Constitution V while remaining within the allowed script domain.  
  **Verification**: state YAML is updated after each phase; no other script writes to `state/`.

## Phase 2: Supporting infrastructure and compliance tasks

- [ ] T013 Create `code/requirements.txt` pinned to exact versions of all dependencies (pymunk, diffusers, torch‑cpu, ultralytics, scikit‑image, pandas, numpy, scipy, pytest).  
  **Verification**: file exists and matches the environment used in CI.

- [ ] T014 Implement `code/utils/update_state.py` (see T012 description) with robust hashing and safe YAML update.

- [ ] T015 Extend `specs/001-llmxive-follow-up-extending-visual-gener/contracts/evaluation-result.schema.yaml` to include a boolean `manual_review_flag` (true when confidence < 0.7). Update `code/evaluation/detector.py` accordingly.  
  **Verification**: schema validation passes for all generated records.

- [ ] T016 Retire the orphan `contracts/physics_constraint.json` file (remove it from the repo) and document in `README.md` that the YAML schema is the single source of truth.

- [ ] T017 Add integration test `code/tests/integration/test_pipeline.py` that runs a minimal end‑to‑end run on 3 scenes (baseline & experimental) and checks that all intermediate artifacts are produced and valid.

- [ ] T019 Compute the False Negative Rate threshold (see T007) using a deterministic rule: `acceptable_fnr = 0.1 * observed_fnr`. Record the rule in `data/derived/evaluation_results/fnr_threshold.json`.  
  **Verification**: JSON contains both `observed_fnr` and `acceptable_fnr`.

- [ ] T020 Assemble a manual verification set of 20 images with ground‑truth violation labels in `data/derived/evaluation_results/manual_labels.csv`. Use this set in T006 verification.  
  **Verification**: file exists; counts match expectations.

- [ ] T021 Verify seed‑locking tolerance: after image generation, project the physics bounding boxes onto the 512×512 canvas and compute pixel‑wise deviation between the generated image’s detected boxes and the reference. Assert **max deviation ≤ 1 pixel**; record results in `seed_lock_status.json`.  
  **Verification**: JSON reports `tolerance_ok: true` for all scenes.

## Phase 3: Reproducible results and paper handoff

- [ ] T022 Re‑run the documented workflow end‑to‑end using the commands in `quickstart.md` and confirm that all `pytest` suites pass, all contract schemas validate, image/record counts reconcile with manifests, and statistical artifacts regenerate identically. Document any non‑deterministic observations (should be none).  
  **Verification**: log of successful re‑run attached to `quickstart.md`.

- [ ] T023 Ensure no script writes to `state/` except `update_state.py`; audit the codebase for stray state writes.  
  **Verification**: static analysis passes.