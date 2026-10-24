# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”; 4 command(s) failed: python -m src.run_pipeline --sample 5 (rc=1); python -m src.run_pipeline --full (rc=1); python -m pytest tests/contract/ (rc=1); 1 declared deliverable(s) absent: data/raw/commit_pairs.csv

## Failing / missing run-book commands

- python -m src.run_pipeline --sample 5 -> rc=1

2026-10-24 19:27:19,177 WARNING code.data_extraction: GITHUB_TOKEN not set – proceeding unauthenticated (rate‑limited).
2026-10-24 19:27:19,744 INFO code.run_pipeline: Running smoke test (sample=5)
2026-10-24 19:27:19,744 ERROR code.run_pipeline: Smoke test failed: CommitPair.__init__() got an unexpected keyword argument 'doc_diff'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 71, in run_smoke_test
    _write_smoke_output()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 46, in _write_smoke_output
    dummy_pair = CommitPair(
                 ^^^^^^^^^^^
TypeError: CommitPair.__init__() got an unexpected keyword argument 'doc_diff'

- python -m src.run_pipeline --full -> rc=1
airs()
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 183, in extract_commit_pairs
    detail = _get_commit_detail(owner, repo, sha)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 146, in _get_commit_detail
    return _github_get(url)
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 117, in _github_get
    raise RuntimeError(
RuntimeError: GitHub API request failed [403]: https://api.github.com/repos/psf/requests/commits/9450dd51fb423c17f01325d5f23e62b0450696c6
{"message":"API rate limit exceeded for 20.40.222.213. (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.)","documentation_url":"https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"}

2026-10-24 19:28:12,938 ERROR code.run_pipeline: Data extraction failed with exit code 1

- python -m pytest tests/contract/ -> rc=1
_________________

    def test_commitpair_csv_schema():
        schema = load_schema()
        csv_path = paths.data("raw", "commit_pairs.csv")
>       assert csv_path.exists(), f"{csv_path} does not exist"
E       AssertionError: /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv does not exist
E       assert False
E        +  where False = <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv')>()
E        +    where <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv').exists

tests/contract/test_commitpair_schema.py:27: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_commitpair_schema.py::test_commitpair_csv_schema
============================== 1 failed in 0.15s ===============================


- python -m pytest tests/unit/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/



## Declared deliverables still missing

- data/raw/commit_pairs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/commit_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/commit_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
