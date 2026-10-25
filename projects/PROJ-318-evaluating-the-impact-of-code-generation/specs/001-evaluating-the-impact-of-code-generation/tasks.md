# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, existing code and test files.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) extracts public method signatures and human docstrings from a stratified sample of PyPI repositories, (2) generates docstrings with the `Salesforce/codegen-350M-mono` model under CPU‑only, low‑bit constraints, (3) computes Parameter Coverage, Description Coverage, and semantic‑similarity scores, (4) performs a Wilcoxon signed‑rank test, and (5) produces a validated final report, all while respecting the resource limits and scientific requirements of the specification.

---

## Phase 0 – Plan alignment  

- [ ] **T001** [P] Edit `plan.md` to enforce the hard 1 000‑method cap and remove any fallback‑to‑8‑bit or full‑precision notes.  
  *Verification*:  
  ```bash
  grep -q "MAX_METHODS = 1000" plan.md && \
  ! grep -q "fallback to 8-bit" plan.md && \
  ! grep -q "fallback to full precision" plan.md
  ```

---

## Phase 1 – Project skeleton & reproducibility  

- [ ] **T002** [P] Create project directory skeleton (`code/`, `data/raw/`, `data/processed/`, `tests/`, `logs/`, `state/`) and install pinned dependencies via `code/requirements.txt`.  
  *Verification*: `tree -L 2` shows required directories and `pip install -r code/requirements.txt` exits with status 0.  

- [ ] **T003** [P] Add `code/config.py` (`SEED = 42`, `MAX_METHODS = 1000`, `TEMPERATURE = 0.2`) and `code/utils/seed_manager.py` that seeds Python, NumPy, and PyTorch from `config.SEED`.  
  *Verification*:  
  ```bash
  python -c "import code.config, code.utils.seed_manager; print('ok')"
  ```

---

## Phase 2 – Data‑source infrastructure & contract validation  

- [ ] **T004** [S] Implement `code/utils/repo_fetcher.py` to (a) fetch the top‑20 PyPI packages, (b) perform stratified sampling across high/medium/low popularity tiers (≥ 5 repos per tier), and (c) write `data/raw/frozen_repo_list.json`. Validate the file against a lightweight schema derived from `contracts/dataset.schema.yaml`.  
  *Verification*:  
  ```bash
  python -c "import json, jsonschema, pathlib; schema=json.load(open('contracts/dataset.schema.yaml')); data=json.load(open('data/raw/frozen_repo_list.json')); jsonschema.validate(data,schema)"
  ```

- [ ] **T005** [S] Add `code/utils/model_loader.py` that loads `Salesforce/codegen-350M-mono` with `bitsandbytes` in **4‑bit CPU‑only** mode (`load_in_4bit=True`). It raises `RuntimeError` if `torch.cuda.is_available()` or if the model is not 4‑bit.  
  *Verification*: Running the loader prints “Model loaded in 4‑bit CPU mode” and exits with status 0; any deviation raises an exception.

---

## Phase 3 – Extraction (User Story 1)  

- [ ] **T006** [US1] Clone each repository listed in `frozen_repo_list.json` into `data/raw/repos/{repo_slug}` (via `code/utils/git_clone.py`), walk the source tree, parse public methods with `code/utils/ast_parser.py`, truncate to `config.MAX_METHODS` per repo, and write `data/raw/repos/{repo_slug}.json`. Missing docstrings are stored as `null`.  
  *Verification*:  
  ```bash
  python code/extract.py && \
  jq '. | length' data/raw/repos/requests.json | grep -E '^[0-9]{1,3}$' && \
  grep -q '"human_docstring": null' data/raw/repos/requests.json
  ```

