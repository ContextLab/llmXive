# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic delay discounting data b…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic procrastination scale da…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic n-back working memory ta…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…fails.     """     # For synthetic data, we already have k. For…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…Since we are generating synthetic data with k already, we retur…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic data...")     delay_df = gene…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/ingestion.py --mode generate --n [N] --seed 42, where N represents a sufficiently large sample size to ensure statistical power for the study.`
  - script usage: `ingestion.py [-h] [--mode {generate,validate}] [--n N] [--seed SEED]`
  - argparse error: `ingestion.py: error: argument --n: invalid int value: '[N]'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic delay discounting data b…”; code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic procrastination scale da…”; code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic n-back working memory ta…”; 2 command(s) failed: python code/ingestion.py --mode generate --n [N] --seed 42, where N represents a sufficiently large sample size to ensure statistical power for the study. (rc=2); python code/main.py (rc=1)

## Failing / missing run-book commands

- python code/ingestion.py --mode generate --n [N] --seed 42, where N represents a sufficiently large sample size to ensure statistical power for the study. -> rc=2
    usage: ingestion.py [-h] [--mode {generate,validate}] [--n N] [--seed SEED]
ingestion.py: error: argument --n: invalid int value: '[N]'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/main.py", line 19, in <module>
    from modeling import run_full_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/modeling.py", line 41, in <module>
    def load_and_prepare_data() -> Tuple[pd.DataFrame, bool]:
                                   ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?
