# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl`
  - script usage: `run_solver.py [-h] --input INPUT --output OUTPUT --latency-log`
  - argparse error: `run_solver.py: error: the following arguments are required: --latency-log, --exclusion-log`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data/download.py --sample-size 1000 (rc=1); python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl (rc=1); python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl (rc=2); 2 declared deliverable(s) absent: data/results/benchmark_results.csv; data/results/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/data/download.py --sample-size 1000 -> rc=1
    0af2-2477edb04d32547650de0efb;9752143f-fa96-45b6-ad08-21165df5707d)

Repository Not Found for url: https://huggingface.co/api/models/llmXive/S-AgentK.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/download.py", line 119, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/download.py", line 116, in main
    download_dataset()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/download.py", line 86, in download_dataset
    raise FileNotFoundError(f"Dataset {dataset_id} not found at HuggingFace Hub")
FileNotFoundError: Dataset llmXive/S-AgentK not found at HuggingFace Hub
- python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl -> rc=1
    INFO:config:Loading scene data from /home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/data/raw...
ERROR:config:Raw data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/data/raw/s_agent_k_subset.jsonl
- python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl -> rc=2
    usage: run_solver.py [-h] --input INPUT --output OUTPUT --latency-log
                     LATENCY_LOG --exclusion-log EXCLUSION_LOG
run_solver.py: error: the following arguments are required: --latency-log, --exclusion-log
- python code/benchmark/analyze_failures.py --results data/derived/benchmark_results.csv --output data/derived/failure_report.json -> rc=1
    ERROR:config:Benchmark results not found: data/derived/benchmark_results.csv

## Declared deliverables still missing

- data/results/benchmark_results.csv
- data/results/sensitivity_analysis.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `DATA_DERIVED`, `DATA_DIR`, `DERIVED_PATH`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.DATA_DERIVED` call sites (0):

`Config.DATA_DIR` call sites (0):

`Config.DERIVED_PATH` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/benchmark_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/verify_acceptance_scenarios.py` — NOT invoked by the run-book
    - `code/benchmark/metrics.py` — IS a run-book command
    - `code/benchmark/sensitivity.py` — NOT invoked by the run-book
    - `code/benchmark/generate_failure_report.py` — NOT invoked by the run-book
    - `code/benchmark/analyze_failures.py` — IS a run-book command
  Make ONE of these WRITE `data/results/benchmark_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/derived/predictions.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/solver/run_solver.py`, `code/benchmark/generate_benchmark_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/derived/predictions.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/solver/run_solver.py`, `code/data/load_vlm_baseline.py`, `code/benchmark/generate_benchmark_results.py`.

### `data/raw/s_agent_k_subset.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/extract_geometry.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/s_agent_k_subset.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/extract_geometry.py`, `code/data/download.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/data/raw/s_agent_k_subset.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/extract_geometry.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/data/raw/s_agent_k_subset.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/extract_geometry.py`, `code/data/download.py`.
