# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 command(s) failed: python -m src.data.download_smiles  --url https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet  --output data/raw/smiles.parquet (rc=1); python -m src.data.download_fqy  --url https://doi.org/10.48700/datst.mff4d-q4a24  --output data/raw/fqy.json (rc=1); python -m src.preprocessing.run  --smiles data/raw/smiles.parquet  --fqy data/raw/fqy.json  --output data/processed/dataset.csv  --split-output data/processed/split.json (rc=1)

## Failing / missing run-book commands

- python -m src.data.download_smiles  --url https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet  --output data/raw/smiles.parquet -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.data.download_fqy  --url https://doi.org/10.48700/datst.mff4d-q4a24  --output data/raw/fqy.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.preprocessing.run  --smiles data/raw/smiles.parquet  --fqy data/raw/fqy.json  --output data/processed/dataset.csv  --split-output data/processed/split.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.training.train_gnn  --data data/processed/dataset.csv  --split data/processed/split.json  --epochs 50  --patience 10  --output models/gnn_best.pt -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.training.train_lr  --data data/processed/dataset.csv  --split data/processed/split.json  --output models/lr.pkl -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.evaluation.evaluate  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --data data/processed/dataset.csv  --split data/processed/split.json  --output results/metrics.json  --fig-dir figures/ -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.interpretability.compute_attributions  --model models/gnn_best.pt  --data data/processed/dataset.csv  --split data/processed/split.json  --top-k 20  --method integrated_gradients  --output attributions/ -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.interpretability.validate_attributions  --attribution-dir attributions/  --reference-motifs data/reference/fluorophore_motifs.csv  --output results/attribution_validation.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.reporting.generate_report  --metrics results/metrics.json  --attribution-validation results/attribution_validation.json  --fig-dir figures/  --output report/ -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/__init__.py", line 9, in <module>
    import code.config.seed_config  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/config/seed_config.py", line 18, in <module>
    from code.data.download_raw import load_and_set_seeds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/code/data/download_raw.py", line 10, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

