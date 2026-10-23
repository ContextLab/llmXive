# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, existing code and test files.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) extracts public method signatures and human docstrings from a stratified sample of PyPI repositories, (2) generates docstrings with the `Salesforce/codegen-350M-mono` model under CPU‑only, low‑bit constraints, (3) computes Parameter Coverage, Description Coverage, and semantic‑similarity scores, (4) performs a Wilcoxon signed‑rank test, and (5) produces a validated final report, all while respecting the resource limits and scientific requirements of the specification.

---

## Phase 0 – Plan alignment  

- [ ] T001 [P] **Edit `plan.md` to enforce the hard 1 000‑method cap and remove any fallback‑to‑8‑bit or full‑precision notes**  
  *Implementation*: `scripts/edit_plan.sh` inserts `MAX_METHODS = 1000` in the configuration section and deletes any lines containing “fallback to 8‑bit”, “fallback to full precision”, or references to a 100‑method limit.  
  *Verification*:  
  ```bash
  grep -q "MAX_METHODS = 1000" plan.md && \
  ! grep -q "fallback to 8-bit" plan.md && \
  ! grep -q "fallback to full precision" plan.md && \
  ! grep -q "100 methods" plan.md
  ```

---

## Phase 1 – Project skeleton & dependencies  

- [ ] T002 [P] **Create project directory skeleton and install pinned dependencies**  
  *Creates*: `code/`, `data/raw/`, `data/processed/`, `tests/`, `logs/`, `state/` (with `.gitkeep` files).  
  *Adds*: `code/requirements.txt` (pinned versions of `torch`, `bitsandbytes`, `transformers`, `datasets`, `sentence-transformers`, `nltk`, `scipy`, `gitpython`, `requests`).  
  *Verification*: `tree` shows required directories and `pip install -r code/requirements.txt` completes without errors.

- [ ] T003 [P] **Add basic configuration and reproducibility utilities**  
  *File*: `code/config.py` defines `SEED = 42`, `MAX_METHODS = 1000`, `TEMPERATURE = 0.2`.  
  *File*: `code/utils/seed_manager.py` sets Python, NumPy, and PyTorch seeds from `config.SEED`.  
  *Verification*: Running `python -c "import code.config, code.utils.seed_manager; print('ok')"` prints `ok` and reproduces identical random numbers across runs.

---

## Phase 2 – Infrastructure & contract validation  

- [ ] T004 [S] **Implement repository list fetcher and schema validation**  
  *File*: `code/utils/repo_fetcher.py` fetches the top‑20 PyPI packages, performs stratified sampling across high/medium/low popularity tiers (≥ 5 repos per tier), writes `data/raw/frozen_repo_list.json`.  
  *Task*: After creation, run `jsonschema.validate` against `contracts/dataset.schema.yaml` (adapted for repo list) to ensure correctness.  
  *Verification*: `python -c "import json, jsonschema, pathlib; schema=json.load(open('contracts/dataset.schema.yaml')); data=json.load(open('data/raw/frozen_repo_list.json')); jsonschema.validate(data,schema)"` exits with status 0.

- [ ] T005 [S] **Add model‑loader utility with strict 4‑bit CPU‑only loading**  
  *File*: `code/utils/model_loader.py` loads `Salesforce/codegen-350M-mono` via `bitsandbytes` with `load_in_4bit=True`. It aborts if `torch.cuda.is_available()` is true or if the loader falls back to a higher‑bit mode.  
  *Verification*: Running the loader on the CI runner prints “Model loaded in 4‑bit CPU mode” and exits with status 0; any deviation raises `RuntimeError`.

---

## Phase 3 – Extraction (User Story 1)  

- [ ] T006 [US1] **Clone repositories and extract public method signatures with AST**  
  *Files*: `code/utils/git_clone.py` (clones each repo into `data/raw/repos/{repo_slug}`), `code/utils/file_walker.py` (yields `.py` files), `code/utils/ast_parser.py` (parses public methods, extracts signatures, human docstrings, and `ast_params`).  
  *Script*: `code/extract.py` iterates over `data/raw/frozen_repo_list.json`, clones, parses, truncates to `config.MAX_METHODS` per repo, writes `data/raw/repos/{repo_slug}.json`. Missing docstrings are stored as `null`.  
  *Verification*:  
  ```bash
  python code/extract.py && \
  jq '. | length' data/raw/repos/requests.json | grep -E '^[0-9]{1,3}$' && \
  grep -q '"human_docstring": null' data/raw/repos/requests.json
  ```

