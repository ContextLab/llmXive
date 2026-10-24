# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_all.sh; 3 command(s) failed: python code/data/preprocess.py (rc=1); python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1); 2 declared deliverable(s) absent: data/processed/processed_data.parquet; data/raw/checksums.json

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1

2026-10-24 18:31:55,918 WARNING __main__: Config file not found at projects/PROJ-422-predicting-molecular-permeability-coeffi/config.yaml, using defaults.
2026-10-24 18:31:55,919 ERROR __main__: No CSV files found in raw data directory: /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/raw
2026-10-24 18:31:55,919 ERROR __main__: Preprocessing failed: No CSV files in /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/raw

- python code/analysis/train.py --config config.yaml -> rc=1
<module>
    import torch.nn.functional as F
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/__init__.py", line 1, in <module>
    from .modules import *  # noqa: F403
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/__init__.py", line 35, in <module>
    from .transformer import TransformerEncoder, TransformerDecoder, \
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/transformer.py", line 20, in <module>
    device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/transformer.py:20: UserWarning: Failed to initialize NumPy: _ARRAY_API not found (Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
  device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),

- python code/analysis/explain.py -> rc=1
<module>
    import torch.nn.functional as F
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/__init__.py", line 1, in <module>
    from .modules import *  # noqa: F403
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/__init__.py", line 35, in <module>
    from .transformer import TransformerEncoder, TransformerDecoder, \
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/transformer.py", line 20, in <module>
    device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/transformer.py:20: UserWarning: Failed to initialize NumPy: _ARRAY_API not found (Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
  device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),

- bash ./run_all.sh -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/processed/processed_data.parquet
- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/processed_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/split.py` — NOT invoked by the run-book
    - `code/models/gnn.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
