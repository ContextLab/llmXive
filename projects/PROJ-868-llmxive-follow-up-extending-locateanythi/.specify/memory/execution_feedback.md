# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ (rc=1); python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true (rc=1); python -m pytest -q tests/contract/ (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/src/cli/run_experiment.py", line 33, in <module>
    from code.data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/code/data/download.py", line 18, in <module>
    from huggingface_hub import hf_hub_download
ModuleNotFoundError: No module named 'huggingface_hub'

- python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/src/cli/run_experiment.py", line 33, in <module>
    from code.data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-locateanythi/code/data/download.py", line 18, in <module>
    from huggingface_hub import hf_hub_download
ModuleNotFoundError: No module named 'huggingface_hub'

- python -m pytest -q tests/contract/ -> rc=1
coder.JSONDecoder object at 0x7f70bf1a0390>
s = '# JSON Schema for inference result records.\n# This schema validates the parquet files produced by the pipeline.\ntyp...\n    minimum: 0.0\nrequired:\n  - image_id\n  - prediction\n  - mean_iou\n  - latency_ms\nadditionalProperties: false'
idx = 0

    def raw_decode(self, s, idx=0):
        """Decode a JSON document from ``s`` (a ``str`` beginning with
        a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
    
        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.
    
        """
        try:
            obj, end = self.scan_once(s, idx)
        except StopIteration as err:
>           raise JSONDecodeError("Expecting value", s, err.value) from None
E           json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/decoder.py:355: JSONDecodeError
=========================== short test summary info ============================
ERROR tests/contract/test_contracts.py::test_parquet_files_conform_to_schema
1 error in 0.50s


