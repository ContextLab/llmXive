# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/inference/hybrid_sim.py: metric `latency_reduction` assigned from an RNG draw (line 206)
- code/data/extract_latents.py: synthetic/fake INPUT data not authorized by the spec — “…used.         # Here we generate a synthetic latent vector based on a…”
- code/models/gru_estimator.py: synthetic/fake INPUT data not authorized by the spec — “…n{model}")          # 3. Dummy Data Generation for Verificat…”
- code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…...")          # Prepare dummy input based on sample data str…”
- code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…al()          # Create a dummy input for tracing         # Sh…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/extract_latents.py --source voxceleb2`
  - script usage: `extract_latents.py [-h] [--seed SEED]`
  - argparse error: `extract_latents.py: error: unrecognized arguments: --source voxceleb2`
- run-book command: `python code/models/trainer.py --input data/processed/train.parquet --epochs [specified number of training epochs]`
  - script usage: `trainer.py [-h] [--config CONFIG] [--train_data TRAIN_DATA]`
  - argparse error: `trainer.py: error: unrecognized arguments: --input data/processed/train.parquet --epochs [specified number of training epochs]`
- run-book command: `python code/inference/hybrid_sim.py --model data/artifacts/model.pt --data data/processed/val.parquet`
  - script usage: `hybrid_sim.py [-h] [--config CONFIG] [--dataset DATASET]`
  - argparse error: `hybrid_sim.py: error: unrecognized arguments: --model data/artifacts/model.pt`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/inference/hybrid_sim.py: metric `latency_reduction` assigned from an RNG draw (line 206); code/data/extract_latents.py: synthetic/fake INPUT data not authorized by the spec — “…used.         # Here we generate a synthetic latent vector based on a…”; code/models/gru_estimator.py: synthetic/fake INPUT data not authorized by the spec — “…n{model}")          # 3. Dummy Data Generation for Verificat…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/metrics/stats_tests.py --input data/artifacts/simulation_metrics.parquet; python code/utils/state_manager.py --update; 4 command(s) failed: python code/data/extract_latents.py --source voxceleb2 (rc=2); python code/data/validate_sampling.py --input data/processed/extracted.parquet (rc=1); python code/models/trainer.py --input data/processed/train.parquet --epochs [specified number of training epochs] (rc=2); 9 declared deliverable(s) absent: data/metrics/human_data_status.json; data/metrics/latency_bootstrap_results.csv; data/metrics/power_analysis_initial.json

## Failing / missing run-book commands

- python code/data/extract_latents.py --source voxceleb2 -> rc=2
    usage: extract_latents.py [-h] [--seed SEED]
extract_latents.py: error: unrecognized arguments: --source voxceleb2
- python code/data/validate_sampling.py --input data/processed/extracted.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/data/validate_sampling.py", line 130, in <module>
    output_path: Optional[Path] = None
                 ^^^^^^^^
NameError: name 'Optional' is not defined
- python code/models/trainer.py --input data/processed/train.parquet --epochs [specified number of training epochs] -> rc=2
    usage: trainer.py [-h] [--config CONFIG] [--train_data TRAIN_DATA]
                  [--val_data VAL_DATA] [--output OUTPUT]
trainer.py: error: unrecognized arguments: --input data/processed/train.parquet --epochs [specified number of training epochs]
- python code/inference/hybrid_sim.py --model data/artifacts/model.pt --data data/processed/val.parquet -> rc=2
    usage: hybrid_sim.py [-h] [--config CONFIG] [--dataset DATASET]
                     [--counterfactual COUNTERFACTUAL]
                     [--checkpoint CHECKPOINT] [--output OUTPUT] [--seed SEED]
hybrid_sim.py: error: unrecognized arguments: --model data/artifacts/model.pt
- python code/metrics/stats_tests.py --input data/artifacts/simulation_metrics.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/metrics/stats_tests.py': [Errno 2] No such file or directory
- python code/utils/state_manager.py --update -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/utils/state_manager.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/metrics/human_data_status.json
- data/metrics/latency_bootstrap_results.csv
- data/metrics/power_analysis_initial.json
- data/metrics/tost_results.csv
- data/processed/counterfactual_indices.parquet
- data/processed/hybrid_output.parquet
- data/processed/raw_extract.parquet
- data/processed/sampled_dataset.parquet
- data/raw/human_ratings.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/human_data_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/check_human_ratings.py` — NOT invoked by the run-book
    - `code/metrics/validate_proxy_mos.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/human_data_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/latency_bootstrap_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/inference/analyze_latency_bias.py` — NOT invoked by the run-book
    - `code/tests/integration/test_hybrid_simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/latency_bootstrap_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/power_analysis_initial.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/update_power_analysis_with_literature.py` — NOT invoked by the run-book
    - `code/tasks/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/power_analysis_initial.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/tost_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_hybrid_simulation.py` — NOT invoked by the run-book
    - `code/utils/validators.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/metrics/tost_equivalence.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/tost_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/counterfactual_indices.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/inference/hybrid_sim.py` — IS a run-book command
    - `code/inference/precedence_rule.py` — NOT invoked by the run-book
    - `code/inference/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/inference/fallback_handler.py` — NOT invoked by the run-book
    - `code/inference/fallback_logic_handler.py` — NOT invoked by the run-book
    - `code/data/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/tests/integration/test_hybrid_simulation.py` — NOT invoked by the run-book
    - `code/tasks/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/counterfactual_indices.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/hybrid_output.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/inference/hybrid_sim.py` — IS a run-book command
    - `code/inference/analyze_latency_bias.py` — NOT invoked by the run-book
    - `code/tests/integration/test_hybrid_simulation.py` — NOT invoked by the run-book
    - `code/metrics/tost_equivalence.py` — NOT invoked by the run-book
    - `code/metrics/validate_proxy_mos.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/hybrid_output.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_extract.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/generate_power_analysis.py` — NOT invoked by the run-book
    - `code/tasks/validate_thresholds.py` — NOT invoked by the run-book
    - `code/tasks/calibrate_thresholds.py` — NOT invoked by the run-book
    - `code/tasks/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_extract.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sampled_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/models/trainer.py` — IS a run-book command
    - `code/inference/hybrid_sim.py` — IS a run-book command
    - `code/inference/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/inference/fallback_handler.py` — NOT invoked by the run-book
    - `code/inference/fallback_logic_handler.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/tests/integration/test_hybrid_simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sampled_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/human_ratings.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/check_human_ratings.py` — NOT invoked by the run-book
    - `code/metrics/validate_proxy_mos.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/human_ratings.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
