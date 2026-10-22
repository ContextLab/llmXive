# Tasks: Extending “$π$‑Bench” with Intent Graphs for Proactive Agent Evaluation  

**Inputs**: `spec.md`, `plan.md`, existing project layout, and the research‑stage reviewer feedback.  

The checklist below implements **all functional requirements (FR‑001 – FR‑009)** and **success criteria (SC‑001 – SC‑005)**.  
Tasks are ordered to respect data flow and the 6‑hour CPU‑only CI budget. All files are written under the project‑owned directories (`data/`, `code/`, `figures/`, `paper/`). No task touches platform‑owned state files.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [P] [US1] **Download and verify the π‑Bench dataset**   <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 -->
  *Script*: `code/pipelines/download_pi_bench.py`  
  *Action*: Use `datasets.load_dataset("pi_bench", streaming=True)` to stream the official release (≈ 100 tasks) into `data/raw/`. For each file compute a SHA‑256 checksum and compare against the list published with the dataset (provided in the script).  
  *Verification*:  
  - `tests/test_dataset_download.py` asserts that the dataset loads without error and that every file’s checksum matches the reference.  
  - A CI step prints “✅ π‑Bench download verified”.  

- [ ] **T002** [P] [US1] **Parse raw interaction traces into a normalized CSV**  
  *Script*: `code/pipelines/parse_traces.py`  
  *Action*: Read each JSON trace from `data/raw/`, extract `task_id`, `turn_index`, `speaker`, `utterance`, and any `ground_truth_intent`. Write the flattened table to `data/derived/normalized_traces.csv`.  
  *Verification*:  
  - `tests/test_parse_traces.py` checks that the CSV contains exactly one row per turn and that required columns are present with correct dtypes.  
  - A CI sanity check confirms the row count equals the sum of turns across all tasks.  

- [ ] **T003** [P] [US1] **Deterministic intent inference for tasks lacking ground‑truth**  
  *Script*: `code/pipelines/infer_missing_intents.py`  
  *Action*: For every task where `ground_truth_intent` is missing, invoke a fixed‑seed LLM prompt (`seed=42`) to generate an intent label and a confidence score ∈[0,1]. Store results in `data/derived/inferred_intents.csv`.  
  *Verification*:  
  - All confidence values are bounded `[0,1]`.  
  - `tests/test_inferred_intents.py` runs the script twice and asserts identical CSV output (determinism).  

- [ ] **T004** [P] [US1] **Construct directed Intent Graphs and serialize to JSON**  
  *Script*: `code/pipelines/build_intent_graph.py`  
  *Action*: For each task, build a `networkx.DiGraph` using only the inferred intents (or deterministic inference results). Nodes contain `{id, label, confidence}`; edges encode temporal order and special patterns (e.g., `conflict_resolution`). Serialize each graph to `data/derived/intent_graphs/<task_id>.json`.  
  *Verification*:  
  - Each JSON validates against `specs/001-llmxive-follow-up-extending-bench-evalua/contracts/intent_graph.schema.yaml` (`tests/test_intent_graph_schema.py`).  
  - CI asserts a graph‑construction success rate ≥ 95 % (number of valid JSON files / total tasks).  

- [ ] **T005** [P] [US2] **Run lightweight CPU‑tractable agent on the Intent‑Graph condition**  
  *Script*: `code/pipelines/run_lightweight_agent.py`  
  *Action*: For every turn, feed the current user prompt plus the full Intent Graph JSON to a 1 B‑parameter distilled transformer (CPU‑only). Execute three seeds `{101,202,303}`; record `predicted_action`, a binary `is_correct` flag (by comparing to ground‑truth action), and `latency_sec`. Write rows to `data/derived/inference_logs/graph_log.csv`.  
  *Verification*:  
  - Every row contains a non‑null `latency_sec` ≤ 60 s.  
  - `tests/test_lightweight_agent.py` checks that exactly three seed entries exist per turn and that `predicted_action` is drawn from the allowed action vocabulary.  

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T006** [P] [US2] **Run raw‑history baseline with token‑budget truncation**  
  *Script*: `code/pipelines/run_raw_baseline.py`  
  *Action*: Load the full dialogue, compute its token count, and truncate to the median token budget used by the Intent Graph (≈ 2 k tokens) before feeding to the same model architecture as T005. Execute three seeds and log to `data/derived/inference_logs/raw_trunc_log.csv`.  
  *Verification*:  
  - Input token count ≤ budget for every turn (asserted in `tests/test_raw_truncation.py`).  
  - No “context‑window overflow” errors occur.  

- [ ] **T007** [P] [US2] **Run null‑history baseline (no prior context)**  
  *Script*: `code/pipelines/run_null_baseline.py`  
  *Action*: Provide only the current user prompt (empty history) to the lightweight model. Execute three seeds and write to `data/derived/inference_logs/null_log.csv`.  
  *Verification*:  
  - `predicted_action` is either a valid action label or the literal string `"no_action"`.  
  - `tests/test_null_baseline.py` confirms that when the prompt is empty the model never outputs a non‑null action.  

- [ ] **T008** [P] [US3] **Compute per‑turn and per‑task mean F1 scores**  
  *Script*: `code/pipelines/evaluate_f1.py`  
  *Action*: Using ground‑truth action labels (available for tasks with annotated intents), compute binary F1 for each turn, then average over turns and over the three seeds to obtain a per‑task mean F1 for each condition (graph, raw, null). Output `data/derived/eval_results/f1_scores.csv`.  
  *Verification*:  
  - All scores lie in `[0,1]`.  
  - `tests/test_f1_computation.py` validates row count equals number of tasks and that the CSV header matches the schema.  

