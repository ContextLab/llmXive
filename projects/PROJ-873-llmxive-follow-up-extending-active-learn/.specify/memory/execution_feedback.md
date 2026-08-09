# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/generate_charts.py: self-declared fabricated metric — “…atios = [0.45, 0.38, 0.52]  # Placeholder values     else:         datasets =…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data_loader.py --prepare`
  - script usage: `data_loader.py [-h] {prepare} ...`
  - argparse error: `data_loader.py: error: unrecognized arguments: --prepare`
- run-book command: `python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5`
  - script usage: `run_pipeline.py [-h] --variant {baseline,clustering_aided}`
  - argparse error: `run_pipeline.py: error: argument --variant: invalid choice: 'unique_baseline' (choose from 'baseline', 'clustering_aided')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/generate_charts.py: self-declared fabricated metric — “…atios = [0.45, 0.38, 0.52]  # Placeholder values     else:         datasets =…”; 4 command(s) failed: python code/data_loader.py --prepare (rc=2); python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 (rc=1); python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 (rc=1); 9 declared deliverable(s) absent: data/processed/clusters.json; data/processed/comparison_log.json; data/processed/injected_datasets.json

## Failing / missing run-book commands

- python code/data_loader.py --prepare -> rc=2
    usage: data_loader.py [-h] {prepare} ...
data_loader.py: error: unrecognized arguments: --prepare
- python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 -> rc=1
    2026-08-09 08:54:03,999 - INFO - Logging initialized
2026-08-09 08:54:03,999 - INFO - Resource monitoring started
2026-08-09 08:54:04,000 - ERROR - Pipeline execution failed: Required artifact missing: data/processed/injected_datasets.json
2026-08-09 08:54:05,000 - INFO - Resource monitoring stopped
- python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 -> rc=1
    2026-08-09 08:54:05,052 - INFO - Logging initialized
2026-08-09 08:54:05,052 - INFO - Resource monitoring started
2026-08-09 08:54:05,052 - ERROR - Pipeline execution failed: Required artifact missing: data/processed/injected_datasets.json
2026-08-09 08:54:06,053 - INFO - Resource monitoring stopped
- python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5 -> rc=2
    usage: run_pipeline.py [-h] --variant {baseline,clustering_aided}
                       [--budgets BUDGETS [BUDGETS ...]]
                       [--seeds SEEDS [SEEDS ...]] [--cross-dataset]
run_pipeline.py: error: argument --variant: invalid choice: 'unique_baseline' (choose from 'baseline', 'clustering_aided')

## Declared deliverables still missing

- data/processed/clusters.json
- data/processed/comparison_log.json
- data/processed/injected_datasets.json
- data/processed/unique_subset.json
- data/results/consensus_sample.json
- data/results/flagged_pairs_count.json
- data/results/us1_baseline_metrics.json
- data/results/us1_efficiency_ratio.json
- data/results/us2_baseline_095.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `beir` to the project's `requirements.txt` and `pip install beir`.
- **Verified**: this loads **339** real records with fields: query_id, query_text, doc_id, passage_text, relevance_score, split.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os
from beir import util
from beir.datasets.data_loader import GenericDataLoader

dataset = "scifact"
url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
# Download and unzip the dataset to a local directory
data_path = util.download_and_unzip(url, "beir_data")
# Load the corpus, queries, and relevance judgments for the test split
loader = GenericDataLoader(data_path)
corpus, queries, qrels = loader.load(split="test")
# Count the number of (query, document) relevance pairs
record_count = sum(len(docs) for docs in qrels.values())
print(f"RECORDS={record_count}")
print("FIELDS=query_id,query_text,doc_id,passage_text,relevance_score,split")
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
    - `code/ranker.py` — NOT invoked by the run-book
    - `code/verify_redundancy_clusters.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/clustering.py` — NOT invoked by the run-book
    - `code/cross_dataset_generalization.py` — NOT invoked by the run-book
    - `code/validate_artifact_chain.py` — NOT invoked by the run-book
    - `code/unique_subset_generator.py` — NOT invoked by the run-book
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/clusters.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/comparison_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/logging_config.py` — NOT invoked by the run-book
    - `code/sampling.py` — NOT invoked by the run-book
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/run_sampling.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/comparison_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/injected_datasets.json` is declared but was NOT written. Scripts referencing it:
    - `code/ranker.py` — NOT invoked by the run-book
    - `code/clustering.py` — NOT invoked by the run-book
    - `code/cross_dataset_generalization.py` — NOT invoked by the run-book
    - `code/validate_artifact_chain.py` — NOT invoked by the run-book
    - `code/data_loader.py` — IS a run-book command
    - `code/run_pipeline.py` — IS a run-book command
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/injected_datasets.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unique_subset.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/setup_linting.py` — NOT invoked by the run-book
    - `code/run_baseline_unique.py` — NOT invoked by the run-book
    - `code/unique_subset_generator.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unique_subset.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/consensus_sample.json` is declared but was NOT written. Scripts referencing it:
    - `code/sampling.py` — NOT invoked by the run-book
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/run_sampling.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/consensus_sample.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/flagged_pairs_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/flagged_pairs_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us1_baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us1_baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us1_efficiency_ratio.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_proxy_chain.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
    - `code/audit/validate_constitution.py` — NOT invoked by the run-book
    - `code/scripts/generate_charts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us1_efficiency_ratio.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us2_baseline_095.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/scripts/generate_charts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us2_baseline_095.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/ranker.py`, `code/clustering.py`, `code/cross_dataset_generalization.py`, `code/data_loader.py`, `code/audit/validate_constitution.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/data/processed/injected_datasets.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/ranker.py`, `code/clustering.py`, `code/cross_dataset_generalization.py`, `code/validate_artifact_chain.py`, `code/data_loader.py`, `code/run_pipeline.py`, `code/audit/validate_constitution.py`.
