# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py  --scenarios all      # processes every scenario present in the dataset`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py  --scenarios all      # processes every scenario present in the dataset (rc=1); python -m pytest code/tests/test_graph_construction.py -q (rc=1); 1 declared deliverable(s) absent: data/raw/ctu13_scenario1.csv

## Failing / missing run-book commands

- python code/main.py  --scenarios all      # processes every scenario present in the dataset -> rc=1
rio', 'present', 'in', 'the', 'dataset'], seeds=[42, 123, 456, 789, 101112]
2026-10-19 03:12:47,357 INFO create_layout: Project directories ready: code, code/data, code/models, code/analysis, code/utils, data, data/raw, data/processed, data/results, data/models, data/targets, docs, tests, contracts, figures, logs
2026-10-19 03:12:47,357 INFO create_layout: Config already exists at /home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/code/config.yaml; leaving untouched
2026-10-19 03:12:47,357 INFO create_layout: Project layout creation complete.
2026-10-19 03:12:47,357 INFO data.download_ctu13: Fetching CTU-13 dataset via Hugging Face (up to 5000 rows)
2026-10-19 03:12:47,402 INFO httpx2: HTTP Request: GET https://huggingface.co/api/datasets/ctu13/ctu13 "HTTP/1.1 401 Unauthorized"
2026-10-19 03:12:47,403 ERROR __main__: Failed to download CTU‑13 dataset: Failed to fetch CTU-13 data from Hugging Face: Dataset 'ctu13/ctu13' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/ctu13/ctu13 to ask for access.

- python -m pytest code/tests/test_graph_construction.py -q -> rc=1
nd contains at least one byte of data.
        """
        csv_path = paths.data("raw", "ctu13_scenario1.csv")
>       assert csv_path.exists(), f"Expected CSV at {csv_path} to exist"
E       AssertionError: Expected CSV at /home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/data/raw/ctu13_scenario1.csv to exist
E       assert False
E        +  where False = <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/data/raw/ctu13_scenario1.csv')>()
E        +    where <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/data/raw/ctu13_scenario1.csv')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo/data/raw/ctu13_scenario1.csv').exists

code/tests/test_graph_construction.py:21: AssertionError
=========================== short test summary info ============================
FAILED code/tests/test_graph_construction.py::test_raw_ctu13_csv_exists - Ass...
============================== 1 failed in 0.03s ===============================



## Declared deliverables still missing

- data/raw/ctu13_scenario1.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/ctu13_scenario1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/create_layout.py` — NOT invoked by the run-book
    - `code/data/download_ctu13.py` — NOT invoked by the run-book
    - `code/tests/test_graph_construction.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/ctu13_scenario1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
