# Tasks: llmXive follow‑up: extending “Mellum2 Technical Report”

**Input**: Active `spec.md` and `plan.md` in `specs/001-llmxive-follow-up-extending-mellum2-tech/`, contracts in the same feature dir, original research idea, and prior verifier feedback (rejected tasks listed at bottom, now folded into the tasks below).

**Scope**: Smallest complete study answering the research question: real code from `codeparrot/github-code`, static complexity labels, frozen‑LLM per‑token loss on CPU, correlation + threshold detection + significance validation, reproducible result artifacts and figures. Paper writing is a later stage; this file ends at the paper‑stage handoff.

**Compute feasibility note**: FR‑003 requires running a frozen open‑weight LLM. The pipeline now **attempts** the specified large model (Mistral‑7B or Llama‑3‑8B) on CPU; if the model cannot be loaded due to OOM the task fails loudly (no silent fallback). A small model may be used only after a spec amendment (flagged for kick‑back). All data loading streams the real dataset and FAILS LOUDLY on fetch errors — no synthetic fallbacks.

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001a [US1] **Environment & Config** – Create a fully reproducible Python 3.11 environment:
  * Write `code/requirements.txt` with **pinned** versions of `datasets`, `transformers`, `tree-sitter`, `tree-sitter-python`, `tree-sitter-java`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `kenlm`, `ruptures`, `pwlf`, `jsonschema`, `pytest`, `pytest-cov`, `psutil`.
  * Add `code/config.py` defining `SEED=12345`, project‑wide `paths` via `llmxive_toolkit`, and the **primary** frozen model identifier (`Mistral-7B` or `Llama-3-8B`).
  * Verification: `pip install -r code/requirements.txt` succeeds; `python -c "import code.config"` runs without error.

- [ ] T001b [US1] **Quickstart Documentation** – Write `quickstart.md` with a single runnable command:
  ```bash
  python -m code.main --phase all --sample small
  ```
  * Include usage notes, required environment activation, and expected runtime limits.
  * Verification: the file exists and the command runs without raising parsing errors.

- [ ] T002 [US1] **Dataset Download & Raw Storage** – Stream `codeparrot/github-code` (Python & Java) via:
  ```python
  ds = datasets.load_dataset("codeparrot/github-code", split="train", streaming=True)
  ```
  * Apply a deterministic reservoir sample of **N** chunks per language (`N` derived from Phase‑0 power analysis, seeded with `SEED`).
  * Write raw records to **Parquet** (`data/processed/raw_chunks.parquet`) with columns: `id`, `repo_name`, `language`, `content`, `status`.
  * Record SHA‑256 checksums in `data/checksums.txt`.
  * Verification: the Parquet file exists, contains exactly `N` rows per language, and a simple row‑count check passes. Any fetch error raises an exception (no fallback).

- [ ] T003 [US1] **Static Analysis (CodeQL + tree‑sitter)** – For each raw chunk:
  * **Run CodeQL CLI** to extract additional security‑relevant metrics; abort the task if the CLI is missing.
  * Run **tree‑sitter** parsers for Python and Java to compute:
    - `cyclomatic_complexity`
    - `nesting_depth`
    - `repetition_ratio`
    - `token_count`
  * Annotated results are written to **Parquet** (`data/processed/annotated_chunks.parquet`) conforming to `dataset.schema.yaml`.
  * Unparseable files receive `status="parse_error"` and are logged; processing continues.
  * Verification: annotated Parquet validates against `dataset.schema.yaml`; parse‑error rate is logged and finite.

- [ ] T004 [US1] **KenLM Baseline & LLM Inference (nested schema & division‑norm)**
  *Part A – KenLM* – Train a 5‑gram Kneser‑Ney model per language on a disjoint training split of the sampled chunks. Save ARPA files to `data/processed/kenlm_model_python.arpa` and `..._java.arpa`. Score each annotated chunk, adding field `ngram_probability` (log‑prob per token) to the **Parquet** inference input.
  *Part B – LLM Inference* – Load the **primary** frozen model (Mistral‑7B/Llama‑3‑8B) on CPU (`device="cpu"`). For each annotated chunk compute:
    - `per_token_loss` (cross‑entropy)
    - `prediction_entropy`
    - `inference_time_ms`
  * Normalized loss is computed by **division**: `norm_loss = per_token_loss / exp(ngram_probability)`.
  * Retry logic: up to 3 attempts with exponential back‑off; after final failure log and set `status="timeout"`. Successful chunks have `status="success"`.
  * Output a **nested** Parquet file `data/results/inference.parquet` matching `code_chunk.schema.yaml` (fields under `static_labels`, `inference_metrics`, `metadata`; includes required `baseline_model`).
  * Verification: ARPA files load with `kenlm`; inference Parquet contains only rows with `status` either `"success"` or `"timeout"`; schema validation passes; no synthetic values are present.

