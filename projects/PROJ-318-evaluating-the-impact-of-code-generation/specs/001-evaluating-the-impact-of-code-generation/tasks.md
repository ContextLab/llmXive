# Tasks: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, existing code and test files.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) extracts public method signatures and human docstrings from a stratified sample of PyPI repositories, (2) generates docstrings with the `Salesforce/codegen-350M-mono` model under CPU‑only, low‑bit constraints, (3) computes Parameter Coverage, Description Coverage, and semantic‑similarity scores, (4) performs a Wilcoxon signed‑rank test, and (5) produces a validated final report, all while respecting the resource limits and scientific requirements of the specification.

---

## Phase 0 – Plan alignment  

- [X] T001 [P] Edit `plan.md` to enforce the hard **1 000‑method cap per repository**, add a constant `MAX_METHODS = 1000` in a new `code/config.py`, and remove any fallback‑to‑8‑bit or full‑precision notes.  
  *Verification*: `grep -q "MAX_METHODS = 1000" plan.md && ! grep -q "fallback"` succeeds.

---

## Phase 1 – Project skeleton & reproducibility  

- [ ] T002 [P] Create the standard directory layout (`code/`, `data/raw/`, `data/processed/`, `tests/`, `scripts/`, `state/`) and add a pinned `code/requirements.txt` (Python 3.11, `torch`, `transformers`, `bitsandbytes`, `datasets`, `sentence-transformers`, `nltk`, `scipy`, `gitpython`, `jsonschema`, `pytest`).  
  *Verification*: `tree -L 2` shows the required folders and `pip install -r code/requirements.txt` exits with status 0.  

- [ ] T003 [P] Add `code/config.py` containing `SEED = 42`, `MAX_METHODS = 1000`, `TEMPERATURE = 0.2`, and add `code/utils/seed_manager.py` that seeds Python’s `random`, NumPy, and PyTorch from `config.SEED`.  
  *Verification*: `python -c "import code.config, code.utils.seed_manager; print('ok')"` prints `ok` without error.

---

## Phase 2 – Data‑source infrastructure  

- [ ] T004 [US1] Implement `code/utils/repo_fetcher.py` that (a) queries the PyPI JSON API for the top‑20 packages, (b) performs **stratified sampling** across high/medium/low popularity tiers (≥ 5 repos per tier) as required by FR‑010, (c) uses an exponential backoff retry mechanism (max 5 retries, backoff factor 2) for all HTTP calls, and (d) writes `data/raw/frozen_repo_list.json`. Validate the file with a lightweight JSON‑schema derived from `contracts/dataset.schema.yaml`.   <!-- FAILED-IN-EXECUTION: code/utils/repo_fetcher.py exit=-1 (TIMEOUT) -->
  *Verification*: `python -m code.utils.repo_fetcher && jsonschema -i data/raw/frozen_repo_list.json contracts/dataset.schema.yaml` exits with status 0.  

- [ ] T005 [US2] Implement `code/utils/model_loader.py` that loads `Salesforce/codegen-350M-mono` with **bitsandbytes 4‑bit CPU‑only** (`load_in_4bit=True`). The loader must raise a `RuntimeError` if `torch.cuda.is_available()` or if the model is not quantized to 4‑bit.  
  *Verification*: Running the loader on the CI runner prints “Model loaded in 4‑bit CPU mode” and exits with status 0; forcing a GPU environment or disabling 4‑bit raises an exception.

---

## Phase 3 – Extraction (User Story 1)  

- [ ] T006 [US1] Implement `code/extract.py` that (1) clones each repository listed in `frozen_repo_list.json` into `data/raw/repos/{repo_slug}` using `code/utils/git_clone.py`, (2) walks the source tree, (3) parses **public** methods with `code/utils/ast_parser.py`, (4) truncates to `config.MAX_METHODS` per repo, and (5) writes `data/raw/repos/{repo_slug}.json`. Missing docstrings are stored as `null`.  
  *Verification*: After `python -m code.extract`, `jq '. | length' data/raw/repos/requests.json` returns a number ≤ 1000 and the file contains `"human_docstring": null` for undocumented methods.  

