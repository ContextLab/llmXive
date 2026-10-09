# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/derived/failure_signatures.json: results file is EMPTY ([]) — the analysis produced no values
- every produced artifact is gitignored (data/derived/failure_signatures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/dataset/loader.py --download`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/derived/failure_signatures.json: results file is EMPTY ([]) — the analysis produced no values; every produced artifact is gitignored (data/derived/failure_signatures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/dataset/loader.py --download (rc=1); python code/analysis/stats.py --baseline data/logs/baseline_execution_log.json --augmented data/logs/augmented_execution_log.json --report data/report.md (rc=1); python -m pytest tests/unit/ (rc=2); 1 declared deliverable(s) absent: data/results/final_report.json

## Failing / missing run-book commands

- python code/dataset/loader.py --download -> rc=1
ith `huggingface-cli login`.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py", line 117, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py", line 111, in main
    out_dir = download_planbench_xl()
              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py", line 82, in download_planbench_xl
    raise RuntimeError(
RuntimeError: Failed to download PlanBench-XL after 3 attempts: Couldn't find a dataset script at /home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/PlanBench/planbench-xl/planbench-xl.py or any data file in the same directory. Couldn't find 'PlanBench/planbench-xl' on the Hugging Face Hub either: FileNotFoundError: Dataset 'PlanBench/planbench-xl' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

- python code/analysis/stats.py --baseline data/logs/baseline_execution_log.json --augmented data/logs/augmented_execution_log.json --report data/report.md -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/stats.py", line 6, in <module>
    def calculate_statistical_significance(baseline_path: Path, augmented_path: Path) -> Dict[str, Any]:
                                                          ^^^^
NameError: name 'Path' is not defined

- python -m pytest tests/unit/ -> rc=2
_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_stats.py:2: in <module>
    from analysis.stats import calculate_statistical_significance
code/analysis/stats.py:6: in <module>
    def calculate_statistical_significance(baseline_path: Path, augmented_path: Path) -> Dict[str, Any]:
E   NameError: name 'Path' is not defined
=========================== short test summary info ============================
ERROR tests/unit/test_config_t030a.py
ERROR tests/unit/test_stats.py - NameError: name 'Path' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 2.40s ===============================



## Declared deliverables still missing

- data/results/final_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
