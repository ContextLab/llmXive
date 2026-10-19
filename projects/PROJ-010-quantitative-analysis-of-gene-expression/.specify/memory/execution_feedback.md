# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python src/data_pipeline/setup_data.py  --seed 42  --output_dir data/raw (rc=1); python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42 (rc=1)

## Failing / missing run-book commands

- python src/data_pipeline/setup_data.py  --seed 42  --output_dir data/raw -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/setup_data.py", line 1, in <module>
    from code.data_pipeline.setup_data import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline/__init__.py", line 8, in <module>
    from .data_pipeline import (
ModuleNotFoundError: No module named 'code.data_pipeline.data_pipeline'

- python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/preprocess.py", line 36, in <module>
    from code.data_pipeline import calculate_lisi, calculate_stage_variance
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline/__init__.py", line 8, in <module>
    from .data_pipeline import (
ModuleNotFoundError: No module named 'code.data_pipeline.data_pipeline'

