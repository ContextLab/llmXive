# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…produces a deterministic synthetic surrogate dataset without attempting to do…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…---------------------- # Synthetic data generation (used when ``…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…tr) -> None:     """     Generate a deterministic synthetic dataset without external…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…ult=False,         help="Generate deterministic synthetic data without downloading…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…nly`` takes precedence – generate synthetic data.     if args.verify…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.curators.curate_failed_figures  --num-tasks <appropriate count>  --output-dir data/`
  - script usage: `curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]`
  - argparse error: `curate_failed_figures.py: error: argument --num-tasks: invalid int value: '<appropriate'`
- run-book command: `python -m src.simulation.simulate_participants  --participants a sufficient sample size  --seed 42  --log-dir data/logs/`
  - script usage: `simulate_participants.py [-h] [--participants PARTICIPANTS]`
  - argparse error: `simulate_participants.py: error: argument --participants: invalid int value: 'a'`
- run-book command: `python -m src.analysis.wilcoxon_analysis --validation-dir data/validation/ --output-dir outputs/`
  - script usage: `wilcoxon_analysis.py [-h] --output-dir OUTPUT_DIR`
  - argparse error: `wilcoxon_analysis.py: error: unrecognized arguments: --validation-dir data/validation/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…produces a deterministic synthetic surrogate dataset without attempting to do…”; src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…---------------------- # Synthetic data generation (used when ``…”; src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…tr) -> None:     """     Generate a deterministic synthetic dataset without external…”; 6 command(s) failed: python -m src.curators.curate_failed_figures  --num-tasks <appropriate count>  --output-dir data/ (rc=2); python -m src.simulation.simulate_participants  --participants a sufficient sample size  --seed 42  --log-dir data/logs/ (rc=2); python -m src.analysis.retention_check --log-dir data/logs/ --min-valid 25 (rc=1)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures  --num-tasks <appropriate count>  --output-dir data/ -> rc=2

usage: curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]
                                [-o OUTPUT_DIR] [--verify-only]
curate_failed_figures.py: error: argument --num-tasks: invalid int value: '<appropriate'

- python -m src.simulation.simulate_participants  --participants a sufficient sample size  --seed 42  --log-dir data/logs/ -> rc=2

usage: simulate_participants.py [-h] [--participants PARTICIPANTS]
                                [--seed SEED] [--log-dir LOG_DIR]
simulate_participants.py: error: argument --participants: invalid int value: 'a'

- python -m src.analysis.retention_check --log-dir data/logs/ --min-valid 25 -> rc=1

Error processing validation file: "Successful validation record missing session identifier: {'validation_id': '162bf21e-b59a-44e2-949b-d552b41b1856', 'task_id': '0', 'vector_match': True, 'semantic_score': 1.0, 'semantic_pass': True, 'overall_success': True}"

- python -m src.analysis.wilcoxon_analysis --validation-dir data/validation/ --output-dir outputs/ -> rc=2

usage: wilcoxon_analysis.py [-h] --output-dir OUTPUT_DIR
wilcoxon_analysis.py: error: unrecognized arguments: --validation-dir data/validation/

- python -m pytest -q tests/contract -> rc=2

==================================== ERRORS ====================================
_ ERROR collecting projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/tests/contract/test_analysis_result_schema.py _
tests/contract/test_analysis_result_schema.py:11: in <module>
    with schema_path.open("r", encoding="utf-8") as f:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py:1044: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
E   FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/specs/001-llmxive-cognitive-load/contracts/analysis_result.schema.yaml'
=========================== short test summary info ============================
ERROR tests/contract/test_analysis_result_schema.py - FileNotFoundError: [Err...
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s


- python -m src.run_pipeline --config config.yaml -> rc=-1
0.0%0.0%0.1%0.1%0.1%0.1%0.1%0.2%0.2%0.2%0.2%0.2%0.2%0.3%0.3%0.3%0.3%0.3%0.4%0.4%0.4%0.4%0.4%0.5%0.5%0.5%0.5%0.5%0.6%0.6%0.6%0.6%0.6%0.7%0.7%0.7%0.7%0.7%0.7%0.8%0.8%0.8%0.8%0.8%0.9%0.9%0.9%0.9%0.9%1.0%1.0%1.0%1.0%1.0%1.1%1.1%1.1%1.1%1.1%1.2%1.2%1.2%1.2%1.2%1.2%1.3%1.3%1.3%1.3%1.3%1.4%1.4%1.4%1.4%1.4%1.5%1.5%1.5%1.5%1.5%1.6%1.6%1.6%1.6%1.6%1.7%1.7%1.7%1.7%1.7%1.7%1.8%1.8%1.8%1.8%1.8%1.9%1.9%1.9%1.9%1.9%2.0%2.0%2.0%2.0%2.0%2.1%2.1%2.1%2.1%2.1%2.2%2.2%2.2%2.2%2.2%2.2%2.3%2.3%2.3%2.3%2.3%2.4%2.4%2.4%2.4%2.4%2.5%2.5%2.5%2.5%2.5%2.6%2.6%2.6%2.6%2.6%2.7%2.7%2.7%2.7%2.7%2.7%2.8%2.8%2.8%2.8%2.8%2.9%2.9%2.9%2.9%2.9%3.0%3.0%3.0%3.0%3.0%3.1%3.1%3.1%3.1%3.1%3.2%3.2%3.2%3.2%3.2%3.2%3.3%3.3%3.3%3.3%3.3%3.4%3.4%3.4%3.4%3.4%3.5%3.5%3.5%3.5%3.5%3.6%3.6%3.6%3.6%3.6%3.7%3.7%3.7%3.7%3.7%3.7%3.8%3.8%3.8%3.8%3.8%3.9%3.9%3.9%3.9%3.9%4.0%4.0%4.0%4.0%4.0%4.1%4.1%4.1%4.1%4.1%4.2%4.2%4.2%4.2%4.2%4.2%4.3%4.3%4.3%4.3%4.3%4.4%4.4%4.4%4.4%4.4%4.5%4.5%4.5%4.5%4.5%
[TIMEOUT after 120s]
