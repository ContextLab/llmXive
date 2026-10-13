# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness  

**Input**: `specs/001-evaluating-the-impact-of-code-generation/`, `plan.md`, `data-model.md`, contracts, existing code and test files.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that extracts method signatures, generates LLM docstrings, computes coverage & similarity scores, performs statistical testing, and produces a final report, all while respecting the resource constraints and scientific requirements of the specification.

---

## Phase 0 – Plan Alignment (Prerequisite)

- [ ] T018a [P] **Edit `plan.md` to enforce hard 1 000‑method cap and remove any fallback‑to‑8‑bit or full‑precision notes**  
  *Implementation:* script `scripts/edit_plan.sh` updates the plan file, setting `MAX_METHODS = 1000` in the configuration section and deleting any lines containing “fallback to 8‑bit” or “fallback to full precision”.  
  **Verification**:  
  ```bash
  grep -q "MAX_METHODS = 1000" plan.md && \
  ! grep -q "fallback to 8-bit" plan.md && \
  ! grep -q "fallback to full precision" plan.md && \
  ! grep -q "100 methods" plan.md
  ```

- [ ] T018b [S] **Update `plan.md` to align with `spec.md`** *(BLOCKED: plan edit required – plan still contains fallback‑to‑8‑bit clause)*  
  *Add a hard cap of 1 000 methods per repository, remove any “100 methods” mentions, and delete the fallback‑to‑8‑bit note.*  
  **Verification**:  
  ```bash
  grep -q "MAX_METHODS = 1000" plan.md && \
  ! grep -q "100 methods" plan.md && \
  ! grep -q "fallback to 8-bit" plan.md && \
  ! grep -q "fallback to full precision" plan.md
  ```

- [ ] T018c [S] **Meta‑task: Flag plan‑root cause for kick‑back**  
  *If `plan.md` still contains disallowed text, raise a reviewer flag and pause further execution until the plan is corrected.*  
  **Verification**: Same as T018b; task remains pending until plan passes.

- [ ] T018d [S] **Meta‑task: Request deterministic‑generation clause removal**  
  *Ensure the plan no longer contains any fallback to 8‑bit or full‑precision model loading.*  
  **Verification**:  
  ```bash
  ! grep -q "fallback to 8-bit" plan.md && ! grep -q "fallback to full precision" plan.md
  ```

---

## Phase 1 – Setup (already verified)

- [ ] T001a [P] Create project directory skeleton via `scripts/setup.sh` (paths: `code/`, `data/raw/repos/`, `data/processed/`, `tests/`, `state/`, `logs/`).  
- [ ] T001b [S] Verify `.gitkeep` files exist in every created directory (log in `logs/setup.log`).  
- [ ] T002a [P] Add `code/requirements.txt` with pinned dependencies.  
- [ ] T002b [P] Add `code/config.py` defining `SEED = 42`, `MAX_METHODS = 1000`, **and** `TEMPERATURE = 0.2`.  
- [ ] T002c [P] Add `code/verify_seed.py` and confirm reproducible random output.  
- [ ] T002d [P] Create initial `specs/001-evaluating-the-impact-of-code-generation/data-model.md`.  
- [ ] T003   [P] Add `.flake8` and `pyproject.toml` for lint/formatting.  

---

## Phase 2 – Foundational Infrastructure (already verified)

- [ ] T011b [S] Add `code/utils/exceptions.py` with `MemoryLimitException`.  
- [ ] T010  [S] Implement `code/utils/repo_fetcher.py` to fetch top‑20 PyPI repos, write `data/raw/frozen_repo_list.json`, and copy to `data/raw/repo_list.json`.  
- [ ] T011  [S] Implement `code/utils/model_loader.py` that loads `Salesforce/codegen-mono` in **4‑bit** quantization via `bitsandbytes`; abort on any fallback.  
- [ ] T012  [US1] Unit test `tests/unit/test_ast_parser.py` – ensure malformed files are skipped.  
- [ ] T013  [US1] Unit test `tests/unit/test_coverage.py` – ensure `human_docstring` is `null` when missing.  
- [ ] T014  [US1] Integration test `tests/integration/test_extraction.py` – run extraction on a single repo.  
- [ ] T027a [S] Extend `data-model.md` with schema for `generation_batch_{repo_slug}_cleaned.json`.  
  **Verification**:  
  ```bash
  grep -q "generation_batch_.*_cleaned.json" data-model.md
  ```
