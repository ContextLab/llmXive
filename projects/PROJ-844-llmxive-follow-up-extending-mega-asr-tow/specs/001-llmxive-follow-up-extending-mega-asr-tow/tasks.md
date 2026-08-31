---
description: "Task list template for feature implementation"
---

# Tasks: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Input**: Design documents from `/specs/001-semantic-collapse-threshold/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `code/` directory at repository root per plan.md
- [ ] T001b [P] Create `data/raw/` directory at repository root per plan.md
- [ ] T001c [P] Create `data/derived/` directory at repository root per plan.md
- [ ] T001d [P] Create `tests/` directory at repository root per plan.md
- [ ] T002a [P] Create `ruff.toml` configuration file with specific rules for linting
- [ ] T002b [P] Create `pyproject.toml` configuration file with specific rules for black formatting
- [ ] T003a Resolve Deferred Parameters: Read `research.md` and `plan.md` to explicitly resolve all `[deferred]` parameters (sample size=500, correlation threshold=0.6, SNR/RT60 ranges). Write these values as hardcoded constants in `code/config.py`. (Resolves FR-023; Depends on plan.md/research.md availability)
- [ ] T003 Implement `code/config.py` with paths, random seeds, and hyperparameters (thresholds, distortion counts) (Depends on T003a)
- [ ] T003b Document Power Limitation: Update `docs/research.md` to explicitly state that the study is powered for **medium-to-large effects (f² ≥ 0.05)** only, and that the original small effect requirement (f² ≥ 0.02) is unachievable with the available data (AMI+LibriSpeech). (Resolves FR-001 power conflict; Depends on T003a)
- [ ] T003c Re‑scope US‑3 Hypothesis: Explicitly update the US‑3 acceptance criteria (R² ≥ 0.6) and the research hypothesis in `docs/research.md` to state that the regression analysis is **valid only for detecting medium-to-large interaction effects**, explicitly excluding small effects. (Resolves FR‑001/US‑3 conflict; Depends on T003b)
- [ ] T004 Implement `code/monitor_resources.py` to track peak RSS and wall‑clock time (SC‑004)
- [ ] T005 Implement `code/hash_updater.py` to compute content hashes for `data/derived/` and update state YAML (Principle V)
- [ ] T006 Create base entity classes (`AudioClip`, `DistortionVector`, `StressCurve`) in `code/models.py` (or dataclasses)
- [ ] T008c Create `tests/unit/` directory for unit tests (new)
- [ ] T008d Create `pytest.ini` (or configure in `pyproject.toml`) for pytest discovery and enable `tests/unit/` (new)
- [ ] T008_test Verify that `pytest.ini` exists and is syntactically valid
- [ ] T008d_test Verify that `tests/unit/` directory is present and contains at least one placeholder test
- [ ] T009 Unit test for distortion vector generation: verify that a collection of distinct vectors is produced from the defined SNR and RT60 ranges. (Moved to Phase 3 after T012c)
- [ ] T010 Implement `code/monitor_resources.py` unit tests (ensuring resource monitor works) (optional)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data fetching, stratification, and distortion engine setup.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007a Fetch and verify checksums for **LibriSpeech** subset (`openslr/librispeech_asr`, split='test.clean') in `code/data_loader.py`; implement **streaming=True** and **chunked iteration** to prevent OOM (>7 GB RAM) as per FR‑001; **Apply stratification by speaker ID and SNR bucket** (adapted from Voices‑in‑the‑Wild‑2M logic). (Resolves coverage‑a79c0482; Depends on T003a)
- [ ] T007a_test Validate LibriSpeech fetch, checksum file existence, and streaming behavior.
- [ ] T007b Fetch and verify checksums for **AMI** subset (`hf-audio/ami`, split='test') in `code/data_loader.py`; implement **streaming=True** and **chunked iteration** to prevent OOM (>7 GB RAM) as per FR‑001; **Apply stratification by speaker ID and SNR bucket**. (Resolves coverage‑3941c0cc; Depends on T003a)
- [ ] T007b_test Validate AMI fetch, checksum file existence, and streaming behavior.
- [ ] T007c Document Spec Deviation: Create `docs/dataset_substitution_rationale.md` explicitly stating that the plan deviates from FR‑001 (CHiME‑5, 50k clips) to LibriSpeech/AMI (approximately several thousand clips) due to availability constraints, and that this document serves as the approved exception for the project. Must include exact dataset IDs and stratification mapping. (Resolves constraint‑preservation‑6834b210)
- [ ] T008a Fetch & Generate DNS‑Challenge Data: Implement `code/data_loader.py` function `fetch_dns_challenge` to download an appropriate number of clips from `hf-audio/dns-challenge` (train split). Output: `data/raw/dns_reference.parquet`. (Resolves FR‑018)
- [ ] T008b Distortion Realism Validation (FR‑018): Implement `code/realism_validator.py` to compare synthetic distortion parameters against DNS‑Challenge using Log‑Mel Spectral Distance ≤ 0.15. (Resolves FR‑018)
- [ ] T012d Validate Distortion Vector Definition: Ensure the The SNR list contains exactly nine numeric entries, covering a range from a low negative SNR value up to +30. with no empty placeholder. Fail fast with clear error if definition is incorrect. (New validation task)
- [ ] T012c Implement `code/distortion_engine.py` to apply **exactly 54** distinct compound distortion vectors (Cartesian product of SNR: [-10, -5, 0, 5, 10, 15, 20, 25, 30] dB and RT60: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] s). Enforce count and fail if mismatched. (Resolves FR‑002, executability‑f121ccd7)
- [ ] T012b Implement `code/realism_validator.py` (depends on T012c) to validate synthetic distortion realism. (Resolves executability‑d99914bb)
- [ ] T012_test Verify exactly 54 scenarios are generated and saved. (New)
- [ ] T015a Generate Stress Curves: Extend `code/main.py` to iterate clips → apply 54 distortions (T012c) → run Whisper‑tiny ASR → compute SSS/WER → write `data/derived/stress_curves.parquet`. (Resolves CRITICAL T015)
- [ ] T015a_test Verify `data/derived/stress_curves.parquet` exists, is non‑empty, and matches `contracts/stress_curve.schema.yaml`.
- [ ] T015c Verify Artifact Non‑Emptiness: Add check in `code/main.py` to raise RuntimeError if `stress_curves.parquet` is empty. (Resolves executability‑46e3ca9a)
- [ ] T016 Validation Logic in `code/metrics.py` to handle hysteresis (K=3 consecutive steps below threshold), empty ASR output mapping, and missing distortion scenarios (log warning). (Resolves FR‑001 edge cases)
- [ ] T042 Distortion Coverage Validator: Log which distortion scenarios were applied or skipped; output `data/derived/distortion_coverage_report.json`. (Resolves FR‑017)

