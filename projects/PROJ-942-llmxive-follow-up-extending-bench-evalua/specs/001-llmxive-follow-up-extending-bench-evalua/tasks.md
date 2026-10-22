# Tasks: Extending “$π$‑Bench” with Intent Graphs for Proactive Agent Evaluation  

**Inputs**: `spec.md`, `plan.md`, existing project layout, and reviewer feedback.  

All tasks respect the data‑flow order, stay within the CPU‑only CI budget, and produce real artifacts under the project‑owned directories (`data/`, `code/`, `figures/`, `paper/`).  

---

## Phase 0 – Setup  

- [ ] **T000** [US0] **Install dependencies and pin reproducibility seeds**  
  *Script*: `code/pipelines/install_dependencies.py` (or run `pip install -r requirements.txt`) and `code/utils/seed.py` to set global seeds.  
  *Action*: Create a virtual environment, install all packages from `requirements.txt`, then run `python -c "import utils.seed; utils.seed.set_seeds()"`.  
  *Verification*: `tests/test_setup.py` asserts that required packages are installed and that a deterministic random number (e.g., `np.random.rand()`) matches a stored reference value.

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] **Download and verify the π‑Bench dataset**  
  *Script*: `code/pipelines/download_pi_bench.py`  
  *Action*: Stream the official π‑Bench release (`datasets.load_dataset("pi_bench", streaming=True)`) into `data/raw/`. Compute a SHA‑256 checksum for each file and compare against the checksum list bundled with the dataset. Retry up to three times on transient network errors; abort with a clear error if any checksum mismatches.  
  *Verification*: `tests/test_dataset_download.py` asserts that all files are present, loadable, and pass checksum verification; CI prints “✅ π‑Bench download verified”.

- [ ] **T002** [US1] **Parse raw interaction traces into a normalized CSV**  
  *Script*: `code/pipelines/parse_traces.py`  
  *Action*: Read each JSON trace from `data/raw/`, extract `task_id`, `turn_index`, `speaker`, `utterance`, and any `ground_truth_intent`. Write the flattened table to `data/derived/normalized_traces.csv`.  
  *Verification*: `tests/test_parse_traces.py` checks that the CSV contains exactly one row per turn, required columns exist with correct dtypes, and the total row count equals the sum of turns across all tasks.

- [ ] **T003** [US1] **Deterministic intent inference for missing ground‑truth**  
  *Script*: `code/pipelines/infer_missing_intents.py`  
  *Action*: For every turn lacking a `ground_truth_intent`, invoke a small deterministic LLM (e.g., `google/flan-t5-small`) with a fixed random seed (`torch.manual_seed(42)`, greedy decoding). Output `{task_id, turn_index, inferred_intent, confidence}` to `data/derived/inferred_intents.csv`. Confidence is a float in `[0,1]`.  
  *Verification*: `tests/test_inferred_intents.py` runs the script twice and asserts identical CSV output and that all confidence values lie within `[0,1]`.

- [ ] **T004** [US1] **Construct directed Intent Graphs and serialize to JSON**  
  *Script*: `code/pipelines/build_intent_graph.py`  
  *Action*: For each task, build a `networkx.DiGraph` using **only inferred intents** (or deterministic LLM output) and never ground‑truth hidden‑intent labels. Nodes contain `{id, label, confidence}`; edges encode temporal order and special patterns (e.g., `conflict_resolution`). Serialize each graph to `data/derived/intent_graphs/<task_id>.json`. Record wall‑clock time per graph in `data/derived/graph_construction_latency.csv`.  
  *Verification*:  
  - `tests/test_intent_graph_schema.py` validates every JSON against `specs/001-llmxive-follow-up-extending-bench-evalua/contracts/intent_graph.schema.yaml`.  
  - CI asserts a graph‑construction success rate ≥ 95 % (valid JSON files / total tasks).  

- [ ] **T005** [US1] **Measure graph‑construction computational cost**  
  *Script*: `code/pipelines/measure_graph_cost.py`  
  *Action*: Run the graph‑construction pipeline on a representative sample of 10 tasks while profiling FLOPs (via `fvcore.nn.FlopCountAnalysis`) and wall‑clock time **on CPU only**. Output aggregate statistics (`mean_flops`, `mean_latency_sec`) to `data/derived/graph_cost_summary.csv`.  
  *Verification*: `tests/test_graph_cost.py` checks that FLOPs > 0, latency > 0, and that the CSV header matches the schema.  

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T006** [P] [US2] **Run lightweight CPU‑tractable agent on the Intent‑Graph condition**  
  *Script*: `code/pipelines/run_lightweight_agent.py`  
  *Action*: For every turn, feed the current user prompt together with the full Intent Graph JSON to a 125 M‑parameter OPT model (`facebook/opt-125m`, CPU‑only). Execute three seeds `{101,202,303}`; record `predicted_action`, a binary `is_correct` flag (by comparing to ground‑truth action), and `latency_sec` per turn. Write rows to `data/derived/inference_logs/graph_log.csv`.  
  *Verification*: `tests/test_lightweight_agent.py` ensures three seed entries per turn, `latency_sec` ≤ 60 s, and that `predicted_action` belongs to the allowed action vocabulary.

