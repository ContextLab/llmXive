# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/raw_thermoelectric.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/raw_thermoelectric.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/01_ingest_and_clean.py (rc=1); python code/02_engineer_features.py (rc=1); python code/03_train_and_evaluate.py (rc=1); 3 declared deliverable(s) absent: data/processed/cleaned_compositions.csv; data/processed/final_features.csv; data/processed/model_output.json

## Failing / missing run-book commands

- python code/01_ingest_and_clean.py -> rc=1
 from https://ndownloader.figstatic.com/files/8663971...
Data saved to /home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/data/raw/raw_thermoelectric.csv

Error parsing CSV: 'list' object has no attribute 'strip'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/01_ingest_and_clean.py", line 275, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/01_ingest_and_clean.py", line 233, in main
    records = parse_csv_data(raw_file)
              ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/01_ingest_and_clean.py", line 67, in parse_csv_data
    if any(v.strip() for v in row.values()):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/01_ingest_and_clean.py", line 67, in <genexpr>
    if any(v.strip() for v in row.values()):
           ^^^^^^^
AttributeError: 'list' object has no attribute 'strip'

- python code/02_engineer_features.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/02_engineer_features.py", line 10, in <module>
    from utils.periodic_data import get_atomic_radius, get_electronegativity, get_valence_electrons, get_atomic_number
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/utils/periodic_data.py", line 13, in <module>
    from mendeleev.exceptions import NotFoundError
ModuleNotFoundError: No module named 'mendeleev.exceptions'

- python code/03_train_and_evaluate.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/03_train_and_evaluate.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/03_train_and_evaluate.py", line 223, in main
    df = load_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/03_train_and_evaluate.py", line 20, in load_data
    raise FileNotFoundError(f"Data file not found: {full_path}")
FileNotFoundError: Data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/data/processed/final_features.csv

- python code/04_visualize_and_report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/04_visualize_and_report.py", line 13, in <module>
    from utils.periodic_data import get_element
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/utils/periodic_data.py", line 13, in <module>
    from mendeleev.exceptions import NotFoundError
ModuleNotFoundError: No module named 'mendeleev.exceptions'


## Declared deliverables still missing

- data/processed/cleaned_compositions.csv
- data/processed/final_features.csv
- data/processed/model_output.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_compositions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_and_clean.py` — IS a run-book command
    - `code/02_engineer_features.py` — IS a run-book command
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_compositions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_engineer_features.py` — IS a run-book command
    - `code/03_train_and_evaluate.py` — IS a run-book command
    - `code/04_visualize_and_report.py` — IS a run-book command
    - `code/05_compute_correlations.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_output.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_train_and_evaluate.py` — IS a run-book command
    - `code/04_visualize_and_report.py` — IS a run-book command
    - `code/06_save_model_output.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_output.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
