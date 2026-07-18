# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download.py --limit 50 --output data/raw/cif/ (rc=1); python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ (rc=1); python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv (rc=1); 2 declared deliverable(s) absent: data/processed/filtered_features.csv; data/processed/metrics.csv

## Failing / missing run-book commands

- python code/download.py --limit 50 --output data/raw/cif/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/download.py", line 242, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/download.py", line 208, in main
    api_key = config.get("MP_API_KEY")
              ^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'get'
- python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/construct_network.py", line 9, in <module>
    from pymatgen.analysis.structure_analyzer import get_bonds
ImportError: cannot import name 'get_bonds' from 'pymatgen.analysis.structure_analyzer' (/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/.venv/lib/python3.11/site-packages/pymatgen/analysis/structure_analyzer.py)
- python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv -> rc=1
    2026-07-18 16:56:57,420 - metrics_logger - INFO - Starting metrics computation. Input: data/processed/networks/, Output: data/processed/metrics.csv
2026-07-18 16:56:57,420 - metrics_logger - ERROR - Directory not found: data/processed/networks/

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 219, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 178, in main
    graphs = load_graphs_from_directory(args.input)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/compute_metrics.py", line 33, in load_graphs_from_directory
    raise FileNotFoundError(f"Directory not found: {graph_dir}")
FileNotFoundError: Directory not found: data/processed/networks/
- python code/analyze.py --input data/processed/metrics.csv --output results/ -> rc=1
    2026-07-18 16:56:58,709 - analyze_main - INFO - Starting analysis pipeline...
2026-07-18 16:56:58,710 - analyze_main - ERROR - Analysis pipeline failed: Metrics file not found: data/processed/metrics.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 319, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 272, in main
    metrics_df = load_metrics_csv()
                 ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-360-quantifying-the-impact-of-network-struct/code/analyze.py", line 45, in load_metrics_csv
    raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV_PATH}")
FileNotFoundError: Metrics file not found: data/processed/metrics.csv

## Declared deliverables still missing

- data/processed/filtered_features.csv
- data/processed/metrics.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `get`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.get` call sites (11):
- code/runtime_monitor.py: return data.get("start_epoch")
- code/report.py: r2_interpretation = performance_data.get("r2_interpretation")
- code/compute_metrics.py: material_data = manifest['materials'].get(material_id)
- code/compute_metrics.py: k_x = material_data.get('k_x')
- code/compute_metrics.py: k_y = material_data.get('k_y')
- code/compute_metrics.py: k_z = material_data.get('k_z')
- code/download.py: response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
- code/download.py: materials = data.get("data", [])
- code/download.py: cif_content = response.get("cif")
- code/download.py: material_id = material.get("material_id")
- code/download.py: api_key = config.get("MP_API_KEY")

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/validate_outputs.py` — NOT invoked by the run-book
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/quickstart.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/compute_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analyze.py`, `code/quickstart_validator.py`, `code/compute_metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/integration_test.py`, `code/validate_outputs.py`, `code/quickstart.py`, `code/validate_artifacts.py`, `code/analyze.py`, `code/quickstart_validator.py`, `code/compute_metrics.py`.
