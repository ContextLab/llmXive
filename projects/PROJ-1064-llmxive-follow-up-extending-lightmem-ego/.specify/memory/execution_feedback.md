# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.data.download`
  - script usage: `download.py [-h] --output-dir OUTPUT_DIR`
  - argparse error: `download.py: error: the following arguments are required: --output-dir`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.data.download (rc=2); python -m src.data.preprocess (rc=1); python -m src.cli.run (rc=1); 11 declared deliverable(s) absent: data/processed/faiss_index_mapping.json; data/processed/memory_nodes.parquet; data/processed/validation_queries.json

## Failing / missing run-book commands

- python -m src.data.download -> rc=2

usage: download.py [-h] --output-dir OUTPUT_DIR
download.py: error: the following arguments are required: --output-dir

- python -m src.data.preprocess -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/bin/python: No module named src.data.preprocess

- python -m src.cli.run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/bin/python: Error while finding module specification for 'src.cli.run' (ModuleNotFoundError: No module named 'src.cli')

- python -m pytest -q tests/contract/test_evaluation_report.py -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/test_evaluation_report.py



## Declared deliverables still missing

- data/processed/faiss_index_mapping.json
- data/processed/memory_nodes.parquet
- data/processed/validation_queries.json
- data/results/evaluation_metrics.json
- data/results/evaluation_queries.json
- data/results/evaluation_report.json
- data/results/mcnemar_test.json
- data/results/optimal_parameters.json
- data/results/validation_run.json
- figures/latency_vs_age.png
- figures/long_term_accuracy.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/faiss_index_mapping.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/memory_nodes.parquet` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/validation_queries.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_metrics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_queries.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_report.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/mcnemar_test.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/optimal_parameters.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/validation_run.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/latency_vs_age.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/long_term_accuracy.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