- [ ] **T007** [P] [US2] **Run raw‑history baseline with token‑budget truncation**  
  *Script*: `code/pipelines/run_raw_baseline.py`  
  *Action*: Load the full dialogue history for each turn, compute token count, and truncate to the model’s maximum context window (2048 tokens) by discarding the oldest tokens. Feed the truncated history to the same OPT model, run three seeds, and log to `data/derived/inference_logs/raw_log.csv`.  
  *Verification*: `tests/test_raw_truncation.py` asserts that the token count never exceeds 2048 and that no “context‑window overflow” errors occur.

- [ ] **T008** [P] [US2] **Run null‑history baseline (no prior context)**  
  *Script*: `code/pipelines/run_null_baseline.py`  
  *Action*: Provide only the current user prompt (empty history) to the OPT model, execute three seeds, and write to `data/derived/inference_logs/null_log.csv`.  
  *Verification*: `tests/test_null_baseline.py` checks that `predicted_action` is either a valid action label or the literal string `"no_action"` and that the model never produces a non‑null action when the prompt is empty.

- [ ] **T009** [P] [US3] **Compute F1 scores, variability, and aggregate latency**  
  *Script*: `code/pipelines/evaluate_metrics.py`  
  *Action*:  
  1. Using ground‑truth action labels, compute binary F1 for each turn, then average over turns and over the three seeds to obtain a per‑task mean F1 for each condition (graph, raw, null).  
  2. From the three seed values per task, compute the standard deviation of the per‑task mean F1 (variability) and seed‑level variance.  
  3. Aggregate online inference latency: median per turn → average per condition.  
  4. Combine the offline graph‑construction latency (from `graph_construction_latency.csv`) with online latency to produce a **total pipeline latency** per condition.  
  Output `data/derived/eval_results/f1_latency_summary.csv` with columns: `task_id, condition, mean_f1, std_f1, seed_variance, mean_online_latency, total_latency`.  
  *Verification*: `tests/test_evaluate_metrics.py` validates that all numeric fields lie in expected ranges (`F1 ∈ [0,1]`, latencies > 0) and that the CSV contains one row per task per condition.

- [ ] **T010** [P] [US3] **Statistical significance testing and bootstrap confidence intervals**  
  *Script*: `code/pipelines/statistical_analysis.py`  
  *Action*: Perform (a) Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null), (b) paired *t*‑test as secondary check, and (c) bootstrap 10 000 resamples to obtain 95 % confidence intervals for the mean differences. Also report effect‑size (Cohen’s d). Write `data/derived/eval_results/statistics.csv` with rows `Graph‑Raw` and `Graph‑Null` and columns `wilcoxon_p`, `ttest_p`, `ci_lower`, `ci_upper`, `cohen_d`.  
  *Verification*: `tests/test_statistics.py` checks numeric types, that `ci_lower < ci_upper`, and that p‑values are within `[0,1]`.

- [ ] **T011** [P] [US3] **Power analysis report**  
  *Script*: `code/pipelines/power_analysis.py`  
  *Action*: Using `statsmodels.stats.power.TTestPower`, compute statistical power for N ≈ 100 tasks, effect size d = 0.5, α = 0.05. Write a markdown summary to `data/derived/eval_results/power_analysis.md` (including the computed power value).  
  *Verification*: `tests/test_power_analysis.py` asserts that the markdown contains a line matching `Power: <float>` and that the float ≥ 0.8.

- [ ] **T012** [P] [US3] **Verify success‑criteria thresholds (SC‑001)**  
  *Script*: `code/pipelines/verify_sc001.py`  
  *Action*: Load `f1_latency_summary.csv` and assert:  
  1. `mean_f1_graph ≥ mean_f1_null + 0.10 × mean_f1_null` (≥ 10 % higher than null).  
  2. `mean_f1_graph ≥ mean_f1_raw − 0.10 × mean_f1_raw` (no more than 10 % lower than raw).  
  If either condition fails, raise an `AssertionError` to cause CI failure.  
  *Verification*: The script’s exit code is 0 when both inequalities hold; otherwise CI reports the assertion message.

- [ ] **T013** [P] [US3] **Generate final evaluation report and figures**  
  *Script*: `code/pipelines/generate_report.py`  
  *Action*: Compile a markdown report `data/derived/eval_results/report.md` that includes:  
  1. Table of mean F1 scores and total latency (online + graph‑construction) per condition.  
  2. P‑values, bootstrap CIs, effect sizes, and power‑analysis summary.  
  3. Bar plot of mean F1 (`figures/f1_comparison.png`) and box‑plot of total latency (`figures/latency_boxplot.png`).  
  4. Graph‑construction success rate (≥ 95 %).  
  5. List of tasks flagged as “Null Graph” for manual review.  
  *Verification*: CI renders the markdown to HTML without errors; `tests/test_report_contents.py` checks that all required sections and figure files exist.

- [ ] **T014** [P] [US1] **Generate SHA‑256 checksums for all data artifacts**  
  *Script*: `code/pipelines/generate_checksums.py`  
  *Action*: Recursively walk `data/` after the full pipeline, compute SHA‑256 hashes for every file, and write a manifest `data/derived/checksums.txt` (`<hash>  <relative-path>`). The platform reads this manifest to update project checksum records (Constitution III).  
  *Verification*: `tests/test_checksums_manifest.py` validates that each listed file exists and that the stored hash matches a freshly computed hash.