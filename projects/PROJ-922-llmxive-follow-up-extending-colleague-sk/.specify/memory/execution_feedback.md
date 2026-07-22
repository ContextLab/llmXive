# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_generation/profiles.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic expert profiles.…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -c "import torch; print('CUDA available:', torch.cuda.is_available())"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data_generation/profiles.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic expert profiles.…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/data/generators/profile_generator.py --count [variable] --seed 42; python code/data/generators/task_generator.py --count [sufficient_sample_size] --seed 42; python code/evaluation/score.py --input data/interim/inference_outputs.jsonl; 1 command(s) failed: python code/scripts/run_inference.py --model Llama-3-8B-Q4 --backend cpu (rc=1); 3 declared deliverable(s) absent: data/processed/final_results.csv; data/processed/glm_results.json; data/processed/hypothesis_verification.json

## Failing / missing run-book commands

- python -c "import torch; print('CUDA available:', torch.cuda.is_available())" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'
- python code/data/generators/profile_generator.py --count [variable] --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/data/generators/profile_generator.py': [Errno 2] No such file or directory
- python code/data/generators/task_generator.py --count [sufficient_sample_size] --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/data/generators/task_generator.py': [Errno 2] No such file or directory
- python code/scripts/run_inference.py --model Llama-3-8B-Q4 --backend cpu -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/scripts/run_inference.py", line 21, in <module>
    from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/utils/config.py", line 11, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/evaluation/score.py --input data/interim/inference_outputs.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/evaluation/score.py': [Errno 2] No such file or directory
- python code/analysis/stats.py --input data/processed/evaluation_results.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-922-llmxive-follow-up-extending-colleague-sk/code/analysis/stats.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/final_results.csv
- data/processed/glm_results.json
- data/processed/hypothesis_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_hypothesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/glm_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_hypothesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/glm_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/hypothesis_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_hypothesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/hypothesis_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
