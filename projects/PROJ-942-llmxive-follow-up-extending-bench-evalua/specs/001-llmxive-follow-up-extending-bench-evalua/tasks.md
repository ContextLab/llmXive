# Tasks: Extending “$π$‑Bench” with Intent Graphs for Proactive Agent Evaluation

**Inputs**: `spec.md`, `plan.md`, existing project layout, and the research‑stage reviewer feedback.

The following checklist implements **all functional requirements (FR‑001 – FR‑009)** and **success criteria (SC‑001 – SC‑005)**.  
Tasks are ordered to respect data flow and compute limits. All paths are relative to the repository root and write under the project‑owned directories (`data/`, `code/`, `figures/`, `paper/`). No task creates or modifies platform‑owned state files.

---

- [ ] T001 [P] [US1] **Download and verify the π‑Bench dataset**   <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 -->
  *Create* `data/raw/` with the official release (≈ 100 tasks).  
  *Verification*: checksum of each downloaded file matches the published SHA‑256 list; a pytest test (`tests/test_dataset_download.py`) asserts successful load via `datasets.load_dataset("pi_bench")`.  
  *File*: `code/pipelines/download_pi_bench.py`

- [ ] T002 [P] [US1] **Parse raw interaction traces into a normalized CSV**  
  *Read* JSON files from `data/raw/`, extract `task_id`, `turn_index`, `speaker`, `utterance`, and optional `ground_truth_intent`.  
  *Write* `data/derived/normalized_traces.csv`.  
  *Verification*: schema validation (pandas dtypes) and a unit test (`tests/test_parse_traces.py`) confirming 1‑to‑1 mapping of turns to rows.  
  *File*: `code/pipelines/parse_traces.py`

- [ ] T003 [P] [US1] **Deterministic intent inference for tasks lacking ground‑truth**  
  For each task without `ground_truth_intent`, invoke a fixed‑seed LLM prompt (seed = 42) to produce intent labels and confidence scores.  
  *Write* temporary inference CSV `data/derived/inferred_intents.csv`.  
  *Verification*: all confidence values lie in `[0,1]`; reproducibility test ensures identical output across runs.  
  *File*: `code/pipelines/infer_missing_intents.py`

- [ ] T004 [P] [US1] **Construct directed Intent Graphs and serialize to JSON**  
  Using `networkx`, create a graph per task **without** using any ground‑truth hidden‑intent labels. Nodes are only inferred intents (or deterministic inference results) with fields `{id, label, confidence}`; edges encode temporal order and special patterns (e.g., conflict → resolution).  
  *Write* `data/derived/intent_graphs/<task_id>.json`.  
  *Verification*: each JSON validates against `specs/001-llmxive-follow-up-extending-bench-evalua/contracts/intent_graph.schema.yaml` (test `tests/test_intent_graph_schema.py`); graph‑construction success rate ≥ 95 % (asserted in CI).  
  *File*: `code/pipelines/build_intent_graph.py`

- [ ] T005 [P] [US2] **Run lightweight CPU‑tractable agent on the Intent Graph condition**  
  For every turn, feed the current user prompt plus the full Intent Graph JSON to the lightweight model (e.g., a 1 B‑parameter distilled transformer). Execute three seeds `{101,202,303}` and record `predicted_action`, correctness flag, and latency.  
  *Write* `data/derived/inference_logs/graph_log.csv`.  
  *Verification*: each row contains non‑null `latency_sec` ≤ 60 s; a pytest check confirms three distinct seed entries per turn.  
  *File*: `code/pipelines/run_lightweight_agent.py`

- [ ] T006 [P] [US2] **Run raw‑history baseline with token‑budget truncation**  
  Load the full dialogue, truncate to the same token budget used by the Intent Graph (≈ 2 k tokens) before feeding to the reference model (same architecture as the lightweight agent). Execute three seeds and record outputs.  
  *Write* `data/derived/inference_logs/raw_trunc_log.csv`.  
  *Verification*: token count per input ≤ budget; sanity test ensures no “context‑window overflow” errors.  
  *File*: `code/pipelines/run_raw_baseline.py`

- [ ] T007 [P] [US2] **Run null‑history baseline (no prior context)**  
  Provide only the current user prompt to the lightweight model (empty history). Execute three seeds and record outputs.  
  *Write* `data/derived/inference_logs/null_log.csv`.  
  *Verification*: all `predicted_action` values are either a valid action label or `"no_action"`; test checks that no action is produced when the prompt is empty.  
  *File*: `code/pipelines/run_null_baseline.py`

- [ ] T008 [P] [US3] **Compute per‑turn and per‑task mean F1 scores**  
  Using ground‑truth action labels (available for tasks with annotated intents), calculate binary F1 for each turn, then average over turns and over the three seeds to obtain a per‑task mean F1 for each condition (graph, raw, null).  
  *Write* `data/derived/eval_results/f1_scores.csv`.  
  *Verification*: rows sum to the number of tasks; a unit test (`tests/test_f1_computation.py`) checks that scores lie in `[0,1]`.  
  *File*: `code/pipelines/evaluate_f1.py`

