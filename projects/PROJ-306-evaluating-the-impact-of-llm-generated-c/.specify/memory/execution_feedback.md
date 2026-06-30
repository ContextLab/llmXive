# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely CANNOT be measured on a CPU (it needs a GPU), do NOT fake it — measure a different, genuinely-computable proxy and name it honestly, or report that the metric is unmeasurable here. Never present a simulated number as a measurement.

- code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”
- code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”
- code/.venv/lib/python3.11/site-packages/_pytest/subtests.py: self-declared fabricated metric — “…:param kwargs:             Arbitrary values that are also added to the s…”
- code/.venv/lib/python3.11/site-packages/anyio/_backends/_asyncio.py: self-declared fabricated metric — “…_queue = deque(maxlen=100)  # arbitrary value         self.read_event = asy…”
- code/.venv/lib/python3.11/site-packages/attr/_make.py: self-declared fabricated metric — “…yping.Callable]):             Arbitrary number of validators.      .. versio…”
- code/.venv/lib/python3.11/site-packages/attr/_make.py: self-declared fabricated metric — “…yping.Callable]):             Arbitrary number of converters.      .. versio…”
- code/.venv/lib/python3.11/site-packages/attr/validators.py: self-declared fabricated metric — “…yping.Callable]):             Arbitrary number of validators.      Raises:…”
- code/.venv/lib/python3.11/site-packages/click/core.py: self-declared fabricated metric — “…in how it works but supports arbitrary number of                      argum…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 235 fabricated/simulated-result signal(s) — results are not real measurements: code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”; code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”; code/.venv/lib/python3.11/site-packages/_pytest/subtests.py: self-declared fabricated metric — “…:param kwargs:             Arbitrary values that are also added to the s…”; 1 command(s) failed: python code/main.py --num-tasks 100 --output-dir data/processed (rc=1); 1 declared deliverable(s) absent: data/benchmarks/processed/catalog.json

## Failing / missing run-book commands

- python code/main.py --num-tasks 100 --output-dir data/processed -> rc=1
    ojects/PROJ-306-evaluating-the-impact-of-llm-generated-c/code/error_handling.py", line 16, in <module>
    from utils import exponential_backoff_retry
ImportError: cannot import name 'exponential_backoff_retry' from partially initialized module 'utils' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-306-evaluating-the-impact-of-llm-generated-c/code/utils.py)

## Declared deliverables still missing

- data/benchmarks/processed/catalog.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real, installable source was discovered AND verified by actually loading data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

ds_dict = datasets.load_dataset('openai/openai_humaneval')
total_records = sum(len(split) for split in ds_dict.values())
print(f"RECORDS={total_records}")

first_split = next(iter(ds_dict.values()))
print("FIELDS=" + ",".join(first_split.column_names))
```

Write the loader to use this package/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/benchmarks/processed/catalog.json` is declared but was NOT written. Scripts referencing it:
    - `code/dataset_loader.py` — NOT invoked by the run-book
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/llm_generator.py` — NOT invoked by the run-book
    - `code/coverage_runner.py` — NOT invoked by the run-book
    - `code/visualizer.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/benchmarks/processed/catalog.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
