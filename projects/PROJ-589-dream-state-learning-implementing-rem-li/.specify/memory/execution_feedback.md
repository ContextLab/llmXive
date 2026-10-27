# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/eval.py: self-declared fabricated metric — “…oss on the QNLI inputs)   * a dummy accuracy metric (token‑level match rat…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/eval.py: self-declared fabricated metric — “…oss on the QNLI inputs)   * a dummy accuracy metric (token‑level match rat…”; 4 command(s) failed: python code/train.py  --seed 42  --total_steps 20  --warmup_steps 5  --ratio 4:1  --mode debug (rc=1); python code/train.py  --seeds 0,1,2  --total_steps 100  --warmup_steps 20  --ratio 4:1  --temp 1.0  --baseline (rc=1); python code/train.py  --seeds 3,4  --total_steps 100  --warmup_steps 20  --ratio 4:1  --temp_sweep 0.5 1.0 1.5 2.0  --baseline (rc=1)

## Failing / missing run-book commands

- python code/train.py  --seed 42  --total_steps 20  --warmup_steps 5  --ratio 4:1  --mode debug -> rc=1
9-dream-state-learning-implementing-rem-li/code/train.py", line 240, in main
    run_one(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 139, in run_one
    tokenizer = DistilBertTokenizerFast.from_pretrained(cfg.model_name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/tokenization_utils_base.py", line 2010, in from_pretrained
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/utils/hub.py", line 421, in cached_file
    raise EnvironmentError(
OSError: sshleifer/tiny-distilbert-base-uncased is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`

- python code/train.py  --seeds 0,1,2  --total_steps 100  --warmup_steps 20  --ratio 4:1  --temp 1.0  --baseline -> rc=1
9-dream-state-learning-implementing-rem-li/code/train.py", line 240, in main
    run_one(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 139, in run_one
    tokenizer = DistilBertTokenizerFast.from_pretrained(cfg.model_name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/tokenization_utils_base.py", line 2010, in from_pretrained
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/utils/hub.py", line 421, in cached_file
    raise EnvironmentError(
OSError: sshleifer/tiny-distilbert-base-uncased is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`

- python code/train.py  --seeds 3,4  --total_steps 100  --warmup_steps 20  --ratio 4:1  --temp_sweep 0.5 1.0 1.5 2.0  --baseline -> rc=1
9-dream-state-learning-implementing-rem-li/code/train.py", line 240, in main
    run_one(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 139, in run_one
    tokenizer = DistilBertTokenizerFast.from_pretrained(cfg.model_name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/tokenization_utils_base.py", line 2010, in from_pretrained
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/utils/hub.py", line 421, in cached_file
    raise EnvironmentError(
OSError: sshleifer/tiny-distilbert-base-uncased is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`

- python code/eval.py --results_dir data/results/ -> rc=1
_checkpoint
    model = _load_checkpoint(checkpoint_path)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 52, in _load_checkpoint
    model = DistilBertForMaskedLM.from_pretrained(cfg.model_name)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/modeling_utils.py", line 3015, in from_pretrained
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/transformers/utils/hub.py", line 421, in cached_file
    raise EnvironmentError(
OSError: sshleifer/tiny-distilbert-base-uncased is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `huggingface-cli login` or by passing `token=<your_token>`