- [ ] T041b [S] Refactor `code/analyze.py` to expose `main()` with `--step` CLI (`coverage`, `similarity`, `stats`, `report`).  
- [ ] T041c [S] **Unit test for CLI** – invoke `python -m code.analyze --step coverage` and assert exit code 0.  

---

## Phase 3 – User Story 1: Repository Extraction & Ground‑Truth Preparation (P1)

- [ ] T015 [US1] Add `code/utils/git_clone.py` – clones a repo into `data/raw/repos/`.  
- [ ] T016 [US1] Add `code/utils/file_walker.py` – yields `.py` files from a cloned repo.  
- [ ] T017 [US1] Implement `code/extract.py` – parses public methods with `ast`, extracts signatures & human docstrings, writes per‑repo JSON to `data/raw/repos/{repo_slug}.json`.  
- [ ] T018 [US1] Enforce truncation to `MAX_METHODS` (1 000) per repository; log row count.  
- [ ] T019 [US1] Serialize each extraction JSON, compute SHA‑256, and record in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` under `artifact_hashes`.  
- [ ] T020 [US1] Ensure missing docstrings are stored as `null` (not empty string).  

---

## Phase 4 – User Story 2: LLM Docstring Generation (P2)

- [ ] T021 [US2] Unit test `tests/unit/test_generation.py` – verify 4‑bit model loads without fallback.  
- [ ] T022 [US2] Unit test `tests/unit/test_monitor.py` – confirm RAM monitor logs `RAM_LIMIT_EXCEEDED` and aborts > 7 GB.  
- [ ] T023 [US2] Integration test `tests/integration/test_generation.py` – generate docs for a small batch and check output fields.  
- [ ] T024b [P] **Add temperature constant** – insert `TEMPERATURE = 0.2` into `code/config.py`.  
- [ ] T024c [P] **Enforce CPU‑only execution** – in `code/generate.py` check `torch.cuda.is_available()`; abort if true.  
- [ ] T024 [US2] Implement `code/generate.py` – iterates over all `data/raw/repos/*.json`, loads the 4‑bit model, generates docstrings with temperature from `config.py`, respects `MAX_METHODS`, writes batch files `data/processed/generation_batch_{repo_slug}.json`.  
- [ ] T025 [US2] Add `code/utils/memory_monitor.py` and integrate into `code/generate.py`.  
- [ ] T027 [US2] Implement `code/post_process.py` – flags empty/whitespace generated docstrings (`needs_review: true`) and writes cleaned files `data/processed/generation_batch_{repo_slug}_cleaned.json`.  
- [ ] T026a [P] **Synthetic results for early testing** – create `data/processed/results.json` with minimal valid records for unit‑test development.  
  **Verification**:  
  ```bash
  test -s data/processed/results.json && head -n 1 data/processed/results.json | grep -q '"repo_slug"'
  ```
- [ ] T026 [US2] Implement `code/aggregate.py` – merges all cleaned batch files into `data/processed/results.json`; validates per‑repo ≤ 1 000 rows and total ≤ 20 000 rows.  

---

## Phase 5 – User Story 3: Coverage, Similarity & Statistical Analysis (P3)

- [ ] T030 [P] Unit tests `tests/unit/test_stats.py` – verify semantic‑similarity calculation and Wilcoxon test, including low‑sample warning.  

- [ ] T033 [US3] **Parameter‑Coverage Calculation**  
  *Read `data/processed/results.json`, compute `coverage_score` for each record using `docstring_parser` (case‑insensitive param match). On parse failure set `parse_error: true` and score 0.0. Write `data/processed/results_with_coverage.json`.*  
  **Verification**: File exists, non‑empty, each entry contains `coverage_score` (0.0 – 1.0).  

- [ ] T033c [S] **Coverage range test** – pytest that asserts every `coverage_score` is a float within [0.0, 1.0].  

- [ ] T034 [US3] **Semantic‑Similarity Calculation**  
  *Read `data/processed/results_with_coverage.json`, embed human & generated docstrings with `sentence-transformers/all-MiniLM-L-v2`, compute cosine similarity, append `semantic_similarity` field, and write `data/processed/results_with_scores.json`.*  
  **Verification**: File exists, non‑empty, each entry contains `semantic_similarity` (‑1 – 1).  

- [ ] T034c [S] **Semantic similarity range test** – pytest that checks `semantic_similarity` lies within [‑1.0, 1.0].  

- [ ] T035 [US3] **Wilcoxon Signed‑Rank Test**  
  *Read `data/processed/results_with_scores.json`, extract paired `human` and `LLM` coverage scores, run `scipy.stats.wilcoxon`, log warning if n < 30, write `data/processed/results_with_stats.json` containing `wilcoxon_statistic` and `wilcoxon_p_value`.*  
  **Verification**: File exists, contains numeric `wilcoxon_statistic` and `wilcoxon_p_value`.  

- [ ] T035c [S] **Wilcoxon numeric verification** – pytest that asserts both fields are numbers.  

- [ ] T037 [US3] **Final Report Generation**  
  *Read `data/processed/results_with_stats.json`, compute mean coverage for human & LLM, total method count, significance flag (`p < 0.05` && |mean diff| > 0.05), record total runtime, and write `data/processed/final_report.json`.*  
  **Verification**: File exists, matches `specs/001-evaluating-the-impact-of-code-generation/contracts/results.schema.yaml`.  

- [ ] T037c [S] **Final report schema validation** – run `jsonschema.validate` against `results.schema.yaml`.  

- [ ] T042 [S] **Contract validation** – run JSON‑schema validation on all intermediate and final JSON artifacts (`dataset.schema.yaml`, `results.schema.yaml`).  
  **Verification**: All validated without errors; failures abort the pipeline.  

- [ ] T042a [S] **Schema validation task for generated artifacts**  
  *After each major step (extraction, generation, coverage, similarity, stats), invoke `jsonschema.validate` against the corresponding schema files to ensure conformity.*  
  **Verification**: Pipeline logs “Schema validation passed” for each artifact; any validation error causes immediate failure.  

---

## Phase 6 – Polish & Cross‑Cutting Tasks

- [ ] T039 [P] **Update `README.md`** – add installation instructions (`pip install -r code/requirements.txt`), usage examples for each pipeline stage (`extract.py`, `generate.py`, `analyze.py --step=…`), and a brief description of the research question.  
  **Verification**: `grep -q "## Installation" README.md && grep -q "## Usage" README.md`.  

- [ ] T040 [P] **Create/Update `quickstart.md`** – step‑by‑step guide that runs the full pipeline on a single repo (e.g., `requests`) from data download to final report, with exact CLI commands.  
  **Verification**: `grep -q "bash scripts/setup.sh" quickstart.md && grep -q "python code/extract.py" quickstart.md`.  

- [ ] T043 [P] **Add Unit Tests for Previously Uncovered Paths**  
  *Examples: test that `code/utils/model_loader.py` raises `QuantizationError` on non‑4‑bit load, test that `code/post_process.py` correctly flags whitespace docstrings, test that `code/analyze.py` CLI rejects unknown `--step` values.*  
  **Verification**: `pytest -q tests/unit/ | wc -l` returns a count ≥ 3 and all tests pass.  

- [ ] T048 [P] **Documentation of Runtime & Resource Monitoring** – add a short `docs/runtime.md` file describing how RAM usage is logged, how timeouts are handled, and where logs are stored (`logs/monitor.log`).  
  **Verification**: `grep -q "docs/runtime.md" README.md`.  

- [ ] T048c [S] **Reference check** – ensure `README.md` contains a link to `docs/runtime.md`.  

---

## Dependency & Execution Order Summary  

| Phase | Task ID(s) | Depends On |
|------|------------|------------|
| 0 | T018a, T018b, T018c, T018d | – |
| 1 | T001a‑T003 | – |
| 2 | T011b‑T041c | Phase 1 |
| 3 | T015‑T020 | Phase 2 |
| 4 | T021‑T024c, T025, T026a, T026 | Phase 3 |
| 5 | T030, T033‑T037c, T042, T042a | Phase 4 |
| 6 | T039‑T048c | Phases 1‑5 |

All tasks respect the data‑flow: extraction → generation → post‑processing → aggregation → coverage → similarity → statistical test → final report. New verification tasks ensure every step is programmatically checked, contract compliance is enforced, and the plan‑related constitutional violations are flagged for author correction.  

*All unchecked tasks are pending implementation; checked tasks have been verified as complete.*  