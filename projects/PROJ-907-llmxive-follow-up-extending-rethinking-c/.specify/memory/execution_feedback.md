# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m json.tool data/routing_cache/canonical_map.json | grep -q "static_weights" && echo "Valid"`
  - script usage: `python -m json.tool [-h] [--sort-keys] [--no-ensure-ascii]`
  - argparse error: `python -m json.tool: error: argument infile: can't open 'data/routing_cache/canonical_map.json': [Errno 2] No such file or directory: 'data/routing_cache/canonical_map.json'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/src/tracing.py --images 100 --batch-size 10 (rc=1); python code/src/clustering.py --input data/routing_cache/ (rc=1); python code/src/canonical_map.py --input data/routing_cache/cluster_centers.json --output data/routing_cache/canonical_map.json (rc=1); 9 declared deliverable(s) absent: data/results/benchmark_results.csv; data/results/benchmark_results.json; data/results/final_report.json

## Failing / missing run-book commands

- python code/src/tracing.py --images 100 --batch-size 10 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/tracing.py", line 11, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-907-llmxive-follow-up-extending-rethinking-c/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-907-llmxive-follow-up-extending-rethinking-c/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-907-llmxive-follow-up-extending-rethinking-c/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/src/clustering.py --input data/routing_cache/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py", line 122, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py", line 119, in main
    run_clustering_analysis(routing_cache_path, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py", line 99, in run_clustering_analysis
    routing_tensor = load_routing_cache(routing_cache_path)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py", line 15, in load_routing_cache
    raise FileNotFoundError(f"Routing cache not found at {path}")
FileNotFoundError: Routing cache not found at data/routing_cache/routing_aggregated.npy

- python code/src/canonical_map.py --input data/routing_cache/cluster_centers.json --output data/routing_cache/canonical_map.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/canonical_map.py", line 46, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/canonical_map.py", line 42, in main
    canonical_map = derive_canonical_map(cluster_centers_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/canonical_map.py", line 16, in derive_canonical_map
    with open(cluster_centers_path, 'r') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/routing_cache/cluster_centers.json'

- python code/src/benchmark.py --mode dynamic --seed 42 --images 500 --output data/results/benchmark_results.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/benchmark.py", line 21, in <module>
    def compute_data_source_hash(data_iterator: Iterator) -> str:
                                                ^^^^^^^^
NameError: name 'Iterator' is not defined

- python code/src/benchmark.py --mode static --seed 42 --images 500 --output data/results/benchmark_results.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/benchmark.py", line 21, in <module>
    def compute_data_source_hash(data_iterator: Iterator) -> str:
                                                ^^^^^^^^
NameError: name 'Iterator' is not defined

- python code/src/stats_analysis.py --input data/results/benchmark_results.json --output data/results/statistical_analysis.json --sweep -> rc=1

2026-10-11 15:26:13,271 - INFO - Running statistical analysis...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/stats_analysis.py", line 100, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/stats_analysis.py", line 97, in main
    run_statistical_analysis()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/stats_analysis.py", line 89, in run_statistical_analysis
    output_path = Path("data/results/statistical_analysis.json")
                  ^^^^
NameError: name 'Path' is not defined

- python -m json.tool data/routing_cache/canonical_map.json | grep -q "static_weights" && echo "Valid" -> rc=2

usage: python -m json.tool [-h] [--sort-keys] [--no-ensure-ascii]
                           [--json-lines]
                           [--indent INDENT | --tab | --no-indent | --compact]
                           [infile] [outfile]
python -m json.tool: error: argument infile: can't open 'data/routing_cache/canonical_map.json': [Errno 2] No such file or directory: 'data/routing_cache/canonical_map.json'


## Declared deliverables still missing

- data/results/benchmark_results.csv
- data/results/benchmark_results.json
- data/results/final_report.json
- data/results/memory_profile.json
- data/results/sensitivity_sweep.json
- data/results/statistical_analysis.json
- data/routing_cache/canonical_map.json
- data/routing_cache/cluster_centers.json
- data/routing_cache/routing_aggregated.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/benchmark_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/benchmark.py` — IS a run-book command
  Make ONE of these WRITE `data/results/benchmark_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/benchmark_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/benchmark.py` — IS a run-book command
  Make ONE of these WRITE `data/results/benchmark_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/final_report.py` — NOT invoked by the run-book
    - `code/tests/unit/test_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/memory_profile.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/memory_analysis.py` — NOT invoked by the run-book
    - `code/src/memory_report_generator.py` — NOT invoked by the run-book
    - `code/src/tracing.py` — IS a run-book command
    - `code/src/utils.py` — NOT invoked by the run-book
    - `code/tests/unit/test_memory_analysis.py` — NOT invoked by the run-book
    - `code/tests/unit/test_memory_report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/memory_profile.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/final_report.py` — NOT invoked by the run-book
    - `code/src/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/statistical_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/final_report.py` — NOT invoked by the run-book
    - `code/src/stats_analysis.py` — IS a run-book command
    - `code/tests/unit/test_final_report.py` — NOT invoked by the run-book
    - `code/tests/unit/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/statistical_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/routing_cache/canonical_map.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/canonical_map.py` — IS a run-book command
    - `code/src/clustering.py` — IS a run-book command
    - `code/src/sensitivity.py` — NOT invoked by the run-book
    - `code/src/static_model.py` — NOT invoked by the run-book
    - `code/tests/unit/test_canonical_map.py` — NOT invoked by the run-book
    - `code/tests/unit/test_clustering.py` — NOT invoked by the run-book
    - `code/tests/unit/test_static_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/routing_cache/canonical_map.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/routing_cache/cluster_centers.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/canonical_map.py` — IS a run-book command
    - `code/src/clustering.py` — IS a run-book command
    - `code/tests/unit/test_canonical_map.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/routing_cache/cluster_centers.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/routing_cache/routing_aggregated.npy` is declared but was NOT written. Scripts referencing it:
    - `code/src/clustering.py` — IS a run-book command
    - `code/src/sensitivity.py` — NOT invoked by the run-book
    - `code/src/tracing.py` — IS a run-book command
  Make ONE of these WRITE `data/routing_cache/routing_aggregated.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
