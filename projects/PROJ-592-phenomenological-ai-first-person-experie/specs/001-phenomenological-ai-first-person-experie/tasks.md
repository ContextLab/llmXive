# Tasks: Phenomenological AI: First-Person Experience Modeling

**Input**: Design documents from `/specs/592-phenomenological-ai-first-person-experie/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Dependent (must wait for specific prior tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Write `scripts/init_project.py` script to scaffold directories: `code/`, `data/raw/`, `data/processed/`, `data/qualitative/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`. **Execution**: Run `python scripts/init_project.py` to verify completion.
- [X] T002 [P] Create `.gitignore` (exclude `data/`, `*.pyc`, `__pycache__`) and `.github/workflows/ci.yml` (basic lint/test trigger). **Verification**: Run `ls -la.gitignore.github/workflows/ci.yml` and verify `.gitignore` contains `data/` and `*.pyc`, and `ci.yml` contains `pytest` trigger.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Deliverable**: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Verification**: Run `ruff check. --exit-zero` and `black --check.`; verify a successful exit code.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with:
 1. Seeds, paths, and model IDs (Primary: `TheBloke/TinyLlama-Chat-v-GGUF` for CI; Secondary: `mistralai/Mistral-7B-Instruct-v0.2` and `meta-llama/Llama-7b-chat-hf` for GPU offload).
 2. **Phenomenological Marker Dictionaries**: Define concrete lists for 'sensory' (e.g., see, hear, feel, touch, taste, smell, light, sound), 'temporal' (e.g., now, then, before, after, moment, duration), and 'intentional' (e.g., think, believe, desire, intend, perceive, experience) keywords as per FR-008 and FR-009.
 **Verification**: Run `python -c "from code.config import MARKER_DICTS; assert 'sensory' in MARKER_DICTS and len(MARKER_DICTS['sensory']) > 0"`; verify exit code.
- [X] T005 [P] Setup `code/utils/logging.py` for structured logging, warning capture, and retry logic (multiple attempts per sample)
- [X] T006 [P] Implement `code/utils/io.py` for JSON/CSV schema validation and artifact archiving. **CLI**: Expose `python -m code.utils.io --validate-schema <file> <schema>`. **Verification**: Run `python -m code.utils.io --validate-schema data/test.json specs/contracts/test.schema.yaml`; verify successful execution.
- [X] T007 [P] Create base data schemas in `specs/contracts/`: `specs/contracts/generation_output.schema.yaml`, `specs/contracts/validity_scores.schema.yaml`, `specs/contracts/qualitative_ratings.schema.yaml`, `specs/contracts/generation_log.schema.yaml`, `specs/contracts/final_report.schema.yaml`
- [X] T020 [P] [US3] **Create** `code/validation/rubric.md`: Author the independent validation rubric document required by FR-010. **Content**: Define clear criteria for human raters: 1) Coherence (logical flow), 2) Marker Density (presence of sensory/temporal/intentional markers), 3) Structural Integrity (adherence to first-person perspective). **Verification**: Run `grep -c "Coherence" code/validation/rubric.md` and `grep -c "Marker Density" code/validation/rubric.md` and `grep -c "Structural Integrity" code/validation/rubric.md`; verify all return >= 1.
- [X] T000 [P] [Plan Alignment] **Update Plan** to resolve contradictions with Spec FR-009 and FR-001. **Content**: Explicitly document the NLI metric status (secondary vs primary) and mandate the execution of sensitivity analysis OR literature citation for FR-009. Document the scope limitation for CI (TinyLlama) vs Full Study (Mistral/Llama). **Crucial**: The Plan MUST explicitly state that the CI path is restricted to TinyLlama due to hardware constraints, and the second checkpoint is a 'Manual/GPU-Offload' path. If the Spec's requirement for two checkpoints in CI is infeasible, the Plan MUST propose a formal Spec amendment or a documented deviation. **Deliverable**: Modify `plan.md` to include the auto-offload strategy for the second checkpoint and create `docs/scope_limitation.md`. **Verification**: Run `grep -c "FR-009" plan.md` and `grep -c "TinyLlama" plan.md` and `grep -c "CI Execution Path" plan.md` and `grep -c "GPU Offload" plan.md`; verify Plan is updated and `docs/scope_limitation.md` exists.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Report Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate the corpus of phenomenological reports using CPU-tractable models and four prompting strategies.

**Independent Test**: Execute `code/generation/runner.py` and verify `data/raw/` contains ≥80 samples per prompt per strategy (totaling a substantial number per strategy) with valid JSON metadata (seed, prompt, strategy) and no CUDA errors.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/generation/runner.py` using `llama-cpp-python` for `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` (specifically `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`) on CPU-only environment (FR-002). **Constraint**: This is the ONLY model for the primary CI path due to limited hardware constraints. Target volume: ≥80 samples **per prompt** per strategy (prompts × 80 = 1600 per strategy). **Schema**: Output JSON must contain fields: `seed`, `prompt`, `strategy`, `text`. **Directory**: Ensure `data/raw/` exists before writing. **Logging**: MUST create `data/raw/generation_log.json` with schema `{"total": int, "success": int, "fail": int, "strategy_counts": {str: int}}` upon completion. **Verification**: Run `python -c "import json, glob, os, collections; files=glob.glob('data/raw/generation_batch_*.json'); data=[json.load(open(f)) for f in files]; counts=collections.defaultdict(lambda: collections.defaultdict(int)); [counts[d['strategy']][d['prompt_id']]+1 for d in data]; assert all(all(c>=80 for c in p_counts.values()) for p_counts in counts.values()), f'Missing: {dict(counts)}'";` AND verify `data/raw/generation_log.json` exists and contains valid schema. <!-- FAILED: unspecified -->
- [X] T009b [US1] **Mandatory GPU-Offload**: Implement `code/generation/runner_gpu.py` to generate samples using `mistralai/Mistral-7B-Instruct-v0.2` via `llama-cpp-python` with `device="cuda"` and -bit quantization. **Constraint**: This task is designed to be executed on a free-tier GPU runner (Kaggle) when the CPU runner detects a CUDA requirement. **Target**: ≥80 samples per prompt per strategy (1600 per strategy) for the second checkpoint. **Dependency**: T009 (logic reuse). **Note**: This task is **NOT** part of the primary CI path. It is executed ONLY when the execution stage auto-offloads due to resource constraints. **Verification**: Run `python -c "import json, glob; files=[f for f in glob.glob('data/raw/generation_batch_*.json') if 'Mistral' in f]; assert len(files) >= 80*4*20, f'Expected a substantial volume of files, got {len(files)}'"`.
- [X] T009c [US1] **Mandatory GPU-Offload**: Implement `code/generation/runner_gpu.py` (or extend) to generate samples using `meta-llama/Llama-7b-chat-hf` via `llama-cpp-python` with `device="cuda"` and -bit quantization. **Constraint**: This task ensures the second mandatory checkpoint (Llama-7B) from FR-001 is covered. **Target**: ≥80 samples per prompt per strategy. **Dependency**: T009 (logic reuse). **Note**: This task is **NOT** part of the primary CI path. It is executed ONLY when the execution stage auto-offloads. **Verification**: Run `python -c "import json, glob; files=[f for f in glob.glob('data/raw/generation_batch_*.json') if 'Llama' in f]; assert len(files) >= 80*4*20, f'Expected a substantial volume of files, got {len(files)}'"`. <!-- FAILED: unspecified -->
- [ ] T009d [US1] **Power Analysis & Gap Resolution**: Create `code/generation/power_analysis.py` to calculate the sample size gap between Spec (N=80) and CI limits (N=20). **Deliverable**: Create `data/raw/power_gap_report.md` defining the 'Pilot Mode' vs 'Full Study' execution path. **Verification**: Run `python code/generation/power_analysis.py`; verify `data/raw/power_gap_report.md` exists and contains a calculated sample size and gap analysis.
- [X] T010 [US1] Implement retry logic in `runner.py`: Implement a fixed number of attempts per prompt/strategy combination with exponential backoff (increasing intervals). Mark samples as missing only after a consecutive series of failures. **Deliverable**: Create `tests/unit/test_retry.py`. **Verification**: Run `pytest tests/unit/test_retry.py::test_retry_logic` which mocks a timeout on an initial sequence of attempts; verify log contains sequential retry attempts followed by success.
- [ ] T011 [US1] Create `code/generation/control_corpus.py` to generate ≥80 control samples using `datasets.load_dataset('arxiv', split='train', streaming=True)` (filtered for technical domains) or `arxiv_abstracts`. **Logic**: Append `type=control` to each sample. Filter for abstracts/text that resemble technical reports. Merge with phenomenological outputs into `data/processed/merged_dataset.csv` for downstream analysis (discriminant validity per Plan Complexity Tracking). **Dependency**: T009. **Schema**: Ensure merged CSV has 'type' column and 'text' column. **Additional Verification**: Verify the control corpus lacks phenomenological markers (sensory, temporal, intentional) using `code/config.py` dictionary. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/merged_dataset.csv'); assert 'type' in df.columns and (df['type']=='control').any() and len(df[df['type']=='control'])>=80"`. Verify file exists and contains "control" rows with count >= 80.
- [ ] T013 [US1] **REMOVED**: Task merged into T009 to ensure log creation is atomic with generation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3b: Local Reproduction (Optional)

