# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/model.py: synthetic/fake INPUT data not authorized by the spec — “…led.")          # Create dummy data         num_nodes = 20…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/model.py: synthetic/fake INPUT data not authorized by the spec — “…led.")          # Create dummy data         num_nodes = 20…”; 6 command(s) failed: python code/ingest.py --source nist --output data/raw/nist_polyesters.csv (rc=1); python code/ingest.py --source smiles --output data/raw/smiles_dataset.csv (rc=1); python code/preprocess.py --input data/raw/nist_polyesters.csv --output data/processed/graph_dataset.pt (rc=1); 1 declared deliverable(s) absent: data/processed/augmented_graph_dataset.csv

## Failing / missing run-book commands

- python code/ingest.py --source nist --output data/raw/nist_polyesters.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/ingest.py", line 48, in <module>
    def validate_smiles_and_convert(smiles: str) -> Optional[Chem.Mol]:
                                                             ^^^^
NameError: name 'Chem' is not defined
- python code/ingest.py --source smiles --output data/raw/smiles_dataset.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/ingest.py", line 48, in <module>
    def validate_smiles_and_convert(smiles: str) -> Optional[Chem.Mol]:
                                                             ^^^^
NameError: name 'Chem' is not defined
- python code/preprocess.py --input data/raw/nist_polyesters.csv --output data/processed/graph_dataset.pt -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 409, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 353, in main
    raw_data, processed_data, reports, state = get_project_paths()
                                               ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 36, in get_project_paths
    base = get_project_paths()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 36, in get_project_paths
    base = get_project_paths()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 36, in get_project_paths
    base = get_project_paths()
           ^^^^^^^^^^^^^^^^^^^
  [Previous line repeated 995 more times]
RecursionError: maximum recursion depth exceeded
- python code/preprocess.py --augment --input data/processed/graph_dataset.pt --output data/processed/augmented_graph_dataset.pt -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 409, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 353, in main
    raw_data, processed_data, reports, state = get_project_paths()
                                               ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 36, in get_project_paths
    base = get_project_paths()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 36, in get_project_paths
    base = get_project_paths()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 36, in get_project_paths
    base = get_project_paths()
           ^^^^^^^^^^^^^^^^^^^
  [Previous line repeated 995 more times]
RecursionError: maximum recursion depth exceeded
- python code/train.py --data data/processed/augmented_graph_dataset.pt --epochs 50 --cv 5 -> rc=1
    2026-08-20 23:34:50,304 - llmXive.__main__ - INFO - Random seed set to 42
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/train.py", line 359, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/train.py", line 287, in main
    raise FileNotFoundError(f"Neither {paths['processed'] / 'final_augmented_dataset.csv'} nor {paths['processed'] / 'pre_augmented_graph_dataset.csv'} found.")
FileNotFoundError: Neither /home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/data/processed/final_augmented_dataset.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/data/processed/pre_augmented_graph_dataset.csv found.
- python code/evaluate.py --model models/gnn_model.pt --data data/processed/graph_dataset.pt --output reports/motif_report.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/evaluate.py", line 416, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/evaluate.py", line 384, in main
    model_path = str(paths['data_reports'] / 'model_best.pth')
                     ~~~~~^^^^^^^^^^^^^^^^
KeyError: 'data_reports'

## Declared deliverables still missing

- data/processed/augmented_graph_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/augmented_graph_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/augment.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/save_augmented_dataset.py` — NOT invoked by the run-book
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/augmented_graph_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `final_dataset.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[data_reports]`
- PRODUCER(s) to edit: `code/evaluate.py`
- CONSUMER(s) that read it: `code/evaluate.py`
  → Edit the producer so every required name [data_reports] is in `final_dataset.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/data/processed/final_augmented_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/save_augmented_dataset.py`, `code/train.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/data/processed/final_augmented_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/save_augmented_dataset.py`, `code/train.py`.
