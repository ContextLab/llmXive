# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/correlation_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…task requirements      # Simulated data for demonstration     #…”
- code/train.py: synthetic/fake INPUT data not authorized by the spec — “…device          # Create dummy input     dummy_input = torch.…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_loader.py --download-only`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/correlation_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…task requirements      # Simulated data for demonstration     #…”; code/train.py: synthetic/fake INPUT data not authorized by the spec — “…device          # Create dummy input     dummy_input = torch.…”; 5 command(s) failed: python code/data_loader.py --download-only (rc=1); python code/train.py --config code/config.py (rc=1); python code/eval.py --checkpoint code/codebook.pt (rc=1); 8 declared deliverable(s) absent: data/raw/checksums.json; data/results/correlation_plot.png; data/results/embeddings_high_res.h5

## Failing / missing run-book commands

- python code/data_loader.py --download-only -> rc=1
tFoundError(message) from e
datasets.exceptions.DatasetNotFoundError: Dataset 'imagenet-1k' is a gated dataset on the Hub. You must be authenticated to access it.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/data_loader.py", line 230, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/data_loader.py", line 138, in main
    it = get_imagenet_iterator(split="validation", streaming=True)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/data_loader.py", line 100, in get_imagenet_iterator
    raise RuntimeError(f"Failed to load ImageNet-1K dataset. Ensure internet connectivity and correct dataset ID. Error: {str(e)}") from e
RuntimeError: Failed to load ImageNet-1K dataset. Ensure internet connectivity and correct dataset ID. Error: Dataset 'imagenet-1k' is a gated dataset on the Hub. You must be authenticated to access it.

- python code/train.py --config code/config.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/train.py", line 12, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'

- python code/eval.py --checkpoint code/codebook.pt -> rc=1
put=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/.venv/bin/python', 'code/train.py', '--config', 'code/config.py']' returned non-zero exit status 1.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py", line 123, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py", line 88, in main
    run_command(train_cmd, "Training (Codebook Initialization)")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py", line 35, in run_command
    raise RuntimeError(f"Pipeline step failed: {description}") from e
RuntimeError: Pipeline step failed: Training (Codebook Initialization)

- python code/analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/analysis.py", line 26, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'

- python -m pytest tests/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/raw/checksums.json
- data/results/correlation_plot.png
- data/results/embeddings_high_res.h5
- data/results/fidelity_metrics.json
- data/results/semantic_baseline.json
- data/results/semantic_diff.json
- data/results/semantic_high_res.json
- data/results/train_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/extract_native_images.py` — NOT invoked by the run-book
    - `code/verify_data_integrity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_analysis.py` — NOT invoked by the run-book
    - `code/eval.py` — IS a run-book command
  Make ONE of these WRITE `data/results/correlation_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/embeddings_high_res.h5` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_fidelity_metrics.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/eval.py` — IS a run-book command
    - `code/eval_high_res.py` — NOT invoked by the run-book
    - `code/eval_semantic.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/embeddings_high_res.h5` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_fidelity_metrics.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_analysis.py` — NOT invoked by the run-book
    - `code/eval.py` — IS a run-book command
  Make ONE of these WRITE `data/results/fidelity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/semantic_baseline.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/semantic_diff_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/semantic_baseline.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/semantic_diff.json` is declared but was NOT written. Scripts referencing it:
    - `code/semantic_diff_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/semantic_diff.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/semantic_high_res.json` is declared but was NOT written. Scripts referencing it:
    - `code/eval_semantic.py` — NOT invoked by the run-book
    - `code/semantic_diff_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/semantic_high_res.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/train_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/results/train_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