**Goal**: Provide a script for users with local hardware (≥16GB RAM) to run larger models (Phi-2) for optional validation, NOT for the primary CI path.

- [X] T012 [US1-Optional] **DEPRECATED**: Task removed. Phi-2 is not authorized by Spec FR-001 or Plan Summary. Use T009c for Llama-7B if local reproduction is needed for the second checkpoint.

---

## Phase 4: User Story 2 - Phenomenological Metric Computation (Priority: P2)

**Goal**: Compute Internal Consistency, Semantic Stability, and Marker Presence metrics, then perform statistical analysis.

**Independent Test**: Run `code/analysis/stats.py` on a small subset of reports and verify `data/processed/validity_scores.csv` contains non-null scores for all three metrics and correct statistical test outputs.

### Implementation for User Story 2

- [X] T014 [US2] Implement `code/analysis/consistency.py`: Load NLI model `cross-encoder/stsb-distilroberta-base` (CPU-safe), compute pairwise contradiction counts, handle length limits by skipping pairs with warnings (US-2 Edge Case). **Deliverable**: Create `tests/unit/test_consistency.py`. **Verification**: Run `pytest tests/unit/test_consistency.py::test_pairwise_contradiction` with a known input string; verify output matches expected contradiction count.
- [X] T015 [US2] Implement `code/analysis/stability.py`: Compute embeddings for repeated generations, calculate cosine similarity, and store stability scores. **Deliverable**: Create `tests/unit/test_stability.py`. **Verification**: Run `pytest tests/unit/test_stability.py::test_cosine_similarity` with known embeddings; verify output matches expected similarity score within tolerance sufficiently small to ensure numerical stability.
- [ ] T016 [US2] Implement `code/analysis/markers.py`: Load the keyword dictionary defined in `code/config.py` (T004) to count sensory, temporal, and intentional markers (FR-008). **Deliverable**: Create `tests/unit/test_markers.py`. **Dependency**: Requires T004 (Phase 2). **Verification**: Run `pytest tests/unit/test_markers.py::test_count_keywords` with a known text; verify output matches expected count.
- [ ] T017 [US2] Implement `code/analysis/fdr_correction.py` and `code/analysis/tukey_hsd.py` for Benjamini-Hochberg FDR and Tukey HSD post-hoc tests (FR-005). **Deliverable**: Create `tests/unit/test_stats.py`. **Verification**: Run `pytest tests/unit/test_stats.py::test_fdr_correction` with known p-values; verify output matches expected adjusted p-values.
- [ ] T018 [US2] Implement `code/analysis/stats.py` to orchestrate metric aggregation. **Logic**: Run Shapiro-Wilk and Levene tests (FR-012). **CRITICAL**: If assumptions (p≥0.05) hold, run ANOVA + FDR + Tukey. **IF VIOLATED**: Run Kruskal-Wallis **INSTEAD** of ANOVA and **SKIP** FDR/Tukey (as they are parametric corrections). Report the violation and the non-parametric result. **Output**: JSON with `method: "parametric" | "non-parametric"`. **Verification**: Run `python code/analysis/stats.py --input data/processed/merged_dataset.csv --output data/processed/stats_report.json`; verify `data/processed/stats_report.json` exists, contains a `method` field, and the input CSV has a 'type' column.
- [ ] T019 [US2] Implement `code/analysis/sensitivity_analysis.py` to test validity score weights (FR-006) by varying weights across a range from a low threshold to a high threshold and analyzing robustness across sample subsets. **Justification**: Output a report justifying the fixed weights used in the Constitution based on sensitivity results. **Verification**: Run `python code/analysis/sensitivity_analysis.py --weights [low_value, mid_value, high_value]`; verify `data/processed/sensitivity_report.md` exists and contains a table of results for the tested weights.
- [ ] T039 [US2] **Implement Construct Validity Justification (FR-009)**: Create `code/analysis/construct_validity.py` to EITHER cite phenomenological literature (minimum 3 citations from primary sources like Husserl, Merleau-Ponty) OR perform sensitivity analysis on alternative metric definitions (weights range from low to high). **Logic**: Generate a report citing specific phenomenological texts OR output a sensitivity analysis report. **Dependency**: T004, T016. **Verification**: Run `python code/analysis/construct_validity.py`; verify `data/processed/construct_validity_report.md` exists and contains either citations (count >= 3) or sensitivity results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Qualitative Validation & Reproducibility (Priority: P3)

