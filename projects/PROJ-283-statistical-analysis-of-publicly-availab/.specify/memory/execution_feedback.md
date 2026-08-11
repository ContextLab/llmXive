# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/reports/generate_plots.py: synthetic/fake INPUT data not authorized by the spec — “…a placeholder plot with dummy data if we can't get actual v…”
- code/src/reports/generate_plots.py: synthetic/fake INPUT data not authorized by the spec — “…ze=(10, 8))     # Create dummy data for demonstration since…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/validation/validate_contracts.py --input data/processed/game_records.csv --schema contracts/game_record.schema.yaml`
  - script usage: `validate_contracts.py [-h] --data DATA [--contracts CONTRACTS]`
  - argparse error: `validate_contracts.py: error: the following arguments are required: --data`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/reports/generate_plots.py: synthetic/fake INPUT data not authorized by the spec — “…a placeholder plot with dummy data if we can't get actual v…”; code/src/reports/generate_plots.py: synthetic/fake INPUT data not authorized by the spec — “…ze=(10, 8))     # Create dummy data for demonstration since…”; 3 command(s) failed: python src/data/download.py --sample-size 100 --output data/raw/sample_games.parquet (rc=1); python src/validation/validate_contracts.py --input data/processed/game_records.csv --schema contracts/game_record.schema.yaml (rc=2); python src/main.py --config config.yaml (rc=1); 2 declared deliverable(s) absent: data/processed/games.parquet; data/results/model_metrics.json

## Failing / missing run-book commands

- python src/data/download.py --sample-size 100 --output data/raw/sample_games.parquet -> rc=1
    - Starting download from: https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn
2026-08-11 20:20:02,925 - INFO - Checking URL reachability: https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn
2026-08-11 20:20:03,090 - ERROR - URL returned status code: 401
2026-08-11 20:20:03,091 - CRITICAL - HALTING: URL returned status code: 401
2026-08-11 20:20:03,091 - ERROR - Pipeline failed: Dataset URL unreachable: URL returned status code: 401
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

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/games.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_feature_preparation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_main_integration.py` — NOT invoked by the run-book
    - `code/tests/unit/test_process_metrics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_validate.py` — NOT invoked by the run-book
    - `code/tests/unit/test_optimization_performance.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/games.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_diagnostics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_save_metrics.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/models/fit.py` — NOT invoked by the run-book
    - `code/src/models/save_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
