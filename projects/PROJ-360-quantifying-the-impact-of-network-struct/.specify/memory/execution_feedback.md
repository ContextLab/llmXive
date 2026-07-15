# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download.py --limit 50 --output data/raw/cif/ (rc=1); python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ (rc=1); python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv (rc=1); 3 declared deliverable(s) absent: data/processed/filtered_features.csv; data/processed/metrics.csv; data/processed/network_manifest.json

## Failing / missing run-book commands

- python code/download.py --limit 50 --output data/raw/cif/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/download.py", line 23, in <module>
    logger = setup_logging("download", "results/download.log")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/utils.py", line 50, in setup_logging
    logger.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'download'
- python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/construct_network.py", line 14, in <module>
    from pymatgen.analysis.structure_analyzer import bond_order
ImportError: cannot import name 'bond_order' from 'pymatgen.analysis.structure_analyzer' (/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/.venv/lib/python3.11/site-packages/pymatgen/analysis/structure_analyzer.py)
- python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv -> rc=1
    2026-07-15 12:49:18,520 - metrics_logger - INFO - Starting metrics computation. Input: data/processed/networks/, Output: data/processed/metrics.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 272, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 233, in main
    graphs = load_graphs_from_directory(args.input)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 36, in load_graphs_from_directory
    raise FileNotFoundError(f"Directory not found: {graph_dir}")
FileNotFoundError: Directory not found: data/processed/networks/
- python code/analyze.py --input data/processed/metrics.csv --output results/ -> rc=1
    2026-07-15 12:49:19,780 - analysis - INFO - Starting analysis...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 315, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 214, in main
    df = load_metrics_csv()
         ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 56, in load_metrics_csv
    raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV_PATH}")
FileNotFoundError: Metrics file not found: data/processed/metrics.csv

## Declared deliverables still missing

- data/processed/filtered_features.csv
- data/processed/metrics.csv
- data/processed/network_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/compute_metrics.py` — IS a run-book command
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/quickstart.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/network_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/compute_metrics.py` — IS a run-book command
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
    - `code/construct_network.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/network_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/quickstart_validator.py`, `code/analyze.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/quickstart_validator.py`, `code/analyze.py`, `code/integration_test.py`, `code/validate_artifacts.py`.
