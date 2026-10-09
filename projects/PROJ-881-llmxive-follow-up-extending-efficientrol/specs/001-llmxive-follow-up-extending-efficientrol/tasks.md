# Tasks: llmXive Follow‑up: Entropy‑Guided Validity Prediction in RL Rollouts  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, contracts, and reviewer feedback.  

The checklist below follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
Checked boxes (`[X]`) indicate work already verified as correct.  
Unchecked boxes (`[ ]`) denote work that still needs to be completed or has been reopened for revision.  
Tasks are ordered to respect data‑flow dependencies; later tasks depend only on artifacts produced by earlier ones.

---

## Phase 0 – Research & Design  

- [X] T001a [Plan] Define Semantic Alignment logic for GSM8K.  
  *Deliverable*: `specs/001-entropy-validity-prediction/contracts/semantic_alignment_gsm8k.md`.  
- [X] T001a_v [Test] Verify `semantic_alignment_gsm8k.md` exists and conforms to the semantic‑alignment schema.  
  *Path*: `tests/contract/test_semantic_alignment_gsm8k.py`.  

- [X] T001b [Plan] Define Semantic Alignment logic for MiniGrid.  
  *Deliverable*: `specs/001-entropy-validity-prediction/contracts/semantic_alignment_minigrid.md`.  
- [ ] T001b_v [Test] Verify `semantic_alignment_minigrid.md` exists and conforms to the semantic‑alignment schema.  
  *Path*: `tests/contract/test_semantic_alignment_minigrid.py`.  

- [ ] T002 [Plan] Select a CPU‑feasible model and benchmark 0.5 B / 1.5 B / 7 B‑Int4 variants.   <!-- FAILED-IN-EXECUTION: code/scripts/evaluate_model_feasibility.py exit=1 -->
  *Deliverable*: `docs/model_selection.md`.  
- [X] T002_v [Test] Verify `docs/model_selection.md` exists and documents a Llama‑2‑7B (or 1.5B) model as required by FR‑002.  

- [X] T003 [Plan] Design the Mixed‑Effects Logistic Regression (GLMM) formula and stratification plan.  
  *Deliverable*: `docs/glmm_design.md`.  
- [ ] T003_v [Test] Verify `docs/glmm_design.md` exists and is syntactically valid (basic markdown checks).  

---

## Phase 1 – Project Setup  

- [ ] T004a [P] Create root directory structure (`setup.sh`).  
- [ ] T004b [P] Add verification script `scripts/verify_structure.py`.  
- [ ] T004c [P] Run verification and capture `project_structure.log`.  

- [ ] T005 [P] **Create `requirements.txt` at the correct location**  
  *Path*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt`  
  *Content*: Pin exact versions of `torch`, `transformers`, `datasets`, `scikit‑learn`, `pandas`, `numpy`, `pyyaml`, `pytest`, `statsmodels`, `psutil`, `huggingface_hub`, `pymer4`, `minigrid`, and any quantization libraries needed for Qwen‑1.5 models.  
- [ ] T005_v [Test] Unit test `tests/unit/test_requirements_exist.py` checks file existence and that each line matches `^[a-zA-Z0-9_-]+==[0-9\.]+$`.  

- [ ] T006 [P] **Add full Python project configuration files**  
  *Files & Paths*:  
  - `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/pyproject.toml` (declares project metadata, build system, and `[tool.black]` settings).  
  - `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/ruff.toml` (ruff linter configuration).  
  - `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/.black.toml` (black formatter config).  
- [ ] T006_v [Test] Unit test `tests/unit/test_pyproject_configs.py` asserts each file exists, is non‑empty, and parses as valid TOML.  

- [ ] T007a [P] Implement Shannon‑entropy helper `src/utils/entropy_calc.py`.  
- [ ] T007a_v [Test] Unit test `tests/unit/test_entropy_calc.py` verifies correct entropy calculation on a known probability vector.  

- [ ] T007b [P] Unit test for entropy clamping (`tests/unit/test_entropy_calc.py`).  
- [ ] T007b_v [Test] Verify the clamping test file exists and runs without error.  

- [ ] T008 [P] Implement schema validators in `src/utils/validators.py`.  
- [ ] T008_v [Test] Test `tests/contract/test_validators.py` ensures validators load and correctly validate example contracts.  

---

## Phase 2 – Foundational Infrastructure  

### Data Download & Ground‑Truth Acquisition  

- [ ] T009 [P] **Implement robust streaming batcher**  
  *Path*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/preprocessing.py`  
  *Function*: `stream_batch(examples: Iterable[Any], batch_size: int = 50) -> Iterator[List[Any]]`  
  - Yields lists of at most `batch_size` items.  
  - Raises `ConnectionError` or `FileNotFoundError` immediately if `datasets.load_dataset` fails.  
  - Includes docstring describing the 50‑token guarantee.  
- [ ] T009_v [Test] Integration test `tests/integration/test_preprocessing.py::test_stream_batch_yields_50_or_less` asserts every yielded batch length ≤ 50 and that a simulated load failure propagates as `ConnectionError`.  

- [ ] T010 [P] **Download GSM8K and MiniGrid with strict caps**  
  *Path*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py`  
  *Behaviour*:  
  1. Use `datasets.load_dataset("gsm8k", split="train", streaming=True)` and `datasets.load_dataset("minigrid", name="MiniGrid", split="train", streaming=True)`.  
  2. Apply `itertools.islice` to each iterator to keep **≤ 500 examples** per dataset.  
  3. Write the streamed records to `data/raw/gsm8k.jsonl` and `data/raw/minigrid.jsonl` (JSONL, one record per line).  
  4. If either download raises an exception, re‑raise `ConnectionError` or `FileNotFoundError` (no synthetic fallback).  
- [ ] T010_v [Test] Unit test `tests/unit/test_download.py::test_download_capped_examples` asserts that the output files contain ≤ 500 lines each and that a forced network error bubbles up as `ConnectionError`.  

- [ ] T012a [P] **Create canonical ground‑truth file**  
  *Path*: `data/canonical_ground_truth.jsonl`  
  *Process*:  
  1. Load the raw GSM8K and MiniGrid files produced by T010.  
  2. For GSM8K, extract the `answer` field from each record and write `{ "prompt_id": <id>, "task_type": "gsm8k", "canonical_solution": <answer> }`.  
  3. For MiniGrid, extract `start_state` and `goal_state` (or the provided solution path) and write `{ "prompt_id": <id>, "task_type": "minigrid", "valid_paths": [] }` – the `valid_paths` list will be populated later by BFS (T012b).  
- [ ] T012a_v [Test] Schema validation test `tests/contract/test_canonical_ground_truth_schema.py` loads the file and validates each record against `contracts/semantic_alignment.md` expectations.  

- [ ] T012b [P] **Populate MiniGrid `valid_paths`** using BFS over the environment graph.  
  *Path*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/minigrid_paths.py`.  

- [ ] T012c [P] Verify model fits into 7 GB RAM (report generated).  
- [ ] T012d‑e (failure‑path tasks) remain checked as they are only needed on SPEC‑VIOLATION.

---

## Phase 3 – User Story 1: Baseline Generation & Ground‑Truth Labelling  

- [ ] T013 [Impl] Generate ground‑truth token sequences for GSM8K using the selected CPU‑feasible model (temperature 0.0).  
  *Output*: `data/processed/gsm8k_sequences.jsonl`.  
- [ ] T014 [Impl] Generate ground‑truth token sequences for MiniGrid (temperature 0.0).  
  *Output*: `data/processed/minigrid_sequences.jsonl`.  
- [ ] T015 [Impl] Apply Semantic Alignment (GSM8K) to label each token as valid/invalid.  
  *Output*: `data/processed/gsm8k_labels.jsonl`.  
- [ ] T016 [Impl] Apply Semantic Alignment (MiniGrid) to label each token as valid/invalid.  
  *Output*: `data/processed/minigrid_labels.jsonl`.  
- [ ] T017 [Impl] Merge GSM8K and MiniGrid labeled sequences into a unified dataset.  
  *Output*: `data/processed/ground_truth_labels.jsonl`.  
- [ ] T018 [Test] Unit test `tests/unit/test_generation.py` checks that generation scripts produce the expected number of records and that token IDs are integers.  
- [ ] T019 [Test] Integration test `tests/integration/test_full_generation.py` runs the full generation‑labelling pipeline on a subset of 10 examples and verifies that every record contains a `validity_labels` array of matching length.  

---

## Phase 4 – User Story 2: Intermediate‑State Extraction & Entropy Calculation  

- [ ] T022 [Impl] Instrument the model to capture logits at every transformer layer during generation.  
  *File*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/hook.py`.  
- [ ] T023 [Impl] Compute Shannon entropy for each token at each layer from captured logits.  
  *Output*: `data/processed/entropy_profiles.jsonl`.  
- [ ] T024 [Impl] Process sequences **one at a time**, batching tokens in groups of 50 to stay within the 7 GB RAM limit (uses `stream_batch`).  
  *File*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/entropy_extractor.py`.  
- [ ] T025 [Test] Unit test `tests/unit/test_entropy_calc.py` validates entropy values against a manually computed example.  
- [ ] T026 [Test] Integration test `tests/integration/test_entropy_pipeline.py` runs the full extraction on a small sample (≤ 20 tokens) and checks that the resulting JSONL contains the correct number of layer entries per token.  
- [ ] T027 [Doc] Document the entropy extraction pipeline, including required environment variables and resource usage guidelines.  
  *Path*: `docs/entropy_pipeline.md`.  

