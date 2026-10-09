# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…cution halted to prevent synthetic data fabrication.")…”
- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…s this check or generate fake data.\n"             "=" * 70…”
- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…ta requirement disabled. Synthetic data generation is permitted.…”
- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…line configured to allow synthetic data.")  def main():     """…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…oad real NAB/UCI data OR generate synthetic time-series via `synthpo…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic time-series data mimicki…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic data to {output_path}")     r…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…a is False or fails,     generates synthetic data. Validates the resu…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 20 fabricated/simulated-result signal(s) — results are not real measurements: code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…cution halted to prevent synthetic data fabrication.")…”; code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…s this check or generate fake data.\n"             "=" * 70…”; code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…ta requirement disabled. Synthetic data generation is permitted.…”; 9 command(s) failed: python code/extract_features.py --mode simulate --n 500 --signal (rc=1); python code/extract_features.py --mode simulate --n 500 --null (rc=1); python code/compute_metrics.py (rc=1); 5 declared deliverable(s) absent: data/processed/clean_features.csv; data/processed/metrics.csv; data/processed/raw_facial_features.csv

## Failing / missing run-book commands

- python -c "import openface; import librosa; import statsmodels; import synthpop; print('Dependencies OK')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'openface'

- python code/extract_features.py --mode simulate --n 500 --signal -> rc=1
-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py", line 237, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py", line 197, in main
    generated = generate_synthetic_media_batch(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/synthetic_media_gen.py", line 119, in generate_synthetic_media_batch
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 548, in run
    with Popen(*popenargs, **kwargs) as process:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 1026, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 1955, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'

- python code/extract_features.py --mode simulate --n 500 --null -> rc=1
-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py", line 237, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py", line 197, in main
    generated = generate_synthetic_media_batch(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/synthetic_media_gen.py", line 119, in generate_synthetic_media_batch
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 548, in run
    with Popen(*popenargs, **kwargs) as process:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 1026, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 1955, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'

- python code/compute_metrics.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 246, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 177, in main
    log_pipeline_start("T015_compute_metrics")
TypeError: log_pipeline_start() takes 0 positional arguments but 1 was given

- python code/analyze.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/analyze.py", line 319, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/analyze.py", line 216, in main
    logger.log_operation("analysis_failed", reason="Input file not found", path=args.input)
    ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'log_operation'

- python code/visualize.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 265, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 256, in main
    data = load_data(input_path)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 98, in load_data
    raise FileNotFoundError(f"Data file not found: {filepath}")
FileNotFoundError: Data file not found: data/processed/clean_features.csv

- python code/extract_features.py --mode real -> rc=1
2026-10-09 22:17:13,480 - __main__ - INFO - Scanning data/raw for existing media.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py", line 237, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py", line 213, in main
    audio_files = find_audio_files("data/raw")
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: find_audio_files() takes 0 positional arguments but 1 was given

- python code/compute_metrics.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 246, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 177, in main
    log_pipeline_start("T015_compute_metrics")
TypeError: log_pipeline_start() takes 0 positional arguments but 1 was given

- python code/analyze.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/analyze.py", line 319, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/analyze.py", line 216, in main
    logger.log_operation("analysis_failed", reason="Input file not found", path=args.input)
    ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'log_operation'

- python code/visualize.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 265, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 256, in main
    data = load_data(input_path)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 98, in load_data
    raise FileNotFoundError(f"Data file not found: {filepath}")
FileNotFoundError: Data file not found: data/processed/clean_features.csv


## Declared deliverables still missing

- data/processed/clean_features.csv
- data/processed/metrics.csv
- data/processed/raw_facial_features.csv
- data/processed/raw_vocal_features.csv
- data/processed/synthetic_features.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clean_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_metrics.py` — IS a run-book command
    - `code/visualize.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/clean_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/benchmark.py` — NOT invoked by the run-book
    - `code/compute_metrics.py` — IS a run-book command
    - `code/extract_facial.py` — NOT invoked by the run-book
    - `code/extract_features.py` — IS a run-book command
    - `code/generate_unified_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_facial_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extract_facial.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_facial_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_vocal_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extract_vocal.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_vocal_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_metrics.py` — IS a run-book command
    - `code/extract_facial.py` — NOT invoked by the run-book
    - `code/extract_vocal.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synthetic_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
