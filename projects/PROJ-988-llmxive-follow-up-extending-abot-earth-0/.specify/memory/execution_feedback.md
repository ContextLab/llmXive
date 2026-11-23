# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_acquire_cloud_masks.py: self-declared fabricated metric — “…# We return a placeholder result structure that T016 will fill…”
- code/01_validate_masks.py: self-declared fabricated metric — “…e return a failure state or a placeholder result indicating missing data.…”
- code/01_acquire_cloud_masks.py: synthetic/fake INPUT data not authorized by the spec — “…# Load synthetic data (assuming it's in a know…”
- code/01_acquire_cloud_masks.py: synthetic/fake INPUT data not authorized by the spec — “…# Placeholder for synthetic data loading logic (to be imp…”
- code/01_validate_masks.py: synthetic/fake INPUT data not authorized by the spec — “…np.ndarray:     """     Generate a synthetic mask with similar proper…”
- code/01_validate_masks.py: synthetic/fake INPUT data not authorized by the spec — “…istributions)          # Generate synthetic masks to compare against…”
- code/01_validate_masks.py: synthetic/fake INPUT data not authorized by the spec — “…against     # We need to generate synthetic masks that mimic the rea…”
- code/01_validate_masks.py: synthetic/fake INPUT data not authorized by the spec — “…4f}")                  # Generate synthetic masks         # We assum…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.get_default_device()}')"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/01_acquire_cloud_masks.py: self-declared fabricated metric — “…# We return a placeholder result structure that T016 will fill…”; code/01_validate_masks.py: self-declared fabricated metric — “…e return a failure state or a placeholder result indicating missing data.…”; code/01_acquire_cloud_masks.py: synthetic/fake INPUT data not authorized by the spec — “…# Load synthetic data (assuming it's in a know…”; 5 run-book script(s) missing (plan/impl path mismatch): python code/data/download_sentinel.py --count 50 --output data/raw/sentinel_aligned; python code/data/synthesize_degradation.py --input data/raw/sentinel_aligned --output data/processed/degraded_scenes --seeds 12345; python code/pipeline/run_full_experiment.py  --input data/processed/degraded_scenes  --lidar data/raw/sentinel_aligned/lidar  --output data/results  --max-samples 20  --log-performance; 9 declared deliverable(s) absent: data/manifest.json; data/processed/aligned_pairs.csv; data/processed/alignment_report.csv

## Failing / missing run-book commands

- python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.get_default_device()}')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- python code/data/download_sentinel.py --count 50 --output data/raw/sentinel_aligned -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-988-llmxive-follow-up-extending-abot-earth-0/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/data/download_sentinel.py': [Errno 2] No such file or directory

- python code/data/synthesize_degradation.py --input data/raw/sentinel_aligned --output data/processed/degraded_scenes --seeds 12345 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-988-llmxive-follow-up-extending-abot-earth-0/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/data/synthesize_degradation.py': [Errno 2] No such file or directory

- python code/pipeline/run_full_experiment.py  --input data/processed/degraded_scenes  --lidar data/raw/sentinel_aligned/lidar  --output data/results  --max-samples 20  --log-performance -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-988-llmxive-follow-up-extending-abot-earth-0/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/pipeline/run_full_experiment.py': [Errno 2] No such file or directory

- python code/analysis/statistical_tests.py --input data/results/metrics.csv --output data/results/report.pdf -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-988-llmxive-follow-up-extending-abot-earth-0/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/analysis/statistical_tests.py': [Errno 2] No such file or directory

- python code/analysis/plot_thresholds.py --input data/results/metrics.csv --output data/results/threshold_curve.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-988-llmxive-follow-up-extending-abot-earth-0/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/analysis/plot_thresholds.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/manifest.json
- data/processed/aligned_pairs.csv
- data/processed/alignment_report.csv
- data/processed/degraded_manifest.json
- data/processed/patch_manifest.csv
- data/processed/raw_manifest.csv
- data/results/mask_similarity_score.json
- data/results/metrics.csv
- data/results/performance_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_acquire_cloud_masks.py` — NOT invoked by the run-book
    - `code/01_data_curation.py` — NOT invoked by the run-book
    - `code/01_patch_extraction.py` — NOT invoked by the run-book
    - `code/02_degradation_pipeline.py` — NOT invoked by the run-book
    - `code/03_3dgs_baseline.py` — NOT invoked by the run-book
    - `code/03_inpainting_restoration.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
    - `code/03_render_interface.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — NOT invoked by the run-book
    - `code/01_patch_extraction.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alignment_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alignment_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/degraded_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_degradation_pipeline.py` — NOT invoked by the run-book
    - `code/03_3dgs_baseline.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
    - `code/04_metrics_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/degraded_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patch_manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_patch_extraction.py` — NOT invoked by the run-book
    - `code/02_degradation_pipeline.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patch_manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mask_similarity_score.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_validate_masks.py` — NOT invoked by the run-book
    - `code/02b_validate_masks.py` — NOT invoked by the run-book
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mask_similarity_score.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_3dgs_baseline.py` — NOT invoked by the run-book
    - `code/03_inpainting_restoration.py` — NOT invoked by the run-book
    - `code/03_performance_logger.py` — NOT invoked by the run-book
    - `code/04_metrics_evaluation.py` — NOT invoked by the run-book
    - `code/setup_data_dirs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/performance_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_manifest_generator.py` — NOT invoked by the run-book
    - `code/03_performance_aggregator.py` — NOT invoked by the run-book
    - `code/03_performance_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/performance_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
