# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipeline.run_all  --dataset_name something-something-v2  --subset_size 200  --train_split 0.8  --val_split 0.1  --test_split 0.1  --lambda_values 0.1 0.5 1.0  --seeds 1 2 3 4 5 6 7 8 9 10  --optical_flow_divergence_threshold 0.15  --feature_similarity_threshold 0.9  --output_dir ./output (rc=1)

## Failing / missing run-book commands

- python -m src.pipeline.run_all  --dataset_name something-something-v2  --subset_size 200  --train_split 0.8  --val_split 0.1  --test_split 0.1  --lambda_values 0.1 0.5 1.0  --seeds 1 2 3 4 5 6 7 8 9 10  --optical_flow_divergence_threshold 0.15  --feature_similarity_threshold 0.9  --output_dir ./output -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i/src/pipeline/run_all.py", line 48, in <module>
    from src.train.trainer import main as trainer_main
ModuleNotFoundError: No module named 'src.train'

