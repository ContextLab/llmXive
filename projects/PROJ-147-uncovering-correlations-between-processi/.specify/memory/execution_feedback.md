# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “….info("Will fall back to synthetic data generation")         ret…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “….info("Will fall back to synthetic data generation")         ret…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “….info("Will fall back to synthetic data generation")         ret…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data when real data is u…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…t_path: Path to save the synthetic data         n_samples: Total…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…pd.DataFrame with synthetic data     """     logger.info(…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic data...")          # Generate…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…logger.error("Synthetic data validation failed - insu…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 fabricated/simulated-result signal(s) — results are not real measurements: code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “….info("Will fall back to synthetic data generation")         ret…”; code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “….info("Will fall back to synthetic data generation")         ret…”; code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “….info("Will fall back to synthetic data generation")         ret…”; 2 command(s) failed: python code/data/synthetic.py --output data/raw/synthetic_data.csv --samples 250 (rc=1); python code/main.py --data data/raw/synthetic_data.csv --output data/processed/ --model-output code/models/ (rc=1)

## Failing / missing run-book commands

- python code/data/synthetic.py --output data/raw/synthetic_data.csv --samples 250 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-147-uncovering-correlations-between-processi/code/data/synthetic.py", line 6, in <module>
    from code.utils.logging import get_logger, log_warning_structured
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-147-uncovering-correlations-between-processi/code/utils/logging.py", line 63, in <module>
    def log_warning_structured(message: str, context: Dict[str, Any] = None) -> None:
                                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/main.py --data data/raw/synthetic_data.csv --output data/processed/ --model-output code/models/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-147-uncovering-correlations-between-processi/code/main.py", line 18, in <module>
    from code.config import ensure_dirs, get_config
ImportError: cannot import name 'get_config' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-147-uncovering-correlations-between-processi/code/config.py)

## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
