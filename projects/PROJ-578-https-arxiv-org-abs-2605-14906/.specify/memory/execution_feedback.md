# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/run_memlens_demo.py (rc=1)

## Failing / missing run-book commands

- python code/run_memlens_demo.py -> rc=1
    eturn self.writer.writerows(map(self._dict_to_list, rowdicts))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/csv.py", line 149, in _dict_to_list
    raise ValueError("dict contains fields not in fieldnames: "
ValueError: dict contains fields not in fieldnames: 'condition'
