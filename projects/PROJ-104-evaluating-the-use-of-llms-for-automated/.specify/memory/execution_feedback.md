# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…un the smoke test with a synthetic sample (ignores other stages)."…”
- data/repos/pandas/pandas/core/groupby/groupby.py: synthetic/fake INPUT data not authorized by the spec — “…index_sample = None  # Dummy sample          if isinstance(i…”
- data/repos/pandas/pandas/core/reshape/encoding.py: synthetic/fake INPUT data not authorized by the spec — “…al data decoded from the dummy input-data.      Raises     --…”
- data/repos/pandas/pandas/core/reshape/encoding.py: synthetic/fake INPUT data not authorized by the spec — “…`` ``data`` contains non-dummy data.         * When the pass…”
- data/repos/pandas/pandas/core/reshape/encoding.py: synthetic/fake INPUT data not authorized by the spec — “…he columns of the passed dummy data should only include 1's…”
- data/repos/pandas/pandas/core/reshape/encoding.py: synthetic/fake INPUT data not authorized by the spec — “…d DataFrame contains non-dummy data") from err      # collec…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/run_pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…un the smoke test with a synthetic sample (ignores other stages)."…”; data/repos/pandas/pandas/core/groupby/groupby.py: synthetic/fake INPUT data not authorized by the spec — “…index_sample = None  # Dummy sample          if isinstance(i…”; data/repos/pandas/pandas/core/reshape/encoding.py: synthetic/fake INPUT data not authorized by the spec — “…al data decoded from the dummy input-data.      Raises     --…”; 2 command(s) failed: python -m code.run_pipeline --sample 5 (rc=1); python -m pytest tests/quickstart_test.py tests/test_power_analysis.py (rc=1); 1 declared deliverable(s) absent: data/gold_standard/annotations.json

## Failing / missing run-book commands

- python -m code.run_pipeline --sample 5 -> rc=1

2026-10-17 07:13:34,083 INFO __main__: Running smoke test with 5 sample(s)
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 89, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 80, in main
    return run_smoke_test()
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 24, in run_smoke_test
    pair = CommitPair(
           ^^^^^^^^^^^
TypeError: CommitPair.__init__() got an unexpected keyword argument 'doc_diff'

- python -m pytest tests/quickstart_test.py tests/test_power_analysis.py -> rc=1
___________________ test_smoke_test ________________________________

    def test_smoke_test():
        """Run the smoke test and verify the placeholder file exists."""
        result = subprocess.run(
>           [sys.executable, "-m", "code.run_pipeline", "--sample", "1"],
            capture_output=True,
            text=True,
        )
E       NameError: name 'sys' is not defined

tests/quickstart_test.py:12: NameError
______________________________ test_full_pipeline ______________________________

    def test_full_pipeline():
        """Run the full pipeline and verify that the commit‑pair CSV is created."""
        result = subprocess.run(
>           [sys.executable, "-m", "code.run_pipeline", "--full"],
            capture_output=True,
            text=True,
        )
E       NameError: name 'sys' is not defined

tests/quickstart_test.py:23: NameError
=========================== short test summary info ============================
FAILED tests/quickstart_test.py::test_smoke_test - NameError: name 'sys' is n...
FAILED tests/quickstart_test.py::test_full_pipeline - NameError: name 'sys' i...
========================= 2 failed, 5 passed in 5.30s ==========================



## Declared deliverables still missing

- data/gold_standard/annotations.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/gold_standard/annotations.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/generation.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
    - `code/power_analysis.py` — IS a run-book command
    - `code/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/gold_standard/annotations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