- [ ] T007 [US1] **Record artifact hashes for reproducibility**  
  *File*: `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` is updated with SHA‑256 hashes of each `data/raw/repos/*.json`.  
  *Verification*: `cat state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml | grep sha256` shows entries for at least one repo.

---

## Phase 4 – Generation (User Story 2)  

- [ ] T008 [US2] **Generate LLM docstrings under CPU‑only, low‑bit constraints**  
  *Script*: `code/generate.py` loads the model via `model_loader.py`, reads each extraction JSON, prompts the model **solely with the method signature** (no surrounding code), uses `config.TEMPERATURE = 0.2`, enforces a per‑method timeout of 30 s, monitors RAM (abort > 7 GB). Writes batch files `data/processed/generation_batch_{repo_slug}.json` with fields `generated_docstring`, `generation_status`, `error_message`.  
  *Verification*: After running on a single repo (e.g., `requests`), `jq '.[] | .generated_docstring' data/processed/generation_batch_requests.json | wc -l` equals the number of input records and no `generation_status` is `"error"`.

---

## Phase 5 – Post‑processing & aggregation  

- [ ] T009 [US2] **Flag empty/whitespace generated docstrings and compute preliminary coverage fields**  
  *Script*: `code/post_process.py` reads each generation batch, adds `needs_review: true` for empty/whitespace `generated_docstring`, sets `coverage_score: 0.0` for those records, and writes cleaned files `data/processed/generation_batch_{repo_slug}_cleaned.json`.  
  *Verification*: `grep -A1 '"needs_review": true' data/processed/generation_batch_*_cleaned.json` returns at least one match.

- [ ] T010 [P] **Aggregate all cleaned batches into a unified results file**  
  *Script*: `code/aggregate.py` concatenates all `*_cleaned.json` files, verifies per‑repo row count ≤ 1000 and total rows ≤ 20 000, writes `data/processed/results.json`.  
  *Verification*: `jq '. | length' data/processed/results.json` returns a number ≤ 20000 and `head -n 1 data/processed/results.json | grep -q '"repo_slug"'`.

---

## Phase 6 – Coverage & description metrics (User Story 3 – Part 1)  

- [ ] T011 [US3] **Compute Parameter Coverage and Description Coverage scores**  
  *Extension*: `code/analyze.py --step=coverage` reads `data/processed/results.json`, for each record applies the deterministic matching rule (FR‑018) to compute `parameter_coverage_score`, tokenises each docstring with NLTK to compute `description_coverage_score` (average non‑stop‑word tokens per documented parameter, zero for undocumented ones). Writes `data/processed/results_with_coverage.json`.  
  *Verification*:  
  ```bash
  python -m code.analyze --step=coverage && \
  jq '.[0] | .parameter_coverage_score, .description_coverage_score' data/processed/results_with_coverage.json | head -n 2
  ```

- [ ] T012 [S] **Unit test for coverage range**  
  *File*: `tests/unit/test_coverage.py` asserts that every `parameter_coverage_score` is a float in `[0.0,1.0]` and every `description_coverage_score` is a non‑negative float.  
  *Verification*: `pytest -q tests/unit/test_coverage.py` exits with 0 and reports ≥ 1 passed test.

---

## Phase 7 – Semantic similarity (User Story 3 – Part 2)  

- [ ] T013 [US3] **Compute semantic similarity between human and generated docstrings**  
  *Extension*: `code/analyze.py --step=similarity` loads `sentence-transformers/all-MiniLM-L6-v2`, embeds both docstrings, computes cosine similarity, adds `semantic_similarity` field, and writes `data/processed/results_with_scores.json`.  
  *Verification*:  
  ```bash
  python -m code.analyze --step=similarity && \
  jq '.[0] | .semantic_similarity' data/processed/results_with_scores.json
  ```

