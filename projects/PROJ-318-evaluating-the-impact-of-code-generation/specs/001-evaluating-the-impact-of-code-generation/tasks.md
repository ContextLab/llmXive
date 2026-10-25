# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, existing code and test files.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) extracts public method signatures and human docstrings from a stratified sample of PyPI repositories, (2) generates docstrings with the `Salesforce/codegen-350M-mono` model under CPU‑only, low‑bit constraints, (3) computes Parameter Coverage, Description Coverage, and semantic‑similarity scores, (4) performs a Wilcoxon signed‑rank test, and (5) produces a validated final report, all while respecting the resource limits and scientific requirements of the specification.

---

## Phase 0 – Plan alignment  

- [ ] T001 [P] Edit `plan.md` to enforce the hard 1 000‑method cap per repository, remove any fallback‑to‑8‑bit or full‑precision notes, and add a concise “MAX_METHODS = 1000” constant comment.  
  *Verification*: `grep -q "MAX_METHODS = 1000" plan.md && ! grep -q "fallback" plan.md`.

---

## Phase 1 – Project skeleton & reproducibility  

- [ ] T002 [P] Create the standard directory layout (`code/`, `data/raw/`, `data/processed/`, `tests/`, `state/`) and add a pinned `code/requirements.txt` (Python 3.11, `torch`, `transformers`, `bitsandbytes`, `datasets`, `sentence-transformers`, `nltk`, `scipy`, `gitpython`, `jsonschema`, `pytest`).  
  *Verification*: `tree -L 2` shows the required folders and `pip install -r code/requirements.txt` exits with status 0.  

- [ ] T003 [P] Add `code/config.py` containing `SEED = 42`, `MAX_METHODS = 1000`, `TEMPERATURE = 0.2`, and add `code/utils/seed_manager.py` that seeds Python’s `random`, NumPy, and PyTorch from `config.SEED`.  
  *Verification*: `python -c "import code.config, code.utils.seed_manager; print('ok')"` prints `ok` without error.

---

## Phase 2 – Data‑source infrastructure  

- [ ] T004 [US1] Implement `code/utils/repo_fetcher.py` that (a) queries the PyPI JSON API for the top‑20 packages, (b) performs stratified sampling across high/medium/low popularity tiers (≥ 5 repos per tier) as required by FR‑010, and (c) writes `data/raw/frozen_repo_list.json`. Validate the file with a lightweight JSON‑schema derived from `contracts/dataset.schema.yaml`.  
  *Verification*: `python -m code.utils.repo_fetcher && jsonschema -i data/raw/frozen_repo_list.json contracts/dataset.schema.yaml` exits with status 0.

- [ ] T005 [US2] Implement `code/utils/model_loader.py` that loads `Salesforce/codegen-350M-mono` with `bitsandbytes` in **4‑bit CPU‑only** mode (`load_in_4bit=True`). The loader must raise a `RuntimeError` if `torch.cuda.is_available()` or if the model is not quantized to 4‑bit.  
  *Verification*: Running the loader prints “Model loaded in 4‑bit CPU mode” and exits with status 0; forcing a GPU environment or disabling 4‑bit raises an exception.

---

## Phase 3 – Extraction (User Story 1)  

- [ ] T006 [US1] Implement `code/extract.py` that (1) clones each repository listed in `frozen_repo_list.json` into `data/raw/repos/{repo_slug}` using `code/utils/git_clone.py`, (2) walks the source tree, (3) parses public methods with `code/utils/ast_parser.py`, (4) truncates to `config.MAX_METHODS` per repo, and (5) writes `data/raw/repos/{repo_slug}.json`. Missing docstrings are stored as `null`.  
  *Verification*: After running `python -m code.extract`, `jq '. | length' data/raw/repos/requests.json` returns a number ≤ 1000 and the file contains `"human_docstring": null` for undocumented methods.

