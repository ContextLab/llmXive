# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m src.cli.main --step analysis`
- `python -m src.cli.main --step analysis --debug`
- `python -m src.cli.main --step embeddings --batch-size 64`
- `python -m src.cli.main --step embeddings --debug`
- `python -m src.cli.main --step ingest --sample-size 100 --debug`
- `python -m src.cli.main --step ingest --sample-size [DEFERRED]`
- `python -m src.cli.main --step report`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python -m src.cli.main --step ingest --sample-size [DEFERRED] (rc=1); python -m src.cli.main --step embeddings --batch-size 64 (rc=1); python -m src.cli.main --step analysis (rc=1); 2 declared deliverable(s) absent: data/processed/final_analysis_dataset.parquet; data/processed/subgraph_with_clusters.parquet

## Failing / missing run-book commands

- python -m src.cli.main --step ingest --sample-size [DEFERRED] -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.cli.main --step embeddings --batch-size 64 -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.cli.main --step analysis -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.cli.main --step report -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.cli.main --step ingest --sample-size 100 --debug -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.cli.main --step embeddings --debug -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.cli.main --step analysis --debug -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')

## Declared deliverables still missing

- data/processed/final_analysis_dataset.parquet
- data/processed/subgraph_with_clusters.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_analysis_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/save_final_dataset.py` — NOT invoked by the run-book
    - `code/scripts/run_validation.py` — NOT invoked by the run-book
    - `code/scripts/save_statistical_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_analysis_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/subgraph_with_clusters.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_save_graph.py` — NOT invoked by the run-book
    - `code/tests/unit/test_graph_utils.py` — NOT invoked by the run-book
    - `code/scripts/save_final_dataset.py` — NOT invoked by the run-book
    - `code/scripts/save_graph_pipeline.py` — NOT invoked by the run-book
    - `code/scripts/run_validation.py` — NOT invoked by the run-book
    - `code/src/services/save_graph.py` — NOT invoked by the run-book
    - `code/src/services/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/subgraph_with_clusters.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
