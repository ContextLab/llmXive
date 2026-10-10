# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock data for demonstration if rea…”
- code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…old results found. Using simulated data for demonstration.")…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -c "import torch; import rdkit; print('CPU:', torch.cuda.is_available())"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock data for demonstration if rea…”; code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…old results found. Using simulated data for demonstration.")…”; 5 command(s) failed: python code/src/data/download.py --source ufukhaman (rc=1); python code/src/data/parse.py --input data/raw/uspto_subset.parquet --output data/processed/graphs.h5 (rc=1); python code/src/analysis/train.py --epochs 200 --patience 5 --device cpu --cv-folds 5 (rc=1)

## Failing / missing run-book commands

- python -c "import torch; import rdkit; print('CPU:', torch.cuda.is_available())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- python code/src/data/download.py --source ufukhaman -> rc=1
File Error: Data file not found at --source. Ensure T012 (download) has been executed successfully.


- python code/src/data/parse.py --input data/raw/uspto_subset.parquet --output data/processed/graphs.h5 -> rc=1

[06:40:28] SMILES Parse Error: syntax error while parsing: invalid_smiles
[06:40:28] SMILES Parse Error: Failed parsing SMILES 'invalid_smiles' for input: 'invalid_smiles'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/data/parse.py", line 208, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/data/parse.py", line 198, in main
    parsed_df, valid, invalid = parse_reaction_dataframe(df)
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/data/parse.py", line 117, in parse_reaction_dataframe
    log_invalid_smiles(logger, idx, reactants_smiles, product_smiles)
TypeError: log_invalid_smiles() takes from 1 to 2 positional arguments but 4 were given

- python code/src/analysis/train.py --epochs 200 --patience 5 --device cpu --cv-folds 5 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/analysis/train.py", line 17, in <module>
    from src.utils.seeding import set_seed, get_seed_hash, DeterministicContext
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/utils/seeding.py", line 15, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/models/explainers.py --model models/mpnn_fold_1.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/models/explainers.py", line 19, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/analysis/uncertainty.py --model models/mpnn_fold_1.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/analysis/uncertainty.py", line 17, in <module>
    from src.utils.seeding import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/utils/seeding.py", line 15, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