- [ ] T009 [P] [US3] **Aggregate latency statistics per condition**  
  From the three latency measurements per turn, compute the median latency per turn, then the average latency per condition. Calculate percentage reduction of the Graph condition relative to Raw and Null.  
  *Write* `data/derived/eval_results/latency_summary.csv`.  
  *Verification*: median latency ≤ mean latency for each condition; a test (`tests/test_latency_aggregation.py`) asserts the reduction percentage is a finite float.  
  *File*: `code/pipelines/evaluate_latency.py`

- [ ] T010 [P] [US3] **Statistical significance testing and bootstrap confidence intervals**  
  Perform (a) Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null); (b) paired *t*‑test as secondary check; (c) bootstrap 10 000 resamples to obtain 95 % CI for the mean differences. Record p‑values and CIs.  
  *Write* `data/derived/eval_results/statistics.csv`.  
  *Verification*: p‑values are numeric; CI bounds satisfy `lower < upper`; a test (`tests/test_statistics.py`) confirms the file contains exactly two rows (Graph‑Raw, Graph‑Null).  
  *File*: `code/pipelines/statistical_analysis.py`

- [ ] T011 [P] [US3] **Power analysis report**  
  Using `statsmodels.stats.power.TTestPower`, compute the statistical power given N ≈ 100 tasks, effect size d = 0.5, α = 0.05. Include the result in the final report; if observed effect size is smaller, note the limitation.  
  *Write* `data/derived/eval_results/power_analysis.md`.  
  *Verification*: script prints power ≥ 0.8 for d = 0.5; test (`tests/test_power_analysis.py`) asserts the markdown contains a numeric power value.  
  *File*: `code/pipelines/power_analysis.py`

- [ ] T012 [P] [US3] **Generate final evaluation report and figures**  
  Compile a markdown report `data/derived/eval_results/report.md` containing:  
  * Table of mean F1 scores and latency per condition.  
  * P‑values, bootstrap CIs, and power analysis summary.  
  * Bar plot of F1 scores and box‑plot of latency reductions (saved under `figures/`).  
  * Graph‑construction success rate (≥ 95 %).  
  * List of “Null Graph” tasks for manual review.  
  *Verification*: CI/CD step renders the markdown to HTML without errors; a visual‑diff test (`tests/test_report_contents.py`) checks that all required sections are present.  
  *Files*: `code/pipelines/generate_report.py`, `figures/f1_comparison.png`, `figures/latency_boxplot.png`

- [ ] T013 [P] [US3] **Assert SC‑001 performance thresholds**  
  After T010, load `data/derived/eval_results/f1_scores.csv` and verify that:  
  1. `mean_f1_graph` ≥ `mean_f1_null` + 0.10 × `mean_f1_null` (≥ 10 % higher).  
  2. `mean_f1_graph` ≥ `mean_f1_raw` − 0.10 × `mean_f1_raw` (≤ 10 % lower).  
  If either condition fails, raise an AssertionError causing CI failure.  
  *File*: `code/pipelines/verify_sc001_thresholds.py`

- [ ] T014 [P] [US1] **Compute and record F1 variability statistics**  
  From the per‑task mean F1 scores across the three seeds, compute:  
  * Standard deviation of per‑task mean F1 for each condition.  
  * Variance across seeds for each task (seed‑level variance).  
  Append these metrics to `data/derived/eval_results/f1_variability.csv`.  
  *Verification*: test (`tests/test_f1_variability.py`) checks that standard deviation values lie in `[0,1]` and that variance columns are present.  
  *File*: `code/pipelines/compute_f1_variability.py`

- [ ] T015 [P] [US1] **Generate SHA‑256 checksums for all data artifacts**  
  Recursively walk the `data/` directory after each pipeline stage, compute SHA‑256 hashes for every file, and write a manifest `data/derived/checksums.txt` (format: `<hash>  <relative-path>`). The CI platform automatically reads this manifest to update the `state/projects/...yaml` checksum entries, thereby satisfying Constitution Principle III.  
  *Verification*: a pytest test (`tests/test_checksums_manifest.py`) validates that each listed file exists and its hash matches the recorded value.  
  *File*: `code/pipelines/generate_checksums.py`

---

**Dependency Mapping**

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001 | T001, T002 |
| FR‑002 | T004 |
| FR‑003 | T005 |
| FR‑004 | T006 |
| FR‑005 | T008, T010 |
| FR‑006 | T009 |
| FR‑007 | T003, T004 |
| FR‑008 | T007 |
| FR‑009 | T004 (now excludes ground‑truth) |
| SC‑001 | T008, T010, **T013** |
| SC‑002 | T009 |
| SC‑003 | T010 |
| SC‑004 | T004 (success‑rate check) |
| SC‑005 | T008, **T014** |
| Data‑hygiene (Constitution III) | **T015** (now explicitly updates state) |

All tasks together constitute a minimal, end‑to‑end executable pipeline that can be run on the default CPU‑only GitHub Actions runner within the 6‑hour limit. The checklist can be executed sequentially; each task’s output feeds the next, guaranteeing reproducibility and compliance with the specification.  