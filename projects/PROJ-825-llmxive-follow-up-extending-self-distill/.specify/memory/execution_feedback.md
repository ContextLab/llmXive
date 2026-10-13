# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: self-declared fabricated metric — “…s.max_steps):         # Dummy placeholder values – in a real implementation t…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: self-declared fabricated metric — “…s.max_steps):         # Dummy placeholder values – in a real implementation t…”; 1 run-book script(s) missing (plan/impl path mismatch): python metrics/statistical_test.py  --grpo-dir data/processed/grpo-alfworld  --baseline-dir data/processed/baseline-alfworld  --student-only-dir data/processed/student-only-alfworld  --replay-dir data/processed/student-only-replay-alfworld  --output data/processed/comparison_report.json; 4 command(s) failed: python code/main.py --variant grpo --env alfworld --seed 42 --max-steps 1000 --output-dir data/processed/grpo-alfworld (rc=1); python code/main.py --variant baseline --env alfworld --seed 42 --max-steps 1000 --output-dir data/processed/baseline-alfworld (rc=1); python code/main.py --variant student-only --env alfworld --seed 42 --max-steps 1000 --output-dir data/processed/student-only-alfworld (rc=1); 1 declared deliverable(s) absent: data/processed/memory_dry_run.json

## Failing / missing run-book commands

- python code/main.py --variant grpo --env alfworld --seed 42 --max-steps 1000 --output-dir data/processed/grpo-alfworld -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 105, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 44, in main
    logger.info("Starting training run", extra={
    ^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'info'

- python code/main.py --variant baseline --env alfworld --seed 42 --max-steps 1000 --output-dir data/processed/baseline-alfworld -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 105, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 44, in main
    logger.info("Starting training run", extra={
    ^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'info'

- python code/main.py --variant student-only --env alfworld --seed 42 --max-steps 1000 --output-dir data/processed/student-only-alfworld -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 105, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 44, in main
    logger.info("Starting training run", extra={
    ^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'info'

- python code/main.py --variant student-only-replay --env alfworld --input-trajectories data/processed/baseline-alfworld/trajectories.jsonl --output-dir data/processed/student-only-replay-alfworld -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 105, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/main.py", line 44, in main
    logger.info("Starting training run", extra={
    ^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'info'

- python metrics/statistical_test.py  --grpo-dir data/processed/grpo-alfworld  --baseline-dir data/processed/baseline-alfworld  --student-only-dir data/processed/student-only-alfworld  --replay-dir data/processed/student-only-replay-alfworld  --output data/processed/comparison_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/metrics/statistical_test.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/memory_dry_run.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/memory_dry_run.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_memory_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_dry_run.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
