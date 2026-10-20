# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…ides helper functions to generate synthetic uniform and biased resid…”
- code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…t[int, int]:     """     Generate a synthetic *uniform* residue freque…”
- code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…t[int, int]:     """     Generate a synthetic *biased* residue frequen…”
- code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…tatistical analysis on a synthetic dataset and generate     the cor…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/stats_3_10.json, data/raw/residues_3_10.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/run_analysis.py --primes 3,5,7,11 --n 5000000`
  - script usage: `run_analysis.py [-h] [--N N] [--primes PRIMES [PRIMES ...]]`
  - argparse error: `run_analysis.py: error: argument --primes: invalid int value: '3,5,7,11'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…ides helper functions to generate synthetic uniform and biased resid…”; code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…t[int, int]:     """     Generate a synthetic *uniform* residue freque…”; code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…t[int, int]:     """     Generate a synthetic *biased* residue frequen…”; every produced artifact is gitignored (data/processed/stats_3_10.json, data/raw/residues_3_10.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/run_analysis.py --primes 3,5,7,11 --n 5000000 (rc=2); python -m pytest tests/unit/ (rc=1); python -m pytest tests/integration/ (rc=1)

## Failing / missing run-book commands

- python code/run_analysis.py --primes 3,5,7,11 --n 5000000 -> rc=2

2026-10-20 10:17:42,394 INFO matplotlib.font_manager: Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-20 10:17:43,273 INFO matplotlib.font_manager: generated new fontManager
usage: run_analysis.py [-h] [--N N] [--primes PRIMES [PRIMES ...]]
                       [--memory_limit_mb MEMORY_LIMIT_MB] [--seed SEED]
                       [--memory_check_interval MEMORY_CHECK_INTERVAL]
run_analysis.py: error: argument --primes: invalid int value: '3,5,7,11'

- python -m pytest tests/unit/ -> rc=1
sts/unit/test_stats_fallback.py::test_chi2_exact_execution - Asserti...
FAILED tests/unit/test_stats_method.py::test_chi_squared_method_exact - Value...
FAILED tests/unit/test_stats_method.py::test_full_statistical_result_includes_method
FAILED tests/unit/test_stats_save.py::test_save_statistical_result - TypeErro...
FAILED tests/unit/test_stats_save.py::test_load_statistical_result - TypeErro...
FAILED tests/unit/test_stats_save.py::test_run_sieve_analysis_integration - F...
FAILED tests/unit/test_stats_t022.py::TestT022PrimaryPassFail::test_integration_with_statistical_result
FAILED tests/unit/test_stats_t022.py::TestT022PrimaryPassFail::test_integration_with_biased_distribution
FAILED tests/unit/test_stats_t022.py::TestT022bBonferroniCorrection::test_bonferroni_stricter_threshold
FAILED tests/unit/test_stats_t022.py::TestT022EdgeCases::test_custom_alpha - ...
FAILED tests/unit/test_visualize.py::test_plot_residual_qq_creates_file - Att...
FAILED tests/unit/test_visualize.py::test_plot_residual_qq_empty_residuals - ...
FAILED tests/unit/test_visualize.py::test_plot_residual_qq_single_value - Att...
================= 32 failed, 156 passed, 13 warnings in 5.04s ==================


- python -m pytest tests/integration/ -> rc=1
ePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_pipeline.py::test_sieve_module_exports - Import...
FAILED tests/integration/test_pipeline.py::test_stats_module_exports - Import...
FAILED tests/integration/test_pipeline.py::test_end_to_end_small_run - System...
FAILED tests/integration/test_quickstart_validation.py::test_quickstart_validation_smoke
FAILED tests/integration/test_quickstart_validation.py::test_error_handling_in_validation
FAILED tests/integration/test_t013_save_residues.py::TestT013Integration::test_full_pipeline_save_residues
FAILED tests/integration/test_t013_save_residues.py::TestT013Integration::test_multiple_primes_save
FAILED tests/integration/test_t013_save_residues.py::TestT013Integration::test_large_n_save
FAILED tests/integration/test_t020_integration.py::test_t020_full_pipeline_integration
FAILED tests/integration/test_t020_integration.py::test_t020_save_load_result
================== 10 failed, 11 passed, 13 warnings in 0.77s ==================


