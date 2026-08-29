# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/features.py: self-declared fabricated metric — “…_j * (chi_i - chi_j)^2) * 10 (arbitrary scaling)     This is a proxy for chem…”
- code/features.py: self-declared fabricated metric — “…le)     return h_mix * 10.0 # Arbitrary scaling factor to match typical entha…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingestion.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/features.py: self-declared fabricated metric — “…_j * (chi_i - chi_j)^2) * 10 (arbitrary scaling)     This is a proxy for chem…”; code/features.py: self-declared fabricated metric — “…le)     return h_mix * 10.0 # Arbitrary scaling factor to match typical entha…”; 4 command(s) failed: python code/ingestion.py (rc=1); python code/features.py (rc=1); python code/train.py (rc=1); 1 declared deliverable(s) absent: data/processed/processed_alloys.csv

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
    env/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 222, in <module>
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 202, in run_ingestion
    df = load_glass_data()
         ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 108, in load_glass_data
    raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")
ValueError: Data fetch failed: matsci/glass-forming-ability unavailable. Error: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.
- python code/features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 231, in <module>
    def compute_features(df: pd.DataFrame) -> pd.DataFrame:
                             ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?
- python code/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 23, in <module>
    from code.features import compute_features
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 231, in <module>
    def compute_features(df: pd.DataFrame) -> pd.DataFrame:
                             ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?
- python code/analyze.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py", line 21, in <module>
    logging.FileHandler('projects/PROJ-510-predicting-the-glass-forming-region-of-a/logs/analysis.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/projects/PROJ-510-predicting-the-glass-forming-region-of-a/logs/analysis.log'

## Declared deliverables still missing

- data/processed/processed_alloys.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/processed_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/analyze.py` — IS a run-book command
    - `code/features.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/processed_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
