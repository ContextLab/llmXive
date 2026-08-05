# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/semi_empirical.py: synthetic/fake INPUT data not authorized by the spec — “…d the crash (by removing synthetic data and using real structure…”
- code/semi_empirical.py: synthetic/fake INPUT data not authorized by the spec — “…xed the rc=1 by removing synthetic data and using real structure…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/download_summary.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/semi_empirical.py: synthetic/fake INPUT data not authorized by the spec — “…d the crash (by removing synthetic data and using real structure…”; code/semi_empirical.py: synthetic/fake INPUT data not authorized by the spec — “…xed the rc=1 by removing synthetic data and using real structure…”; every produced artifact is gitignored (data/processed/download_summary.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/download.py (rc=1); python code/validate.py (rc=1); python code/dft_runner.py --test-system Li7La3Zr2O12 (rc=1); 2 declared deliverable(s) absent: data/processed/analysis_results.json; data/processed/citation_status.json

## Failing / missing run-book commands

- python code/download.py -> rc=1
    7.50s...
2026-08-05 06:01:53,038 - __main__ - INFO - Attempt 5/5 for https://api.obelix-db.org/v1/structures/OBEL-002
2026-08-05 06:01:53,050 - __main__ - WARNING - Network error (HTTPSConnectionPool(host='api.obelix-db.org', port=443): Max retries exceeded with url: /v1/structures/OBEL-002 (Caused by NameResolutionError("HTTPSConnection(host='api.obelix-db.org', port=443): Failed to resolve 'api.obelix-db.org' ([Errno -2] Name or service not known)"))). Retrying in 33.25s...
2026-08-05 06:02:26,299 - __main__ - ERROR - Failed to fetch https://api.obelix-db.org/v1/structures/OBEL-002 after 5 attempts. Last error: HTTPSConnectionPool(host='api.obelix-db.org', port=443): Max retries exceeded with url: /v1/structures/OBEL-002 (Caused by NameResolutionError("HTTPSConnection(host='api.obelix-db.org', port=443): Failed to resolve 'api.obelix-db.org' ([Errno -2] Name or service not known)"))
2026-08-05 06:02:26,299 - __main__ - INFO - Download complete. Total successful: 0, Failed: 6
2026-08-05 06:02:26,299 - __main__ - INFO - Summary report saved to data/processed/download_summary.json
2026-08-05 06:02:26,299 - __main__ - ERROR - No structures were downloaded. Check network or API keys.
- python code/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/validate.py", line 17, in <module>
    logger = setup_logging(__name__)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/utils.py", line 30, in setup_logging
    logger.setLevel(log_level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: '__main__'
- python code/dft_runner.py --test-system Li7La3Zr2O12 -> rc=1
    mXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/dft_runner.py", line 570, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/dft_runner.py", line 523, in main
    logger = setup_dft_logging(log_file)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/dft_runner.py", line 61, in setup_dft_logging
    file_handler = logging.FileHandler(log_file)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/data/processed/dft_results/dft_runner.log'
- python code/semi_empirical.py --all -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/semi_empirical.py", line 7, in <module>
    from pymatgen.analysis.defects.core import Defect
ModuleNotFoundError: No module named 'pymatgen.analysis.defects'
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/analysis.py", line 21, in <module>
    logger = setup_logging(__name__)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/utils.py", line 30, in setup_logging
    logger.setLevel(log_level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: '__main__'

## Declared deliverables still missing

- data/processed/analysis_results.json
- data/processed/citation_status.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/semi_empirical.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/citation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/citation_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/citation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