- [ ] T005 [US1] **Repository‑Level Aggregation & Correlation (pre‑permutation)** –  
  * Aggregate successful chunks (`status="success"`) to repository‑level means (`RepositoryAggregate` as defined in `data-model.md`) and store in `data/results/repo_aggregates.parquet`.
  * Compute Pearson and Spearman coefficients for each complexity metric vs. **normalized** loss, controlling for `token_count` and `ngram_probability` via partial correlation (implemented with `statsmodels`).
  * Write `data/results/correlation_stats.parquet` containing `metric`, `language`, `coefficient`, `method`, `sample_size`. **Do not** write p‑values yet (they will be added after permutation).
  * Verification: Parquet contains rows for all metric × language combos; coefficients are numeric; schema‑compatible with `correlation_result.schema.yaml` (p‑values optional at this stage).

- [ ] T006 [US1] **Visualizations** – Generate PNG figures in `data/figures/`:
  * Scatter plots for each metric vs. normalized loss (stratified by language) with OLS regression lines.
  * Axis labels: “Cyclomatic Complexity”, “Nesting Depth”, “Prediction Loss (Perplexity)”.
  * Deterministic naming (e.g., `scatter_cyclomatic_complexity.png`).
  * Verification: PNG files exist, non‑empty, and are regenerated identically from the same `correlation_stats.parquet`.

- [ ] T007 [US1] **Threshold Detection with Covariate Control** –  
  * Using `repo_aggregates.parquet`, regress out `token_count` and `ngram_probability` from both predictor and outcome, then apply piecewise regression (one breakpoint) via `pwlf` or `ruptures`.
  * Select model by AIC/BIC; report `model_fit`, `aic_difference`, `threshold_value`, `slope_before`, `slope_after`.
  * If linear model is preferred (ΔAIC ≤ 2), report honestly.
  * Output `data/results/threshold_results.parquet` conforming to `threshold_result.schema.yaml`.
  * Verification: Parquet validates; report includes covariate‑adjusted slopes.

- [ ] T008 [US2] **Threshold Sensitivity & Bootstrap Stability** –  
  * Sweep identified breakpoint by offsets `{0.01, 0.05, 0.1}` and recompute piecewise fits.
  * Perform ≥200 bootstrap resamples of repositories (fixed `SEED`), compute max shift in threshold (`bootstrap_stability`) and 95 % CI width.
  * Store results in `data/results/threshold_sensitivity.parquet`.
  * Verification: JSON‑schema‑compatible Parquet contains `sensitivity_range`, `bootstrap_stability`, `confidence_interval_width`; stability ≤ 0.05 units is asserted in test.

- [ ] T009 [US3] **Cluster‑Robust Permutation Tests & Multiple‑Comparison Correction** –  
  * Execute ≥1 000 block permutations at the repository level for each correlation and each detected threshold.
  * Compute empirical p‑values, then apply Bonferroni and Benjamini‑Hochberg FDR across all hypotheses.
  * Update `correlation_stats.parquet` and `threshold_results.parquet` with `p_value` and `adjusted_p_value`.
  * Persist raw permutation results in `data/results/permutation_results.parquet`.
  * Verification: permutation count recorded; adjusted p‑values present for every hypothesis; schema validation passes.

- [ ] T010 [US3] **Cross‑Language Validation & Human‑Labeled Benchmark** –  
  * Re‑run correlation and threshold pipelines on the held‑out Java subset; compare coefficients and breakpoints to Python results, writing `cross_language_consistency` boolean to `data/results/cross_validation.parquet`.
  * Load a real human‑labeled complexity benchmark (e.g., `datasets.load_dataset("code_x_glue_cc_code_to_text", ...)`). If loading fails, the task aborts (no limitation report), satisfying the MUST clause of FR‑011.
  * If benchmark loads, compute correlation between our metrics and the benchmark labels and store in `data/results/benchmark_validation.parquet`.
  * Verification: task succeeds only when benchmark is available; otherwise CI fails, prompting a spec amendment.

