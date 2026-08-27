# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…a forward pass with dummy inputs to ensure no CUDA calls…”
- code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…=2, help='Batch size for dummy input')     parser.add_argumen…”
- code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…# Create dummy inputs on CPU         batch_siz…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…a forward pass with dummy inputs to ensure no CUDA calls…”; code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…=2, help='Batch size for dummy input')     parser.add_argumen…”; code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…# Create dummy inputs on CPU         batch_siz…”; 1 command(s) failed: python code/scripts/run_full_benchmark.py --mode benchmark --subset-size 500 (rc=1); 7 declared deliverable(s) absent: data/processed/fidelity_report.json; data/processed/filtered_subset_manifest.json; data/processed/latency_verification_report.json

## Failing / missing run-book commands

- python code/scripts/run_full_benchmark.py --mode benchmark --subset-size 500 -> rc=1
    in main
    run_text_adapter_pipeline_with_bottleneck_analysis(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-829-llmxive-follow-up-extending-fashionchame/code/src/pipeline/runner.py", line 141, in run_text_adapter_pipeline_with_bottleneck_analysis
    adapter = TextCrossAttentionAdapter(config) # Assuming config has necessary params
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-829-llmxive-follow-up-extending-fashionchame/code/src/adapters/text_cross_attention.py", line 34, in __init__
    self.text_projection = nn.Linear(text_dim, hidden_dim, device=device)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-829-llmxive-follow-up-extending-fashionchame/code/.venv/lib/python3.11/site-packages/torch/nn/modules/linear.py", line 98, in __init__
    self.weight = Parameter(torch.empty((out_features, in_features), **factory_kwargs))
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: empty(): argument 'size' failed to unpack the object at pos 2 with error "type must be tuple of ints,but got dict"

## Declared deliverables still missing

- data/processed/fidelity_report.json
- data/processed/filtered_subset_manifest.json
- data/processed/latency_verification_report.json
- data/processed/manifest.json
- data/processed/motion_labels.json
- data/processed/sensitivity_analysis.csv
- data/processed/stratified_subset_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/fidelity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fidelity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_subset_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/stratified_subset.py` — NOT invoked by the run-book
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/runner.py` — NOT invoked by the run-book
    - `code/scripts/verify_runner_6h_cpu.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_subset_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/latency_verification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/metrics/latency.py` — NOT invoked by the run-book
    - `code/src/pipeline/runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/latency_verification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/feasibility_filter.py` — NOT invoked by the run-book
    - `code/src/data/stratified_subset.py` — NOT invoked by the run-book
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/manifest.py` — NOT invoked by the run-book
    - `code/src/pipeline/runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/reporter.py` — NOT invoked by the run-book
    - `code/tests/unit/test_runner_6h_verification.py` — NOT invoked by the run-book
    - `code/scripts/verify_runner_6h_cpu.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/motion_labels.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats/sensitivity.py` — NOT invoked by the run-book
    - `code/src/stats/motion_labels.py` — NOT invoked by the run-book
    - `code/tests/unit/test_motion_labels.py` — NOT invoked by the run-book
    - `code/scripts/run_motion_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/motion_labels.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats/sensitivity.py` — NOT invoked by the run-book
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stratified_subset_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/stratified_subset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stratified_subset_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
