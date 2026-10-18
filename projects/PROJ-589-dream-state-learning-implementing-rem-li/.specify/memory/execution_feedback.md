# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…model.to(device)      # Dummy data loader – 10 batches of r…”
- code/train.py: synthetic/fake INPUT data not authorized by the spec — “…s/trainer.py`. It uses a dummy dataset (random token IDs) so th…”
- code/train.py: synthetic/fake INPUT data not authorized by the spec — “…help="Batch size for the dummy data loader."     )     parse…”
- code/train.py: synthetic/fake INPUT data not authorized by the spec — “….to(device)      # Build dummy data loader     dataloader =…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/train.py --seed 42 --steps 10 --mode debug`
  - script usage: `train.py [-h] [--steps STEPS] [--batch-size BATCH_SIZE] [--seed SEED]`
  - argparse error: `train.py: error: unrecognized arguments: --mode debug`
- run-book command: `python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20`
  - script usage: `train.py [-h] [--steps STEPS] [--batch-size BATCH_SIZE] [--seed SEED]`
  - argparse error: `train.py: error: unrecognized arguments: --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…model.to(device)      # Dummy data loader – 10 batches of r…”; code/train.py: synthetic/fake INPUT data not authorized by the spec — “…s/trainer.py`. It uses a dummy dataset (random token IDs) so th…”; code/train.py: synthetic/fake INPUT data not authorized by the spec — “…help="Batch size for the dummy data loader."     )     parse…”; 3 command(s) failed: python code/train.py --seed 42 --steps 10 --mode debug (rc=2); python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 (rc=2); python code/eval.py --results-dir data/results/ (rc=1)

## Failing / missing run-book commands

- python code/train.py --seed 42 --steps 10 --mode debug -> rc=2

usage: train.py [-h] [--steps STEPS] [--batch-size BATCH_SIZE] [--seed SEED]
train.py: error: unrecognized arguments: --mode debug

- python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 -> rc=2

usage: train.py [-h] [--steps STEPS] [--batch-size BATCH_SIZE] [--seed SEED]
train.py: error: unrecognized arguments: --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20

- python code/eval.py --results-dir data/results/ -> rc=1
rating evaluation report

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 225, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 207, in main
    report_path = generate_evaluation_report(results, analysis, Path(args.output_dir))
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 143, in generate_evaluation_report
    interpretation = generate_interpretation(
                     ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval/reporting.py", line 31, in generate_interpretation
    significance = "statistically significant" if p_value < alpha else "not statistically significant"
                                                  ^^^^^^^^^^^^^^^
TypeError: '<' not supported between instances of 'NoneType' and 'float'

