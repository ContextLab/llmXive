# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/metrics/statistical_analysis_results.json: EVERY metric is null/NaN ([0].power_analysis.power, [0].power_analysis.effect_size, [0].power_analysis.sample_size, [0].power_analysis.threshold_met…) — nothing was computed

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/metrics/statistical_analysis_results.json: EVERY metric is null/NaN ([0].power_analysis.power, [0].power_analysis.effect_size, [0].power_analysis.sample_size, [0].power_analysis.threshold_met…) — nothing was computed; 2 command(s) failed: python code/data_ingestion.py (rc=1); python code/metric_extraction.py (rc=1)

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-488-evaluating-the-impact-of-code-generation/code/data_ingestion.py", line 26, in <module>
    logger = setup_logger("data_ingestion", log_file="data/ingestion.log")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-488-evaluating-the-impact-of-code-generation/code/logging_config.py", line 108, in setup_logger
    logger.parameters['log_file'] = log_file
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
TypeError: 'function' object does not support item assignment
- python code/metric_extraction.py -> rc=1
    Error: Input file not found: data/processed/filtered_snippets.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logger` — defined in `code/pilot_study.py`; called 21 way(s):

- code/ast_validation.py: logger = setup_logger(logger_name or "ast_validation", level=logging.INFO)
- code/data_filtering.py: setup_logger(level=logging.INFO)
- code/metric_validation.py: return setup_logger("metric_validation", log_file)
- code/main.py: logger = setup_logger(
- code/pilot_study.py: logger = setup_logger()
- code/sensitivity_analysis.py: logger = setup_logger(__name__, level=logging.INFO)
- code/logging_config.py: - setup_logger("name")
- code/logging_config.py: - setup_logger("name", "suffix")
- code/logging_config.py: - setup_logger("name", log_file="path")
- code/logging_config.py: - setup_logger("name", level=logging.INFO)
- code/logging_config.py: - setup_logger()
- code/logging_config.py: - setup_logger(level=logging.INFO)
- code/logging_config.py: # Handle the case where the first arg is a level (if called as setup_logger(level=...))
- code/logging_config.py: logger = setup_logger("test_logger", log_file="data/test.log")
- code/data_ingestion.py: logger = setup_logger("data_ingestion", log_file="data/ingestion.log")
- code/length_filtering.py: logger = setup_logger("length_filtering", "data/logs/length_filtering.log")
- code/guideline_generator.py: return setup_logger("guideline_generator", "guideline_generator")
- code/metric_aggregation.py: logger = setup_logger('metric_aggregation', level=logging.INFO)
- code/visualization.py: logger = setup_logger("visualization", "visualization")
- code/snippet_counter.py: logger = setup_logger("snippet_counter")
- code/cliffs_delta_analysis.py: logger = setup_logger("cliffs_delta", level=logging.INFO)

Make `setup_logger` in `code/pilot_study.py` accept ALL of the above.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/filtered_snippets.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/metric_extraction.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/filtered_snippets.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/metric_extraction.py`.