**Goal**: Facilitate human evaluation, compute inter-rater reliability, and archive all artifacts.

**Independent Test**: Verify `data/qualitative/` contains anonymized rating sheets, `code/validation/human_rater.py` calculates Cohen's κ correctly, and the archive script commits all artifacts.

### Implementation for User Story 3

- [ ] T026 [US3] **Perform Power Analysis and Sample Size Determination for SC-002**. **Logic**: Calculate minimum sample size required to achieve κ≥0.6 with power 0.8, alpha=0.05, using the appropriate formula for Cohen's κ reliability (based on expected kappa distribution, not t-test effect size). **Deliverable**: Create `data/qualitative/power_analysis_report.md`. **Verification**: Run `python code/validation/power_analysis.py`; verify `data/qualitative/power_analysis_report.md` exists and contains a calculated sample size ≥10 per condition.
- [ ] T023 [US3] Create `code/validation/stratified_sampler.py` to select a representative set of reports per condition for human rating (SC-002). **Logic**: Select a representative sample of reports per condition using stratified random sampling based on prompt strategy. **Dependency**: T009, **T026** (for sample size 'n'). **Constraint**: Must enforce exactly **10 reports per condition** (strategy) if data available, otherwise `min(10, available)`. **Verification**: Run `python code/validation/stratified_sampler.py --n 10`; Verify `data/qualitative/sampling_list.csv` exists and contains a representative number of rows per strategy (Direct, Hypothetical, Comparative, Role-play). Run `python -c "import pandas as pd; df=pd.read_csv('data/qualitative/sampling_list.csv'); counts=df['strategy'].value_counts(); assert all(c<=10 for c in counts.values()) and all(c>0 for c in counts.values()), f'Expected <=10 per strategy, got {counts}'"`.
- [ ] T021b [US3] **Implement Blinded Distribution Workflow**: Create `code/validation/blind_distribution.py` to anonymize strategy metadata from reports and generate a CSV for raters. **Logic**: Remove 'strategy' column and assign random IDs. **Dependency**: T023. **Verification**: Run `python code/validation/blind_distribution.py`; verify `data/qualitative/blinded_samples.csv` exists and does not contain 'strategy' column.
- [ ] T021 [US3] Implement `code/validation/human_rater.py` to load generated reports, apply independent validation rubric from `code/validation/rubric.md` (FR-010), and store ratings. **Dependency**: Depends on T020 (rubric creation) and **T021b** (blinded distribution) and T023 (sampling list). **Verification**: Run `python -m code.utils.io --validate-schema data/qualitative/ratings_test.csv specs/contracts/qualitative_ratings.schema.yaml`; verify `data/qualitative/ratings_test.csv` exists and schema matches `specs/contracts/qualitative_ratings.schema.yaml`.
- [ ] T022 [P] [US3] Implement Cohen's κ calculation and threshold sensitivity analysis in `code/analysis/sensitivity_kappa.py`. **Logic**: Analyze robustness of conclusions across a range of kappa thresholds per FR-011. **Constraint**: If κ < 0.6, trigger the mandatory re-evaluation workflow: select new samples and re-instruct raters via the rubric. **Dependency**: T021. **Verification**: Run `python code/analysis/sensitivity_kappa.py --kappa 0.5`; verify `data/qualitative/flags.json` exists and contains a "re-evaluate" flag for the test batch with the schema `{"flag": "re-evaluate", "action": "re-rate"}`.
- [ ] T025 [P] [US3] Implement `code/utils/archiver.py` to package prompts, seeds, scripts, and anonymized ratings for public reproducibility (FR-007). **Verification**: Run `python code/utils/archiver.py --output archive.zip`; verify `archive.zip` exists and contains `code/`, `data/prompts/`, `data/qualitative/ratings.csv` by running `unzip -l archive.zip | grep -E "code/|data/prompts/|data/qualitative/ratings.csv"`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Exploratory & Review-Driven Enhancements (Priority: P2) [Exploratory]

