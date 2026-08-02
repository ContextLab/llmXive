# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/validation/validate_contracts.py --input data/processed/game_records.csv --schema contracts/game_record.schema.yaml`
  - script usage: `validate_contracts.py [-h] --data DATA [--contracts CONTRACTS]`
  - argparse error: `validate_contracts.py: error: the following arguments are required: --data`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python src/data/download.py --sample-size 100 --output data/raw/sample_games.parquet (rc=1); python src/validation/validate_contracts.py --input data/processed/game_records.csv --schema contracts/game_record.schema.yaml (rc=2); python src/main.py --config config.yaml (rc=1); 2 declared deliverable(s) absent: data/processed/games.parquet; data/results/model_metrics.json

## Failing / missing run-book commands

- python src/data/download.py --sample-size 100 --output data/raw/sample_games.parquet -> rc=1
    - Starting download from: https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn
2026-08-02 14:36:13,601 - INFO - Checking URL reachability: https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn
2026-08-02 14:36:13,685 - ERROR - URL returned status code: 401
2026-08-02 14:36:13,686 - CRITICAL - HALTING: URL returned status code: 401
2026-08-02 14:36:13,686 - ERROR - Pipeline failed: Dataset URL unreachable: URL returned status code: 401
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/data/download.py", line 146, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/data/download.py", line 138, in main
    output_path = download_chess_data()
                  ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/data/download.py", line 123, in download_chess_data
    raise RuntimeError(f"Dataset URL unreachable: {message}")
RuntimeError: Dataset URL unreachable: URL returned status code: 401
- python src/validation/validate_contracts.py --input data/processed/game_records.csv --schema contracts/game_record.schema.yaml -> rc=2
    usage: validate_contracts.py [-h] --data DATA [--contracts CONTRACTS]
                             [--format {parquet,csv}]
validate_contracts.py: error: the following arguments are required: --data
- python src/main.py --config config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/main.py", line 23, in <module>
    from src.data.download import download_lichess_data
ImportError: cannot import name 'download_lichess_data' from 'src.data.download' (/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/code/src/data/download.py)

## Declared deliverables still missing

- data/processed/games.parquet
- data/results/model_metrics.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **7136017970** real records with fields: Event, Site, White, Black, Result, WhiteTitle, BlackTitle, WhiteElo, BlackElo, WhiteRatingDiff, BlackRatingDiff, UTCDate, UTCTime, ECO, Opening, Termination, TimeControl, movetext.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

builder = datasets.load_dataset_builder("Lichess/standard-chess-games")
split_info = builder.info.splits["train"]
count = split_info.num_examples
fields = list(builder.info.features.keys())

print(f"RECORDS={count}")
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/games.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_feature_preparation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_main_integration.py` — NOT invoked by the run-book
    - `code/tests/unit/test_validate.py` — NOT invoked by the run-book
    - `code/tests/unit/test_optimization_performance.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/games.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_diagnostics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_save_metrics.py` — NOT invoked by the run-book
    - `code/src/models/save_metrics.py` — NOT invoked by the run-book
    - `code/src/reports/sensitivity.py` — NOT invoked by the run-book
    - `code/src/reports/generate_plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
