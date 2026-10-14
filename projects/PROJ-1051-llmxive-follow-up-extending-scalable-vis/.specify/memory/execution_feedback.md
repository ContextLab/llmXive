# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.data.download  --dataset-name publaynet  --output-dir data/raw`
- `python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.data.download  --dataset-name publaynet  --output-dir data/raw (rc=1); python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name publaynet  --output-dir data/raw -> rc=1
s://huggingface.co/api/datasets/nielsr/docbank/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
Attempting to download logical dataset 'publaynet' using HF identifier 'layoutparser/docbank'...
⚠️ Warning: Failed to download 'layoutparser/docbank': 401 Client Error. (Request ID: Root=1-6acf8e9f-7af84daa1ef7ca08243246f1;9c7d1818-052c-45fa-b55e-d47e3a813ab0)

Repository Not Found for url: https://huggingface.co/api/datasets/layoutparser/docbank/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated. For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

=== Summary of layout‑annotation pages ===
  Primary (pubmed-layout): 0
  Fallback (docbank) added: 0
  TOTAL: 0


❌ ERROR: Insufficient total pages with layout annotations: 0 (minimum required is 10000). Pipeline aborting as per FR‑007.

- python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

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

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu -> rc=1
ed for parquet support. Use pip or conda to install fastparquet.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/latent_generator.py", line 113, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/latent_generator.py", line 89, in main
    raise RuntimeError(
RuntimeError: Unable to read Parquet file 'data/processed/document_pairs.parquet'. Ensure 'pyarrow' is installed. Original error: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=1
Downloading generic dataset 'docvqa'...


❌ ERROR: Failed to download dataset 'docvqa': 401 Client Error. (Request ID: Root=1-6acf8ea3-2568e1b65892a5011289aec4;27e0c476-b3fe-40f8-b3eb-42f55f06cae3)

Repository Not Found for url: https://huggingface.co/api/datasets/docvqa/revision/main.
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
======================== 1 deselected, 1 error in 2.56s ========================