## Phase 3: User Story 1 – Generate Compound Distortion Stress Curves (Priority: P1)

**Goal**: Systematically apply a diverse range of compound acoustic distortions to a stratified subset of audio data to generate stress curves mapping distortion intensity to semantic integrity.

- [ ] T010 [US1] Extend `code/data_loader.py` to add US1‑specific stress‑curve generation logic (building on T012c). (Depends on T007a‑b, T012c)
- [ ] T011 [US1] Integration test for `code/data_loader.py` verifying stratified sampling and stress‑curve generation workflow. (Depends on T010)
- [ ] T013 [US1] Implement `code/metrics.py` to compute SSS using `all‑MiniLM‑L6‑v2` (CPU‑only) per FR‑003.
- [ ] T014 [US1] Implement `code/metrics.py` to compute WER using `jiwer` per FR‑009.
- [ ] T017 [US1] Unit test for SSS computation correctness. (New)
- [ ] T018 [US1] Unit test for WER computation correctness. (New)
- [ ] T019 [US1] Verify that `data/derived/stress_curves.parquet` contains rows for all 54 scenarios per clip. (New verification task)
- [ ] T019_test Verify the per‑clip scenario count in `stress_curves.parquet`.
- [ ] T009_test Verify distortion vector generation produces the full Cartesian product of 9 SNR × 6 RT60 levels (54 vectors). (Moved from Phase 2)

