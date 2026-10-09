# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/validation/generate_report.py: self-declared fabricated metric — “…n")         p_value = 0.05  # placeholder          result = ValidationResult(…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/validation/generate_report.py: self-declared fabricated metric — “…n")         p_value = 0.05  # placeholder          result = ValidationResult(…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/pipeline/run_full_pipeline.py; 9 command(s) failed: python code/data_acquisition/download_datasets.py (rc=1); python code/agency_scoring/ingest_transcripts.py --input data/raw/transcripts.csv --output data/derived/cleaned_transcripts.parquet (rc=1); python code/agency_scoring/compute_scores.py --input data/derived/cleaned_transcripts.parquet --output data/derived/agency_scores.csv (rc=1); 4 declared deliverable(s) absent: data/processed/adherence_metrics.csv; data/processed/agency_scores.csv; data/processed/demographics.csv

## Failing / missing run-book commands

- python code/data_acquisition/download_datasets.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/data_acquisition/download_datasets.py", line 32, in <module>
    from logging.pipeline_logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/pipeline/run_full_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/pipeline/run_full_pipeline.py': [Errno 2] No such file or directory

- python code/agency_scoring/ingest_transcripts.py --input data/raw/transcripts.csv --output data/derived/cleaned_transcripts.parquet -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/agency_scoring/compute_scores.py --input data/derived/cleaned_transcripts.parquet --output data/derived/agency_scores.csv -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/adherence_extraction/extract_metrics.py --input data/raw/usage_metadata.csv --output data/derived/adherence_metrics.csv -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/adherence_extraction/impute_confounders.py --input data/raw/demographics.csv --output data/derived/demographics_imputed.csv -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/validation/compute_reliability.py --input data/derived/agency_scores.csv --output data/validated_features/reliability.yaml -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/validation/compute_convergent.py --agency data/derived/agency_scores.csv --scale data/raw/external_agency_scale.csv --output data/validated_features/convergent.yaml -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/analysis/merge_datasets.py --agency data/derived/agency_scores.csv --adherence data/derived/adherence_metrics.csv --demo data/derived/demographics_imputed.csv --output data/derived/merged_data.csv -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)

- python code/analysis/run_regression.py --input data/derived/merged_data.csv --output data/derived/regression_results.csv -> rc=1
/python3.11/site-packages/pandas/testing.py", line 5, in <module>
    from pandas._testing import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/.venv/lib/python3.11/site-packages/pandas/_testing/__init__.py", line 3, in <module>
    from concurrent.futures import ThreadPoolExecutor
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/__init__.py", line 8, in <module>
    from concurrent.futures._base import (FIRST_COMPLETED,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/concurrent/futures/_base.py", line 7, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/__init__.py", line 7, in <module>
    from .pipeline_logger import get_logger, log_dict
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-547-the-impact-of-perceived-agency-in-ai-dri/code/logging/pipeline_logger.py", line 23, in <module>
    _LOGGER: logging.Logger | None = None
             ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)


## Declared deliverables still missing

- data/processed/adherence_metrics.csv
- data/processed/agency_scores.csv
- data/processed/demographics.csv
- data/processed/merged_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/adherence_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/adherence_extraction/extract_metrics.py` — IS a run-book command
    - `code/adherence_extraction/impute_confounders.py` — IS a run-book command
    - `code/analysis/merge_datasets.py` — IS a run-book command
    - `code/benchmark/run_benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/adherence_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/agency_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/agency_scoring/__init__.py` — NOT invoked by the run-book
    - `code/agency_scoring/compute_scores.py` — IS a run-book command
    - `code/analysis/check_agency_variance.py` — NOT invoked by the run-book
    - `code/analysis/merge_datasets.py` — IS a run-book command
    - `code/benchmark/run_benchmark.py` — NOT invoked by the run-book
    - `code/validation/select_subset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/agency_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/demographics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/adherence_extraction/__init__.py` — NOT invoked by the run-book
    - `code/adherence_extraction/ingest_demographics.py` — NOT invoked by the run-book
    - `code/analysis/merge_datasets.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/demographics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_results.py` — NOT invoked by the run-book
    - `code/analysis/merge_datasets.py` — IS a run-book command
    - `code/analysis/run_regression.py` — IS a run-book command
    - `code/analysis/select_regression.py` — NOT invoked by the run-book
    - `code/validation/compute_convergent.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merged_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
