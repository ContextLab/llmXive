# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/ri_dataset.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/ri_dataset.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 run-book script(s) missing (plan/impl path mismatch): python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1; python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j)); python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt; 1 command(s) failed: python code/data/preprocess.py --filter-mw 500 (rc=1); 1 declared deliverable(s) absent: data/processed/filtered.csv

## Failing / missing run-book commands

- python code/data/preprocess.py --filter-mw 500 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/code/data/preprocess.py", line 310, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/code/data/preprocess.py", line 195, in main
    schema = load_schema()
             ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/code/data/preprocess.py", line 62, in load_schema
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/contracts/dataset.schema.yaml'

- python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/data/split.py': [Errno 2] No such file or directory

- python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j)) -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/training/train.py': [Errno 2] No such file or directory

- python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/training/evaluate.py': [Errno 2] No such file or directory

- python models/attribution.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt --output results/attributions_${i}_${j}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-296-predicting-molecular-refractive-indices-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-296-predicting-molecular-refractive-indices-/models/attribution.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/filtered.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
