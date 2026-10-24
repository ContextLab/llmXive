# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/data/curate.py: self-declared fabricated metric — “…rompt_text - synthetic_score (placeholder value 0.5) - human_score (null/NaN)…”
- code/src/data/curate.py: self-declared fabricated metric — “…3️⃣ Combine, assign UUIDs and placeholder scores         # ------------------…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/data/curate.py: self-declared fabricated metric — “…rompt_text - synthetic_score (placeholder value 0.5) - human_score (null/NaN)…”; code/src/data/curate.py: self-declared fabricated metric — “…3️⃣ Combine, assign UUIDs and placeholder scores         # ------------------…”; 10 command(s) failed: python -m spacy download en_core_web_sm (rc=1); python -m code.src.data.download (rc=1); python -m code.src.data.curate (rc=1); 3 declared deliverable(s) absent: data/raw/checksums_manifest.json; data/raw/prompts_sample.parquet; data/results/curated_prompts.csv

## Failing / missing run-book commands

- python -m spacy download en_core_web_sm -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named spacy

- python -m code.src.data.download -> rc=1

2026-10-24 04:08:52,012 ERROR __main__: HF streaming loader failed: pyarrow requires NumPy 2.0 or newer, found 1.26.4
2026-10-24 04:08:52,013 ERROR __main__: Data collection failed: Unable to stream dataset timbrooks/instructpix2pix from Hugging Face

- python -m code.src.data.curate -> rc=1

2026-10-24 04:08:52,241 ERROR __main__: Curate step failed: Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python -m src.data.human_annotation -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named src.data.human_annotation

- python -m src.parser.graph_builder -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.parser.graph_builder' (ModuleNotFoundError: No module named 'src.parser')

- python -m src.verifier.baseline -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.verifier.baseline' (ModuleNotFoundError: No module named 'src.verifier')

- python -m src.verifier.augmented -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.verifier.augmented' (ModuleNotFoundError: No module named 'src.verifier')

- python -m src.analysis.stats -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.analysis.stats' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.report -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.analysis.report' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest tests/contract/test_evaluation_report.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_evaluation_report.py



## Declared deliverables still missing

- data/raw/checksums_manifest.json
- data/raw/prompts_sample.parquet
- data/results/curated_prompts.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/prompts_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/curate.py` — IS a run-book command
    - `code/src/data/download.py` — IS a run-book command
    - `code/tests/test_download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/prompts_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/curated_prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/curate.py` — IS a run-book command
    - `code/tests/test_curate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/curated_prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
