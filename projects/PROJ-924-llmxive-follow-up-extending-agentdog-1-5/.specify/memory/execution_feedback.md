# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m code.data_loader --streaming --output data/raw/atbench.parquet`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.data_loader --streaming --output data/raw/atbench.parquet`
  - script usage: `data_loader.py [-h] [--test-taxonomy] [--test-advbench]`
  - argparse error: `data_loader.py: error: unrecognized arguments: --streaming --output data/raw/atbench.parquet`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m code.data_loader --streaming --output data/raw/atbench.parquet (rc=2); python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json (rc=1); python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv (rc=1); 3 declared deliverable(s) absent: data/processed/drift_scores.csv; data/processed/taxonomy_agentdog.json; data/processed/us01_final_stats.json

## Failing / missing run-book commands

- python -m code.data_loader --streaming --output data/raw/atbench.parquet -> rc=2
    usage: data_loader.py [-h] [--test-taxonomy] [--test-advbench]
data_loader.py: error: unrecognized arguments: --streaming --output data/raw/atbench.parquet
- python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 226, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 201, in main
    ensure_directories([str(Path(args.output).parent)])
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/config.py", line 83, in ensure_directories
    p.mkdir(parents=True, exist_ok=True)
    ^^^^^^^
AttributeError: 'str' object has no attribute 'mkdir'
- python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv -> rc=1
    Starting drift scoring pipeline...
Loading taxonomy centroids...

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 273, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 235, in main
    centroids = load_centroids()
                ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 22, in load_centroids
    centroid_path = str(get_path("data", "processed", "taxonomy_centroids.json"))
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 3 were given
- python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/validation_report.json -> rc=1
    Starting US-01 validation...
Running statistical tests...

❌ Validation failed with error: get_path() takes 1 positional argument but 2 were given

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 266, in main
    results = run_us01_validation()
              ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 143, in run_us01_validation
    merged_df, _ = load_ground_truth_for_validation()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 87, in load_ground_truth_for_validation
    drift_scores_path = get_path("processed", "drift_scores.csv")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given
- python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/human_annotations.csv --output data/processed/validation_report.json -> rc=1
    Starting US-01 validation...
Running statistical tests...

❌ Validation failed with error: get_path() takes 1 positional argument but 2 were given

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 266, in main
    results = run_us01_validation()
              ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 143, in run_us01_validation
    merged_df, _ = load_ground_truth_for_validation()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 87, in load_ground_truth_for_validation
    drift_scores_path = get_path("processed", "drift_scores.csv")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given

## Declared deliverables still missing

- data/processed/drift_scores.csv
- data/processed/taxonomy_agentdog.json
- data/processed/us01_final_stats.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/main.py: centroid_path = get_path("centroid_file")
- code/main.py: output_path = get_path("drift_scores_csv")
- code/ensure_test_dir.py: base_path = path or get_path("data_test")
- code/generate_static_test_fixture.py: output_path = get_path('data/test_static_logs.json')
- code/utils.py: base_dir = get_path("specs")
- code/ensure_specs_dir.py: project_root = get_path(base_path)
- code/data_loader.py: output_path = get_path("raw_data") / "atbench.parquet"
- code/data_loader.py: output_path = get_path("raw_data") / "hf4.parquet"
- code/config.py: dir_path = get_path(name)
- code/annotator_interface.py: export_stratified_bins(df, get_path("output_dir"))
- code/annotator_interface.py: scores_path = get_path("output_dir") / "drift_scores.csv"
- code/drift_scoring.py: centroid_path = str(get_path("data", "processed", "taxonomy_centroids.json"))
- code/drift_scoring.py: output_path = str(get_path("data", "processed", "drift_scores.csv"))
- code/drift_scoring.py: logs_path = get_path("data", "test", "test_static_logs.json")
- code/drift_scoring.py: logs_path = get_path("data", "test", "real_ground_truth_fixture.json")
- code/generate_test_fixture.py: data_path = get_path("data")
- code/validation.py: drift_scores_path = get_path("processed", "drift_scores.csv")
- code/validation.py: merged_annotations_path = get_path("processed", "merged_annotations.csv")
- code/validation.py: ground_truth_fixture_path = get_path("test", "real_ground_truth_fixture.json")
- code/validation.py: output_path = get_path("processed", "us01_final_stats.json")
- code/generate_ground_truth_fixture.py: output_path = get_path("test", "real_ground_truth_fixture.json")
- code/checksums_generator.py: project_root = get_path("project_root")
- code/checksums_generator.py: relative_path = str(file_path.relative_to(get_path("project_root")))
- code/checksums_generator.py: raw_dir = get_path("raw_data")
- code/checksums_generator.py: output_file = get_path("checksums")

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/drift_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils.py` — NOT invoked by the run-book
    - `code/annotator_interface.py` — NOT invoked by the run-book
    - `code/drift_scoring.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/drift_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/taxonomy_agentdog.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/taxonomy_agentdog.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/us01_final_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/us01_final_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/taxonomy_centroids.json`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[Path]`
- PRODUCER(s) to edit: `code/drift_scoring.py`
- CONSUMER(s) that read it: `code/drift_scoring.py`
  → Edit the producer so every required name [Path] is in `data/processed/taxonomy_centroids.json`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