- [ ] T014 [S] **Unit test for similarity bounds**  
  *File*: `tests/unit/test_similarity.py` checks that each `semantic_similarity` lies within `[-1.0, 1.0]`.  
  *Verification*: `pytest -q tests/unit/test_similarity.py` passes.

---

## Phase 8 – Statistical analysis & final report (User Story 3 – Part 3)  

- [ ] T015 [US3] **Run Wilcoxon signed‑rank test on paired Composite Scores and produce final report**  
  *Extension*: `code/analyze.py --step=stats` reads `results_with_scores.json`, computes the Composite Documentation Completeness Score (`0.4 * parameter_coverage_score + 0.6 * description_coverage_score`) for human and LLM records, aggregates per‑repository means, runs `scipy.stats.wilcoxon` on the paired repository means, logs a warning if total paired records `< 30`, and writes `data/processed/final_report.json` containing fields required by `results.schema.yaml` (p‑value, statistic, effect size, significance flag, runtime).  
  *Verification*:  
  ```bash
  python -m code.analyze --step=stats && \
  jq '.wilcoxon_p_value, .significance' data/processed/final_report.json
  ```

- [ ] T016 [S] **Schema validation of final report**  
  *File*: `tests/integration/test_final_report_schema.py` runs `jsonschema.validate` against `contracts/results.schema.yaml`.  
  *Verification*: `pytest -q tests/integration/test_final_report_schema.py` passes.

---

## Phase 9 – Documentation for users  

- [ ] T017 [P] **Create/Update `quickstart.md` with a step‑by‑step runnable guide**  
  *Contents*: Installation (`pip install -r code/requirements.txt`), data download (`python code/utils/repo_fetcher.py`), extraction (`python code/extract.py`), generation (`python code/generate.py`), analysis steps (`python -m code.analyze --step=coverage`, `--step=similarity`, `--step=stats`), and how to view the final report (`cat data/processed/final_report.json`).  
  *Verification*: `grep -q "python -m code.analyze --step=stats" quickstart.md`.

---

## Phase 10 – Expanded testing for uncovered paths  

- [ ] T018 [S] **Add unit tests for previously uncovered code paths**  
  *Files*:  
  - `tests/unit/test_model_loader.py` ensures `model_loader.load_model()` raises an error if GPU is available or if the loaded bits are not 4‑bit.  
  - `tests/unit/test_post_process.py` verifies that whitespace‑only generated docstrings are flagged with `needs_review: true`.  
  - `tests/unit/test_analyze_cli.py` checks that `code.analyze` exits with a non‑zero code for an unknown `--step` argument.  
  *Verification*: `pytest -q tests/unit/` reports ≥ 3 passed tests and 0 failures.

---

## Phase 11 – Continuous contract enforcement  

- [ ] T019 [S] **Run JSON‑schema validation after each major pipeline stage**  
  *Implementation*: After extraction, generation, coverage, similarity, and stats steps, a thin wrapper script (`scripts/validate_contracts.sh`) invokes `jsonschema.validate` against the appropriate contract (`dataset.schema.yaml` or `results.schema.yaml`). Failures abort the pipeline.  
  *Verification*: The CI log contains “Schema validation passed for *stage*” messages; manually running the script on a fresh run exits with status 0.

---

### Execution order summary  

| Phase | Task IDs | Depends on |
|------|----------|------------|
| 0 | T001 | – |
| 1 | T002, T003 | T001 |
| 2 | T004, T005 | T002, T003 |
| 3 | T006, T007 | T004, T005 |
| 4 | T008 | T006 |
| 5 | T009, T010 | T008 |
| 6 | T011, T012 | T010 |
| 7 | T013, T014 | T011 |
| 8 | T015, T016 | T013 |
| 9 | T017 | T015 |
|10 | T018 | T017 |
|11 | T019 | All previous phases |

All tasks are unchecked to allow fresh execution; completed artifacts from prior runs remain untouched. The pipeline respects data flow, real‑data usage, CPU‑only computation, and the scientific requirements of the specification.
