# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/ingestion/validate_data.py --input data/raw/sample.csv (rc=1); python code/analysis/lmm_model.py --input data/processed/cleaned.csv (rc=1); python code/reporting/generate_report.py --input output/results/analysis.json (rc=1)

## Failing / missing run-book commands

- python code/ingestion/validate_data.py --input data/raw/sample.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/ingestion/validate_data.py", line 28, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/utils/__init__.py", line 3, in <module>
    from .data_integrity import compute_checksum, verify_checksum, generate_checksum_manifest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/utils/data_integrity.py", line 7, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

- python code/analysis/lmm_model.py --input data/processed/cleaned.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/analysis/lmm_model.py", line 13, in <module>
    from utils.config import get_project_root, load_config, get_data_path
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/utils/__init__.py", line 3, in <module>
    from .data_integrity import compute_checksum, verify_checksum, generate_checksum_manifest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/utils/data_integrity.py", line 7, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

- python code/reporting/generate_report.py --input output/results/analysis.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/reporting/generate_report.py", line 14, in <module>
    from utils.config import get_project_root, get_output_path
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/utils/__init__.py", line 3, in <module>
    from .data_integrity import compute_checksum, verify_checksum, generate_checksum_manifest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-387-the-impact-of-visual-attention-allocatio/code/utils/data_integrity.py", line 7, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