**Goal**: Address specific philosophical and methodological concerns raised by reviewers (Turing, Rockmore, Kahneman, Krakauer, Dyson) regarding operational tests, stylistic distinction, debiasing, and incoherence. **Note**: These tasks are supplementary to the core FRs and do not replace them.

- [ ] T030a [P] Add CLI usage examples and environment setup instructions to `quickstart.md`. **Examples**: Document `python main.py --mode generation`, `python main.py --mode analysis`, `python main.py --mode validate`. **Specifics**: Include `--limit`, `--config` flags. **Verification**: Run `grep -c "python main.py --mode generation" quickstart.md` and `grep -c "--limit" quickstart.md` and `grep -c "--config" quickstart.md` and verify it returns >= 1. **Note**: This task is currently incomplete; verification must confirm file is non-empty.
- [X] T031a [P] Refactor `code/analysis/stats.py` to add type hints and remove duplicate imports. **Verification**: Run `ruff check code/analysis/stats.py`; verify exit code.
- [X] T031b [P] Refactor `code/utils/logging.py` to standardize log levels and output formats. **Verification**: Run `ruff check code/utils/logging.py`; verify exit code.
- [X] T032 [P] Add unit tests in `tests/unit/`: specifically `tests/unit/test_markers.py::test_count_sensory_keywords`, `tests/unit/test_consistency.py::test_pairwise_contradiction`. **Verification**: Run `pytest tests/unit/test_markers.py::test_count_sensory_keywords tests/unit/test_consistency.py::test_pairwise_contradiction`; verify all tests pass.
- [ ] T033a [P] Create `config.yaml` with all necessary parameters for the pipeline. **Deliverable**: Create `config.yaml` in the root. **Verification**: Run `python -c "import yaml; yaml.safe_load(open('config.yaml')); print('Content verified')"`. Verify exit code 0 and file is non-empty.
- [ ] T033 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤6 hours on free-tier. **Dependency**: T033a, T030a. **Verification**: Run `time python code/main.py --mode generation --limit 100 --config config.yaml`; verify exit code 0 and total time < 6h (simulated by limit). [UNRESOLVED-CLAIM: c_ed2c572c — status=not_enough_info]
- [ ] T034a [US2] **Generate Human Corpus**: Create `code/analysis/human_corpus.py` to load or generate a small set of human-written phenomenological reports for the Turing Test. **Logic**: Use a verified public dataset or a small set of manually written samples. [UNRESOLVED-CLAIM: c_b62b93b1 — status=not_enough_info] **Verification**: Run `python code/analysis/human_corpus.py`; verify `data/processed/human_corpus.json` exists.
- [D] T034 [P] [US2] **Implement Turing-Style Operational Test (Exploratory)**: Create `code/analysis/turing_test.py` to evaluate the "indistinguishability" criterion (Turing Review). **Logic**: Generate a mixed corpus of human-written phenomenological reports (from T034a) and LLM reports. Implement a classifier (Logistic Regression) with TF-IDF features, using a train/test split, to predict origin. Report the accuracy; if accuracy is near chance ([deferred]), the model sustains the "fiction" effectively. **Note**: This is **SUPPLEMENTARY** and does **NOT** replace FR-010 (Human Qualitative Auditing). **Dependency**: T009, T041, T034a. **Verification**: Run `python code/analysis/turing_test.py --n 100`; verify `data/processed/turing_accuracy.json` exists and contains a key `accuracy` as a float and a `confusion_matrix` key.
- [D] T035 [P] [US2] **Implement "Experience Trace" Visualization**: Create `code/analysis/experience_trace.py` to map model latent states to phenomenological categories (Rockmore Review). **Logic**: Use attention head visualization or embedding projection (t-SNE/UMAP) on the generated reports to show clustering of "sensory", "temporal", and "intentional" concepts in the latent space. Output a static plot or HTML report. **Dependency**: T009, T041. **Verification**: Run `python code/analysis/experience_trace.py --input data/processed/merged_dataset.csv --n 100`; verify `data/processed/latent_trace.html` or `.png` exists.
- [D] T036 [P] [US2] **Implement Debiasing/Contradiction Test**: Create `code/analysis/debiasing_test.py` to address Kahneman's concern about "consistently wrong" systems (Kahneman Review). **Logic**: For a subset of prompts, force the model to generate a report under "high noise" conditions (e.g., corrupted prompt, random seed injection) and then generate a contradictory report. Measure if the "phenomenological markers" dissolve or persist incoherently. Compare marker density between "clean" and "noisy" conditions. **Dependency**: T009, T041. **Verification**: Run `python code/analysis/debiasing_test.py --noise 0.5`; verify `data/processed/debiasing_report.md` exists and contains a key `p_value` as a float.
- [D] T037 [P] [US2] **Implement Embodiment/Style Distinction Metric**: Create `code/analysis/embodiment_score.py` to measure the difference between "phenomenological style" and "ordinary conversation" (Krakauer Review). **Logic**: Define a set of "embodied" features (e.g., sensorimotor verbs, spatial prepositions) and compare their frequency in the generated reports vs. a baseline of standard technical reports. Calculate a "Phenomenological Index" (ratio of embodied features to total features). **Dependency**: T009, T041. **Verification**: Run `python code/analysis/embodiment_score.py --n 100`; verify `data/processed/embodiment_index.csv` exists and contains a key `index` as a float.
- [D] T038 [P] [US2] **Implement Incoherence/Quantum Metric**: Create `code/analysis/incoherence_metric.py` to test Dyson's hypothesis that "truthful" reports might be inherently incoherent (Dyson Review). **Logic**: Compute a "logical contradiction density" (using NLI) but also a "semantic entropy" (variance in embeddings of repeated generations for the *same* prompt). Correlate high entropy with high marker density. If high entropy correlates with high marker presence, it supports the "incoherent truth" hypothesis. **Dependency**: T009, T041. **Verification**: Run `python code/analysis/incoherence_metric.py --n 100`; verify `data/processed/incoherence_correlation.json` exists and contains a key `correlation` as a float.
- [ ] T040 [P] [US1] **Document Scope Limitation**: Create `docs/scope_limitation.md` to formally document the deviation from FR-001 (two checkpoints) due to hardware constraints. **Content**: Explain that TinyLlama is used in CI due to RAM constraints., and the second checkpoint is available via T009b/T009c (GPU offload). **Verification**: Run `grep -c "TinyLlama" docs/scope_limitation.md` and `grep -c "GPU" docs/scope_limitation.md`; verify both return >= 1.

---

## Phase 7: Integration & Orchestration (Priority: P3)

**Goal**: Chain generation, analysis, and validation into a single reproducible pipeline.

- [ ] T041 [D] Implement `code/orchestration/main.py` to execute the full pipeline: Generation (T009) → Metrics (T016, T014, T015) → Statistics (T018) → Qualitative (T021, T022). **Logic**: Ensure all outputs are checksummed and logged. **Schema**: `final_report.json` must contain: `metrics` (consistency, stability, markers), `stats` (ANOVA/Kruskal, FDR), `qualitative` (Cohen's κ). **Execution Order**: Generation -> Metrics -> Stats -> Qualitative. **Validation**: Output MUST conform to `specs/contracts/final_report.schema.yaml`. **Dependency**: T009, T016, T014, T015, T018, T021, T022. **Verification**: Run `python code/orchestration/main.py --config config.yaml --mode full`; verify `data/processed/final_report.json` exists, contains all required metrics, and passes schema validation against `specs/contracts/final_report.schema.yaml`.
- [ ] T042 [D] Implement `code/orchestration/reproducibility_check.py` to verify that re-running the pipeline with the same seeds produces identical outputs (bit-for-bit). **Logic**: Compare checksums of all generated artifacts. **Dependency**: T041. **Verification**: Run `python code/orchestration/reproducibility_check.py --run-id 1`; verify `data/processed/reproducibility_report.md` exists and confirms bit-for-bit identity.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review-Driven Enhancements (Phase 6)**: Depends on US1 and US2 logic to be functional.
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, US3 logic AND Phase 6 enhancements to be in place.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (schema only for parallel dev)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics
- **Review-Driven Enhancements (Phase 6)**: Depends on US1 and US2 logic to be functional.
- **Integration & Orchestration (Phase 7)**: Depends on US1, US2, US3 logic AND Phase 6 enhancements to be in place.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Review-Driven Enhancements (Phase 6) can be implemented in parallel once US1 and US2 are functional.
- Integration & Orchestration (Phase 7) tasks can be implemented in parallel once the base analysis pipeline (US2) and review enhancements (Phase 6) are functional.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Review-Driven Enhancements (Phase 6) → Address specific philosophical concerns
6. Add Integration & Orchestration (Phase 7) → Address specific philosophical concerns
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generation)
 - Developer B: User Story 2 (Analysis)
 - Developer C: User Story 3 (Validation)
 - Developer D: Review-Driven Enhancements (Phase 6)
 - Developer E: Integration & Orchestration (Phase 7)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [D] tasks = Dependent (must wait for specific prior tasks)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must be executable on a minimal CPU configuration. No CUDA, no 8-bit/4-bit quantization requiring GPU drivers. Use `llama-cpp-python` with GGUF for TinyLlama and Phi-2.
- **Model Constraint**: TinyLlama-1.1B (T009) is the **only** model for the primary CI pipeline. Mistral-7B (T009b) and Llama-7B (T009c) are for **GPU offload** and are mandatory for FR-001 compliance. Phi-2 (T012) is **DEPRECATED** and removed.
- **Review Integration**: Tasks T034-T038 address the specific concerns raised by Turing (operational test), Rockmore (latent trace), Kahneman (debiasing), Krakauer (embodiment distinction), and Dyson (incoherence/entropy).
- **Review Integration**: Task T042 ensures reproducibility of the entire pipeline, addressing the need for a "single source of truth" and auditability.