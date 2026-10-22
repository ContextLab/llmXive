# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_data.py: function `generate_noise_vector` returns a bare RNG draw (line 187) — a reported value computed from no real input

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/evaluate.py  --model data/processed/trained_model.pt  --baseline data/processed/geometry_baseline.pt  --control data/processed/random_baseline.pt  --test data/processed/test.parquet  --output data/processed/metrics_report.json`
  - script usage: `evaluate.py [-h] [--config CONFIG] [--device DEVICE]`
  - argparse error: `evaluate.py: error: unrecognized arguments: --model data/processed/trained_model.pt --baseline data/processed/geometry_baseline.pt --control data/processed/random_baseline.pt --test data/processed/test.parquet --output data/processed/metrics_report.json`
- run-book command: `python code/evaluate.py  --model data/processed/trained_model.pt  --baseline data/processed/geometry_baseline.pt  --control data/processed/random_baseline.pt  --test data/processed/test.parquet  --output data/processed/metrics_report.json`
  - script usage: `evaluate.py [-h] [--config CONFIG] [--device DEVICE]`
  - argparse error: `evaluate.py: error: unrecognized arguments: --model data/processed/trained_model.pt --baseline data/processed/geometry_baseline.pt --control data/processed/random_baseline.pt --test data/processed/test.parquet --output data/processed/metrics_report.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_data.py: function `generate_noise_vector` returns a bare RNG draw (line 187) — a reported value computed from no real input; 3 run-book script(s) missing (plan/impl path mismatch): python code/split_data.py --input data/raw/synthetic_episodes.parquet  --train data/processed/train.parquet  --test data/processed/test.parquet; python code/sensitivity.py  --model data/processed/trained_model.pt  --test data/processed/test.parquet  --output data/sweep/variance_report.json; python code/split_data.py --input data/raw/synthetic_episodes.parquet  --train data/processed/train.parquet  --test data/processed/test.parquet; 8 command(s) failed: python code/generate_data.py --config code/config.yaml (rc=-1); python code/train_model.py --train data/processed/train.parquet  --output data/processed/trained_model.pt (rc=1); python code/train_baseline.py --train data/processed/train.parquet  --output data/processed/geometry_baseline.pt (rc=1); 4 declared deliverable(s) absent: data/checksums.json; data/processed/test.parquet; data/processed/train.parquet

## Failing / missing run-book commands

- python code/generate_data.py --config code/config.yaml -> rc=-1
 file.
[generate_data] Episode failed (attempt 90): Cannot load URDF file.
[generate_data] Episode failed (attempt 104): Cannot load URDF file.
[generate_data] Episode failed (attempt 107): Cannot load URDF file.
[generate_data] Episode failed (attempt 111): Cannot load URDF file.
[generate_data] Episode failed (attempt 112): Cannot load URDF file.
[generate_data] Episode failed (attempt 116): Cannot load URDF file.
[generate_data] Episode failed (attempt 129): Cannot load URDF file.
[generate_data] Episode failed (attempt 133): Cannot load URDF file.
[generate_data] Episode failed (attempt 138): Cannot load URDF file.
[generate_data] Episode failed (attempt 139): Cannot load URDF file.
[generate_data] Episode failed (attempt 141): Cannot load URDF file.
[generate_data] Episode failed (attempt 147): Cannot load URDF file.
[generate_data] Episode failed (attempt 148): Cannot load URDF file.
[generate_data] Episode failed (attempt 151): Cannot load URDF file.
[generate_data] Episode failed (attempt 152): Cannot load URDF file.
[generate_data] Episode failed (attempt 153): Cannot load URDF file.
[generate_data] Episode failed (attempt 154): Cannot load URDF file.

[TIMEOUT after 120s]
- python code/split_data.py --input data/raw/synthetic_episodes.parquet  --train data/processed/train.parquet  --test data/processed/test.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-855-llmxive-follow-up-extending-translation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/split_data.py': [Errno 2] No such file or directory

- python code/train_model.py --train data/processed/train.parquet  --output data/processed/trained_model.pt -> rc=1
ROJ-855-llmxive-follow-up-extending-translation/code/train_model.py", line 136, in main
    train_dataset = StabilityDataset(data_path_train)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/train_model.py", line 58, in __init__
    self.df = pd.read_parquet(parquet_path)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 651, in read_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 67, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python code/train_baseline.py --train data/processed/train.parquet  --output data/processed/geometry_baseline.pt -> rc=1
Loading data from: data/processed/train.parquet

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/train_baseline.py", line 260, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/train_baseline.py", line 196, in main
    raise FileNotFoundError(f"Training data not found at {data_path}. Run T016c first.")
FileNotFoundError: Training data not found at data/processed/train.parquet. Run T016c first.

