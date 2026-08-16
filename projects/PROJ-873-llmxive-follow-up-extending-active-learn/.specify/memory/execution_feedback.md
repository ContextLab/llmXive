# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m pytest tests/integration/test_full_pipeline.py -v`
- `python code/main.py --dataset scifact --redundancy 0.4 --seeds 30`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py --dataset scifact --redundancy 0.4 --seeds 30; 1 command(s) failed: python -m pytest tests/integration/test_full_pipeline.py -v (rc=2); 8 declared deliverable(s) absent: data/processed/clusters.json; data/processed/injected_datasets.json; data/processed/unique_subset.json

## Failing / missing run-book commands

- python code/main.py --dataset scifact --redundancy 0.4 --seeds 30 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/main.py': [Errno 2] No such file or directory
- python -m pytest tests/integration/test_full_pipeline.py -v -> rc=2
    strap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    exec(co, module.__dict__)
tests/integration/test_full_pipeline.py:11: in <module>
    from run_pipeline import run_single_seed_experiment
code/run_pipeline.py:16: in <module>
    from ranker import run_ranker_with_filter, load_cluster_results
E   ImportError: cannot import name 'run_ranker_with_filter' from 'ranker' (/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/tests/integration/../../code/ranker.py)
=========================== short test summary info ============================
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 6.01s ===============================

## Declared deliverables still missing

- data/processed/clusters.json
- data/processed/injected_datasets.json
- data/processed/unique_subset.json
- data/results/consensus_ground_truth.json
- data/results/consensus_sample.json
- data/results/correction_factor.json
- data/results/flagged_pairs_count.json
- data/results/real_world_validation.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `beir` to the project's `requirements.txt` and `pip install beir`.
- **Verified**: this loads **3633** real records with fields: doc_id, title, text.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os
from beir import util
from beir.datasets.data_loader import GenericDataLoader

dataset = "nfcorpus"
url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
out_dir = "beir_data"
# download and unzip the dataset
data_path = util.download_and_unzip(url, out_dir)
# load corpus, queries and relevance judgments (qrels)
corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")
print(f"RECORDS={len(corpus)}")
print("FIELDS=doc_id,title,text")
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

- `data/processed/clusters.json` is declared but was NOT written. Scripts referencing it:
    - `code/clustering.py` — NOT invoked by the run-book
    - `code/validate_artifact_chain.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/verify_redundancy_clusters.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/ranker.py` — NOT invoked by the run-book
    - `code/cross_dataset_generalization.py` — NOT invoked by the run-book
    - `code/unique_subset_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clusters.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/injected_datasets.json` is declared but was NOT written. Scripts referencing it:
    - `code/clustering.py` — NOT invoked by the run-book
    - `code/validate_artifact_chain.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/ranker.py` — NOT invoked by the run-book
    - `code/cross_dataset_generalization.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/injected_datasets.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unique_subset.json` is declared but was NOT written. Scripts referencing it:
    - `code/setup_linting.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/ranker.py` — NOT invoked by the run-book
    - `code/run_baseline_unique.py` — NOT invoked by the run-book
    - `code/unique_subset_generator.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unique_subset.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/consensus_ground_truth.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/consensus_ground_truth.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/consensus_sample.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/run_sampling.py` — NOT invoked by the run-book
    - `code/sampling.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/consensus_sample.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/correction_factor.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correction_factor.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/flagged_pairs_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
    - `code/scripts/run_t013b.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/flagged_pairs_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/real_world_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_charts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/real_world_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/clustering.py`, `code/data_loader.py`, `code/ranker.py`, `code/cross_dataset_generalization.py`, `code/audit/validate_constitution.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/clustering.py`, `code/validate_artifact_chain.py`, `code/data_loader.py`, `code/ranker.py`, `code/cross_dataset_generalization.py`, `code/run_pipeline.py`, `code/audit/validate_constitution.py`.
