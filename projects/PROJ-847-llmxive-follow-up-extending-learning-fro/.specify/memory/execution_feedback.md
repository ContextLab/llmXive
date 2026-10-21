# Execution failures — fix these before the analysis can run

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json (rc=1); python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/adaptive_run.json (rc=1); python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/control_shuffle.json (rc=1)

## Failing / missing run-book commands

- python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json -> rc=1
, line 120, in _run_fixed_mode
    run_fixed_baselines(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/trainer.py", line 149, in run_fixed_baselines
    model = load_diffusion_model()
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/model.py", line 71, in load_diffusion_model
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="cpu")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/transformers/models/auto/auto_factory.py", line 563, in from_pretrained
    return model_class.from_pretrained(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/transformers/modeling_utils.py", line 3122, in from_pretrained
    raise ImportError(
ImportError: Using `low_cpu_mem_usage=True` or a `device_map` requires Accelerate: `pip install accelerate`

- python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/adaptive_run.json -> rc=1

2026-10-21 16:10:49,761 WARNING code.run_experiments: Adaptive mode is not yet implemented (T006).

- python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/control_shuffle.json -> rc=1

2026-10-21 16:10:51,567 WARNING code.run_experiments: Control-shuffle mode is not yet implemented (T007).

