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

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/run_analysis.py --primes 3,5,7,11 --n 5000000`
  - script usage: `run_analysis.py [-h] [--N N] [--primes PRIMES [PRIMES ...]]`
  - argparse error: `run_analysis.py: error: argument --primes: invalid int value: '3,5,7,11'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…ides helper functions to generate synthetic uniform and biased resid…”; code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…t[int, int]:     """     Generate a synthetic *uniform* residue freque…”; code/synthetic_validation.py: synthetic/fake INPUT data not authorized by the spec — “…t[int, int]:     """     Generate a synthetic *biased* residue frequen…”; 3 command(s) failed: python code/run_analysis.py --primes 3,5,7,11 --n 5000000 (rc=2); python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/ (rc=2)

## Failing / missing run-book commands

- python code/run_analysis.py --primes 3,5,7,11 --n 5000000 -> rc=2

2026-10-25 03:11:09,117 INFO matplotlib.font_manager: Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-25 03:11:09,191 INFO matplotlib.font_manager: generated new fontManager
usage: run_analysis.py [-h] [--N N] [--primes PRIMES [PRIMES ...]]
                       [--memory_limit_mb MEMORY_LIMIT_MB] [--seed SEED]
                       [--memory_check_interval MEMORY_CHECK_INTERVAL]
run_analysis.py: error: argument --primes: invalid int value: '3,5,7,11'

- python -m pytest tests/unit/ -> rc=2
1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_stats_bootstrap.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 2 errors in 0.93s ========================


- python -m pytest tests/integration/ -> rc=2
ntconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_synthetic_stats.py
ERROR tests/integration/test_t020_integration.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 2 errors in 0.75s ========================



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `sympy` to the project's `requirements.txt` and `pip install sympy`.
- **Verified**: this loads **1000** real records with fields: n, phi.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import sympy as sp
records = [{'n': n, 'phi': sp.totient(n)} for n in range(1, 1001)]
print(f'RECORDS={len(records)}')
print('FIELDS=n,phi')
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
