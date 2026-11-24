# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/baseline-alfworld/training_run_20261018_143631.csv, data/processed/grpo-alfworld/training_run_20261018_143606.csv, data/processed/student-only-alfworld/training_run_20261018_143655.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/baseline-alfworld/training_run_20261018_143631.csv, data/processed/grpo-alfworld/training_run_20261018_143606.csv, data/processed/student-only-alfworld/training_run_20261018_143655.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python metrics/statistical_test.py  --grpo-dir data/processed/grpo-alfworld  --baseline-dir data/processed/baseline-alfworld  --student-only-dir data/processed/student-only-alfworld  --replay-dir data/processed/student-only-replay-alfworld  --output data/processed/comparison_report.json; 1 declared deliverable(s) absent: data/processed/memory_dry_run.json

## Failing / missing run-book commands

- python metrics/statistical_test.py  --grpo-dir data/processed/grpo-alfworld  --baseline-dir data/processed/baseline-alfworld  --student-only-dir data/processed/student-only-alfworld  --replay-dir data/processed/student-only-replay-alfworld  --output data/processed/comparison_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/metrics/statistical_test.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/memory_dry_run.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/memory_dry_run.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_memory_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_dry_run.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
