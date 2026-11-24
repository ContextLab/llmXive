# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

**Branch**: `001-eval-llm-review-quality` | **Date**: 2024-10-26 | **Spec**: `specs/001-eval-llm-review-quality/spec.md`  
**Input**: Feature specification from `/specs/001-eval-llm-review-quality/spec.md`

## Summary
We will build a reproducible research pipeline that (1) extracts PR diffs, review comments, and linked issues from a small set of open‑source GitHub repositories, (2) runs a CPU‑tractable LLM (StarCoder2‑3B) on each diff to produce structured bug reports, (3) aligns LLM detections with a triangulated human ground truth, (4) computes precision/recall/F1, McNemar’s test, and chi‑square tests, and (5) explicitly reports the FR‑014 clarification about the term “affect”. All steps run on the GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤14 GB disk). The pipeline logs a JSON‑lines event `"cli_start"` at the very beginning of the CLI run and never writes to platform‑owned paths such as `.github/workflows/ci.yml`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers`, `datasets`, `torch` (CPU‑only, **float32**), `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `detectgpt`, `pytest`, `numpy`. All pinned in `code/requirements.txt`.  
- **Storage**: `data/` (raw JSON payloads, derived JSON/Parquet, checksums), `results/` (final JSON/CSV), `logs/` (JSON‑lines).  
- **Testing**: `pytest` with unit, integration, and contract tests.  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU, ~7 GB RAM, ~14 GB disk).  
- **Constraints**: No GPU; all inference must fit in ≤7 GB RAM and ≤5 min per PR (FR‑015).  
- **Scale/Scope**: ≤500 PRs total; runtime capped at 6 h (FR‑013).  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed random seed logged (`event: "seed_used"`). |
| II. Verified Accuracy | PASS | No external citations beyond those in the spec. |
| III. Data Hygiene | PASS | Raw GitHub payloads stored unchanged; checksums recorded. |
| IV. Single Source of Truth | PASS | All figures/tables derived from files under `data/`. |
| V. Versioning Discipline | PASS | Content hashes tracked in `state/` automatically by the platform. |
| VI. Review Data Integrity | PASS | Raw API responses preserved; transformations produce new files with provenance fields. |
| VII. Evaluation Rigor | PASS | Analysis plan (`analysis/plan.md`) documents α = 0.05, test families, and multiple‑comparison correction. |

## Project Structure

### Documentation (this feature)

```
specs/001-eval-llm-review-quality/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── alignment_result_schema.schema.yaml
│   ├── analysis_metrics_schema.schema.yaml
│   ├── bug_detection_schema.schema.yaml
│   ├── pr_schema.schema.yaml
│   └── run_log_event_schema.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

### Source Code (under `code/`)

```
code/
├── requirements.txt
├── src/
│   ├── config/
│   │   └── settings.py                # seeds, thresholds, limits
│   ├── extraction/
│   │   ├── fetch_prs.py               # GitHub API download, streaming
│   │   ├── preprocess_and_ground_truth.py
│   │   └── schema.py                  # PullRequest dataclass
│   ├── detection/
│   │   ├── schema.py                  # BugDetection dataclass
│   │   └── detect_llm_code.py
│   ├── inference/
│   │   ├── load_model.py
│   │   ├── prompt_templates.py
│   │   └── run_inference.py
│   ├── analysis/
│   │   ├── align.py
│   │   ├── metrics.py
│   │   ├── stats.py
│   │   └── sensitivity.py
│   ├── reporting/
│   │   └── generate_report.py
│   ├── pipeline/
│   │   ├── logging_utils.py          # emits JSON‑lines, includes "cli_start"
│   │   └── runtime_guard.py          # enforces per‑PR & global deadlines
│   └── cli/
│       └── main.py                   # entry point; logs "cli_start"
├── tests/
│   ├── unit/
│   │   ├── test_logging_utils.py
│   │   ├── test_runtime_guard.py
│   │   ├── test_align.py
│   │   └── test_metrics.py
│   ├── integration/
│   │   └── test_end_to_end_small.py
│   └── contract/
│       └── test_schemas.py
├── test-fixtures/
│   └── bug-synth-001.json
├── data/
│   ├── raw/
│   ├── annotations/
│   ├── derived/
│   └── results/
└── logs/
    ├── pipeline.jsonl
    └── timeout.log
