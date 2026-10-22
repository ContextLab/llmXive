# Tasks: Extending “$π$‑Bench” with Intent Graphs for Proactive Agent Evaluation  

**Inputs**: `spec.md`, `plan.md`, existing project layout, and reviewer feedback.  

All tasks respect the data‑flow order, stay within the CPU‑only CI budget, and produce real artifacts under the project‑owned directories (`data/`, `code/`, `figures/`, `paper/`).  

---  

## Phase 0 – Setup  

- [X] T000 **Install dependencies and pin reproducibility seeds** – `code/pipelines/install_dependencies.py` (or `pip install -r requirements.txt`) and `code/utils/seed.py`.  
  *Verification*: `tests/test_setup.py` confirms required packages are installed and a deterministic random number matches the stored reference.  

---  

## Phase 1 – Data acquisition, parsing, and Intent‑Graph construction  

- [ ] T001 **Download and verify the π‑Bench dataset** – `code/pipelines/download_pi_bench.py` streams `datasets.load_dataset("pi_bench", streaming=True)`, writes raw JSON files to `data/raw/`, verifies SHA‑256 checksums, and retries up to 3 times on failure.   <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipelines/download_pi_bench.py exit=1 -->
  *Verification*: `tests/test_dataset_download.py` asserts that every expected file exists, loads without error, and matches published checksums.  

- [ ] T002 **Parse raw interaction traces into a normalized CSV** – `code/pipelines/parse_traces.py` reads `data/raw/*.json` and creates `data/derived/normalized_traces.csv`.  
  *Verification*: `tests/test_parse_traces.py` checks that the CSV contains one row per dialogue turn, includes required columns (`task_id, turn_index, speaker, utterance, ground_truth_intent`), and that the row count equals the sum of turns across all tasks.  

- [ ] T003 **Deterministic intent inference for missing ground‑truth intents** – `code/pipelines/infer_missing_intents.py` runs a fixed‑seed `google/flan-t5-small` LLM (seed 42, greedy decoding) and outputs `data/derived/inferred_intents.csv` (`task_id, turn_index, inferred_intent, confidence`).  
  *Verification*: `tests/test_inferred_intents.py` runs the script twice and asserts identical CSV output and that all confidence values lie in `[0, 1]`.  

- [ ] T004 **Construct inferred‑only Intent Graphs and serialize to JSON** – `code/pipelines/build_intent_graph.py` builds a `networkx.DiGraph` using only inferred intents (never ground‑truth), adds temporal edges between consecutive turns and conflict‑resolution edges when the pattern “Conflict Detected” → “Resolution Strategy” appears, writes each graph to `data/derived/intent_graphs/<task_id>.json`, and records wall‑clock time per graph in `data/derived/graph_construction_latency.csv`.  
  *Verification*:  
    1. `tests/test_intent_graph_schema.py` validates every JSON against `specs/001-llmxive-follow-up-extending-bench-evalua/contracts/intent_graph.schema.yaml`.  
    2. `tests/test_intent_graph_topology.py` asserts that each graph contains at least one temporal edge per turn and includes a conflict‑resolution edge when the dialogue exhibits a conflict scenario (as per spec acceptance criteria).  
    3. CI asserts a graph‑construction success rate ≥ 95 % (valid JSON files ÷ total tasks).  

- [ ] T004b **Construct ground‑truth‑only Intent Graphs (control)** – `code/pipelines/build_intent_graph_gt.py` creates graphs that use only the published hidden‑intent annotations (no LLM inference) and stores them at `data/derived/intent_graphs_gt/<task_id>.json`. The `source` field in each JSON is set to `"ground_truth_only"`.  
  *Verification*: Same schema validation as T004; additionally checks that `source == "ground_truth_only"` for every control graph.  

---  

## Phase 2 – Agent execution, evaluation, and statistical validation  

- [ ] T006 **Run lightweight CPU‑tractable agent on the inferred‑only Intent‑Graph condition** – `code/pipelines/run_lightweight_agent.py` loads each `intent_graphs/<task_id>.json`, feeds it together with the current user prompt to `facebook/opt-125m` (CPU), runs three seeds `{101,202,303}`, and logs `task_id, turn_index, seed, predicted_action, is_correct, latency_sec` to `data/derived/inference_logs/graph_seed<seed>.csv`.  
  *Verification*: `tests/test_lightweight_agent.py` ensures three seed entries per turn, that `latency_sec` ≤ 60 s, and that `predicted_action` belongs to the allowed action vocabulary.  

- [ ] T007 **Run raw‑history baseline with max‑context truncation** – `code/pipelines/run_raw_baseline.py` truncates each dialogue to the model’s 2048‑token window (dropping oldest tokens), feeds the truncated history to the same OPT model, runs three seeds, and writes to `data/derived/inference_logs/raw_seed<seed>.csv`.  
  *Verification*: `tests/test_raw_truncation.py` asserts that token counts never exceed 2048 and that no “context‑window overflow” errors occur.  

