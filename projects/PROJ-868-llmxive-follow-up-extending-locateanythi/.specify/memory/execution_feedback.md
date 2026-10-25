# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/`
  - script usage: `run_experiment.py [-h] --config {global,64,32,16,1} [--sample SAMPLE]`
  - argparse error: `run_experiment.py: error: the following arguments are required: --config`
- run-book command: `python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true`
  - script usage: `run_experiment.py [-h] --config {global,64,32,16,1} [--sample SAMPLE]`
  - argparse error: `run_experiment.py: error: the following arguments are required: --config`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ (rc=2); python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true (rc=2); python -m pytest -q tests/contract/ (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ -> rc=2

usage: run_experiment.py [-h] --config {global,64,32,16,1} [--sample SAMPLE]
run_experiment.py: error: the following arguments are required: --config

- python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true -> rc=2

usage: run_experiment.py [-h] --config {global,64,32,16,1} [--sample SAMPLE]
run_experiment.py: error: the following arguments are required: --config

- python -m pytest -q tests/contract/ -> rc=1
coder.JSONDecoder object at 0x7f12bbca8950>
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
1 error in 0.35s


