# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/03_train.py: function `generate_bert_embeddings` returns a bare RNG draw (line 28) — a reported value computed from no real input
- code/04_inference.py: function `embed_prompt` returns a bare RNG draw (line 30) — a reported value computed from no real input
- code/04_inference.py: function `sample_trajectory_from_cgmm` returns a bare RNG draw (line 39) — a reported value computed from no real input
- code/02_train_models.py: synthetic/fake INPUT data not authorized by the spec — “…eck logic.     # We will mock the data loading if columns are m…”
- code/069_run_fabrication_check.py: synthetic/fake INPUT data not authorized by the spec — “…indicators of synthetic/fake data.     Returns False if sy…”
- code/069_run_fabrication_check.py: synthetic/fake INPUT data not authorized by the spec — “…abrication check FAILED. Synthetic data or missing artifacts det…”
- code/utils/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…(try/except blocks that generate synthetic data) and ensures that a…”
- code/utils/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…ding with     missing or synthetic data.     """     def __init_…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/04_simulate_eval.py  --models-dir artifacts/models  --baseline data/processed/vla_proxy_baseline.parquet  --output-dir data/results  --seed 42`
  - script usage: `04_simulate_eval.py [-h] [--config CONFIG] [--seed SEED]`
  - argparse error: `04_simulate_eval.py: error: unrecognized arguments: --models-dir artifacts/models --baseline data/processed/vla_proxy_baseline.parquet --output-dir data/results`
- run-book command: `python code/08_generate_report.py  --results-dir data/results  --models-dir artifacts/models  --output data/results/evaluation_report.md`
  - script usage: `08_generate_report.py [-h]`
  - argparse error: `08_generate_report.py: error: unrecognized arguments: --results-dir data/results --models-dir artifacts/models --output data/results/evaluation_report.md`
- run-book command: `python code/09_run_final_validation.py  --dataset qwen-vla/Hy-Embodied  --baseline data/processed/vla_proxy_baseline.parquet  --output-dir data/results  --seed 42`
  - script usage: `09_run_final_validation.py [-h] [--log-file LOG_FILE] [--seed SEED]`
  - argparse error: `09_run_final_validation.py: error: unrecognized arguments: --dataset qwen-vla/Hy-Embodied --baseline data/processed/vla_proxy_baseline.parquet --output-dir data/results`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 fabricated/simulated-result signal(s) — results are not real measurements: code/03_train.py: function `generate_bert_embeddings` returns a bare RNG draw (line 28) — a reported value computed from no real input; code/04_inference.py: function `embed_prompt` returns a bare RNG draw (line 30) — a reported value computed from no real input; code/04_inference.py: function `sample_trajectory_from_cgmm` returns a bare RNG draw (line 39) — a reported value computed from no real input; 5 command(s) failed: python code/01_ingest_cluster.py  --dataset qwen-vla/Hy-Embodied  --output-dir data/processed  --silhouette-threshold 0.25  --k-reduction-step 1  --max-iterations 50  --download               # forces dataset download; will fail loudly if unreachable (rc=1); python code/02_train_models.py  --embeddings data/processed/train_embeddings.parquet  --assignments data/processed/assignments.parquet  --clusters data/processed/clusters.json  --output-dir artifacts/models  --r2-threshold 0.6  --inference-time-threshold 2.0  --seed 42 (rc=1); python code/04_simulate_eval.py  --models-dir artifacts/models  --baseline data/processed/vla_proxy_baseline.parquet  --output-dir data/results  --seed 42 (rc=2); 12 declared deliverable(s) absent: data/processed/assignments.parquet; data/processed/clusters.json; data/processed/embedding_verification.json

## Failing / missing run-book commands

- python code/01_ingest_cluster.py  --dataset qwen-vla/Hy-Embodied  --output-dir data/processed  --silhouette-threshold 0.25  --k-reduction-step 1  --max-iterations 50  --download               # forces dataset download; will fail loudly if unreachable -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni/code/01_ingest_cluster.py", line 11, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'

- python code/02_train_models.py  --embeddings data/processed/train_embeddings.parquet  --assignments data/processed/assignments.parquet  --clusters data/processed/clusters.json  --output-dir artifacts/models  --r2-threshold 0.6  --inference-time-threshold 2.0  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-962-llmxive-follow-up-extending-qwen-vla-uni/code/02_train_models.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/04_simulate_eval.py  --models-dir artifacts/models  --baseline data/processed/vla_proxy_baseline.parquet  --output-dir data/results  --seed 42 -> rc=2

usage: 04_simulate_eval.py [-h] [--config CONFIG] [--seed SEED]
04_simulate_eval.py: error: unrecognized arguments: --models-dir artifacts/models --baseline data/processed/vla_proxy_baseline.parquet --output-dir data/results

- python code/08_generate_report.py  --results-dir data/results  --models-dir artifacts/models  --output data/results/evaluation_report.md -> rc=2

usage: 08_generate_report.py [-h]
08_generate_report.py: error: unrecognized arguments: --results-dir data/results --models-dir artifacts/models --output data/results/evaluation_report.md

- python code/09_run_final_validation.py  --dataset qwen-vla/Hy-Embodied  --baseline data/processed/vla_proxy_baseline.parquet  --output-dir data/results  --seed 42 -> rc=2

usage: 09_run_final_validation.py [-h] [--log-file LOG_FILE] [--seed SEED]
09_run_final_validation.py: error: unrecognized arguments: --dataset qwen-vla/Hy-Embodied --baseline data/processed/vla_proxy_baseline.parquet --output-dir data/results


## Declared deliverables still missing

- data/processed/assignments.parquet
- data/processed/clusters.json
- data/processed/embedding_verification.json
- data/processed/streaming_stats.json
- data/processed/train_embeddings.parquet
- data/processed/vla_proxy_baseline.parquet
- data/results/coverage_report.json
- data/results/fidelity_metrics.json
- data/results/fidelity_scores_per_sample.json
- data/results/inference_benchmark.csv
- data/results/memory_profile_e2e.json
- data/results/simulation_logs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/assignments.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_cluster.py` — IS a run-book command
    - `code/02_train_models.py` — IS a run-book command
    - `code/03_train.py` — NOT invoked by the run-book
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/07_verify_coverage.py` — NOT invoked by the run-book
    - `code/09_run_final_validation.py` — IS a run-book command
    - `code/tests/test_cluster.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/assignments.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/clusters.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_cluster.py` — IS a run-book command
    - `code/02_cluster.py` — NOT invoked by the run-book
    - `code/02_train_models.py` — IS a run-book command
    - `code/03_train.py` — NOT invoked by the run-book
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/07_verify_coverage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clusters.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/embedding_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/embedding_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/streaming_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/streaming_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_embeddings.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/02_train_models.py` — IS a run-book command
    - `code/03_train.py` — NOT invoked by the run-book
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/09_run_final_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/train_embeddings.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vla_proxy_baseline.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/04_simulate_eval.py` — IS a run-book command
    - `code/05_simulate.py` — NOT invoked by the run-book
    - `code/068_run_simulation_validation.py` — NOT invoked by the run-book
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/07_calculate_fidelity.py` — NOT invoked by the run-book
    - `code/09_run_final_validation.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vla_proxy_baseline.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/coverage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_cluster.py` — IS a run-book command
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/072_generate_success_checklist.py` — NOT invoked by the run-book
    - `code/07_verify_coverage.py` — NOT invoked by the run-book
    - `code/09_run_final_validation.py` — IS a run-book command
    - `code/tests/test_t066_streaming_validation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/coverage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/072_generate_success_checklist.py` — NOT invoked by the run-book
    - `code/07_calculate_fidelity.py` — NOT invoked by the run-book
    - `code/08_generate_report.py` — IS a run-book command
    - `code/09_run_final_validation.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fidelity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_scores_per_sample.json` is declared but was NOT written. Scripts referencing it:
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/072_generate_success_checklist.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fidelity_scores_per_sample.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/inference_benchmark.csv` is declared but was NOT written. Scripts referencing it:
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/09_run_final_validation.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/inference_benchmark.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/memory_profile_e2e.json` is declared but was NOT written. Scripts referencing it:
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/072_generate_success_checklist.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/memory_profile_e2e.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/simulation_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_simulate_eval.py` — IS a run-book command
    - `code/05_simulate.py` — NOT invoked by the run-book
    - `code/068_run_simulation_validation.py` — NOT invoked by the run-book
    - `code/069_run_fabrication_check.py` — NOT invoked by the run-book
    - `code/06_evaluate.py` — NOT invoked by the run-book
    - `code/071_run_final_validation.py` — NOT invoked by the run-book
    - `code/072_generate_success_checklist.py` — NOT invoked by the run-book
    - `code/07_calculate_fidelity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/simulation_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