## Phase 4: User Story 2 – Identify Semantic Collapse Points (Priority: P2)

**Goal**: Automatically identify the precise "collapse intensity" for each model/scenario where SSS drops below a normalized threshold and WER spikes > 2× baseline.

- [ ] T022b Mock Stress Curves: Generate a minimal synthetic `stress_curves.parquet` (e.g., Multiple clips × 54 scenarios) to enable independent US2 testing without requiring full US1 pipeline. (Moved earlier to satisfy ordering‑d93bf3ba)
- [ ] T020b Compute `baseline_sss.json`: average SSS of clean audio subset per model/scenario. (Resolves FR‑010)
- [ ] T020b_test Validate `baseline_sss.json` schema and checksum. (New)
- [ ] T020c Compute `baseline_wer.json`: average WER of clean audio subset per model/scenario. (Resolves FR‑010)
- [ ] T020c_test Validate `baseline_wer.json` schema and checksum. (New)
- [ ] T020d Normalize Stress Curves: Divide SSS by baseline values, output `data/derived/stress_curves_normalized.parquet`. (Resolves FR‑010)
- [ ] T020d_test Verify normalized file exists and schema matches. (New)
- [ ] T021 Handle "No Collapse": Record `collapse_type: 'max_tested'` when no drop detected. (Resolves US‑2 Acceptance 2)
- [ ] T022a Generate Collapse Points: Using normalized curves, identify intensity where `normalized_sss` < 0.5 **and** WER > 2× baseline; output `data/derived/collapse_points.parquet`. (Resolves CRITICAL missing artifact)
- [ ] T022a_test Verify `collapse_points.parquet` exists, non‑empty, and contains required columns. (New)
- [ ] T023 Compute Phoneme‑Edit‑Distance Fallback (FR‑022): When SSS fails, compute phoneme edit distance using `g2p_en` and `editdistance`; store fallback values in `data/derived/collapse_points_phoneme.parquet`. (Resolves FR‑022)
- [ ] T023_test Verify phoneme fallback artifact exists and matches its schema.

## Phase 5: Human Annotation & HVCM (Priority: P2 – Dependent on US1)

**Goal**: Generate human‑annotated validation set and derive Human‑Validated Collapse Margin (HVCM) to break circularity.

- [ ] T050 Draft Human Annotation Protocol (`docs/annotation_protocol.md`) defining 0‑5 Likert scale and sampling strategy. (Resolves FR‑011)
- [ ] T050a Implement `code/annotation_tool.py` CLI to present clips and collect scores into `data/validation/human_annotations.csv`. (Depends on T015a)
- [ ] T050b **MANUAL** Execute annotation tool on pilot set (N=100 high‑reverb AMI clips) to produce real human labels. (Critical path)
- [ ] T050c Generate synthetic placeholder annotations for CI verification; mark file with metadata `SYNTHETIC`. (CI path)
- [ ] T050d Document manual execution steps in `docs/manual_annotation_steps.md`. (Supports reproducibility)
- [ ] T050e Compute synthetic correlation report (`data/validation/synthetic_correlation_report.json`) and assert `r ≥ 0.6`. (New verification)
- [ ] T050e_test Verify synthetic correlation meets threshold.
- [ ] T050f Implement HALT Logic in `code/main.py`: If real human validation (T050b) yields AUC‑ROC < 0.85 **or** correlation r < 0.6, raise RuntimeError and block downstream US2/US3. (Resolves FR‑016)
- [ ] T050g Spec Amendment for FR‑011 Pilot Reduction: Create `docs/spec_amendment_FR011.md` documenting amendment to N=100 pilot, bump constitution version to 1.0.1, and record PR approval. (Resolves constraint‑preservation‑282f8ac7)
- [ ] T050g_approval Task to record amendment approval workflow (PR link, version bump). (New)
- [ ] T118 Compute AUC‑ROC on real human annotations and verify ≥ 0.85 (SC‑006). (New)
- [ ] T118_test Verify AUC‑ROC meets threshold.

