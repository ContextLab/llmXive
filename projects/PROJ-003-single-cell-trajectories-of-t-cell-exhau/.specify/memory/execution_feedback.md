# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python code/subset_tcells.py --input data/processed/ --output data/processed/; python code/batch_correct.py --input data/processed/ --output data/processed/; python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; 2 command(s) failed: python code/download_data.py  --datasets GSE136103 GSE127465 GSE111075 GSE138852  --output data/raw/ (rc=-1); python code/velocity.py --input data/processed/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/download_data.py  --datasets GSE136103 GSE127465 GSE111075 GSE138852  --output data/raw/ -> rc=-1
SE111nnn/GSE111075/suppl/GSE111075_RAW.tar -> /home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/data/raw/GSE111075/counts/GSE111075_RAW.tar
2026-10-18 19:09:42,269 - INFO - File filelist.txt has only 4 genes; trying next candidate
2026-10-18 19:09:42,269 - WARNING - Could not parse GSE111075_RAW.tar: 'utf-8' codec can't decode byte 0x8b in position 513: invalid start byte
2026-10-18 19:09:42,269 - ERROR - Failed to process GSE111075: Could not extract a valid gene list for GSE111075 from any downloaded file
2026-10-18 19:09:42,272 - INFO - Processing GSE138852 ...
2026-10-18 19:09:42,372 - WARNING - Metadata fetch attempt 1/5 for GSE138852 failed: GEO metadata for GSE138852 lists no supplementary files
2026-10-18 19:09:44,555 - WARNING - Metadata fetch attempt 2/5 for GSE138852 failed: GEO metadata for GSE138852 lists no supplementary files
2026-10-18 19:09:48,661 - WARNING - Metadata fetch attempt 3/5 for GSE138852 failed: GEO metadata for GSE138852 lists no supplementary files
2026-10-18 19:09:54,763 - WARNING - Metadata fetch attempt 4/5 for GSE138852 failed: GEO metadata for GSE138852 lists no supplementary files


[TIMEOUT after 120s]
- python code/subset_tcells.py --input data/processed/ --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/subset_tcells.py': [Errno 2] No such file or directory

- python code/batch_correct.py --input data/processed/ --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/batch_correct.py': [Errno 2] No such file or directory

- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=1
/PROJ-003-single-cell-trajectories-of-t-cell-exhau/lib/python3.11/site-packages/scvelo/datasets/_datasets.py", line 10, in <module>
    from scvelo.core import cleanup
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/lib/python3.11/site-packages/scvelo/core/__init__.py", line 1, in <module>
    from ._anndata import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/lib/python3.11/site-packages/scvelo/core/_anndata.py", line 15, in <module>
    from scvelo import logging as logg
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/lib/python3.11/site-packages/scvelo/logging.py", line 12, in <module>
    from scvelo import settings
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/lib/python3.11/site-packages/scvelo/settings.py", line 91, in <module>
    warnings.filterwarnings("ignore", category=cbook.mplDeprecation)
                                               ^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'matplotlib.cbook' has no attribute 'mplDeprecation'

- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/power_analysis.py --input data/processed/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/power_analysis.py': [Errno 2] No such file or directory

- python code/enrichment.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/enrichment.py': [Errno 2] No such file or directory

- python code/validate.py   --input data/results/validation/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory

