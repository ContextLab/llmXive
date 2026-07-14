# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download.py --limit 50 --output data/raw/cif/ (rc=1); python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ (rc=1); python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv (rc=1); 1 declared deliverable(s) absent: data/processed/network_manifest.json

## Failing / missing run-book commands

- python code/download.py --limit 50 --output data/raw/cif/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/download.py", line 5, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/construct_network.py", line 16, in <module>
    import networkx as nx
ModuleNotFoundError: No module named 'networkx'
- python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 8, in <module>
    from pymatgen.core import Structure
ModuleNotFoundError: No module named 'pymatgen'
- python code/analyze.py --input data/processed/metrics.csv --output results/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/processed/network_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/network_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/quickstart.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
    - `code/construct_network.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/network_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
