# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/data/inject.py: metric `mass_ratio` assigned from an RNG draw (line 74)
- code/provenance/deviation_LALInference_Bilby.md: synthetic/fake INPUT data not authorized by the spec — “…terior estimates for the synthetic injection data used in this study, whil…”
- code/provenance/deviation_constitution_principle_ii.md: synthetic/fake INPUT data not authorized by the spec — “…the system will instead generate synthetic injections into real GW…”
- code/spec.md: synthetic/fake INPUT data not authorized by the spec — “…GWOSC. 2. **Injection**: Generate synthetic CBC signals with known g…”
- code/src/data/inject.py: synthetic/fake INPUT data not authorized by the spec — “…plements Amended FR-001: Generates synthetic Compact Binary Coalescen…”
- code/src/pe/compare_posteriors.py: synthetic/fake INPUT data not authorized by the spec — “…ule Loaded.")          # Mock data for demonstration if run…”
- src/data/inject.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generates a synthetic CBC waveform using LALSi…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/src/data/inject.py: metric `mass_ratio` assigned from an RNG draw (line 74); code/provenance/deviation_LALInference_Bilby.md: synthetic/fake INPUT data not authorized by the spec — “…terior estimates for the synthetic injection data used in this study, whil…”; code/provenance/deviation_constitution_principle_ii.md: synthetic/fake INPUT data not authorized by the spec — “…the system will instead generate synthetic injections into real GW…”; 6 command(s) failed: python code/tests/unit/test_compression_main.py --step download --count 15 (rc=1); python code/tests/unit/test_compression_main.py --step compress --methods all (rc=1); python code/tests/unit/test_compression_main.py --step pe --events 12 (rc=1); 3 declared deliverable(s) absent: data/external/baseline_bias_original.json; data/interim/valid_events.json; data/processed/statistical_test_results.json

## Failing / missing run-book commands

- python code/tests/unit/test_compression_main.py --step download --count 15 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/tests/unit/test_compression_main.py", line 16, in <module>
    from src.compression.main import load_validated_event, process_single_event, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/main.py", line 19, in <module>
    from src.compression.lossless import compress_gzip, decompress_gzip, compress_bzip2, decompress_bzip2, compress_lzma, decompress_lzma
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/lossless.py", line 11, in <module>
    import lz4.frame
ModuleNotFoundError: No module named 'lz4'

- python code/tests/unit/test_compression_main.py --step compress --methods all -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/tests/unit/test_compression_main.py", line 16, in <module>
    from src.compression.main import load_validated_event, process_single_event, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/main.py", line 19, in <module>
    from src.compression.lossless import compress_gzip, decompress_gzip, compress_bzip2, decompress_bzip2, compress_lzma, decompress_lzma
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/lossless.py", line 11, in <module>
    import lz4.frame
ModuleNotFoundError: No module named 'lz4'

- python code/tests/unit/test_compression_main.py --step pe --events 12 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/tests/unit/test_compression_main.py", line 16, in <module>
    from src.compression.main import load_validated_event, process_single_event, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/main.py", line 19, in <module>
    from src.compression.lossless import compress_gzip, decompress_gzip, compress_bzip2, decompress_bzip2, compress_lzma, decompress_lzma
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/lossless.py", line 11, in <module>
    import lz4.frame
ModuleNotFoundError: No module named 'lz4'

- python code/tests/unit/test_compression_main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/tests/unit/test_compression_main.py", line 16, in <module>
    from src.compression.main import load_validated_event, process_single_event, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/main.py", line 19, in <module>
    from src.compression.lossless import compress_gzip, decompress_gzip, compress_bzip2, decompress_bzip2, compress_lzma, decompress_lzma
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/src/compression/lossless.py", line 11, in <module>
    import lz4.frame
ModuleNotFoundError: No module named 'lz4'

- python -m pytest tests/unit/test_compression.py -v -> rc=1
er=80


================================ tests coverage ================================
_______________ coverage: platform linux, python 3.11.17-final-0 _______________

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/__init__.py                   0      0   100%
src/compression/__init__.py       0      0   100%
src/data/__init__.py              0      0   100%
src/data/download.py             90     90     0%   6-284
src/data/fetch_loop.py           83     83     0%   6-177
src/data/inject.py              149    149     0%   15-385
src/data/validate.py            104    104     0%   14-241
src/pe/__init__.py                0      0   100%
src/utils/__init__.py             0      0   100%
src/utils/config.py             104    104     0%   9-168
src/utils/logging.py             66     66     0%   11-162
-----------------------------------------------------------
TOTAL                           596    596     0%
Coverage HTML written to dir reports/coverage
FAIL Required test coverage of 80% not reached. Total coverage: 0.00%
======================== 3 passed, 17 skipped in 0.37s =========================


- python -m pytest tests/integration/test_pipeline.py -v --maxfail=1 -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-273-quantifying-the-impact-of-data-compressi
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: platformdirs-4.12.4, timeout-2.4.0, cov-7.1.0
timeout: 300.0s
timeout method: thread
timeout func_only: True
collecting ... collected 0 items

============================ no tests ran in 0.01s =============================

ERROR: file or directory not found: tests/integration/test_pipeline.py



## Declared deliverables still missing

- data/external/baseline_bias_original.json
- data/interim/valid_events.json
- data/processed/statistical_test_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/external/baseline_bias_original.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/tests/unit/test_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/external/baseline_bias_original.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/valid_events.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/compression/main.py` — NOT invoked by the run-book
    - `code/src/data/batch_processor.py` — NOT invoked by the run-book
    - `code/src/data/fetch_loop.py` — NOT invoked by the run-book
    - `code/src/data/main.py` — NOT invoked by the run-book
    - `code/src/data/validation_logic.py` — NOT invoked by the run-book
    - `code/src/pe/main.py` — NOT invoked by the run-book
    - `code/src/pe/run_bilby.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/valid_events.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/pe/compare_posteriors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