- [ ] **T009** [P] [US3] **Aggregate latency statistics per condition**  
  *Script*: `code/pipelines/evaluate_latency.py`  
  *Action*: From the three latency measurements per turn, compute the median latency per turn, then the average latency per condition. Calculate percentage reduction of the Graph condition relative to Raw and Null. Write `data/derived/eval_results/latency_summary.csv`.  
  *Verification*:  
  - Median latency ≤ mean latency for each condition (asserted in `tests/test_latency_aggregation.py`).  
  - Reduction percentage is a finite float and non‑negative.  

- [ ] **T010** [P] [US3] **Statistical significance testing and bootstrap confidence intervals**  
  *Script*: `code/pipelines/statistical_analysis.py`  
  *Action*: Perform (a) Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null), (b) paired *t*‑test as secondary check, and (c) bootstrap 10 000 resamples to obtain 95 % confidence intervals for the mean differences. Save results to `data/derived/eval_results/statistics.csv`.  
  *Verification*:  
  - File contains two rows (`Graph‑Raw`, `Graph‑Null`) with columns `wilcoxon_p`, `ttest_p`, `ci_lower`, `ci_upper`.  
  - `tests/test_statistics.py` checks numeric types and that `ci_lower < ci_upper`.  

- [ ] **T011** [P] [US3] **Power analysis report**  
  *Script*: `code/pipelines/power_analysis.py`  
  *Action*: Using `statsmodels.stats.power.TTestPower`, compute the statistical power for N ≈ 100 tasks, effect size d = 0.5, α = 0.05. Write a markdown summary to `data/derived/eval_results/power_analysis.md`.  
  *Verification*:  
  - The script prints a power ≥ 0.8 for d = 0.5.  
  - `tests/test_power_analysis.py` asserts that the markdown contains a line matching `Power: <float>` and that the float is ≥ 0.8.  

- [ ] **T012** [P] [US3] **Generate final evaluation report and figures**  
  *Script*: `code/pipelines/generate_report.py`  
  *Action*: Compile a markdown report `data/derived/eval_results/report.md` that includes:  
  1. Table of mean F1 scores and latency per condition.  
  2. P‑values, bootstrap CIs, and power‑analysis summary.  
  3. Bar plot of F1 scores (`figures/f1_comparison.png`) and box‑plot of latency reductions (`figures/latency_boxplot.png`).  
  4. Graph‑construction success rate (≥ 95 %).  
  5. List of “Null Graph” tasks for manual review.  
  *Verification*:  
  - CI renders the markdown to HTML without errors.  
  - `tests/test_report_contents.py` checks that all required sections and figure files are present.  

- [ ] **T013** [P] [US3] **Assert SC‑001 performance thresholds**  
  *Script*: `code/pipelines/verify_sc001_thresholds.py`  
  *Action*: Load `data/derived/eval_results/f1_scores.csv` and assert:  
    1. `mean_f1_graph ≥ mean_f1_null + 0.10 × mean_f1_null` (≥ 10 % higher than null).  
    2. `mean_f1_graph ≥ mean_f1_raw − 0.10 × mean_f1_raw` (no more than 10 % lower than raw).  
  *Verification*:  
  - If either condition fails, the script raises an `AssertionError`, causing CI failure.  

- [ ] **T014** [P] [US1] **Compute and record F1 variability statistics**  
  *Script*: `code/pipelines/compute_f1_variability.py`  
  *Action*: From the per‑task mean F1 scores across the three seeds, compute:  
    - Standard deviation of per‑task mean F1 for each condition.  
    - Seed‑level variance for each task.  
  Append these metrics to `data/derived/eval_results/f1_variability.csv`.  
  *Verification*:  
  - `tests/test_f1_variability.py` ensures all std‑dev values lie in `[0,1]` and that the CSV contains the expected columns (`condition`, `std_f1`, `seed_variance`).  

- [ ] **T015** [P] [US1] **Generate SHA‑256 checksums for all data artifacts**  
  *Script*: `code/pipelines/generate_checksums.py`  
  *Action*: Recursively walk `data/` after each pipeline stage, compute SHA‑256 hashes for every file, and write a manifest `data/derived/checksums.txt` (format: `<hash>  <relative-path>`). The CI platform reads this manifest to update the project’s checksum records (Constitution Principle III).  
  *Verification*:  
  - `tests/test_checksums_manifest.py` validates that each listed file exists and that the stored hash matches the freshly computed hash.  

---

### Dependency Mapping  

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| **FR‑001** | T001, T002 |
| **FR‑002** | T004 |
| **FR‑003** | T005 |
| **FR‑004** | T006 |
| **FR‑005** | T008, T010 |
| **FR‑006** | T009 |
| **FR‑007** | T003, T004 |
| **FR‑008** | T007 |
| **FR‑009** | T004 (excludes ground‑truth) |
| **SC‑001** | T008, T010, **T013** |
| **SC‑002** | T009 |
| **SC‑003** | T010 |
| **SC‑004** | T004 (success‑rate check) |
| **SC‑005** | T008, **T014** |
| **Constitution III (Data hygiene)** | **T015** |

All tasks together constitute a minimal, end‑to‑end executable pipeline that runs on the default CPU‑only GitHub Actions runner within the 6‑hour limit, satisfies every functional requirement and success criterion, and produces real, verifiable artifacts for the research question.