- [ ] T008 **Run null‑history baseline (no prior context)** – `code/pipelines/run_null_baseline.py` provides only the current turn prompt to the OPT model, runs three seeds, and writes to `data/derived/inference_logs/null_seed<seed>.csv`.  
  *Verification*: `tests/test_null_baseline.py` checks that `predicted_action` is either a valid action label or the literal string `"no_action"` and that the model never produces a non‑null action when the prompt is empty.  

- [ ] T009 **Compute per‑task mean F1, variability, and aggregate **online** inference latency** – `code/pipelines/evaluate_metrics.py`  
    1. Uses ground‑truth action labels to compute binary F1 for each turn, then averages over turns and seeds → per‑task mean F1 for each condition (graph, raw, null, GT‑control).  
    2. Calculates standard deviation of the per‑task mean F1 across seeds.  
    3. Aggregates **online** inference latency (median per turn → average per condition).  
    4. Writes `data/derived/eval_results/f1_latency_summary.csv` with columns `task_id, condition, mean_f1, std_f1, seed_variance, mean_online_latency`.  
  *Verification*: `tests/test_evaluate_metrics.py` validates numeric ranges (`F1 ∈ [0,1]`, latencies > 0) and that the CSV contains one row per task per condition.  

- [ ] T010 **Statistical significance testing and bootstrap confidence intervals** – `code/pipelines/statistical_analysis.py` performs (a) Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null, Graph vs GT‑Control), (b) paired *t*‑test as secondary check, (c) 10 000‑sample bootstrap to obtain 95 % confidence intervals for the mean differences, and (d) computes effect size (Cohen’s d). Results are saved to `data/derived/eval_results/statistics.csv`.  
  *Verification*: `tests/test_statistics.py` checks that all numeric fields are present, `ci_lower < ci_upper`, and p‑values lie in `[0,1]`.  

- [ ] T011 **A‑priori power analysis report** – `code/pipelines/power_analysis.py` uses `statsmodels.stats.power.TTestPower` to compute statistical power for N ≈ 100 tasks, effect size d = 0.5, α = 0.05, and writes a markdown summary to `data/derived/eval_results/power_analysis.md`.  
  *Verification*: `tests/test_power_analysis.py` asserts that the markdown contains a line matching `Power: <float>` and that the reported power ≥ 0.8.  

- [ ] T012 **Verify success‑criteria thresholds (SC‑001 & SC‑002)** – `code/pipelines/verify_success_criteria.py` loads `f1_latency_summary.csv` and asserts:  
    1. `mean_f1_graph ≥ mean_f1_null + 0.10 × mean_f1_null` (≥ 10 % higher than null).  
    2. `mean_f1_graph ≥ mean_f1_raw − 0.10 × mean_f1_raw` (no more than 10 % lower than raw).  
    3. `mean_online_latency_graph ≤ mean_online_latency_raw` (pure inference‑time reduction).  
    If any condition fails, the script exits non‑zero and prints the violated inequality.  
  *Verification*: CI passes when the script exits 0; otherwise the failure message is shown.  

---  

## Phase 3 – Reporting, reproducibility, and hand‑off  

- [ ] T013 **Generate final evaluation report and figures** – `code/pipelines/generate_report.py` compiles `data/derived/eval_results/report.md` containing:  
    1. Table of mean F1 scores and **online** latency per condition (Graph, Raw, Null, GT‑Control).  
    2. P‑values, bootstrap CIs, effect sizes, and the power‑analysis summary.  
    3. Bar plot of mean F1 (`figures/f1_comparison.png`) and box‑plot of online latency (`figures/latency_boxplot.png`).  
    4. Graph‑construction success rate (≥ 95 %).  
    5. List of tasks flagged as “Null Graph” for manual review.  
  *Verification*: CI renders the markdown to HTML without errors; `tests/test_report_contents.py` checks that all required sections and figure files exist.  

- [ ] T014 **Generate SHA‑256 checksums for all data artifacts** – `code/pipelines/generate_checksums.py` recursively walks the `data/` directory after the full pipeline, computes SHA‑256 hashes for every file, and writes a manifest `data/derived/checksums.txt` (`<hash>  <relative‑path>`). The platform reads this manifest to update project checksum records (Constitution III).  
  *Verification*: `tests/test_checksums_manifest.py` validates that each listed file exists and that the stored hash matches a freshly computed hash.  

---  

**Note**: Tasks T001, T002, and T003 have been reopened because prior executions failed; the revised definitions include robust retry, checksum verification, and deterministic inference to satisfy FR‑001, FR‑007, and related success criteria. The new control‑graph task (T004b) and the tightened latency handling (T009, T012) directly address reviewer concerns about true cost accounting and structured‑memory fidelity.  
