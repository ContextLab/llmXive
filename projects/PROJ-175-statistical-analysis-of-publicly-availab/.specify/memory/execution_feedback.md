# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluation/metrics.py: function `get_predictions` returns a bare RNG draw (line 49) — a reported value computed from no real input

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py --dataset recipe1m --output data/raw/`
- `python code/run_full_pipeline.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/metrics.py: function `get_predictions` returns a bare RNG draw (line 49) — a reported value computed from no real input; 6 command(s) failed: python code/data/download.py --dataset recipe1m --output data/raw/ (rc=1); python code/data/preprocess.py --input data/raw/ --output data/processed/ (rc=1); python code/data/split.py --input data/processed/ingredient_pairs.csv --output data/processed/ (rc=1); 13 declared deliverable(s) absent: data/logs/bayesian_results.json; data/logs/role_independence_audit.json; data/logs/vif_scores.json

## Failing / missing run-book commands

- python code/data/download.py --dataset recipe1m --output data/raw/ -> rc=1

INFO:__main__:Starting Recipe1M download via streaming...
INFO:httpx:HTTP Request: HEAD https://huggingface.co/datasets/recipe1m/recipe1m/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
ERROR:__main__:Failed to download Recipe1M: Dataset 'recipe1m/recipe1m' doesn't exist on the Hub or cannot be accessed.
INFO:__main__:Saved manifest for recipe1m: FAILED
ERROR:__main__:Pipeline halted due to: Recipe1M download failed: Dataset 'recipe1m/recipe1m' doesn't exist on the Hub or cannot be accessed.

- python code/data/preprocess.py --input data/raw/ --output data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/preprocess.py", line 28, in <module>
    from utils.memory_monitor import check_memory_limit, get_memory_usage_gb
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/utils/memory_monitor.py", line 3, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'

- python code/data/split.py --input data/processed/ingredient_pairs.csv --output data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/split.py", line 17, in <module>
    from code.utils.memory_monitor import check_memory_limit
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/utils/memory_monitor.py", line 3, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'

- python code/models/fit_logistic.py --input data/processed/train.csv --output data/logs/ -> rc=1
Starting Logistic Regression Fit (T022)...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_logistic.py", line 274, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_logistic.py", line 258, in main
    df = load_processed_data()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_logistic.py", line 26, in load_processed_data
    raise FileNotFoundError(f"train_set.parquet not found at {train_path}. Run T019 first.")
FileNotFoundError: train_set.parquet not found at /home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/processed/train_set.parquet. Run T019 first.

- python code/models/bayesian.py --input data/processed/train.csv --output data/logs/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/bayesian.py", line 31, in <module>
    from code.utils.memory_monitor import check_memory_limit
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/utils/memory_monitor.py", line 3, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'

- python code/run_full_pipeline.py -> rc=1

2026-10-09 19:35:06,789 - INFO - INITIALIZED: pipeline_start
2026-10-09 19:35:06,789 - INFO - Starting data pipeline...
2026-10-09 19:35:06,789 - INFO - Running: Download Recipe1M dataset
2026-10-09 19:35:06,789 - INFO - Command: python code/data/download.py --dataset recipe1m --output data/raw/
2026-10-09 19:35:07,038 - ERROR - Failed: Download Recipe1M dataset
2026-10-09 19:35:07,039 - ERROR - Error: ERROR:__main__:Failed to download Recipe1M: No module named 'datasets'
INFO:__main__:Saved manifest for recipe1m: FAILED
ERROR:__main__:Pipeline halted due to: Recipe1M download failed: No module named 'datasets'

2026-10-09 19:35:07,039 - INFO - FAILED: download
2026-10-09 19:35:07,039 - INFO - FAILED: pipeline_end


## Declared deliverables still missing

- data/logs/bayesian_results.json
- data/logs/role_independence_audit.json
- data/logs/vif_scores.json
- data/processed/co_occurrence_matrix.parquet
- data/processed/functional_roles.csv
- data/processed/functional_roles_validated.parquet
- data/processed/ingredient_pairs.csv
- data/processed/ingredient_pairs_with_labels.csv
- data/processed/normalized_ingredients.csv
- data/processed/similarity_scores_chemical.parquet
- data/processed/similarity_scores_embedding.parquet
- data/raw/recipe1m_processed.parquet
- data/raw/recipe1m_raw.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/bayesian_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/capture_metrics.py` — NOT invoked by the run-book
    - `code/models/bayesian.py` — IS a run-book command
    - `code/models/fit_bayesian.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/bayesian_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/role_independence_audit.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/functional_role_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/role_independence_audit.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/vif_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/capture_metrics.py` — NOT invoked by the run-book
    - `code/evaluation/vif_test_set.py` — NOT invoked by the run-book
    - `code/models/diagnostics.py` — NOT invoked by the run-book
    - `code/validate_execution_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/vif_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/co_occurrence_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/circularity_check.py` — NOT invoked by the run-book
    - `code/data/co_occurrence.py` — NOT invoked by the run-book
    - `code/data/derive_roles.py` — NOT invoked by the run-book
    - `code/data/functional_role_validation.py` — NOT invoked by the run-book
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/co_occurrence_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/functional_roles.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/circularity_check.py` — NOT invoked by the run-book
    - `code/data/co_occurrence.py` — NOT invoked by the run-book
    - `code/data/derive_roles.py` — NOT invoked by the run-book
    - `code/data/functional_role_validation.py` — NOT invoked by the run-book
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/functional_roles.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/functional_roles_validated.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/functional_role_validation.py` — NOT invoked by the run-book
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/functional_roles_validated.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingredient_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/audit/leakage_audit.py` — NOT invoked by the run-book
    - `code/data/co_occurrence.py` — NOT invoked by the run-book
    - `code/data/compute_similarity.py` — NOT invoked by the run-book
    - `code/data/derive_compatibility_labels.py` — NOT invoked by the run-book
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
    - `code/models/diagnostics.py` — NOT invoked by the run-book
    - `code/models/fit_bayesian.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ingredient_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingredient_pairs_with_labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/audit/leakage_audit.py` — NOT invoked by the run-book
    - `code/data/derive_compatibility_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ingredient_pairs_with_labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/normalized_ingredients.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/co_occurrence.py` — NOT invoked by the run-book
    - `code/data/compute_similarity.py` — NOT invoked by the run-book
    - `code/data/derive_roles.py` — NOT invoked by the run-book
    - `code/data/embeddings.py` — NOT invoked by the run-book
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
    - `code/data/normalize_ingredients.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/normalized_ingredients.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/similarity_scores_chemical.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/similarity_scores_chemical.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/similarity_scores_embedding.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/embeddings.py` — NOT invoked by the run-book
    - `code/data/impute_and_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/similarity_scores_embedding.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/recipe1m_processed.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/co_occurrence.py` — NOT invoked by the run-book
    - `code/data/derive_compatibility_labels.py` — NOT invoked by the run-book
    - `code/data/normalize_ingredients.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/stream_recipe1m.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/recipe1m_processed.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/recipe1m_raw.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — IS a run-book command
    - `code/data/normalize_ingredients.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/recipe1m_raw.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