- [ ] T007 [P] Record SHA‑256 hashes of each `data/raw/repos/*.json` in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`.  
  *Verification*: `grep -A1 sha256 state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` shows at least one entry.

---

## Phase 4 – Generation (User Story 2)  

- [ ] T008 [US2] Implement `code/generate.py` that loads the model via `model_loader.py`, builds a prompt **using only the method signature** (per FR‑012), generates a docstring with `config.TEMPERATURE = 0.2`, enforces a per‑method timeout of 30 s, monitors RAM (abort if > 7 GB), and writes `data/processed/generation_batch_{repo_slug}.json` containing `generated_docstring`, `generation_status`, and `error_message`.  
  *Verification*: After running on a single repo (e.g., `requests`), `jq '.[] | .generated_docstring' data/processed/generation_batch_requests.json | wc -l` equals the number of input records and no `generation_status` is `"error"`.

---

## Phase 5 – Post‑processing & aggregation  

- [ ] T009 [US2] Implement `code/post_process.py` that (a) flags empty or whitespace‑only generated docstrings (`needs_review: true`), (b) sets `coverage_score: 0.0` for those records, and (c) writes cleaned files `data/processed/generation_batch_{repo_slug}_cleaned.json`.  
  *Verification*: `grep -A1 '"needs_review": true' data/processed/generation_batch_*_cleaned.json | head -n 5` returns at least one match.

- [ ] T010 [P] Implement `code/aggregate.py` that concatenates all cleaned batch files into a single `data/processed/results.json`, enforcing per‑repo ≤ 1000 rows and total ≤ 20 000 rows.  
  *Verification*: `jq '. | length' data/processed/results.json` returns a number ≤ 20000 and each record contains a `"repo_slug"` field.

---

## Phase 6 – Coverage & description metrics (User Story 3 – Part 1)  

- [ ] T011 [US3] Extend `code/analyze.py` with a `--step=coverage` mode that computes **Parameter Coverage** (FR‑018 deterministic token‑exact matching) and **Description Coverage** (tokenisation with NLTK stop‑word removal, average non‑stop‑word tokens per documented parameter). Output is written to `data/processed/results_with_coverage.json`.  
  *Verification*: After `python -m code.analyze --step=coverage`, `head -n 1 data/processed/results_with_coverage.json | jq '.parameter_coverage_score, .description_coverage_score'` prints two numeric values between 0 and 1.

- [ ] T012 [S] Add unit test `tests/unit/test_coverage.py` asserting that every record in `results_with_coverage.json` has `parameter_coverage_score` in `[0.0,1.0]` and `description_coverage_score` ≥ 0.0.  
  *Verification*: `pytest -q tests/unit/test_coverage.py` exits with 0 and reports “passed”.

---

## Phase 7 – Semantic similarity (User Story 3 – Part 2)  

- [ ] T013 [US3] Add a `--step=similarity` mode to `code/analyze.py` that loads `sentence‑transformers/all‑MiniLM‑L6‑v2`, computes cosine similarity between human and generated docstrings, adds a `semantic_similarity` field, and writes `data/processed/results_with_scores.json`.  
  *Verification*: After `python -m code.analyze --step=similarity`, `head -n 1 data/processed/results_with_scores.json | jq '.semantic_similarity'` prints a float in `[-1.0,1.0]`.

- [ ] T014 [S] Add unit test `tests/unit/test_similarity.py` ensuring every `semantic_similarity` value lies within `[-1.0, 1.0]`.  
  *Verification*: `pytest -q tests/unit/test_similarity.py` passes.

---

## Phase 8 – Statistical analysis & final report (User Story 3 – Part 3)  

- [ ] T015 [US3] Implement `--step=stats` in `code/analyze.py` that (a) builds the **Composite Score** (`0.4 * parameter_coverage_score + 0.6 * description_coverage_score`) for each method, (b) logs a warning if total paired records < 30 (FR‑009), (c) aggregates mean scores per repository, (d) runs a Wilcoxon signed‑rank test on paired human vs. LLM composite scores (per‑repository means, respecting FR‑014), and (e) writes `data/processed/final_report.json` containing p‑value, statistic, effect size, significance flag, and execution time.  
  *Verification*: `python -m code.analyze --step=stats && jq '.wilcoxon_p_value, .significance' data/processed/final_report.json` prints two values; if `<30` pairs, the log contains “WARNING: low statistical power”.

- [ ] T016 [S] Add integration test `tests/integration/test_final_report_schema.py` that validates `final_report.json` against `contracts/results.schema.yaml` using `jsonschema`.  
  *Verification*: `pytest -q tests/integration/test_final_report_schema.py` passes.

---

## Phase 9 – User documentation  

- [ ] T017 [P] Create/Update `quickstart.md` with a step‑by‑step runnable guide: (1) install dependencies, (2) fetch frozen repo list, (3) run extraction, (4) run generation, (5) post‑process, (6) compute coverage, (7) compute similarity, (8) run statistical analysis, (9) view `final_report.json`. Include the exact CLI commands used in the verification steps above.  
  *Verification*: `grep -q "python -m code.analyze --step=stats" quickstart.md`.

---

## Phase 10 – Expanded testing for uncovered paths  

- [ ] T018 [S] Add unit tests covering previously uncovered code paths:  
  * `tests/unit/test_model_loader.py` – asserts `model_loader.load_model()` raises when GPU is available or when the model is not 4‑bit.  
  * `tests/unit/test_post_process.py` – checks that whitespace‑only docstrings are flagged with `needs_review: true`.  
  * `tests/unit/test_analyze_cli.py` – verifies that invoking `code.analyze` with an unknown `--step` exits with a non‑zero status.  
  *Verification*: `pytest -q tests/unit/` reports ≥ 3 passed tests and 0 failures.

---

## Phase 11 – Contract enforcement after each major stage  

- [ ] T019 [S] Implement `scripts/validate_contracts.sh` that (a) selects the appropriate JSON schema (`contracts/dataset.schema.yaml` after extraction, `contracts/results.schema.yaml` after coverage/similarity/stats), (b) runs `jsonschema.validate` on the corresponding artifact, and (c) aborts with a non‑zero exit code on failure. The script is invoked automatically (e.g., via a GitHub Actions step) after each stage.  
  *Verification*: Manual run `bash scripts/validate_contracts.sh results_with_scores.json contracts/results.schema.yaml` exits with status 0 and prints “Schema validation passed”.

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
|11 | T019 | All previous phases (run after each stage) |

All tasks are currently **unchecked** to allow fresh execution; completed artifacts from prior runs remain untouched. The pipeline respects data flow, uses real data sources, runs on CPU‑only resources, and fulfills every functional requirement (FR‑001 – FR‑018) and success criterion (SC‑001 – SC‑007) defined in the specification.
