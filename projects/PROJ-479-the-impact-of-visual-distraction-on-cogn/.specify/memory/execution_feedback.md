# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/01_data_acquisition.py`
- `python code/02_visual_metrics.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/01_data_acquisition.py (rc=1); python code/02_visual_metrics.py (rc=1); python code/03_analysis.py (rc=1); 1 declared deliverable(s) absent: data/processed/final_analysis_data.csv

## Failing / missing run-book commands

- python code/01_data_acquisition.py -> rc=1
    2026-07-20 13:53:06,740 - __main__ - INFO - Starting Power Analysis (Task T019)...
2026-07-20 13:53:06,740 - __main__ - ERROR - Power analysis calculation failed: TTestPower.solve_power() got an unexpected keyword argument 'nobs1'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/01_data_acquisition.py", line 165, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/01_data_acquisition.py", line 152, in main
    report_data = run_power_analysis(
                  ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/01_data_acquisition.py", line 43, in run_power_analysis
    calculated_power = tt_solve_power(
                       ^^^^^^^^^^^^^^^
TypeError: TTestPower.solve_power() got an unexpected keyword argument 'nobs1'
- python code/02_visual_metrics.py -> rc=1
    Creating new Ultralytics Settings v0.0.6 file ✅ 
View Ultralytics Settings with 'yolo settings' or at '/home/runner/.config/Ultralytics/settings.json'
Update Settings with 'yolo settings key=value', i.e. 'yolo settings runs_dir=path/to/dir'. For help see https://docs.ultralytics.com/quickstart/#ultralytics-settings.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/02_visual_metrics.py", line 177, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/02_visual_metrics.py", line 155, in main
    for f in os.listdir(raw_dir) 
             ^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw'
- python code/03_analysis.py -> rc=1
    2026-07-20 13:53:11,209 - __main__ - INFO - Starting statistical analysis pipeline...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/03_analysis.py", line 297, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/03_analysis.py", line 260, in main
    df = load_analysis_data()
         ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/03_analysis.py", line 38, in load_analysis_data
    raise FileNotFoundError(f"Analysis data file not found: {path}")
FileNotFoundError: Analysis data file not found: data/processed/final_analysis_data.csv

## Declared deliverables still missing

- data/processed/final_analysis_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_analysis_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_visualization.py` — IS a run-book command
    - `code/02_visual_metrics.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/final_analysis_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/04_visualization.py`, `code/02_visual_metrics.py`, `code/03_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/final_analysis_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/04_visualization.py`, `code/02_visual_metrics.py`, `code/03_analysis.py`.
