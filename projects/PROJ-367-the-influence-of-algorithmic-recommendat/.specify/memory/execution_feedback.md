# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset mimicking user-a…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…s:         pd.DataFrame: Generated synthetic dataset     """     rand…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…(f"Generated {n_samples} synthetic records saved to {output_path}")…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main entry point for synthetic data generation."""     # Loa…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…taset()     logger.info("Synthetic data generation complete")  i…”
- code/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…s script assumes: 1. The synthetic dataset exists at `data/raw/synt…”
- code/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…clean state, though for synthetic data it's static.         # T…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_fetcher.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset mimicking user-a…”; code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…s:         pd.DataFrame: Generated synthetic dataset     """     rand…”; code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…(f"Generated {n_samples} synthetic records saved to {output_path}")…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/preprocessing.py; 5 command(s) failed: python code/data_fetcher.py (rc=1); python code/main.py (rc=1); python -m pytest tests/unit/ -v (rc=2); 1 declared deliverable(s) absent: data/processed/cleaned_data.parquet

## Failing / missing run-book commands

- python code/data_fetcher.py -> rc=1
ne 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: NOT FOUND for url: https://zenodo.org/records/3222405/files/oulad.zip

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/data_fetcher.py", line 305, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/data_fetcher.py", line 296, in main
    fetch_educational_dataset("oulad")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/data_fetcher.py", line 250, in fetch_educational_dataset
    _download_and_extract_oulad()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/data_fetcher.py", line 59, in _download_and_extract_oulad
    raise DataAvailabilityError(
ingestion.DataAvailabilityError: Failed to download OULAD from mirror URL: 404 Client Error: NOT FOUND for url: https://zenodo.org/records/3222405/files/oulad.zip

- python code/preprocessing.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/preprocessing.py': [Errno 2] No such file or directory

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/main.py", line 24, in <module>
    from merger import merge_similar_categories, load_embedding_model
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/merger.py", line 13, in <module>
    from sentence_transformers import SentenceTransformer
ModuleNotFoundError: No module named 'sentence_transformers'

- python -m pytest tests/unit/ -v -> rc=2
n import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_sensitivity.py:12: in <module>
    from sensitivity import run_analysis_for_threshold, main
code/sensitivity.py:12: in <module>
    from merger import merge_similar_categories
code/merger.py:13: in <module>
    from sentence_transformers import SentenceTransformer
E   ModuleNotFoundError: No module named 'sentence_transformers'
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
ERROR tests/unit/test_data_generation.py
ERROR tests/unit/test_merger.py
ERROR tests/unit/test_sensitivity.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 1.98s ===============================


- python -m pytest tests/integration/ -v -> rc=2
opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/integration/test_main_verification.py:15: in <module>
    from main import run_verification_test
code/main.py:24: in <module>
    from merger import merge_similar_categories, load_embedding_model
code/merger.py:13: in <module>
    from sentence_transformers import SentenceTransformer
E   ModuleNotFoundError: No module named 'sentence_transformers'
=========================== short test summary info ============================
ERROR tests/integration/test_main_verification.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.58s ===============================


- python -m pytest tests/contract/ -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat
configfile: pytest.ini
plugins: platformdirs-4.13.0, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/



## Declared deliverables still missing

- data/processed/cleaned_data.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_fetcher.py` — IS a run-book command
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/merger.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
