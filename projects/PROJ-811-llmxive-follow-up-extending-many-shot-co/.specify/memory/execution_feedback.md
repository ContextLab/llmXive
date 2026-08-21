# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9`
  - script usage: `prompt_gen.py [-h] --manifest MANIFEST`
  - argparse error: `prompt_gen.py: error: the following arguments are required: --manifest`
- run-book command: `python code/src/inference.py --prompts data/processed/prompts/ --models qwen2.5-7b llama-3.1-8b`
  - script usage: `inference.py [-h] --model-class {reasoning,non_reasoning} [--seed SEED]`
  - argparse error: `inference.py: error: the following arguments are required: --model-class`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/src/download_data.py; python code/src/validate_metric.py --dags data/processed/dags.json --gold data/processed/gold_standard_annotations.json; 4 command(s) failed: python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9 (rc=2); python code/src/inference.py --prompts data/processed/prompts/ --models qwen2.5-7b llama-3.1-8b (rc=2); python code/src/analysis.py --input data/results/inference_log.csv (rc=1); 3 declared deliverable(s) absent: data/processed/dag_manifest.json; data/processed/gold_standard_annotations.json; data/processed/prompt_manifest.json

## Failing / missing run-book commands

- python code/src/download_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/download_data.py': [Errno 2] No such file or directory
- python code/src/validate_metric.py --dags data/processed/dags.json --gold data/processed/gold_standard_annotations.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/validate_metric.py': [Errno 2] No such file or directory
- python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9 -> rc=2
    usage: prompt_gen.py [-h] --manifest MANIFEST
                     [--strategy {original_cds,logical_ascending,logical_random}]
                     [--seed SEED] [--output OUTPUT]
prompt_gen.py: error: the following arguments are required: --manifest
- python code/src/inference.py --prompts data/processed/prompts/ --models qwen2.5-7b llama-3.1-8b -> rc=2
    usage: inference.py [-h] --model-class {reasoning,non_reasoning} [--seed SEED]
                    [--prompt-file PROMPT_FILE] [--output-dir OUTPUT_DIR]
inference.py: error: the following arguments are required: --model-class
- python code/src/analysis.py --input data/results/inference_log.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/analysis.py", line 7, in <module>
    from statsmodels.stats.effect_size import compute_effsize
ImportError: cannot import name 'compute_effsize' from 'statsmodels.stats.effect_size' (/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/.venv/lib/python3.11/site-packages/statsmodels/stats/effect_size.py)
- python code/src/update_state.py -> rc=1
    Usage: python -m code.src.update_state <command> [arguments]
Commands: hash, update, verify, verify-all, status

## Declared deliverables still missing

- data/processed/dag_manifest.json
- data/processed/gold_standard_annotations.json
- data/processed/prompt_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dag_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_generate_dag_manifest.py` — NOT invoked by the run-book
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
    - `code/tests/test_prompt_gen.py` — NOT invoked by the run-book
    - `code/scripts/filter_invalid_dags.py` — NOT invoked by the run-book
    - `code/scripts/generate_dag_manifest.py` — NOT invoked by the run-book
    - `code/scripts/validate_dag_correlation.py` — NOT invoked by the run-book
    - `code/scripts/run_prompt_strategies.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/dag_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gold_standard_annotations.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_gold_standard_template.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gold_standard_annotations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prompt_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_validate_prompt_orderings.py` — NOT invoked by the run-book
    - `code/tests/test_generate_prompt_manifest.py` — NOT invoked by the run-book
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/scripts/validate_prompt_orderings.py` — NOT invoked by the run-book
    - `code/scripts/generate_prompt_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompt_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
