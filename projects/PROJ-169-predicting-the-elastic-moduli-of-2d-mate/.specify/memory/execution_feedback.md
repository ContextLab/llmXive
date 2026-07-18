# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/ingest/download.py --output data/raw`
  - script usage: `download.py [-h] --source {materials_project,aflow,oqmd}`
  - argparse error: `download.py: error: the following arguments are required: --source`
- run-book command: `python code/model/train.py --data-dir data/filtered --epochs 100 --patience 3 --split-strategy family`
  - script usage: `train.py [-h] [--config CONFIG] [--epochs EPOCHS] [--patience PATIENCE]`
  - argparse error: `train.py: error: unrecognized arguments: --data-dir data/filtered --split-strategy family`
- run-book command: `python code/analysis/importance.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered`
  - script usage: `importance.py [-h] --model MODEL --data DATA --indices INDICES --output`
  - argparse error: `importance.py: error: the following arguments are required: --model, --data, --indices, --output, --descriptors`
- run-book command: `python code/analysis/ablation.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered`
  - script usage: `ablation.py [-h] --graphs GRAPHS --split SPLIT --gnn-model GNN_MODEL`
  - argparse error: `ablation.py: error: the following arguments are required: --graphs, --split, --gnn-model, --output`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/ingest/download.py --output data/raw (rc=2); python code/ingest/bias_check.py --input data/raw --output data/bias_report.json (rc=1); python code/ingest/parse_cif.py --input data/raw --output data/processed (rc=1); 5 declared deliverable(s) absent: data/processed/graphs_v1.parquet; data/processed/test_indices.json; data/results/generalization_metrics.json

## Failing / missing run-book commands

- python code/ingest/download.py --output data/raw -> rc=2
    usage: download.py [-h] --source {materials_project,aflow,oqmd}
                   [--output OUTPUT] [--sample SAMPLE]
download.py: error: the following arguments are required: --source
- python code/ingest/bias_check.py --input data/raw --output data/bias_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/bias_check.py", line 143, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/bias_check.py", line 114, in main
    exclusion_log_path = config.paths.get('exclusion_log', Path('data/processed/exclusion_log.json'))
                         ^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'paths'
- python code/ingest/parse_cif.py --input data/raw --output data/processed -> rc=1
    pymatgen not installed. CIF parsing disabled.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/parse_cif.py", line 251, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/parse_cif.py", line 246, in main
    with open(output_path, 'w') as f:
         ^^^^^^^^^^^^^^^^^^^^^^
IsADirectoryError: [Errno 21] Is a directory: 'data/processed'
- python code/model/train.py --data-dir data/filtered --epochs 100 --patience 3 --split-strategy family -> rc=2
    usage: train.py [-h] [--config CONFIG] [--epochs EPOCHS] [--patience PATIENCE]
                [--batch_size BATCH_SIZE] [--lr LR] [--data_path DATA_PATH]
                [--split_path SPLIT_PATH] [--output_log OUTPUT_LOG]
                [--output_test_indices OUTPUT_TEST_INDICES]
train.py: error: unrecognized arguments: --data-dir data/filtered --split-strategy family
- python code/analysis/importance.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered -> rc=2
    usage: importance.py [-h] --model MODEL --data DATA --indices INDICES --output
                     OUTPUT --descriptors DESCRIPTORS [DESCRIPTORS ...]
importance.py: error: the following arguments are required: --model, --data, --indices, --output, --descriptors
- python code/analysis/ablation.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered -> rc=2
    usage: ablation.py [-h] --graphs GRAPHS --split SPLIT --gnn-model GNN_MODEL
                   --output OUTPUT [--config CONFIG]
ablation.py: error: the following arguments are required: --graphs, --split, --gnn-model, --output

## Declared deliverables still missing

- data/processed/graphs_v1.parquet
- data/processed/test_indices.json
- data/results/generalization_metrics.json
- data/results/terminology_audit.json
- data/results/training_logs.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `matminer` to the project's `requirements.txt` and `pip install matminer`.
- **Verified**: this loads **1181** real records with fields: material_id, cif, elastic_tensor_6c.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
from matminer.datasets import load_dataset
# Load the 2015 elasticity dataset bundled with matminer
df = load_dataset('elastic_tensor_2015')
records = len(df)
print(f'RECORDS={records}')
# Determine which of the required fields are present
required = {
    'material_id': 'material_id',
    'composition': 'composition',
    'cif': 'cif',
    'elastic_tensor_6c': 'elastic_tensor',
    'elastic_tensor_units': 'elastic_tensor_units'
}
fields = [req for req, col in required.items() if col in df.columns]
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Config` (in `code/utils/config.py`) — accessed via method/attribute names this round: `paths`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/utils/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.paths` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/graphs_v1.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/model/cv_runner.py` — NOT invoked by the run-book
    - `code/model/train.py` — IS a run-book command
    - `code/model/baseline_metrics.py` — NOT invoked by the run-book
    - `code/model/inference_benchmark.py` — NOT invoked by the run-book
    - `code/model/generalization_test.py` — NOT invoked by the run-book
    - `code/ingest/pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graphs_v1.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/model/train.py` — IS a run-book command
    - `code/model/inference_benchmark.py` — NOT invoked by the run-book
    - `code/model/generalization_test.py` — NOT invoked by the run-book
    - `code/analysis/ablation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/test_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/generalization_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/model/eval_runner.py` — NOT invoked by the run-book
    - `code/model/inference_benchmark.py` — NOT invoked by the run-book
    - `code/model/disclaimer_injector.py` — NOT invoked by the run-book
    - `code/model/generalization_test.py` — NOT invoked by the run-book
    - `code/analysis/aggregate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/generalization_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/terminology_audit.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/terminology_audit.py` — NOT invoked by the run-book
    - `code/utils/terminology_scanner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/terminology_audit.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/training_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/model/eval_runner.py` — NOT invoked by the run-book
    - `code/model/cv_runner.py` — NOT invoked by the run-book
    - `code/model/train.py` — IS a run-book command
    - `code/model/disclaimer_injector.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/training_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