- [ ] T007 Record SHA‑256 hashes of each `data/raw/repos/*.json` in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`.  
  *Verification*: `grep -A1 sha256 state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` shows at least one entry.  

---

## Phase 4 – Generation (User Story 2)  

- [ ] T008 [US2] Implement `code/generate.py` that loads the model via `model_loader.py`, builds a prompt **using only the method signature** (FR‑012), generates a docstring with `config.TEMPERATURE = 0.2`, enforces a per‑method timeout of 30 s, monitors RAM (abort if > 7 GB), and writes `data/processed/generation_batch_{repo_slug}.json` containing `generated_docstring`, `generation_status`, and `error_message`.  
  *Verification*: After running on a single repo (e.g., `requests`), `jq '.[] | .generated_docstring' data/processed/generation_batch_requests.json | wc -l` equals the number of input records and no `generation_status` is `"error"`.

---

## Phase 5 – Post‑processing & aggregation  

- [ ] T009 [US2] Implement `code/post_process.py` that (a) flags empty or whitespace‑only generated docstrings (`needs_review: true`), (b) sets `coverage_score: 0.0` for those records, and (c) writes cleaned files `data/processed/generation_batch_{repo_slug}_cleaned.json`.  
  *Verification*: `grep -A1 '"needs_review": true' data/processed/generation_batch_*_cleaned.json | head -n 5` returns at least one match.  

- [ ] T010 [P] Implement `code/aggregate.py` that concatenates all cleaned batch files into a single `data/processed/results.json`, enforcing per‑repo ≤ 1000 rows and total ≤ 20 000 rows. Depends on T009.  
  *Verification*: `jq '. | length' data/processed/results.json` returns a number ≤ 20000 and each record contains a `"repo_slug"` field.

---

## Phase 6 – Coverage & description metrics (User Story 3 – Part 1)  

- [ ] T011 [US3] Extend `code/analyze.py` with a `--step=coverage` mode that computes **Parameter Coverage** (FR‑018 deterministic token‑exact matching) and **Description Coverage** (NLTK tokenisation, stop‑word removal, average non‑stop‑word tokens per documented parameter, counting zero for undocumented parameters). Write the output to `data/processed/results_with_coverage.json`.  
  *Verification*: After `python -m code.analyze --step=coverage`, `head -n 1 data/processed/results_with_coverage.json | jq '.parameter_coverage_score, .description_coverage_score'` prints two numeric values between 0 and 1.

- [ ] T012 [US3] **Adjust analysis** so that **null human docstrings are excluded** from the calculation of per‑repository *human* mean scores used in the Wilcoxon test (addressing the FR‑015 bias highlighted by the reviewer). The adjusted means are written to the same `results_with_coverage.json` (field `human_mean_excluding_null`).  
  *Verification*: `jq 'select(.human_docstring != null) | .parameter_coverage_score' data/processed/results_with_coverage.json | wc -l` equals the count of non‑null human records, and the new field appears in the per‑repo aggregates.

- [ ] T017 [US3] Ensure FR‑015: assign `coverage_score: 0.0` for any record where `human_docstring` is `null` and include these records in per‑repository aggregate calculations (both mean and count). Verification: after running `code/analyze --step=coverage`, `jq 'select(.human_docstring == null) | .coverage_score' data/processed/results_with_coverage.json` returns only `0.0`, and per‑repo aggregate fields count these records.  
  *Verification*: `jq '.repo_aggregates[] | select(.null_human_count > 0)' data/processed/results_with_coverage.json` shows non‑zero counts, confirming inclusion.

- [ ] T013 [S] Add unit test `tests/unit/test_coverage.py` asserting that every record in `results_with_coverage.json` has `parameter_coverage_score` in `[0.0,1.0]`, `description_coverage_score` ≥ 0.0, and that the `human_mean_excluding_null` field is present for each repository.  
  *Verification*: `pytest -q tests/unit/test_coverage.py` exits with 0 and reports “passed”.

- [ ] T024 [SC] Compute the proportion of methods whose **Description Coverage Score** meets the ≥ 5‑token threshold and verify that this proportion is ≥ 80 % across the entire dataset. Emit the proportion in `data/processed/results_with_coverage.json` under the field `description_coverage_pass_rate`. Fail the pipeline if the rate falls below 0.8.  
  *Verification*: `jq '.description_coverage_pass_rate' data/processed/results_with_coverage.json` prints a float ≥ 0.8.

---

## Phase 7 – Semantic similarity (User Story 3 – Part 2)  

- [ ] T014 [US3] Add a `--step=similarity` mode to `code/analyze.py` that loads `sentence‑transformers/all‑MiniLM‑L6‑v2`, computes cosine similarity between **human** and **generated** docstrings, adds a `semantic_similarity` field, and writes `data/processed/results_with_scores.json`. Depends on cleaned generation batches (T009/T010).  
  *Verification*: After `python -m code.analyze --step=similarity`, `head -n 1 data/processed/results_with_scores.json | jq '.semantic_similarity'` prints a float in `[-1.0, 1.0]`.

- [ ] T015 [S] Add unit test `tests/unit/test_similarity.py` ensuring every `semantic_similarity` value lies within `[-1.0, 1.0]`.  
  *Verification*: `pytest -q tests/unit/test_similarity.py` passes.

---

## Phase 8 – Composite score, statistical analysis & final report (User Story 3 – Part 3)  

- [ ] T016a [US3] Compute the **Composite Documentation Completeness Score** (`0.4 * parameter_coverage_score + 0.6 * description_coverage_score`) for each method and write it into `data/processed/results_with_scores.json`.  
  *Verification*: `jq '.composite_score' data/processed/results_with_scores.json | head -n 5` shows numeric values between 0 and 1.

- [ ] T016b [US3] Aggregate **mean composite scores per repository** (excluding records where `human_docstring` is `null` as per T012) and run a **Wilcoxon signed‑rank test** on the paired human vs. LLM composite scores **at the repository level** (i.e., using the per‑repo means). Log a warning if total paired repositories < 30 (FR‑009). Write `data/processed/final_report.json` containing p‑value, statistic, effect size, significance flag, and execution time.  
  *Verification*: `python -m code.analyze --step=stats && jq '.wilcoxon_p_value, .significance' data/processed/final_report.json` prints two values; log contains “WARNING: low statistical power” when appropriate.

- [ ] T016c [US3] Extend the final report (`final_report.json`) with a **circularity limitation discussion** (FR‑013) explaining that the LLM may copy parameter names from the prompt and that this is mitigated by the composite weighting and baseline copy comparison.  
  *Verification*: `jq '.circularity_discussion' data/processed/final_report.json` contains a non‑empty string.

---

## Phase 9 – User documentation  

- [ ] T018 [P] Create/Update `quickstart.md` with a step‑by‑step runnable guide (as previously listed) **and** include a note that the pipeline records total runtime and peak RAM (produced by T025). Verify the guide contains the exact CLI commands.  
  *Verification*: `grep -q "python -m code.analyze --step=stats" quickstart.md`.

---

## Phase 10 – Expanded testing for previously uncovered paths  

- [ ] T019 [S] Add unit tests covering critical uncovered paths:  
  * `tests/unit/test_model_loader.py` – asserts `model_loader.load_model()` raises when GPU is available or when the model is not 4‑bit.  
  * `tests/unit/test_post_process.py` – checks that whitespace‑only docstrings are flagged with `needs_review: true`.  
  * `tests/unit/test_analyze_cli.py` – verifies that invoking `code.analyze` with an unknown `--step` exits with a non‑zero status.  
  *Verification*: `pytest -q tests/unit/` reports ≥ 3 passed tests and 0 failures.

- [ ] T023 [US3] Implement `code/human_eval.py` that randomly samples a subset of method records, collects Likert‑scale ratings (1‑5) from annotators, writes `data/processed/human_eval_results.json`, and computes `average_rating`.  
  *Verification*: `jq '.average_rating' data/processed/human_eval_results.json` prints a float ≥ 4.0.

- [ ] T026 [SC] Verify that the **human‑evaluation average Likert rating** meets the success criterion (≥ 4.0). Fail the pipeline if the average is below 4.0.  
  *Verification*: Pipeline aborts with a clear error message when `average_rating < 4.0`.

- [ ] T025 [SC] Measure total wall‑clock time and peak RAM usage of the entire pipeline (from T001 to T016b) using the `time` command and `psutil` monitoring, and assert that runtime ≤ 6 hours and peak RAM ≤ 7 GB. Fail the run if limits are exceeded.  
  *Verification*: After pipeline execution, a log entry `Runtime OK: 5h 42m, Peak RAM: 3.8GB` is emitted; otherwise the job aborts.

---

## Phase 11 – Contract enforcement after each major stage  

- [ ] T020 [S] Implement `scripts/validate_contracts.sh` that (a) selects the appropriate JSON schema (`contracts/dataset.schema.yaml` after extraction, `contracts/results.schema.yaml` after coverage/similarity/stats), (b) runs `jsonschema.validate` on the corresponding artifact, and (c) aborts with a non‑zero exit code on failure. The script is invoked automatically (e.g., via a GitHub Actions step) after each stage.  
  *Verification*: Manual run `bash scripts/validate_contracts.sh data/processed/results_with_scores.json contracts/results.schema.yaml` exits with status 0 and prints “Schema validation passed”.
