# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/05_combine_and_normalize_roi.py: self-declared fabricated metric — “…rom the final CSV as they are not real measurements.     real_data_mask = (df['s…”
- code/train_sae.py: synthetic/fake INPUT data not authorized by the spec — “…if available, otherwise generates     a synthetic sample strictly for init…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/05_combine_and_normalize_roi.py: self-declared fabricated metric — “…rom the final CSV as they are not real measurements.     real_data_mask = (df['s…”; code/train_sae.py: synthetic/fake INPUT data not authorized by the spec — “…if available, otherwise generates     a synthetic sample strictly for init…”; 8 run-book script(s) missing (plan/impl path mismatch): python code/data_ingestion/download_neural.py   # OpenNeuro ds001495; python code/data_ingestion/download_text.py    # ROCStories (pre‑training only); python code/data_ingestion/preprocess.py; 1 declared deliverable(s) absent: data/processed/mask_paths.json

## Failing / missing run-book commands

- python code/data_ingestion/download_neural.py   # OpenNeuro ds001495 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/data_ingestion/download_neural.py': [Errno 2] No such file or directory

- python code/data_ingestion/download_text.py    # ROCStories (pre‑training only) -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/data_ingestion/download_text.py': [Errno 2] No such file or directory

- python code/data_ingestion/preprocess.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/data_ingestion/preprocess.py': [Errno 2] No such file or directory

- python code/models/generator.py --model brain_inspired  --input data/processed/text/fMRI_story_transcripts.jsonl  --output data/processed/brain_inspired_hidden.npy -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/models/generator.py': [Errno 2] No such file or directory

- python code/models/generator.py --model baseline  --input data/processed/text/fMRI_story_transcripts.jsonl  --output data/processed/baseline_hidden.npy -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/models/generator.py': [Errno 2] No such file or directory

- python code/analysis/rsa_computation.py   # computes RSA matrices -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/analysis/rsa_computation.py': [Errno 2] No such file or directory

- python code/analysis/permutation_test.py   # A large number of permutations with early‑stopping -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/analysis/permutation_test.py': [Errno 2] No such file or directory

- python code/analysis/visualization.py      # generates heatmaps & bar plot -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-595-neural-narrative-networks-brain-inspired/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-595-neural-narrative-networks-brain-inspired/code/analysis/visualization.py': [Errno 2] No such file or directory

- python -c "cnt=sum(1 for _ in open('data/processed/text/fMRI_story_transcripts.jsonl')); print('Test stories:', cnt)" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/text/fMRI_story_transcripts.jsonl'


## Declared deliverables still missing

- data/processed/mask_paths.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/mask_paths.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_load_masks.py` — NOT invoked by the run-book
    - `code/04_extract_roi_timecourses.py` — NOT invoked by the run-book
    - `code/04_extract_roi_timecourses_dlpfc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mask_paths.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
