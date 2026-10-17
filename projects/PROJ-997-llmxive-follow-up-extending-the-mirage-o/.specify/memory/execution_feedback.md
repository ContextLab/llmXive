# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/cli/run_proxy_loop.py: self-declared fabricated metric — “…on't have logits here,     we simulate the score based on the correctness of t…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/cli/run_proxy_loop.py: self-declared fabricated metric — “…on't have logits here,     we simulate the score based on the correctness of t…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/models/train_predictor.py --input data/processed/training_sample.parquet --output data/models/gap_predictor.pkl; python code/models/evaluate_predictor.py --model data/models/gap_predictor.pkl --data data/processed/training_sample.parquet --output data/metrics/metrics.json; 1 command(s) failed: python code/data/generate_ground_truth.py --model meta-llama/Meta-Llama-3-8B --levels INT4 INT8 FP8 --output data/processed/training_sample.parquet (rc=1); 1 declared deliverable(s) absent: data/processed/dataset_stats.json

## Failing / missing run-book commands

- python code/data/generate_ground_truth.py --model meta-llama/Meta-Llama-3-8B --levels INT4 INT8 FP8 --output data/processed/training_sample.parquet -> rc=1
uggingface.co/datasets/gsm8k/resolve/main/train.jsonl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/data/generate_ground_truth.py", line 209, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/data/generate_ground_truth.py", line 201, in main
    run_wrapper(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/data/generate_ground_truth.py", line 78, in run_wrapper
    subset = download_gsm8k_subset(sample_size)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_ground_truth.py", line 167, in download_gsm8k_subset
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://huggingface.co/datasets/openai/gsm8k/resolve/main/train.jsonl

- python code/models/train_predictor.py --input data/processed/training_sample.parquet --output data/models/gap_predictor.pkl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-997-llmxive-follow-up-extending-the-mirage-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/models/train_predictor.py': [Errno 2] No such file or directory

- python code/models/evaluate_predictor.py --model data/models/gap_predictor.pkl --data data/processed/training_sample.parquet --output data/metrics/metrics.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-997-llmxive-follow-up-extending-the-mirage-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/models/evaluate_predictor.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/dataset_stats.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dataset_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/cli/generate_ground_truth.py` — NOT invoked by the run-book
    - `code/cli/validate_dataset_stats.py` — NOT invoked by the run-book
    - `code/data/generate_ground_truth.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/dataset_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
