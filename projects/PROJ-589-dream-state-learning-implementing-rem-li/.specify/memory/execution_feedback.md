# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/train.py --seed 42 --steps 10 --mode debug (rc=1); python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 (rc=1)

## Failing / missing run-book commands

- python code/train.py --seed 42 --steps 10 --mode debug -> rc=1
 always resume when possible. If you want to force a new download, use `force_download=True`.
  warnings.warn(
We strongly recommend passing in an `attention_mask` since your input_ids may be padded. See https://huggingface.co/docs/transformers/troubleshooting#incorrect-output-when-padding-tokens-arent-masked.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 106, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 103, in main
    run_one(args.seed)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 86, in run_one
    metrics = trainer.run_training_loop(dataloader, max_steps=args.steps)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/models/trainer.py", line 200, in run_training_loop
    log_event("training_step", {
TypeError: log_event() missing 1 required positional argument: 'data'

- python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 -> rc=1
ownloads always resume when possible. If you want to force a new download, use `force_download=True`.
  warnings.warn(
We strongly recommend passing in an `attention_mask` since your input_ids may be padded. See https://huggingface.co/docs/transformers/troubleshooting#incorrect-output-when-padding-tokens-arent-masked.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 106, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 101, in main
    run_one(s)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py", line 86, in run_one
    metrics = trainer.run_training_loop(dataloader, max_steps=args.steps)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/models/trainer.py", line 200, in run_training_loop
    log_event("training_step", {
TypeError: log_event() missing 1 required positional argument: 'data'

