# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…rator for Ground Truth.  Generates three separate synthetic populations (N=1,000,000…”
- code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic UCI Adult-like populatio…”
- code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic UCI Iris-like population…”
- code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic UCI Wine Quality-like po…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/synthetic_populations/adult_population.csv, data/synthetic_populations/iris_population.csv, data/synthetic_populations/wine_population.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…rator for Ground Truth.  Generates three separate synthetic populations (N=1,000,000…”; code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic UCI Adult-like populatio…”; code/data/synthetic_pop.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic UCI Iris-like population…”; every produced artifact is gitignored (data/synthetic_populations/adult_population.csv, data/synthetic_populations/iris_population.csv, data/synthetic_populations/wine_population.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python code/main.py (rc=1); python code/analysis/convergence_check.py (rc=1)

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/main.py", line 22, in <module>
    from data.dp_noise import inject_laplace_noise, inject_gaussian_noise
ModuleNotFoundError: No module named 'data.dp_noise'
- python code/analysis/convergence_check.py -> rc=1
    2026-09-04 15:03:56,947 - INFO - Starting convergence check analysis.
2026-09-04 15:03:56,947 - ERROR - Results file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/artifacts/coverage_results.csv. Did you run the main simulation (T013a/T042)?

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/artifacts/coverage_results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/tests/test_glm_analysis.py`, `code/tests/test_coverage_pipeline.py`, `code/analysis/summary_table.py`, `code/analysis/convergence_check.py`, `code/analysis/glm_extractor.py`, `code/analysis/coverage_aggregator.py`, `code/analysis/glm_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/artifacts/coverage_results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/tests/test_coverage_pipeline.py`, `code/analysis/summary_table.py`, `code/analysis/convergence_check.py`, `code/analysis/plotting.py`, `code/analysis/glm_extractor.py`, `code/analysis/coverage_aggregator.py`, `code/analysis/glm_analysis.py`.
