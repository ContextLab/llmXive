# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for neural rep…”
- code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…creates a deterministic synthetic dataset consisting of per‑subjec…”
- code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…"     Generate a list of synthetic records adhering to the input sc…”
- code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…n() -> None:     """     Generate the synthetic dataset and write it to…”
- code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…sum_path)     log.info(f"Synthetic data written to: {records_pat…”
- code/src/data/validator.py: synthetic/fake INPUT data not authorized by the spec — “…Input validator for the synthetic dataset.  The validator checks t…”
- code/src/main.py: synthetic/fake INPUT data not authorized by the spec — “…age: ingest — generating synthetic data")         loader.main()…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for neural rep…”; code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…creates a deterministic synthetic dataset consisting of per‑subjec…”; code/src/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…"     Generate a list of synthetic records adhering to the input sc…”; 4 command(s) failed: python -m code.src.data.loader (rc=1); python -m code.src.main --stage all (rc=1); python -m code.src.validation.synthetic --generate --validate (rc=1); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python -m code.src.data.loader -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/src/data/loader.py", line 22, in <module>
    from code.src.data import validator
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/src/data/validator.py", line 25, in <module>
    with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/specs/001-quantify-neural-representation-drift/contracts/input_schema.schema.yaml'

- python -m code.src.main --stage all -> rc=1

  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/src/main.py", line 11, in <module>
    from code.src.data import loader
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/src/data/loader.py", line 22, in <module>
    from code.src.data import validator
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/src/data/validator.py", line 25, in <module>
    with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-171-quantifying-neural-representation-drift-/code/specs/001-quantify-neural-representation-drift/contracts/input_schema.schema.yaml'

- python -m code.src.validation.synthetic --generate --validate -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-171-quantifying-neural-representation-drift-/bin/python: No module named code.src.validation.synthetic

- python -m code.src.validation.sensitivity --thresholds 0.70 0.75 0.80 0.85 0.90 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-171-quantifying-neural-representation-drift-/bin/python: No module named code.src.validation.sensitivity


## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/loader.py` — IS a run-book command
    - `code/tests/test_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
