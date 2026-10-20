# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 (rc=-1)

## Failing / missing run-book commands

- python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 -> rc=-1
ing...
2026-10-20 02:29:52,807 - models.trainer - WARNING - Low entropy (0.0021 < 0.5). Retrying...
2026-10-20 02:29:53,445 - models.trainer - WARNING - Low entropy (0.0016 < 0.5). Retrying...
2026-10-20 02:29:53,445 - models.trainer - WARNING - Low entropy (0.0016 < 0.5). Retrying...
2026-10-20 02:29:54,084 - models.trainer - INFO - [training_step] {"step": 9, "phase": "WAKE", "loss": 5.534078081836924e-05, "entropy": 0.0011952482163906097}
2026-10-20 02:29:54,084 - models.trainer - INFO - [training_step] {"step": 9, "phase": "WAKE", "loss": 5.534078081836924e-05, "entropy": 0.0011952482163906097}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/huggingface_hub/file_download.py:949: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
  warnings.warn(
We strongly recommend passing in an `attention_mask` since your input_ids may be padded. See https://huggingface.co/docs/transformers/troubleshooting#incorrect-output-when-padding-tokens-arent-masked.

[TIMEOUT after 120s]
