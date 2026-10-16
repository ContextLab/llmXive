# Tasks: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.  

The tasks are organized by research phase and map directly to the functional
requirements (FR‑001 … FR‑017) in the specification.  Each task follows the
canonical format `- [ ] T### [P?] [USx?] description – *file path*`.  
`[P]` marks tasks that can be executed in parallel (different files, no
data‑flow dependency).  `USx` links the task to the corresponding user story.  

---  

## Phase 1 – Project scaffolding & core utilities  

- [ ] **T001** Create the required directory layout – `src/`, `src/utils/`, `data/raw/`, `data/derived/`, `data/annotations/`, `results/`, `tests/`, `specs/`, `contracts/`.  
  *Verification*: after running `scripts/setup_dirs.sh` all listed directories exist.  

- [ ] **T002** Add `requirements.txt` (pinned `datasets`, `transformers`, `scikit‑learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `numpy`) and a `config/settings.py` that defines hyper‑parameters, path constants, random seeds, and `TARGET_REPOS = ["microsoft/vscode", "pytorch/pytorch", "tensorflow/tensorflow"]`.  
  *Verification*: both files are present and contain the expected entries; `pip install -r requirements.txt` succeeds.  

- [ ] **T003** Add a `pyproject.toml` configuring **ruff** and **black** (line‑length 88, exclude patterns) and a GitHub Actions workflow that runs `ruff check` and `black --check`.  
  *Verification*: `pyproject.toml` includes the ruff/black sections and `.github/workflows/ci.yml` exists.  

- [ ] **T004** Implement core pipeline utilities – `src/utils/logger.py` (JSON‑lines logger) and `src/utils/timeout_wrapper.py` (global 6 h guard that writes to `logs/timeout.log` and exits with code 143). Add unit tests `tests/unit/test_logger.py` and `tests/unit/test_timeout_wrapper.py` that (a) assert logger emits a valid JSON line conforming to `run_log_event_schema.yaml`, and (b) simulate a timeout and check exit code 143 and log entry.  
  *Verification*: both source files exist, unit‑test suite passes (`pytest -q tests/unit/test_logger.py tests/unit/test_timeout_wrapper.py` returns exit 0), and a manual run of `timeout_wrapper.run(lambda: time.sleep(0.1), deadline_seconds=0)` produces the expected log entry and exit code.  

- [ ] **T005** Create the CLI entry point `src/cli/main.py` that wires the full pipeline (extraction → detection → inference → analysis → reporting) and uses the utilities from T004. The CLI must accept `--config <path>` and `--run {sample,all}` flags. Ensure that `python -m src.cli.main --run sample` executes the end‑to‑end pipeline on the small 10‑PR verification fixture and exits 0.  
  *Verification*: running the command produces `data/results/smoke_report.json` and returns exit 0; the command also logs a `"cli_start"` event via the logger.  

---  

## Phase 2 – Data extraction & ground‑truth construction  

- [ ] **T006** Define the detection‑level data model: create a `BugDetection` dataclass in `src/detection/schema.py` with fields `bug_id`, `source`, `file_path`, `line_start`, `line_end`, `severity`, `description`, optional `confidence`, and `is_llm_only`. Export the corresponding JSON‑schema file `contracts/bug_detection_schema.yaml` (already present) and ensure it validates against the dataclass.  
  *Verification*: `import src.detection.schema as ds; isinstance(ds.BugDetection(...), ds.BugDetection)` succeeds; `pytest tests/contract/test_schema_validation.py::test_bug_detection_schema` passes.  

- [ ] **T007** Implement `src/extraction/fetch_prs.py` that reads `TARGET_REPOS` from `config/settings.py`, authenticates with a GitHub token (env `GITHUB_TOKEN`), fetches up to 500 PRs per repository via the GitHub REST API, writes the raw payloads to `data/raw/prs.json` (one JSON object per PR, newline‑delimited), and generates SHA‑256 checksums stored in `data/raw/checksums.json`. The script must respect API rate limits (respect `X-RateLimit-Remaining`).  
  *Verification*: after execution, both `data/raw/prs.json` and `data/raw/checksums.json` exist, contain entries for the expected number of PRs, and a checksum validation script (`scripts/verify_checksums.py`) returns success.  

- [ ] **T008** Implement `src/extraction/preprocess_and_ground_truth.py` that:  
  1. Loads `data/raw/prs.json`.  
  2. Truncates any diff exceeding the LLM context window (≈ 8 k tokens) to the most recent changed lines, adds a `truncation_flag: true` field, and logs a warning to `logs/truncation.log`.  
  3. Extracts human review comments, builds `data/annotations/human_comments.json` conforming to `pr_schema.yaml` (only the comment‑related fields).  
  4. Applies FR‑011 to construct a triangulated ground‑truth set: a bug is **verified** if it (a) is linked to a closed GitHub issue **and** (b) appears in at least two independent human review comments (or a senior maintainer comment). Produce `data/derived/human_ground_truth.json` with a `verification_method` field.  
  5. Writes the cleaned PR records (with possible truncation) to `data/derived/prs_cleaned.json`.  
  *Verification*: all four output files exist, each validates against its respective schema (`pr_schema.yaml`, `bug_detection_schema.yaml` where appropriate), and a sanity‑check script confirms that at least 50 PRs have `ground_truth_status == "verified"`; otherwise the script exits with error `audit_failure`.  

---  

## Phase 3 – LLM‑assisted bug detection (simulation)  

- [ ] **T009a** Implement `src/detection/detect_llm_code.py` that flags PR diffs likely generated by an LLM using (i) heuristic header detection (`"Generated by"` comment) and (ii) the `detectgpt` model. Output `data/derived/llm_code_flags.json` mapping `pr_id` → `is_llm_generated`. Include a unit test `tests/unit/test_detect_llm_code.py` that verifies the flag is set for a synthetic diff containing the known header.  
  *Verification*: the JSON file exists, matches the schema, and the unit test passes.  

- [ ] **T009** Implement the LLM inference pipeline in `src/inference/run_inference.py`:  
  1. Load StarCoder2‑3B from HuggingFace with `torch.float16`, `low_cpu_mem_usage=True`, and `device="cpu"` (CPU‑only).  
  2. For each PR in `data/derived/prs_cleaned.json`, apply the standardized prompt from `src/inference/prompt_templates.py`.  
  3. Enforce per‑PR latency ≤ 5 minutes using the `RuntimeGuard` from T004; on timeout, record `status: "timeout"` in the output and skip the PR.  
  4. Retry up to 2 times on JSON‑formatting failures (1 s delay).  
  5. Write successful detections to `data/derived/llm_bugs.json`, each entry conforming to `bug_detection_schema.yaml` with `source: "llm"`.  
  *Verification*: after running `python -m src.inference.run_inference --sample`, the output file exists, contains at least 10 detections for the sample set, and all entries validate against the schema.  

---  

## Phase 4 – Alignment, metrics, and statistical testing  

- [ ] **T010** Implement `src/analysis/align.py` that loads `data/derived/human_ground_truth.json` and `data/derived/llm_bugs.json`, then matches bugs using:  
  * Location Jaccard index ≥ 0.5 with a line‑shift tolerance of 5 lines.  
  * Cosine similarity of TF‑IDF description embeddings ≥ threshold (default 0.85, configurable).  
  Valid matches are written to `data/derived/alignments.json` (conforms to `alignment_result_schema.yaml`).  

  Implement `src/analysis/metrics.py` that consumes the alignment file and computes Precision, Recall, F1, and `llm_only_recall` (proportion of LLM‑only bugs that appear in the manual validation set, if present). Write results to `data/derived/metrics_threshold_0.85.json` (validated against `analysis_metrics_schema.yaml`).  

  Implement `src/analysis/stats.py` that performs McNemar’s test on detection rates (paired on the manual validation set) and a chi‑square (or Fisher’s exact) test on severity‑distribution differences; add p‑values, test statistics, and effect sizes to the same metrics JSON.  
  *Verification*: both `alignments.json` and `metrics_threshold_0.85.json` exist, pass schema validation, and a sanity‑check script confirms that `precision + recall + f1_score` are within [0, 1].  

- [ ] **T011** Implement `src/analysis/sensitivity.py` that repeats the alignment and metric computation for similarity thresholds `{0.80, 0.85, 0.90}`. Aggregate the three metric records into `data/derived/sensitivity_analysis.csv` with columns `threshold,precision,recall,f1_score`.  
  *Verification*: the CSV contains exactly three rows, one per threshold, and all numeric fields are within valid ranges.  

- [ ] **T016** Add a runtime‑monitoring module `src/pipeline/runtime_monitor.py` that aggregates per‑PR latency and memory usage recorded by the logger, computes the total wall‑clock time, and writes `data/derived/runtime_report.json` containing `total_runtime_seconds`, `average_latency_seconds`, and `deadline_met` (boolean).  
  *Verification*: after a full run, `runtime_report.json` exists, `deadline_met` is true for the small sample, and the file validates against a simple JSON schema (included in `contracts/runtime_report_schema.yaml`).  

---  

## Phase 5 – Reporting & reproducibility  

- [ ] **T012** Implement `src/reporting/generate_report.py` that reads the final metric files (`metrics_threshold_0.85.json`, `sensitivity_analysis.csv`, `runtime_report.json`) and creates:  
  * `results/final_report.md` – markdown containing tables of precision/recall/F1, p‑values, effect sizes, a paragraph explicitly stating that the study **correlates** LLM assistance with review quality (FR‑014), and a description of the alignment criteria used.  
  * `results/metrics.json` – a machine‑readable copy of the aggregated metrics, annotated with content‑hash footers for each upstream data artifact (to satisfy Constitution IV).  
  *Verification*: both files are non‑empty, the markdown renders a table when viewed, and a checksum‑verification script confirms that the footers match the current hashes of `data/derived/*`.  

- [ ] **T013** Build a comprehensive test suite:  
  * Unit tests under `tests/unit/` for every module (`test_fetch_prs.py`, `test_preprocess.py`, `test_detect_llm_code.py`, `test_alignment.py`, `test_metrics.py`, `test_runtime_monitor.py`).  
  * Integration test `tests/integration/test_end_to_end_small.py` that runs the full pipeline on a real sample of 5 PRs from `microsoft/vscode` and asserts that `results/final_report.md` and `results/metrics.json` are created and contain non‑empty metric fields.  
  * Contract tests `tests/contract/test_schema_validation.py` that validate **all** JSON outputs against the YAML schemas in `contracts/`.  
  *Verification*: `pytest -q` returns exit 0 and all listed test files are present.  

- [ ] **T014** Write `quickstart.md` (and update `README.md`) with a step‑by‑step example:  

  ```bash
  export GITHUB_TOKEN=your_token_here
  python -m src.cli.main --config config/settings.py --run all
  ```  

  The guide must list required environment variables, describe how to reproduce the small‑sample run (`--run sample`), and point to the location of the final report.  
  *Verification*: both markdown files contain the exact snippet above and a “Running the pipeline” section that matches the description.  

---  

## Phase 6 – Verification checklist  

| Check | Expected artifact |
|-------|-------------------|
| Directory layout created | `src/`, `src/utils/`, `data/`, `results/`, `tests/`, `contracts/` |
| Dependencies installed | `requirements.txt` |
| Linting config present | `pyproject.toml` |
| Timeout & logger utilities | `src/utils/timeout_wrapper.py`, `src/utils/logger.py` |
| CLI orchestrator | `src/cli/main.py` |
| Schemas & contracts | `src/*/schema.py`, `contracts/*.yaml` |
| Raw PR data & checksums | `data/raw/prs.json`, `data/raw/checksums.json` |
| Processed PRs, comments, ground truth | `data/derived/prs_cleaned.json`, `data/annotations/human_comments.json`, `data/derived/human_ground_truth.json` |
| LLM‑code detection flags | `data/derived/llm_code_flags.json` |
| LLM inference output | `data/derived/llm_bugs.json` |
| Alignment & metric files | `data/derived/alignments.json`, `data/derived/metrics_threshold_0.85.json` |
| Sensitivity analysis | `data/derived/sensitivity_analysis.csv` |
| Runtime report | `data/derived/runtime_report.json` |
| Final report & metrics copy | `results/final_report.md`, `results/metrics.json` |
| Test suite passing | `pytest -q` returns 0 |
| Quickstart documentation | `quickstart.md`, updated `README.md` |

---  

**Execution order**  

1. **Phase 1** – T001 → T005 (sequential).  
2. **Phase 2** – T006 → T008 (depends on Phase 1).  
3. **Phase 3** – T009a → T009 (depends on Phase 2).  
4. **Phase 4** – T010 → T011 → T016 (depends on Phase 3).  
5. **Phase 5** – T012 → T013 → T014 (depends on Phase 4).  

All tasks remain unchecked (`- [ ]`) until their implementation and verification succeed. When a task is completed, the corresponding checkbox should be marked `[X]` by the developer.