- python code/train_shuffled_control.py --train data/processed/train.parquet --output data/processed/random_baseline.pt -> rc=1
[INFO] Starting Shuffled-Translation Control Training (T027c)
[INFO] Loading config from /home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/config.yaml
[INFO] Using device: cpu
[INFO] Loading training data from /home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/data/processed/train.parquet
[ERROR] Training data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/data/processed/train.parquet. Please run data generation first.


- python code/evaluate.py  --model data/processed/trained_model.pt  --baseline data/processed/geometry_baseline.pt  --control data/processed/random_baseline.pt  --test data/processed/test.parquet  --output data/processed/metrics_report.json -> rc=2

usage: evaluate.py [-h] [--config CONFIG] [--device DEVICE]
evaluate.py: error: unrecognized arguments: --model data/processed/trained_model.pt --baseline data/processed/geometry_baseline.pt --control data/processed/random_baseline.pt --test data/processed/test.parquet --output data/processed/metrics_report.json

- python code/sensitivity.py  --model data/processed/trained_model.pt  --test data/processed/test.parquet  --output data/sweep/variance_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-855-llmxive-follow-up-extending-translation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/sensitivity.py': [Errno 2] No such file or directory

- python code/generate_data.py --config code/config.yaml -> rc=-1
 file.
[generate_data] Episode failed (attempt 90): Cannot load URDF file.
[generate_data] Episode failed (attempt 104): Cannot load URDF file.
[generate_data] Episode failed (attempt 107): Cannot load URDF file.
[generate_data] Episode failed (attempt 111): Cannot load URDF file.
[generate_data] Episode failed (attempt 112): Cannot load URDF file.
[generate_data] Episode failed (attempt 116): Cannot load URDF file.
[generate_data] Episode failed (attempt 129): Cannot load URDF file.
[generate_data] Episode failed (attempt 133): Cannot load URDF file.
[generate_data] Episode failed (attempt 138): Cannot load URDF file.
[generate_data] Episode failed (attempt 139): Cannot load URDF file.
[generate_data] Episode failed (attempt 141): Cannot load URDF file.
[generate_data] Episode failed (attempt 147): Cannot load URDF file.
[generate_data] Episode failed (attempt 148): Cannot load URDF file.
[generate_data] Episode failed (attempt 151): Cannot load URDF file.
[generate_data] Episode failed (attempt 152): Cannot load URDF file.
[generate_data] Episode failed (attempt 153): Cannot load URDF file.
[generate_data] Episode failed (attempt 154): Cannot load URDF file.

[TIMEOUT after 120s]
- python code/split_data.py --input data/raw/synthetic_episodes.parquet  --train data/processed/train.parquet  --test data/processed/test.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-855-llmxive-follow-up-extending-translation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/split_data.py': [Errno 2] No such file or directory

- python code/train_model.py --train data/processed/train.parquet  --output data/processed/trained_model.pt -> rc=1
ROJ-855-llmxive-follow-up-extending-translation/code/train_model.py", line 136, in main
    train_dataset = StabilityDataset(data_path_train)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-855-llmxive-follow-up-extending-translation/code/train_model.py", line 58, in __init__
    self.df = pd.read_parquet(parquet_path)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 651, in read_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 67, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python code/evaluate.py  --model data/processed/trained_model.pt  --baseline data/processed/geometry_baseline.pt  --control data/processed/random_baseline.pt  --test data/processed/test.parquet  --output data/processed/metrics_report.json -> rc=2

usage: evaluate.py [-h] [--config CONFIG] [--device DEVICE]
evaluate.py: error: unrecognized arguments: --model data/processed/trained_model.pt --baseline data/processed/geometry_baseline.pt --control data/processed/random_baseline.pt --test data/processed/test.parquet --output data/processed/metrics_report.json


## Declared deliverables still missing

- data/checksums.json
- data/processed/test.parquet
- data/processed/train.parquet
- data/raw/synthetic_episodes.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/process_data.py` — NOT invoked by the run-book
    - `code/scripts/init_data_dirs.py` — NOT invoked by the run-book
    - `code/train_model.py` — IS a run-book command
    - `code/train_shuffled_control.py` — IS a run-book command
    - `code/utils/data_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
    - `code/process_data.py` — NOT invoked by the run-book
    - `code/tests/contract/test_dataset_schema.py` — NOT invoked by the run-book
    - `code/tests/contract/test_metrics_report.py` — NOT invoked by the run-book
    - `code/train_model.py` — IS a run-book command
    - `code/train_shuffled_control.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/test.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
    - `code/models/transformer.py` — NOT invoked by the run-book
    - `code/process_data.py` — NOT invoked by the run-book
    - `code/train_baseline.py` — IS a run-book command
    - `code/train_model.py` — IS a run-book command
    - `code/train_shuffled_control.py` — IS a run-book command
    - `code/verify_model_params.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_episodes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/process_data.py` — NOT invoked by the run-book
    - `code/tests/contract/test_dataset_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_episodes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
