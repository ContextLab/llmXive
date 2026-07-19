# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/nfcorpus/qrels/dev.tsv, data/raw/nfcorpus/qrels/test.tsv, data/raw/nfcorpus/qrels/train.tsv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5`
  - script usage: `run_pipeline.py [-h] --variant {baseline,clustering_aided}`
  - argparse error: `run_pipeline.py: error: argument --variant: invalid choice: 'unique_baseline' (choose from 'baseline', 'clustering_aided')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/nfcorpus/qrels/dev.tsv, data/raw/nfcorpus/qrels/test.tsv, data/raw/nfcorpus/qrels/train.tsv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/data_loader.py --prepare (rc=1); python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 (rc=1); python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 (rc=1); 1 declared deliverable(s) absent: data/results/consensus_sample.json

## Failing / missing run-book commands

- python code/data_loader.py --prepare -> rc=1
    <00:00, 22.21it/s]
2026-07-19 11:06:49,813 - __main__ - ERROR - Data injection failed for nfcorpus: Injected similarity 0.9139 is below threshold 0.95. Paraphrasing failed to generate sufficient semantic similarity for document MED-3910.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/data_loader.py", line 401, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/data_loader.py", line 382, in main
    prepare_injected_datasets(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/data_loader.py", line 286, in prepare_injected_datasets
    clusters = create_redundancy_clusters(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/data_loader.py", line 207, in create_redundancy_clusters
    raise DataInjectionError(
DataInjectionError: Injected similarity 0.9139 is below threshold 0.95. Paraphrasing failed to generate sufficient semantic similarity for document MED-3910.
- python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 -> rc=1
    2026-07-19 11:06:51,413 - logging_config - INFO - Logging initialized

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 84, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 68, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 17, in check_data_integrity
    os.path.join(get_config().data_dir, 'processed', 'injected_datasets.json'),
                 ^^^^^^^^^^
NameError: name 'get_config' is not defined
- python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 -> rc=1
    2026-07-19 11:06:51,460 - logging_config - INFO - Logging initialized

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 84, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 68, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 17, in check_data_integrity
    os.path.join(get_config().data_dir, 'processed', 'injected_datasets.json'),
                 ^^^^^^^^^^
NameError: name 'get_config' is not defined
- python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5 -> rc=2
    2026-07-19 11:06:51,507 - logging_config - INFO - Logging initialized

usage: run_pipeline.py [-h] --variant {baseline,clustering_aided}
                       [--budgets BUDGETS [BUDGETS ...]]
                       [--seeds SEEDS [SEEDS ...]]
run_pipeline.py: error: argument --variant: invalid choice: 'unique_baseline' (choose from 'baseline', 'clustering_aided')

## Declared deliverables still missing

- data/results/consensus_sample.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `beir` to the project's `requirements.txt` and `pip install beir`.
- **Verified**: this loads **79009** real records with fields: query_id, query_text, doc_id, doc_text, relevance_score, split.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os, tempfile, shutil
from beir import util
from beir.datasets.data_loader import GenericDataLoader

datasets = ["scifact", "nfcorpus", "trec-covid"]
records = []

for ds in datasets:
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{ds}.zip"
    out_dir = tempfile.mkdtemp()
    data_path = util.download_and_unzip(url, out_dir)
    data_folder = os.path.join(data_path, ds) if os.path.isdir(os.path.join(data_path, ds)) else data_path
    corpus, queries, qrels = GenericDataLoader(data_folder=data_folder).load(split="test")
    for qid, rels in qrels.items():
        query_obj = queries[qid]
        query_text = query_obj["text"] if isinstance(query_obj, dict) else query_obj
        for docid, score in rels.items():
            doc_obj = corpus[docid]
            doc_text = doc_obj["text"] if isinstance(doc_obj, dict) else doc_obj
            records.append({
                "query_id": qid,
                "query_text": query_text,
                "doc_id": docid,
                "doc_text": doc_text,
                "relevance_score": score,
                "split": "test"
            })
    shutil.rmtree(out_dir)

print(f"RECORDS={len(records)}")
if records:
    print("FIELDS=" + ",".join(records[0].keys()))
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
    - `code/run_pipeline.py` — IS a run-book command
    - `code/sampling.py` — NOT invoked by the run-book
    - `code/run_sampling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/consensus_sample.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