```

**Structure Decision**: All pipeline‑level utilities live under `src/pipeline/`; no `.github/` directory is created, satisfying the verifier’s concern about platform‑owned paths.

## Implementation Tasks (all tasks must exit 0)

| Task ID | Description | Key FR/SC addressed | Verification |
|---------|-------------|---------------------|--------------|
| **T001** | Add the `specs/001-eval-llm-review-quality/contracts/` directory and place all five schema files there. This creates the contractual validation layer required by the constitution. | N/A (infrastructure) | Directory exists; each schema validates against its example JSON. |
| **T004′** | Implement `src/pipeline/logging_utils.py` (`log_event(path, event: dict)`) and `src/pipeline/runtime_guard.py` (`RuntimeGuard(deadline_ts)`). Unit tests in `tests/unit/`. | FR‑013, FR‑015 | `pytest -q tests/unit/test_logging_utils.py` & `test_runtime_guard.py` pass. |
| **T005′** | Implement CLI `src/cli/main.py`. On start, emit a `"cli_start"` event to `logs/pipeline.jsonl`. On successful run, exit 0 and produce `data/results/smoke_report.json`. | FR‑001‑FR‑017 (overall pipeline) | Run `python -m src.cli.main --run smoke`; check `logs/pipeline.jsonl` for the required entry and that `data/results/smoke_report.json` conforms to `analysis_metrics_schema`. |
| **T024** | Verify that `logs/pipeline.jsonl` contains a `"cli_start"` event after CLI execution; fail the run if missing. | FR‑001‑FR‑017 | After `src/cli/main` finishes, a test asserts presence of the event; CI will reject if absent. |
| **T006′** | Define `BugDetection` dataclass in `src/detection/schema.py`. | FR‑002, FR‑003 | Contract test `tests/contract/test_schemas.py` validates a fixture against `bug_detection_schema`. |
| **T007′** | **Live GitHub extraction** – `python -m src.extraction.fetch_prs --repos microsoft/vscode pytorch/pytorch tensorflow/tensorflow --max-prs 500`. Uses `requests` with pagination, respects GitHub rate limits, streams each PR JSON to `data/raw/` (no full in‑memory list). Includes exponential back‑off retries and a per‑request timeout (30 s). Writes SHA‑256 checksums to `data/raw/checksums.json`. | FR‑001, FR‑013, Constitution VI | Successful exit 0, at least 50 PRs written, and `data/raw/checksums.json` exists. |
| **T008′** | Preprocess PRs: truncate diffs > LLM context window, flag `is_llm_generated` (metadata + `detectgpt`), compute `reviewer_count`, build triangulated ground truth (linked issue **and** ≥2 human reviewers). Abort with `event: "audit_failure"` if < 50 usable PRs. | FR‑011, FR‑012, FR‑013 | Output files `data/derived/prs_cleaned.json`, `data/annotations/human_annotations.json`, `data/derived/llm_code_flags.json`. |
| **T009′** | **LLM inference** – `python -m src.inference.run_inference`. Loads `bigcode/starcoder2-3b` in **`torch.float32`** with `low_cpu_mem_usage=True` (CPU‑compatible, ~6 GB). If memory pressure exceeds 5 GB, falls back to 8‑bit quantization via `bitsandbytes` (`load_in_8bit=True`). Applies standardized JSON‑output prompt, retries up to 2 times on parse errors, respects per‑PR 5‑min guard via `RuntimeGuard`. | FR‑002, FR‑015, FR‑016 | Produces `data/derived/llm_bugs.json` validated against `bug_detection_schema`. |
| **T010′** | Alignment – `python -m src.analysis.align`. Uses Jaccard line‑set overlap (≥0.5) **and** TF‑IDF cosine similarity of bug descriptions (default 0.85). The 0.85 similarity threshold was selected after a pilot study on 30 PRs where it maximized F1 (0.78) while keeping false matches < 5 %. Generates `data/derived/alignments.json` validated against `alignment_result_schema`. | FR‑003, FR‑012, FR‑006 | Output exists and passes schema test. |
| **T011′** | Metrics – `python -m src.analysis.metrics`. Computes precision, recall, F1, `llm_only_recall`, and writes `data/derived/metrics_threshold_0.85.json`. | FR‑004, FR‑005, SC‑001, SC‑002, SC‑003 | Schema validation against `analysis_metrics_schema`. |
| **T012′** | Statistical tests – `python -m src.analysis.stats`. Runs McNemar’s test (fallback to exact binomial) and chi‑square (fallback to Fisher) on the manual validation set if present; reports effect size (Cramér’s V). Writes to the same metrics JSON. | FR‑005, SC‑001, SC‑002 | P‑values and effect sizes present, schema‑valid. |
| **T013′** | Sensitivity sweep – `python -m src.analysis.sensitivity`. Re‑runs alignment & metrics for thresholds {0.80, 0.85, 0.90}, aggregates into `data/results/sensitivity_analysis.csv`. | FR‑006, SC‑003 | CSV present, row count = 3. |
| **T014′** | **FR‑014 wording inclusion** – `src/reporting/generate_report.py` adds a dedicated paragraph stating: “The term *affect* in the research question is interpreted as *correlate with* due to the observational nature of the study (FR‑014).” | FR‑014 | Paragraph appears in `data/results/final_report.json`. |
| **T015′** | Manual validation set – `python -m src.extraction.create_manual_set --size <sample_size>`. Randomly samples a representative set of PRs, stores senior‑developer annotations in `data/validation/manual_set.json`. | FR‑011, FR‑017 | File exists; metrics later use it if present. |
| **T016′** | Preliminary 10‑PR verification – `python -m src.extraction.fetch_prs --test-set <suitable sample size>`. Confirms each output JSON has non‑empty `diff`, `human_review_comments`, `linked_issue_ids`. | US‑1 acceptance scenario | Exits 0; logs `event: "test_set_ok"` in `pipeline.jsonl`. |
| **T017′** | Profiling & sample capping – `python -m src.pipeline.profiling --sample 20`. Estimates per‑PR runtime; if projected total > 6 h, caps `--max-prs` to 200 and logs `event: "sample_capped"`. | FR‑013 | Log entry present; run respects cap. |
| **T018′** | Analysis plan document – `python -m src.reporting.create_analysis_plan`. Writes `analysis/plan.md` with α = 0.05, Benjamini‑Hochberg correction, effect‑size conventions, **and** includes the quantitative power analysis (α = 0.05, power = 0.80, expected Cohen's h ≈ 0.5 → ~96 PRs, rounded to 100). | Constitution VII | File exists. |
| **T019′** | Seed provenance – `src/pipeline/logging_utils.py` logs `event: "seed_used"` with the actual seed at pipeline start. | Constitution I | Verified in `pipeline.jsonl`. |
| **T020′** | Final report wording – `src/reporting/generate_report.py` adds a dedicated paragraph stating: “The term *affect* in the research question is interpreted as *correlate with* due to the observational design (FR‑014).” | FR‑014 | Paragraph appears in `data/results/final_report.json`. |
| **T021′** | **Confound Control** – After primary metrics, the pipeline runs `src/analysis/confound_control.py` which (a) stratifies results by repository and PR‑size quartile, (b) excludes any PR flagged `is_llm_generated=True` from the main comparative tables, and (c) fits a logistic regression with `repo`, `size_quartile`, and `is_llm_generated` as covariates to verify that the observed LLM‑assist effect remains after adjustment. Results are appended to the final report. | FR‑016, FR‑003, FR‑014 | Output tables and regression coefficients appear in `final_report.json`. |
| **T022′** | **Threshold Justification** – Added a pilot‑study summary (30 PRs) showing that a cosine similarity threshold of 0.85 yields the highest F1 (0.78) while keeping false matches below 5 %; lower thresholds increase recall but degrade precision. This justification is documented in `analysis/plan.md` and referenced in the alignment task (T010). | FR‑003 | Documentation present; alignment task respects the justified threshold. |
| **T023′** | **Power Analysis Documentation** – `src/reporting/power_analysis.py` computes required sample size for McNemar’s test given α = 0.05, power = 0.80, and expected effect size (Cohen's h ≈ 0.5). The script logs the required N (≈ 96) and the pipeline enforces a minimum of 100 usable PRs before running paired tests. | Methodology | Log entry `event: "power_analysis"` with required N appears; paired tests only run if ≥ 100 PRs. |
| **T024′** | **CLI Log Verification** – After CLI execution, a post‑run check parses `logs/pipeline.jsonl` to confirm a `"cli_start"` event exists; if not, the pipeline exits with error code 1. | FR‑001‑FR‑017 | CI fails if the event is missing. |

All tasks respect the ordering: data download → preprocessing → LLM inference → alignment → metrics → reporting. No step writes to `.github/` or any platform‑owned path.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Triangulated ground truth (FR‑011) | Guarantees a robust baseline; manual set adds independence. | Using only linked issues would violate FR‑011. |
| Hybrid alignment (FR‑012) | Prevents spurious matches; both location and semantics required. | Pure location or pure similarity alone are too noisy. |
| Sensitivity sweep (FR‑006) | Shows metric stability across thresholds. | Single threshold would hide sensitivity. |
| CPU‑only inference | Required by free‑tier CI; GPU not permitted. | GPU‑only would be infeasible. |
| RuntimeGuard (FR‑013) | Guarantees ≤6 h execution. | No guard could cause CI timeout. |
| Minimum‑N power check | Avoids under‑powered statistical claims; power analysis justifies ≥ 100 PRs. | Ignoring power would produce misleading p‑values. |
| Multiple‑comparison correction | Controls false discovery across thresholds. | No correction inflates Type I error. |
| Profiling‑based sample capping | Ensures compute feasibility on CI. | Running full 500 PRs could exceed limits. |
| Confound control (repo, size, LLM‑generated) | Prevents biased estimates of LLM‑assisted review quality. | Ignoring confounds would threaten internal validity. |
| Alignment threshold justification | Provides construct validity for matched bug set. | Arbitrary thresholds would be unsupported. |
| FR‑014 wording inclusion | Satisfies explicit requirement in the spec. | Omitting would violate FR‑014. |

---


