# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw (rc=1); python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw -> rc=1
r/publaynet': 401 Client Error. (Request ID: Root=1-6ad108ac-68b1053f14f18ef57364e329;5600efbd-0bdb-4dcb-af87-3edf94690e82)

Repository Not Found for url: https://huggingface.co/api/datasets/nielsr/publaynet/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
Primary pages (0) < 10000. Trying fallback...
Downloading repository 'nielsr/docbank'...
Fallback download failed: 401 Client Error. (Request ID: Root=1-6ad108ac-0b5ba7443610e01f352072dd;d5b617d1-dab2-4211-bb19-a931d78ee750)

Repository Not Found for url: https://huggingface.co/api/datasets/nielsr/docbank/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
Total pages with layout after fallback handling: 0

❌ ERROR: Insufficient annotated pages (FR-007). Found 0, need 10000.

- python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/preprocess.py", line 18, in <module>
    import pyarrow  # ensures parquet support
    ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu -> rc=1

2026-10-15 17:09:01,845 ERROR __main__: Latent generation failed: Unable to read Parquet file 'data/processed/document_pairs.parquet': Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=1
Downloading repository 'nielsr/docvqa'...
DocVQA download failed: 401 Client Error. (Request ID: Root=1-6ad108ae-611eef04512badb444e81e97;74605a65-4c8c-439e-8d20-d206346327e1)

Repository Not Found for url: https://huggingface.co/api/datasets/nielsr/docvqa/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

❌ ERROR: 401 Client Error. (Request ID: Root=1-6ad108ae-611eef04512badb444e81e97;74605a65-4c8c-439e-8d20-d206346327e1)

Repository Not Found for url: https://huggingface.co/api/datasets/nielsr/docvqa/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

- python -m pytest -k "contract" tests/ -> rc=2
e importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/tests/unit/test_preprocess.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_preprocess.py:16: in <module>
    from src.data.preprocess import preprocess_dataset
src/data/preprocess.py:18: in <module>
    import pyarrow  # ensures parquet support
../../.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/unit/test_preprocess.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 deselected, 1 error in 1.15s ========================


