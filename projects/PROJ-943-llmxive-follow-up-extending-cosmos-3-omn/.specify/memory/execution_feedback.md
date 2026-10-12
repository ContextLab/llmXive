# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/scripts/download_data.py; python code/scripts/transform_actions.py  --input code/data/raw/bridge_subset.jsonl  --output code/data/processed/symbolic_dataset.jsonl  --threshold 0.5; python code/scripts/train_symbolic.py  --data code/data/processed/symbolic_dataset.jsonl  --model distilbert-base-uncased  --epochs 5  --batch-size 16; 2 command(s) failed: python code/scripts/evaluate.py  --model code/models/symbolic/best_model  --data code/data/processed/symbolic_dataset.jsonl  --output code/reports/metrics.json (rc=1); python code/scripts/analyze_errors.py  --model code/models/symbolic/best_model  --data code/data/processed/symbolic_dataset.jsonl  --output code/reports/error_analysis/ (rc=1)

## Failing / missing run-book commands

- python code/scripts/download_data.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/code/scripts/download_data.py': [Errno 2] No such file or directory

- python code/scripts/transform_actions.py  --input code/data/raw/bridge_subset.jsonl  --output code/data/processed/symbolic_dataset.jsonl  --threshold 0.5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/code/scripts/transform_actions.py': [Errno 2] No such file or directory

- python code/scripts/train_symbolic.py  --data code/data/processed/symbolic_dataset.jsonl  --model distilbert-base-uncased  --epochs 5  --batch-size 16 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/code/scripts/train_symbolic.py': [Errno 2] No such file or directory

- python code/scripts/evaluate.py  --model code/models/symbolic/best_model  --data code/data/processed/symbolic_dataset.jsonl  --output code/reports/metrics.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/code/scripts/evaluate.py", line 306, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/code/scripts/evaluate.py", line 228, in main
    log_script_start(logger, "T016d - Statistical Test Sequence")
TypeError: log_script_start() takes 1 positional argument but 2 were given

- python code/scripts/analyze_errors.py  --model code/models/symbolic/best_model  --data code/data/processed/symbolic_dataset.jsonl  --output code/reports/error_analysis/ -> rc=1

2026-10-12 13:39:14,057 - llmXive - INFO - --- Script Start: analyze_errors ---
Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn/code/data/processed/misclassified_samples.jsonl
Please ensure T016e (extract_errors.py) has been run successfully.

