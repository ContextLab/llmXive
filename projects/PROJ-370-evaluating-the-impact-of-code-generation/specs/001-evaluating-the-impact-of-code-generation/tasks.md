# Tasks: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The tasks are organized by research phase and map directly to the functional
requirements (FR‑001 … FR‑017) in the specification. Each task follows the
canonical format:

`- [ ] T### [P?] [FR‑xxx] description – file_path`
`    <indented verification / requirement details>`

`[P]` marks tasks that can be executed in parallel. Indented continuation lines list the concrete output, verification command, and scientific checks.

---

## Phase 1 – Project scaffolding & core pipeline utilities

- [ ] T001 [P] Verify that the required directory layout exists – `code/`
    *Verification*: Run `mkdir -p code/src/{config,extraction,detection,inference,analysis,reporting,pipeline,cli} code/tests/{unit,integration,contract} code/data/{raw,annotations,derived,results} code/logs specs/001-eval-llm-review-quality/contracts` and confirm all directories are created via `ls -R code/`.

- [X] T002 [P] [FR‑001] Add `requirements.txt` (pinned `datasets`, `transformers`, `scikit‑learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `numpy`, `detectgpt`) and a configuration module `code/src/config/settings.py` that defines hyper‑parameters, path constants, random seeds, and `TARGET_REPOS = ["microsoft/vscode", "pytorch/pytorch", "tensorflow/tensorflow"]` – `code/requirements.txt`, `code/src/config/settings.py`
    *Verification*: `pip install -r code/requirements.txt` succeeds; `python -c "import code.src.config.settings as s; assert s.TARGET_REPOS"` runs without error.

- [ ] T003 [P] Create a `pyproject.toml` configuring **ruff** and **black** (line‑length 88, exclude patterns) and a GitHub Actions workflow that runs `ruff check` and `black --check` – `pyproject.toml`, `.github/workflows/ci.yml`
    *Verification*: `ruff check .` and `black --check .` both return exit 0 on a clean repo.

- [X] T004 [P] Implement core pipeline utilities:
    * `code/src/pipeline/logging_utils.py` – JSON‑lines logger that writes events conforming to `contracts/run_log_event_schema.yaml` to `logs/pipeline.jsonl`.
    * `code/src/pipeline/runtime_guard.py` – `RuntimeGuard` class that records a deadline timestamp, aborts the process with exit code 143 on breach, and writes a `"timeout"` event to `logs/timeout.log`.
    * Unit tests `code/tests/unit/test_logging_utils.py` and `code/tests/unit/test_runtime_guard.py`. – `code/src/pipeline/*.py`, `code/tests/unit/*.py`
    *Verification*: `pytest -q code/tests/unit/test_logging_utils.py code/tests/unit/test_runtime_guard.py` returns exit 0; manual invocation of `RuntimeGuard` with a past deadline exits 143 and creates a valid JSON line in `logs/timeout.log`.

- [ ] T005 [P] Implement the CLI orchestrator `code/src/cli/main.py` that wires the full pipeline (extraction → preprocessing → ground‑truth → LLM‑code flag → inference → alignment → metrics → reporting).
    *Behaviour*: `python -m code.src.cli.main --run smoke` executes the end‑to‑end pipeline on the 10‑PR verification fixture and exits 0, producing `data/results/smoke_report.json` validated against `contracts/analysis_metrics_schema.schema.yaml`.
    *Verification*: Run the command; check exit code, existence of `data/results/smoke_report.json`, and that `logs/pipeline.jsonl` contains a `"cli_start"` event.

---

## Phase 2 – Data extraction, preprocessing, and triangulated ground truth

- [X] T006 [P] Define the `BugDetection` dataclass in the detection package (`code/src/detection/schema.py`) and ensure `PullRequest` is isolated in `code/src/extraction/schema.py`.
    *Verification*: `python -c "from code.src.detection.schema import BugDetection; assert BugDetection"` runs; `pytest code/tests/contract/test_schemas.py` passes.

- [ ] T007 [P] [FR‑001] Implement PR extraction script `code/src/extraction/fetch_prs.py`. <!-- FAILED-IN-EXECUTION: code/src/extraction/fetch_prs.py exit=-1 (TIMEOUT) -->
    * Reads `TARGET_REPOS` from `code/src/config/settings.py`, fetches up to 500 PRs per repo via GitHub REST API, writes raw JSON payloads to `data/raw/`, and generates `data/raw/checksums.json`.
    *Verification*: Command exits 0; `data/raw/checksums.json` matches files; `python -m code.src.extraction.fetch_prs --test-set 10` (T016) confirms non-empty diffs and comments.

- [ ] T008 [P] [FR‑011] Implement preprocessing and ground‑truth construction script `code/src/extraction/preprocess_and_ground_truth.py`.
    1. Load `data/raw/` JSON, truncate diffs exceeding context window, and log warnings.
    2. Build **triangulated ground truth** (FR-011): bug is verified iff linked to closed issue AND confirmed by ≥2 independent reviewers.
    3. Abort with `event: "audit_failure"` and exit 1 if < 50 verified PRs are found.
    4. Outputs: `data/derived/prs_cleaned.json`, `data/annotations/human_annotations.json`.
    *Verification*: All output files exist and validate against schemas; `python scripts/audit_ground_truth.py` reports ≥ 50 verified PRs.

---

## Phase 3 – LLM‑assisted bug detection

- [ ] T009a [P] [FR‑016] Implement LLM‑generated‑code detection `code/src/detection/detect_llm_code.py` using heuristic headers and `detectgpt`.
    * Writes `data/derived/llm_code_flags.json` mapping `pr_id → is_llm_generated`.
    *Verification*: `pytest code/tests/unit/test_detect_llm_code.py` passes; JSON file conforms to boolean-mapping schema.

- [ ] T009 [P] [FR‑002] Implement LLM inference pipeline `code/src/inference/run_inference.py`.
    1. Load `bigcode/starcoder2-3b` in `torch.float16` with `low_cpu_mem_usage=True`, `device="cpu"`.
    2. Apply standardized prompts; enforce per‑PR latency ≤ 5m via `RuntimeGuard`; retry up to 2 times on JSON parse failure.
    3. Write results to `data/derived/llm_bugs.json` conforming to `bug_detection_schema.yaml`.
    *Verification*: `python -m code.src.inference.run_inference --sample` produces `data/derived/llm_bugs.json` with ≥ 10 detections; all entries validate against the schema.

---

## Phase 4 – Alignment, metrics, statistical testing, and runtime monitoring

- [ ] T010 [P] [FR‑003] [FR‑012] Implement alignment script `code/src/analysis/align.py`.
    * Match LLM bugs to human bugs iff (Jaccard line-set overlap ≥ 0.5 with ±5 line tolerance) AND (TF-IDF cosine similarity ≥ threshold, default 0.85).
    * Writes `data/derived/alignments.json` validated against `alignment_result_schema.yaml`.
    *Verification*: JSON file exists; schema validation passes; sanity check confirms matched pairs.

- [ ] T011 [P] [FR‑004] [FR‑005] [FR‑017] Implement metrics & statistical‑test scripts `code/src/analysis/metrics.py` and `code/src/analysis/stats.py`.
    * Compute Precision, Recall, F1, and `llm_only_recall` (confirmed via manual set).
    * Perform McNemar’s test (detection rates) and chi-square (severity distribution) with Fisher's exact fallbacks; report effect size (Cramér’s V).
    * Writes `data/derived/metrics_threshold_0.85.json` conforming to `analysis_metrics_schema.yaml`.
    *Verification*: Schema validation succeeds; numeric fields are within [0,1]; p-values are reported.

- [ ] T012 [P] [FR‑006] [SC‑003] Implement sensitivity‑sweep script `code/src/analysis/sensitivity.py`.
    * Repeat alignment and metrics for thresholds `{0.80, 0.85, 0.90}`.
    * Aggregates results into `data/results/sensitivity_analysis.csv`.
    *Verification*: CSV contains exactly three rows with valid numeric bounds for F1-score.

- [ ] T013 [P] [FR‑013] [SC‑004] Implement runtime recording in `code/src/reporting/generate_report.py`.
    * Record total wall‑clock time (seconds) in `data/results/runtime.json` and as `total_runtime_seconds` in final metrics JSON.
    *Verification*: `data/results/runtime.json` exists and contains a valid integer; `total_runtime_seconds` is present in the final metrics JSON, satisfying SC-004.

---

## Phase 5 – Reporting, testing, and reproducibility

- [ ] T014 [P] [FR‑014] [FR‑007] Implement reporting script `code/src/reporting/generate_report.py`.
    * Produces `results/final_report.md` (tables, p-values, effect sizes, associational framing statement per FR-014) and `results/metrics.json`.
    *Verification*: Both files are non-empty; markdown renders a table; associational framing is explicitly stated.

- [ ] T015 [P] Implement independent manual validation set collection `data/validation/manual_set.json`.
    * Randomly sample PRs and store senior developer verifications.
    *Verification*: `data/validation/manual_set.json` exists and is used by `T011` to compute `llm_only_recall`.

- [ ] T016 [P] Implement preliminary PR extraction verification (10-PR check) `code/src/extraction/fetch_prs.py --test-set 10`.
    * Assert each output JSON contains non‑empty `diff`, `human_review_comments`, and `linked_issue_ids`.
    *Verification*: Command exits 0.

- [ ] T017 [P] Create analysis plan document `analysis/plan.md` via `code/src/reporting/create_analysis_plan`.
    * Document α=0.05, test families, Benjamini-Hochberg correction, and effect-size conventions.
    *Verification*: `analysis/plan.md` exists and contains the specified statistical parameters.

- [ ] T018 [P] Implement pre-run profiling & sample capping `code/src/pipeline/profiler.py`.
    * Estimate per-PR runtime; if projected > 6h, cap full run at 200 PRs and log `"sample_capped"` event.
    *Verification*: Profiler logs an estimate and correctly triggers capping if thresholds are exceeded.

- [ ] T019 [P] Implement seed provenance in `code/src/pipeline/logging_utils.py`.
    * Log the effective random seed at start (`event: "seed_used"`) and write it to `data/results/final_report.json`.
    *Verification*: `logs/pipeline.jsonl` contains a `"seed_used"` event; final report contains the matching seed.

---

## Phase 6 – Verification checklist

| Check | Expected artifact |
|-------|-------------------|
| Directory layout created | `code/` sub-folders |
| Dependencies installed | `code/requirements.txt` |
| Logger & timeout utilities | `code/src/pipeline/logging_utils.py`, `code/src/pipeline/runtime_guard.py` |
| CLI orchestrator | `code/src/cli/main.py` |
| `BugDetection` dataclass | `code/src/detection/schema.py` |
| Raw PR data & checksums | `data/raw/prs.jsonl`, `data/raw/checksums.json` |
| Processed PRs & GT | `data/derived/prs_cleaned.json`, `data/derived/human_ground_truth.json` |
| LLM inference output | `data/derived/llm_bugs.json` |
| Alignment & metrics | `data/derived/alignments.json`, `data/derived/metrics_threshold_0.85.json` |
| Sensitivity analysis | `data/results/sensitivity_analysis.csv` |
| Runtime record (SC-004) | `data/results/runtime.json` |
| Final report | `results/final_report.md`, `results/metrics.json` |
| Analysis Plan | `analysis/plan.md` |
| Seed provenance | `logs/pipeline.jsonl` (`seed_used`) |

**Execution order**:
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009a → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019.