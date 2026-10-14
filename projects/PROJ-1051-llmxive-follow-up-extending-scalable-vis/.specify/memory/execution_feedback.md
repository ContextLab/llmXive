# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python -m src.data.download  --primary-name docbank  --fallback-name pubmed-layout (rc=1); python -m src.data.preprocess  --input-dir data/raw  --output-path data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-path data/processed/document_pairs.parquet  --output-path data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --primary-name docbank  --fallback-name pubmed-layout -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/download.py", line 19, in <module>
    from datasets import load_dataset, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.data.preprocess  --input-dir data/raw  --output-path data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: No module named src.data.preprocess

- python -m src.data.latent_generator  --input-path data/processed/document_pairs.parquet  --output-path data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: No module named src.data.latent_generator

- python -m src.utils.split_generator  --input-path data/processed/document_pairs_with_latent.parquet  --output-dir data/splits  --seed 42  --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.utils.split_generator' (ModuleNotFoundError: No module named 'src.utils')

- python -m src.models.distilled  --data-path data/processed/document_pairs_with_latent.parquet  --splits-dir data/splits  --seed $SEED  --output-dir artifacts/models/distilled_$SEED  --max-epochs 5  --batch-size 16 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.models.distilled' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.baseline  --data-path data/processed/document_pairs.parquet  --splits-dir data/splits  --seed $SEED  --output-dir artifacts/models/baseline_$SEED  --max-epochs 5  --batch-size 16 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.models.baseline' (ModuleNotFoundError: No module named 'src.models')

- python -m src.eval.downstream  --distilled-dir artifacts/models/distilled_*/  --baseline-dir artifacts/models/baseline_*/  --test-data data/processed/downstream_test.parquet  --results-path artifacts/eval/downstream_results.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.eval.downstream' (ModuleNotFoundError: No module named 'src.eval')

- python -m pytest -k "contract" tests/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/