## Phase 6: User Story 3 – Predict Collapse via Critical Interaction Vector (Priority: P3)

**Goal**: Train a lightweight regression model to predict collapse intensities using acoustic parameter vectors + interaction terms, and validate the “critical interaction vector” hypothesis.

- [ ] T026c_mock Generate Mock Collapse Points: Produce a synthetic `collapse_points.parquet` (e.g., 200 rows) to enable independent US3 testing without US2 outputs. (Moved earlier to satisfy ordering‑184fa7b0)
- [ ] T023a Unit test for interaction term generation (SNR×RT60, SNR², RT60²). (Ensures correct features)
- [ ] T025a Implement `code/models.py` function `generate_interaction_terms` to create engineered interaction terms. (Depends on T023a)
- [ ] T026a Regression Training (CI Path): Train CPU‑tractable regression (Linear/Polynomial degree≤3 or DecisionTree max_depth≤5) using features from T025a and target `normalized_inflection_coord` from `collapse_points.parquet`. Output `data/derived/regression_results.json`. (Depends on T022a)
- [ ] T026b Regression Training (Final Path): Same as T026a but target is HVCM from `hvcm_targets.parquet`. Raise RuntimeError if HVCM missing. (Depends on T050b)
- [ ] T026a_test Verify regression results file exists and contains R², MAE fields.
- [ ] T026b_test Verify final regression respects HVCM target presence.
- [ ] T026d Additive Baseline Comparison (FR‑013): Fit additive baseline model (no interaction terms), perform F‑test with FDR correction, output `data/derived/baseline_comparison.json`. (Depends on T026a/b)
- [ ] T024 Implement multiple‑comparison correction in `code/statistics.py` (Bonferroni/FDR) for interaction effects. (Resolves FR‑008)
- [ ] T025 Generate `data/derived/corrected_pvalues.json` with corrected p‑values. (Resolves SC‑003)
- [ ] T025_test Verify corrected p‑values file exists and contains expected keys. (New)
- [ ] T030b Compute Human‑Validated Collapse Margin (HVCM): Using human annotations, calculate HVCM per clip and store `data/derived/hvcm_targets.parquet`. (Addresses executability‑9931f5cf)
- [ ] T030b_test Verify `hvcm_targets.parquet` exists, matches schema, and contains non‑null values.
- [ ] T053 Sensitivity & Morphology Stability Verification (FR‑006, SC‑002): Sweep inflection detection thresholds, classify curve morphology, compute critical interaction vector variance; raise RuntimeError if variance > 10 %. Output `data/derived/sensitivity_analysis.csv` and `morphology_stability_report.json`. (Enhanced to also output inflection points per FR‑012)
- [ ] T053_test Verify sensitivity outputs exist and variance constraints satisfied. (New)
- [ ] T095 Verify R² ≥ 0.6 (SC‑001) and fail pipeline if not met. (New)
- [ ] T095_test Verify R² check passes or fails as expected. (New)
- [ ] T102 Aggregate Missing Scenario Warnings into final report (`data/derived/missing_scenarios_report.json`). (Resolves FR‑017)
- [ ] T103 Generate comprehensive audit log (`audit.log`) covering all intermediate artifacts, timestamps, and hashes. (Resolves FR‑026)
- [ ] T104 Compute and store the “critical interaction vector” per scenario in `data/derived/critical_vectors_detail.parquet`. (Addresses Principle VI granularity)
- [ ] T104_report_per_scenario Add a reporting step that outputs a human‑readable CSV summarizing the critical interaction vector for each of the 54 compound scenarios. (Ensures explicit reporting)
- [ ] T105 Cross‑model similarity calculation: Compute cosine similarity of critical vectors across selected ASR models; output `data/derived/cross_model_similarity.csv`. (Depends on T104)
- [ ] T106 Validate HVCM against human annotations: Correlate HVCM with `human_annotations.csv` and report Pearson r in `data/derived/hvcm_validation.json`. (Depends on T050b)
- [ ] T107 Generate final report (`docs/final_report.md`) aggregating regression results, sensitivity analysis, critical vectors, and validation metrics. (Resolves unspecified final‑report concern)

## Phase 7: Execution Verification & Safety Gates

**Purpose**: Address execution feedback regarding CPU feasibility, data integrity, and statistical rigor.

- [ ] T037 Defensive CPU Enforcement: Raise RuntimeError if any CUDA device is detected. (Resolves executability‑e06b5979)
- [ ] T037_test Simulate CUDA detection and verify RuntimeError.
- [ ] T038 Pre‑flight Dataset Check: Verify datasets are fully downloadable before distortion loop; raise if download fails. (Resolves executability‑3c0bf3da)
- [ ] T038_test Force dataset download failure and verify RuntimeError.
- [ ] T039 Memory‑Streaming Wrapper in `code/data_loader.py` to process stress‑curve data in chunks, ensuring RSS < 7 GB. (Resolves executability‑6f9d332f)
- [ ] T039_test Run wrapper on sample and assert RSS limit.
- [ ] T040 Unit test for correct Bonferroni correction factor based on number of interaction terms. (Resolves executability‑3f58211d)
- [ ] T041 Causality Warning: Assert regression target includes human intelligibility scores; raise if missing. (Resolves executability‑68d2167a)
- [ ] T041_test Provide training data without human scores and verify RuntimeError.
- [ ] T042 Distortion Coverage Validator (already added in Phase 2). (Resolves executability‑a3568198)
- [ ] T042_test Verify coverage report includes all 54 scenarios.
- [ ] T090 Enforce A short wall‑clock deadline via timeout wrapper; raise if exceeded. (Resolves SC‑004)
- [ ] T090_test Simulate long‑running run and verify timeout.
- [ ] T090c Additional check to assert total runtime ≤ 48 h after pipeline completes. (Redundant safety)
- [ ] T090c_test Verify final runtime check passes.

## Phase 8: Specification Amendments & Governance

- [ ] T115 Formal Spec Amendment for Dataset Substitution (FR‑001): Create amendment document, bump constitution version to 1.0.1, and record PR approval. (Resolves constraint‑preservation‑6834b210)
- [ ] T116 Provision Distributed Execution Environment (FR‑002): Set up Ray cluster on GitHub Actions using `ray[default]`; add task to run heavy steps (distortion generation, ASR inference) within Ray actors. (Resolves FR‑002)
- [ ] T117 Formal Amendment Approval for FR‑011 Pilot Reduction: Record PR link, version bump, and update constitution. (Resolves constraint‑preservation‑282f8ac7)

## Phase 9: Contracts & Validation

- [ ] T080 Create contract schema files (`contracts/*.schema.yaml`) for stress curves, collapse points, critical vectors, regression input, regression result, dataset metadata. (Resolves missing contracts)
- [ ] T080b Validate each contract against generated artifacts using `jsonschema`. (Resolves coverage‑f9816e2b)
- [ ] T080b_test Verify contract validation passes for a sample artifact.
- [ ] T059_test Cross‑validate final sample size against power‑analysis parameters defined in FR‑023.

## Phase 10: Polishing & Cross‑Cutting Concerns

- [ ] T031 Documentation updates in `docs/` including `research.md` citations for LibriSpeech/AMI.
- [ ] T033 Performance optimization: Parallelize ASR inference and distortion application where safe, using Ray actors (from T116).
- [ ] T034 Additional unit tests in `tests/unit/` for edge cases and statistical corrections (including all newly added verification tests).
- [ ] T035 Run `quickstart.md` validation to ensure end‑to‑end reproducibility on GitHub Actions free tier.
- [ ] T036 Generate final report section and code comments in `research.md` and `code/models.py` explicitly framing all predictive findings as ASSOCIATIONAL, avoiding causal claims per FR‑007.