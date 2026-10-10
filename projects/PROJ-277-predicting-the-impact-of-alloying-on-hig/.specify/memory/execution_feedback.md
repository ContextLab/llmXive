# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic alloy data for pipeline…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with synthetic alloy data     """     random.seed(…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…hetic_samples: Number of synthetic samples generated     """     re…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…ning": "RESULTS BASED ON SYNTHETIC DATA - NOT VALIDATED AGAINST…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…ecommendation": "Replace synthetic data with real experimental d…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…ated {synthetic_samples} synthetic samples for pipeline validation.…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…al data; if unavailable, generates synthetic data.          Args:…”
- code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…Real data unavailable - generate synthetic     logger.info("Real da…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -c "import torch; print('CUDA available:', torch.cuda.is_available())"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 18 fabricated/simulated-result signal(s) — results are not real measurements: code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic alloy data for pipeline…”; code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with synthetic alloy data     """     random.seed(…”; code/data/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…hetic_samples: Number of synthetic samples generated     """     re…”; 3 command(s) failed: python code/main.py --mode ci (rc=1); python code/main.py --mode local (rc=1); python code/main.py --mode local --task interpret (rc=1)

## Failing / missing run-book commands

- python -c "import torch; print('CUDA available:', torch.cuda.is_available())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- python code/main.py --mode ci -> rc=1
2026-10-10 10:16:47 | INFO     | llmXive.oxidation | Logging infrastructure initialized.
2026-10-10 10:16:47 | INFO     | llmXive.oxidation | Mode: local, Log level: INFO

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-277-predicting-the-impact-of-alloying-on-hig/code/main.py", line 29, in <module>
    from data.processor import process_data, downsample_dataset, validate_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-277-predicting-the-impact-of-alloying-on-hig/code/data/processor.py", line 233, in <module>
    def validate_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
                                                               ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python code/main.py --mode local -> rc=1
2026-10-10 10:16:48 | INFO     | llmXive.oxidation | Logging infrastructure initialized.
2026-10-10 10:16:48 | INFO     | llmXive.oxidation | Mode: local, Log level: INFO

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-277-predicting-the-impact-of-alloying-on-hig/code/main.py", line 29, in <module>
    from data.processor import process_data, downsample_dataset, validate_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-277-predicting-the-impact-of-alloying-on-hig/code/data/processor.py", line 233, in <module>
    def validate_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
                                                               ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python code/main.py --mode local --task interpret -> rc=1
2026-10-10 10:16:48 | INFO     | llmXive.oxidation | Logging infrastructure initialized.
2026-10-10 10:16:48 | INFO     | llmXive.oxidation | Mode: local, Log level: INFO

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-277-predicting-the-impact-of-alloying-on-hig/code/main.py", line 29, in <module>
    from data.processor import process_data, downsample_dataset, validate_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-277-predicting-the-impact-of-alloying-on-hig/code/data/processor.py", line 233, in <module>
    def validate_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
                                                               ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

