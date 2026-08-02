# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data_loader.py --prepare`
  - script usage: `data_loader.py [-h] {prepare,validate_trec_covid} ...`
  - argparse error: `data_loader.py: error: unrecognized arguments: --prepare`
- run-book command: `python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5`
  - script usage: `run_pipeline.py [-h] --variant {baseline,clustering_aided}`
  - argparse error: `run_pipeline.py: error: argument --variant: invalid choice: 'unique_baseline' (choose from 'baseline', 'clustering_aided')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data_loader.py --prepare (rc=2); python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 (rc=1); python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 (rc=1); 3 declared deliverable(s) absent: data/results/consensus_sample.json; data/results/flagged_pairs_count.json; data/results/trec_covid_validation.json

## Failing / missing run-book commands

- python code/data_loader.py --prepare -> rc=2
    usage: data_loader.py [-h] {prepare,validate_trec_covid} ...
data_loader.py: error: unrecognized arguments: --prepare
- python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 -> rc=1
    INFO:logging_config:Logging initialized
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 166, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 145, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 44, in check_data_integrity
    raise FileNotFoundError(f"Required artifact missing: {f}")
FileNotFoundError: Required artifact missing: /home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json
- python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 -> rc=1
    INFO:logging_config:Logging initialized
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 166, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 145, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 44, in check_data_integrity
    raise FileNotFoundError(f"Required artifact missing: {f}")
FileNotFoundError: Required artifact missing: /home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json
- python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5 -> rc=2
    usage: run_pipeline.py [-h] --variant {baseline,clustering_aided}
                       [--budgets BUDGETS [BUDGETS ...]]
                       [--seeds SEEDS [SEEDS ...]] [--cross-dataset]
run_pipeline.py: error: argument --variant: invalid choice: 'unique_baseline' (choose from 'baseline', 'clustering_aided')

## Declared deliverables still missing

- data/results/consensus_sample.json
- data/results/flagged_pairs_count.json
- data/results/trec_covid_validation.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `beir` to the project's `requirements.txt` and `pip install beir`.
- **Verified**: this loads **339** real records with fields: query_id, query_text, doc_id, doc_text, relevance_label, split.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os
from beir import util
from beir.datasets.data_loader import GenericDataLoader

# Define dataset and download location
dataset = "scifact"
url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
out_dir = "beir_data"

# Download and unzip the dataset
data_path = util.download_and_unzip(url, out_dir)

# Load the full corpus, queries, and qrels for the test split
corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")

records = []
for qid, doc_dict in qrels.items():
    # BEIR may store query as a plain string or as a dict with a "text" field
    query_entry = queries[qid]
    query_text = query_entry["text"] if isinstance(query_entry, dict) else str(query_entry)

    for doc_id, rel in doc_dict.items():
        # Corpus entries can be dicts with "text" (and optionally "title") or plain strings
        doc_entry = corpus[doc_id]
        doc_text = (
            doc_entry["text"]
            if isinstance(doc_entry, dict) and "text" in doc_entry
            else str(doc_entry)
        )
        records.append(
            {
                "query_id": qid,
                "query_text": query_text,
                "doc_id": doc_id,
                "doc_text": doc_text,
                "relevance_label": rel,
                "split": "test",
            }
        )

if not records:
    raise RuntimeError("No records loaded; dataset may be empty or split name incorrect.")

print(f"RECORDS={len(records)}")
print("FIELDS=query_id,query_text,doc_id,doc_text,relevance_label,split")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `PipelineConfig` (in `code/config.py`) — accessed via method/attribute names this round: `data_dir`

`PipelineConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `PipelineConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`PipelineConfig.data_dir` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/consensus_sample.json` is declared but was NOT written. Scripts referencing it:
    - `code/ranker.py` — NOT invoked by the run-book
    - `code/sampling.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
    - `code/run_sampling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/consensus_sample.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/flagged_pairs_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/calculate_sample_size.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/flagged_pairs_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/trec_covid_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/results/trec_covid_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/cross_dataset_generalization.py`, `code/data_loader.py`, `code/run_pipeline.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/cross_dataset_generalization.py`, `code/data_loader.py`, `code/run_pipeline.py`.