- [ ] T011 **Runtime & Resource Reporting** –  
  * Measure total wall‑clock time, peak RAM (`psutil`), and assert `torch.cuda.is_available() == False`.
  * Write `data/results/runtime_report.parquet` with fields `execution_time_hours`, `memory_peak_gb`, `cpu_only`.
  * Extend `feasibility_report.parquet` with observed effect size and power, flagging `limitation_noted` if under‑powered.
  * Verification: values are numeric, within limits (≤ 6 h, ≤ 7 GB), and `cpu_only` is true.

## Phase 2: Complete the study and validate its evidence

- [ ] T012 [US1] **Final Report Assembly** –  
  * Merge all result Parquet files into a single JSON report `data/results/final_report.json` that conforms to `output.schema.yaml`.
  * Ensure every summary field (total chunks, primary correlation, threshold detection, cross‑language flag) traces back to a row in a Parquet artifact.
  * Verification: `jsonschema` validation passes; spot‑check three values against source Parquet rows.

- [ ] T013 [US3] **Methods, Results Summary & Paper‑Stage Handoff** –  
  * Write `data/results/study_summary.md` describing data source, sampling rule, static analysis pipeline, model configuration, statistical methods, and limitations (including power analysis and any benchmark‑availability issue).
  * Generate API reference `docs/api.md` for all public functions in `code/`.
  * Create `code/inference/metrics.py` (see T014) and accompanying unit tests.
  * Re‑run the full pipeline from clean `data/processed/` inputs; confirm that `final_report.json` is byte‑identical across runs (modulo timestamps) and that all pytest suites pass.
  * Update `quickstart.md` with a “paper‑hand‑off” section linking to figures and the summary markdown.
  * Verification: pytest green; re‑run reproduces `final_report.json`; handoff section present.

- [ ] T014 [US3] **Metrics Helper Module** –  
  * Implement `code/inference/metrics.py` exposing functions:
    - `compute_per_token_loss(logits, labels) -> float`
    - `compute_prediction_entropy(logits) -> float`
  * Include docstrings, type hints, and unit tests (`tests/unit/test_metrics.py`).
  * Verification: module imports without error; tests pass.

## Phase 3: Reproducibility Checks (implicit in previous tasks)

All tasks are deterministic, seeded, and produce Parquet artifacts that can be streamed on the runner. No task writes to `state/...` or performs silent synthetic fallbacks.

## Dependencies & Plan Alignment

| Requirement | Task(s) | Command |
|-------------|---------|---------|
| FR‑001 dataset download (streamed) | T002 | `python -m code.main --phase download` |
| FR‑002 static labels (CodeQL + tree‑sitter) | T003 | `--phase static` |
| FR‑003 frozen‑LLM inference (CPU) | T004 | `--phase inference` |
| FR‑004 Pearson/Spearman | T005 | `--phase correlation` |
| FR‑005 thresholds with covariates | T007 | `--phase thresholds` |
| FR‑006 sensitivity sweep | T008 | `--phase sensitivity` |
| FR‑007 permutation tests | T009 | `--phase significance` |
| FR‑008 multiple‑comparison correction | T009 | same |
| FR‑009 cross‑language validation | T010 | `--phase validation` |
| FR‑010 n‑gram normalization | T004 | part A/B |
| FR‑011 benchmark validation | T010 | mandatory |
| SC‑001/SC‑003 significance | T009 | |
| SC‑002 stability | T008 | |
| SC‑004 cross‑language consistency | T010 | |
| SC‑005 runtime constraints | T011 | |

**Execution Order** (enforced by `code/main.py`):
T001a → T001b → T002 → T003 → T004 (A → B) → T005 → {T006, T007} → T008 → T009 → T010 → T011 → T012 → T013 → T014.

All tasks respect data flow, storage constraints, and constitutional principles. New tasks address the previously identified panel concerns without weakening any functional requirement. 