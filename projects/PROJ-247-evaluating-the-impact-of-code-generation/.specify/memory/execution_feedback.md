# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- data/raw/clones/CopilotKit_CopilotKit/showcase/GOTCHAS.md: self-declared fabricated metric — “…-tool-based` answered "I used placeholder values since no sales figures were…”
- data/raw/clones/CopilotKit_CopilotKit/showcase/integrations/mastra/qa/background-agents.md: self-declared fabricated metric — “…arted` lifecycle plus a       placeholder result. Do NOT expect the card to an…”
- data/raw/clones/bradygaster_squad/.copilot/skills/secret-handling/SKILL.md: self-declared fabricated metric — “…env.example` (safe — contains placeholder values, no real secrets) - `.env.sa…”
- data/raw/clones/bradygaster_squad/.copilot/skills/secret-handling/SKILL.md: self-declared fabricated metric — “…**What to write instead:** - Placeholder values: `DATABASE_URL=<set in .env>…”
- data/raw/clones/bradygaster_squad/.squad/rai/policy.md: self-declared fabricated metric — “…ion, smoke test | Ableist | | dummy value | placeholder, sample | Poten…”
- data/raw/clones/bradygaster_squad/.squad-templates/rai-policy.md: self-declared fabricated metric — “…ion, smoke test | Ableist | | dummy value | placeholder, sample | Poten…”
- data/raw/clones/bradygaster_squad/.squad-templates/skills/secret-handling/SKILL.md: self-declared fabricated metric — “…env.example` (safe — contains placeholder values, no real secrets) - `.env.sa…”
- data/raw/clones/bradygaster_squad/.squad-templates/skills/secret-handling/SKILL.md: self-declared fabricated metric — “…**What to write instead:** - Placeholder values: `DATABASE_URL=<set in .env>…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/repo_list.csv, data/raw/repo_metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/01_data_curation.py --tag # Assuming tagging is integrated or in a separate script`
  - script usage: `01_data_curation.py [-h] [--curate] [--tag]`
  - argparse error: `01_data_curation.py: error: unrecognized arguments: # Assuming tagging is integrated or in a separate script`
- run-book command: `python code/utils/matching.py # Or the designated matching script`
  - script usage: `matching.py [-h] [--input INPUT] [--output OUTPUT]`
  - argparse error: `matching.py: error: unrecognized arguments: # Or the designated matching script`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 363 fabricated/simulated-result signal(s) — results are not real measurements: data/raw/clones/CopilotKit_CopilotKit/showcase/GOTCHAS.md: self-declared fabricated metric — “…-tool-based` answered "I used placeholder values since no sales figures were…”; data/raw/clones/CopilotKit_CopilotKit/showcase/integrations/mastra/qa/background-agents.md: self-declared fabricated metric — “…arted` lifecycle plus a       placeholder result. Do NOT expect the card to an…”; data/raw/clones/bradygaster_squad/.copilot/skills/secret-handling/SKILL.md: self-declared fabricated metric — “…env.example` (safe — contains placeholder values, no real secrets) - `.env.sa…”; every produced artifact is gitignored (data/raw/repo_list.csv, data/raw/repo_metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 command(s) failed: python code/01_data_curation.py --tag # Assuming tagging is integrated or in a separate script (rc=2); python code/utils/matching.py # Or the designated matching script (rc=2); python code/02_metric_extraction.py (rc=1); 8 declared deliverable(s) absent: data/ground_truth/classifier_metrics.json; data/logs/refactor_validation_report.json; data/logs/repo_exclusions.csv

## Failing / missing run-book commands

- python code/01_data_curation.py --tag # Assuming tagging is integrated or in a separate script -> rc=2

None of PyTorch, TensorFlow >= 2.0, or Flax have been found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
usage: 01_data_curation.py [-h] [--curate] [--tag]
01_data_curation.py: error: unrecognized arguments: # Assuming tagging is integrated or in a separate script

- python code/utils/matching.py # Or the designated matching script -> rc=2

usage: matching.py [-h] [--input INPUT] [--output OUTPUT]
                   [--repo-metadata REPO_METADATA]
                   [--log-level {DEBUG,INFO,WARNING,ERROR}]
matching.py: error: unrecognized arguments: # Or the designated matching script

- python code/02_metric_extraction.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/02_metric_extraction.py", line 437, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/02_metric_extraction.py", line 426, in main
    setup_logging()
TypeError: setup_logging() missing 1 required positional argument: 'name'

- python code/03_analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 365, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 308, in main
    setup_logging()
TypeError: setup_logging() missing 1 required positional argument: 'name'

- python code/03_visualization.py -> rc=1
2026-10-12 16:51:48,703 - visualization - INFO - Starting visualization pipeline (T030)
2026-10-12 16:51:48,704 - visualization - ERROR - Data loading failed: Metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/data/processed/metrics_longitudinal.csv


- python code/04_ground_truth_selection.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/04_ground_truth_selection.py", line 148, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/04_ground_truth_selection.py", line 123, in main
    setup_logging()
TypeError: setup_logging() missing 1 required positional argument: 'name'

- python -m pytest tests/ -> rc=2
runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/tests/unit/test_repo_filter.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_repo_filter.py:17: in <module>
    from utils.repo_filter import (
E   ImportError: cannot import name 'MIN_LLM_BLOCKS' from 'utils.repo_filter' (/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/utils/repo_filter.py)
=========================== short test summary info ============================
ERROR tests/unit/test_05_classifier_evaluation.py
ERROR tests/unit/test_bug_fix_latency.py
ERROR tests/unit/test_checksum_generation.py
ERROR tests/unit/test_classifier_metrics.py
ERROR tests/unit/test_code_block_extraction.py
ERROR tests/unit/test_repo_deletion_handling.py
ERROR tests/unit/test_repo_filter.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 1.24s ===============================



## Declared deliverables still missing

- data/ground_truth/classifier_metrics.json
- data/logs/refactor_validation_report.json
- data/logs/repo_exclusions.csv
- data/processed/matched_pairs.csv
- data/processed/matched_pairs_filtered.csv
- data/processed/metrics_longitudinal.csv
- data/processed/tagged_blocks.csv
- data/raw/code_blocks.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/ground_truth/classifier_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_analysis.py` — IS a run-book command
    - `code/03_visualization.py` — IS a run-book command
    - `code/05_classifier_evaluation.py` — NOT invoked by the run-book
    - `code/08_classifier_threshold_validation.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `scripts/run_classifier_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/ground_truth/classifier_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/refactor_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/git_mv_detector.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/refactor_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/repo_exclusions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/repo_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/repo_exclusions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matched_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_extraction.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
    - `code/03_visualization.py` — IS a run-book command
    - `code/04_ground_truth_selection.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matched_pairs_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_extraction.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/utils/repo_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_pairs_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_longitudinal.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_edge_case_handler.py` — NOT invoked by the run-book
    - `code/02_metric_extraction.py` — IS a run-book command
    - `code/02_metric_validation.py` — NOT invoked by the run-book
    - `code/03_analysis.py` — IS a run-book command
    - `code/03_visualization.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_longitudinal.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tagged_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — IS a run-book command
    - `code/05_classifier_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tagged_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/code_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — IS a run-book command
    - `code/utils/git_mv_detector.py` — NOT invoked by the run-book
    - `code/utils/matching.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/code_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
