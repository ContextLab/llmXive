# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/utils/verify_checksums.py; python code/classification/validator.py --input data/processed/classified_traces.json --golden data/raw/golden_set.json; python code/utils/generate_report.py --stats data/processed/stats_report.json --sensitivity data/processed/sensitivity_analysis.json --output docs/report.md; 6 command(s) failed: python code/data/generator.py --seed 42 --num-tasks a sufficient batch size (rc=1); python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json (rc=1); python code/intervention/runner.py --condition baseline --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/baseline_results.json (rc=1); 3 declared deliverable(s) absent: data/processed/baseline_results.json; data/processed/classification_report.json; data/raw/golden_subset.json

## Failing / missing run-book commands

- python code/data/generator.py --seed 42 --num-tasks a sufficient batch size -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/data/generator.py", line 205, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/data/generator.py", line 196, in main
    pairing_check = verify_pairing(trace.trace_id, seed_val)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/seeds.py", line 82, in verify_pairing
    raise ValueError("task_instance must be a dictionary")
ValueError: task_instance must be a dictionary
- python code/utils/verify_checksums.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/verify_checksums.py': [Errno 2] No such file or directory
- python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 98, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 73, in main
    raise FileNotFoundError(
FileNotFoundError: Input file not found: data/raw/golden_subset.json. Please ensure T015 has been executed to generate the golden subset.
- python code/classification/validator.py --input data/processed/classified_traces.json --golden data/raw/golden_set.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/validator.py': [Errno 2] No such file or directory
- python code/intervention/runner.py --condition baseline --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/baseline_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/runner.py", line 14, in <module>
    from utils.config import load_config, ModelConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/intervention/runner.py --condition intervention --checkpoint-interval 3 --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/intervention_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/runner.py", line 14, in <module>
    from utils.config import load_config, ModelConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/analysis/stats.py --baseline data/processed/baseline_results.json --intervention data/processed/intervention_results.json --output data/processed/stats_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/analysis/stats.py", line 1, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals,3,5 --output data/processed/sensitivity_analysis.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/analysis/sensitivity.py", line 18, in <module>
    from utils.config import load_config, CheckpointConfig, PipelineConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/utils/generate_report.py --stats data/processed/stats_report.json --sensitivity data/processed/sensitivity_analysis.json --output docs/report.md -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/generate_report.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/baseline_results.json
- data/processed/classification_report.json
- data/raw/golden_subset.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/classification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/classification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/golden_subset.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/classification/parser.py` — IS a run-book command
    - `code/classification/state_validator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/golden_subset.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/golden_subset.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/classification/parser.py`, `code/classification/state_validator.py`, `code/analysis/sensitivity.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/golden_subset.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/classification/parser.py`, `code/classification/state_validator.py`, `code/analysis/sensitivity.py`.
