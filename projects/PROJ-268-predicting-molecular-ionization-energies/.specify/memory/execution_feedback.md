# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 run-book script(s) missing (plan/impl path mismatch): python code/data/preprocess.py  --input data/raw/qm9.parquet  --output data/processed/graphs.pt; python code/data/split.py  --graphs data/processed/graphs.pt  --train-ratio 0.80 --val-ratio 0.10 --test-ratio 0.10  --strategy scaffold; python code/data/validate_proxy.py  --qm9 data/processed/graphs.pt  --nist-url https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt  --sample-size 500; 1 command(s) failed: python code/data/download.py (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/download.py", line 4, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/data/preprocess.py  --input data/raw/qm9.parquet  --output data/processed/graphs.pt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/preprocess.py': [Errno 2] No such file or directory

- python code/data/split.py  --graphs data/processed/graphs.pt  --train-ratio 0.80 --val-ratio 0.10 --test-ratio 0.10  --strategy scaffold -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/split.py': [Errno 2] No such file or directory

- python code/data/validate_proxy.py  --qm9 data/processed/graphs.pt  --nist-url https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt  --sample-size 500 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/validate_proxy.py': [Errno 2] No such file or directory

- python code/experiments/train.py  --config code/utils/config.yaml  --batch-size 64  --max-epochs 200  --timeout-hours 6 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/train.py': [Errno 2] No such file or directory

- python code/models/baselines.py --type lr -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/models/baselines.py': [Errno 2] No such file or directory

- python code/models/baselines.py --type dftb -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/models/baselines.py': [Errno 2] No such file or directory

- python code/experiments/ablation.py  --feature bond_type  --perturbation zero  --num-runs 3  --subset-size <sufficiently large subset>  --batch-size 64  --max-epochs 100  --bootstrap-samples a sufficiently large number of samples  --runtime-guard-hours 4 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/ablation.py': [Errno 2] No such file or directory

- python code/experiments/ablation.py  --feature bond_type  --perturbation zero  --num-runs 3  --subset-size 10000  --batch-size 64  --max-epochs 100  --bootstrap-samples 1000  --runtime-guard-hours 4  --resume-from results/ablation_part1.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/ablation.py': [Errno 2] No such file or directory

- python code/experiments/evaluate.py  --model-path code/models/best_model.pth  --test-set data/splits/test.pt  --output-dir results/  --ig-sample-size sufficiently large -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/evaluate.py': [Errno 2] No such file or directory