---

## Phase 5 – User Story 3: Signal‑Decay Analysis & Threshold Optimisation  

- [ ] T030a [Impl] Merge `ground_truth_labels.jsonl` with `entropy_profiles.jsonl` into a single analysis dataset.  
  *Output*: `data/processed/merged_analysis.jsonl`.  
- [ ] T030b [Impl] Fit Mixed‑Effects Logistic Regression (GLMM) per task type (GSM8K, MiniGrid, pooled) and per layer group (early/mid/late).  
  *Outputs*: `data/results/regression_model_gsm8k.json`, `data/results/regression_model_minigrid.json`, `data/results/regression_model_pooled.json`.  
- [ ] T030c [Impl] Compute the log‑odds coefficient (correlation), AUC‑ROC, and record them in `data/results/metrics.json`.  
- [ ] T030d [Impl] Perform sensitivity analysis: sweep entropy threshold across a fine grid (e.g., 0.0 → 2.0 step 0.05), compute false‑positive and false‑negative rates, and store results in `data/results/sensitivity_analysis.json`.  
- [ ] T030e [Impl] Apply Benjamini‑Hochberg (FDR) correction to all p‑values across layers and tasks; output `data/results/fdr_report.json`.  
- [ ] T030f [Impl] Analyze decay of predictive power across sequence‑length groups (“short” < 100 tokens, “long” ≥ 100 tokens) and across task types; store in `data/results/decay_analysis.json`.  
- [ ] T030g [Doc] Summarize all findings, optimal entropy threshold, and statistical significance in the final regression results file.  
  *Output*: `data/results/regression_results.json`.  

---

## Phase 6 – Verification & Reporting  

- [ ] T040 [Test] Run full test suite (`pytest`) and capture results in `test_report.log`.  
- [ ] T041 [Impl] Validate all output artifacts against their JSON schemas (`contracts/*.schema.yaml`).  
  *File*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/utils/validators.py` (extended with schema‑checking utilities).  
- [ ] T042 [Impl] Record content hashes and `updated_at` timestamps for all artifacts in `state/projects/PROJ-881-llmxive-follow-up-extending-efficientrol.yaml`.  
  *Script*: `scripts/update_state.py`.  

---

## Phase 7 – Polish & Cross‑Cutting Concerns  

- [ ] T043 [Doc] Write comprehensive `README.md` with installation, usage, and reproducing the study.  
- [ ] T044 [Doc] Generate API documentation using Sphinx and place under `docs/api/`.  
- [ ] T045 [Impl] Implement command‑line interface `llmxive_entropy_predict` for end‑to‑end execution.  
  *File*: `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/cli/main.py`.  
- [ ] T046 [Test] Verify quick‑start guide works end‑to‑end on a fresh runner; test located at `tests/quickstart_test.py`.  

---

## Phase 8 – Data Integrity & Execution Safety (Revision Pass)  

- [ ] T047 [Impl] Compute SHA‑256 checksums for all raw and processed data files; store in `data/checksums.sha256`.  
- [ ] T048 [Impl] Verify checksums before pipeline execution; abort with clear error if mismatch.  
  *Script*: `scripts/verify_checksums.py`.  
- [ ] T049 [Impl] Ensure all dataset‑loading code raises `ConnectionError` or `FileNotFoundError` on failure (no silent fallback).  
- [ ] T050 [Test] Integration test `tests/integration/test_error_handling.py` confirms pipeline aborts with the correct exception when a required data file is missing.  

---

## Dependencies & Execution Order (summary)

| Task | Produces | Consumes | Parallel? |
|------|----------|----------|-----------|
| T005 | `requirements.txt` | – | ✔ |
| T006 | `pyproject.toml`, `ruff.toml`, `.black.toml` | – | ✔ |
| T009 | `stream_batch` utility | – | ✔ |
| T010 | Raw GSM8K & MiniGrid JSONL files | – | ✔ |
| T012a | `canonical_ground_truth.jsonl` | T010 output | ✔ |
| T012b | Populated `valid_paths` for MiniGrid | T012a | – |
| T013‑T019 | Generation & labeling pipeline | T012a, T012b, model report | – |
| T022‑T027 | Entropy extraction & validation | T019 output | – |
| T030a‑T030g | Statistical analysis & reporting | T025b (merged analysis) | – |
| … | … | … | … |

All unchecked tasks (including newly added ones) must be completed before downstream user‑story tasks can be executed successfully.

---  

*End of `tasks.md`.*  