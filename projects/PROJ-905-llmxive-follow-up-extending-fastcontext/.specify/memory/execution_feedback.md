# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/export_scores.py: self-declared fabricated metric — “…main():     # Demo: generate dummy scores if none exist     input_path…”
- code/export_scores.py: self-declared fabricated metric — “…path)         print(f"Created dummy scores at {input_path}")          #…”
- code/export_scores.py: synthetic/fake INPUT data not authorized by the spec — “…ists():         # Create dummy data for testing         dumm…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/baseline_runner.py --split Regular --mode cpu --output results`
  - script usage: `baseline_runner.py [-h] --repo REPO [--max-memory MAX_MEMORY]`
  - argparse error: `baseline_runner.py: error: the following arguments are required: --repo`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/export_scores.py: self-declared fabricated metric — “…main():     # Demo: generate dummy scores if none exist     input_path…”; code/export_scores.py: self-declared fabricated metric — “…path)         print(f"Created dummy scores at {input_path}")          #…”; code/export_scores.py: synthetic/fake INPUT data not authorized by the spec — “…ists():         # Create dummy data for testing         dumm…”; 4 command(s) failed: python code/fastcontext_lite.py --split Regular --output results (rc=1); python code/baseline_runner.py --split Regular --mode cpu --output results (rc=2); python code/analysis.py --input results/metrics.csv --output results/statistical_analysis.json (rc=1); 1 declared deliverable(s) absent: data/processed/regularity_scores.csv

## Failing / missing run-book commands

- python code/fastcontext_lite.py --split Regular --output results -> rc=1
ve/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/fastcontext_lite.py", line 212, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/fastcontext_lite.py", line 208, in main
    result = run_fastcontext_lite(mock_repo, issue)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/fastcontext_lite.py", line 182, in run_fastcontext_lite
    snippets = extract_snippets(filtered_files, keywords, top_k=5)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/fastcontext_lite.py", line 148, in extract_snippets
    index = build_tfidf_index(repo_files)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/fastcontext_lite.py", line 93, in build_tfidf_index
    idf = vectorizer.id_
          ^^^^^^^^^^^^^^
AttributeError: 'TfidfVectorizer' object has no attribute 'id_'. Did you mean: 'idf_'?

- python code/baseline_runner.py --split Regular --mode cpu --output results -> rc=2

usage: baseline_runner.py [-h] --repo REPO [--max-memory MAX_MEMORY]
                          [--timeout TIMEOUT]
baseline_runner.py: error: the following arguments are required: --repo

- python code/analysis.py --input results/metrics.csv --output results/statistical_analysis.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/analysis.py", line 282, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/analysis.py", line 271, in main
    ensure_directories()
TypeError: ensure_directories() missing 1 required positional argument: 'paths'

- python -m pytest tests/unit/test_scoring.py -v -> rc=3
runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/.venv/lib/python3.11/site-packages/pluggy/_callers.py", line 121, in _multicall
INTERNALERROR>     res = hook_impl.function(*args)
INTERNALERROR>           ^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/.venv/lib/python3.11/site-packages/_pytest/debugging.py", line 71, in pytest_configure
INTERNALERROR>     import pdb
INTERNALERROR>   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pdb.py", line 77, in <module>
INTERNALERROR>     import code
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/__init__.py", line 12, in <module>
INTERNALERROR>     from .data_loader import download_dataset, compute_file_sha256, verify_checksum
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/data_loader.py", line 24, in <module>
INTERNALERROR>     raise ImportError(
INTERNALERROR> ImportError: The 'datasets' package is required. Install it via: pip install datasets


## Declared deliverables still missing

- data/processed/regularity_scores.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/regularity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/export_scores.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/pilot_validation.py` — NOT invoked by the run-book
    - `code/stratification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regularity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