- [ ] **T007** [US1] Record SHA‑256 hashes of each `data/raw/repos/*.json` in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`.  
  *Verification*: `grep -A1 sha256 state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` shows at least one entry.

---

## Phase 4 – Generation (User Story 2)  

- [ ] **T008** [US2] Generate LLM docstrings with `code/generate.py`: load the model via `model_loader.py`, prompt **only the method signature**, use `config.TEMPERATURE = 0.2`, enforce a per‑method timeout of 30 s, monitor RAM (abort > 7 GB), and write `data/processed/generation_batch_{repo_slug}.json` containing `generated_docstring`, `generation_status`, and `error_message`.  
  *Verification*: After running on a single repo (e.g., `requests`), `jq '.[] | .generated_docstring' data/processed/generation_batch_requests.json | wc -l` equals the number of input records and no `generation_status` equals `"error"`.

---

## Phase 5 – Post‑processing & aggregation  

- [ ] **T009** [US2] Flag empty/whitespace generated docstrings in `code/post_process.py`: add `needs_review: true`, set `coverage_score: 0.0` for those records, and write cleaned files `data/processed/generation_batch_{repo_slug}_cleaned.json`.  
  *Verification*: `grep -A1 '"needs_review": true' data/processed/generation_batch_*_cleaned.json | head -n 5` returns at least one match.  

- [ ] **T010** [P] Aggregate all cleaned batches into a unified `data/processed/results.json` with `code/aggregate.py`; enforce per‑repo ≤ 1000 rows and total ≤ 20 000 rows.  
  *Verification*: `jq '. | length' data/processed/results.json` returns a number ≤ 20000 and each record contains `"repo_slug"`.

---

## Phase 6 – Coverage & description metrics (User Story 3 – Part 1)  

- [ ] **T011** [US3] Compute **Parameter Coverage** and **Description Coverage** with `code/analyze.py --step=coverage`. The script applies deterministic matching (FR‑018) to produce `parameter_coverage_score` and tokenises docstrings (NLTK, stop‑word removal) to produce `description_coverage_score`. Output written to `data/processed/results_with_coverage.json`.  
  *Verification*:  
  ```bash
  python -m code.analyze --step=coverage && \
  head -n 1 data/processed/results_with_coverage.json | jq '.parameter_coverage_score, .description_coverage_score'
  ```

- [ ] **T012** [S] Unit test `tests/unit/test_coverage.py` asserts every `parameter_coverage_score` is in `[0.0,1.0]` and every `description_coverage_score` is a non‑negative float.  
  *Verification*: `pytest -q tests/unit/test_coverage.py` exits with 0.

---

## Phase 7 – Semantic similarity (User Story 3 – Part 2)  

- [ ] **T013** [US3] Compute semantic similarity between human and generated docstrings with `code/analyze.py --step=similarity` (uses `sentence‑transformers/all‑MiniLM‑L6‑v2`). Adds `semantic_similarity` field and writes `data/processed/results_with_scores.json`.  
  *Verification*:  
  ```bash
  python -m code.analyze --step=similarity && \
  head -n 1 data/processed/results_with_scores.json | jq '.semantic_similarity'
  ```

- [ ] **T014** [S] Unit test `tests/unit/test_similarity.py` checks that every `semantic_similarity` lies within `[-1.0, 1.0]`.  
  *Verification*: `pytest -q tests/unit/test_similarity.py` passes.

---

## Phase 8 – Statistical analysis & final report (User Story 3 – Part 3)  

- [ ] **T015** [US3] Run Wilcoxon signed‑rank test on **paired Composite Scores** (`0.4 * parameter_coverage_score + 0.6 * description_coverage_score`) with `code/analyze.py --step=stats`. The script logs a warning if total paired records `< 30`, aggregates per‑repository means, computes the test, and writes `data/processed/final_report.json` containing p‑value, statistic, effect size, significance flag, and runtime.  
  *Verification*:  
  ```bash
  python -m code.analyze --step=stats && \
  jq '.wilcoxon_p_value, .significance' data/processed/final_report.json
  ```

- [ ] **T016** [S] Integration test `tests/integration/test_final_report_schema.py` validates `final_report.json` against `contracts/results.schema.yaml`.  
  *Verification*: `pytest -q tests/integration/test_final_report_schema.py` passes.

---

## Phase 9 – User documentation  

- [ ] **T017** [P] Create/Update `quickstart.md` with a step‑by‑step runnable guide: installation, repository list fetch, extraction, generation, coverage, similarity, statistical analysis, and how to view `final_report.json`.  
  *Verification*: `grep -q "python -m code.analyze --step=stats" quickstart.md`.

---

## Phase 10 – Expanded testing for uncovered paths  

- [ ] **T018** [S] Add unit tests for previously uncovered code paths:  
  * `tests/unit/test_model_loader.py` – ensures `model_loader.load_model()` raises if GPU is available or if bits ≠ 4.  
  * `tests/unit/test_post_process.py` – verifies whitespace‑only docstrings are flagged with `needs_review: true`.  
  * `tests/unit/test_analyze_cli.py` – checks that `code.analyze` exits non‑zero for an unknown `--step` argument.  
  *Verification*: `pytest -q tests/unit/` reports ≥ 3 passed tests and 0 failures.

---

## Phase 11 – Contract enforcement after each major stage  

- [ ] **T019** [S] Implement `scripts/validate_contracts.sh` that runs `jsonschema.validate` against the appropriate contract (`dataset.schema.yaml` after extraction, `results.schema.yaml` after coverage, similarity, and stats). The script is invoked automatically after each stage and aborts on failure.  
  *Verification*: CI logs contain “Schema validation passed for *stage*”; manual run exits with status 0.

---

## Phase 12 – Missing artifacts remediation (previously rejected tasks)

- [ ] **T033** [US3] **Generate `results.json` and `results_with_coverage.json`**  
  *Action*: Run the aggregation script (`code/aggregate.py`) to produce `data/processed/results.json`, then execute `code/analyze.py --step=coverage` to create `data/processed/results_with_coverage.json`.  
  *Verification*:  
  ```bash
  [ -s data/processed/results.json ] && \
  [ -s data/processed/results_with_coverage.json ] && \
  jq '. | length' data/processed/results.json | grep -E '^[0-9]+$'
  ```

- [ ] **T034** [US3] **Generate `results_with_scores.json` (semantic similarity)**  
  *Action*: After `results_with_coverage.json` exists, run `code/analyze.py --step=similarity` to produce `data/processed/results_with_scores.json`.  
  *Verification*:  
  ```bash
  [ -s data/processed/results_with_scores.json ] && \
  jq '.[0] | .semantic_similarity' data/processed/results_with_scores.json
  ```

- [ ] **T040** [P] **Update `quickstart.md`** (see T017). The updated file must now be present in the repository root.  
  *Verification*: `test -f quickstart.md && grep -q "python -m code.analyze --step=stats" quickstart.md`.

- [ ] **T043** [S] **Add the new unit tests** (see T018). Ensure the test files exist under `tests/unit/` and are discovered by `pytest`.  
  *Verification*: `pytest -q tests/unit/ | grep -q "passed"`.

---

## Execution order summary  

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
|12 | T033, T034, T040, T043 | T019 (ensures contracts are satisfied before final artifacts) |

All tasks are currently unchecked to allow fresh execution; completed artifacts from prior runs remain untouched. The pipeline respects data flow, real‑data usage, CPU‑only computation, and every scientific requirement of the specification.
