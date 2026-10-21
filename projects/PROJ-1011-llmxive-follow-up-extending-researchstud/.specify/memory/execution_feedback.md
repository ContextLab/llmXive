# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/04_evaluation_recruitment.py: self-declared fabricated metric — “…e rows (commented out or with placeholder values)         # to guide the user…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…# Simulated record structure (in real imple…”
- code/04_evaluation_loader.py: synthetic/fake INPUT data not authorized by the spec — “…NING: This file contains MOCK data for testing ONLY. Do not…”
- code/error_handling_wrapper.py: synthetic/fake INPUT data not authorized by the spec — “…raise DataFetchError("Simulated data‑fetch failure for testin…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/04_evaluation_loader.py --blind    # writes blinded_batches.csv (incl. alignment rubric in instructions)`
  - script usage: `04_evaluation_loader.py [-h] [--generate-mock] [--seed SEED]`
  - argparse error: `04_evaluation_loader.py: error: unrecognized arguments: --blind # writes blinded_batches.csv (incl. alignment rubric in instructions)`
- run-book command: `python code/04_evaluation_loader.py --mock     # deterministic dry-run ratings`
  - script usage: `04_evaluation_loader.py [-h] [--generate-mock] [--seed SEED]`
  - argparse error: `04_evaluation_loader.py: error: unrecognized arguments: --mock # deterministic dry-run ratings`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/04_evaluation_recruitment.py: self-declared fabricated metric — “…e rows (commented out or with placeholder values)         # to guide the user…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…# Simulated record structure (in real imple…”; code/04_evaluation_loader.py: synthetic/fake INPUT data not authorized by the spec — “…NING: This file contains MOCK data for testing ONLY. Do not…”; 9 command(s) failed: python code/01_data_acquisition.py (rc=1); python code/01_data_acquisition.py --dry-run (rc=1); python code/02_pattern_mapping.py (rc=1); 2 declared deliverable(s) absent: data/results/power_analysis_config.json; data/results/ratings_filled.csv

## Failing / missing run-book commands

- python code/01_data_acquisition.py -> rc=1

INFO - Seed set to 42
INFO - Starting data acquisition pipeline...
INFO - Loaded data sources config with 3 sources
INFO - Streaming from arXiv category: cs.LG
INFO - Seed set to 42
ERROR - Pipeline failed unexpectedly: 'list' object has no attribute 'get'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 676, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 653, in main
    corpus = stream_and_sample(seed=42, target_non_ml=50)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 613, in stream_and_sample
    if source_config.get('domain') == 'non_ml':
       ^^^^^^^^^^^^^^^^^
AttributeError: 'list' object has no attribute 'get'

- python code/01_data_acquisition.py --dry-run -> rc=1

INFO - Seed set to 42
INFO - Starting data acquisition pipeline...
INFO - Loaded data sources config with 3 sources
INFO - Streaming from arXiv category: cs.LG
INFO - Seed set to 42
ERROR - Pipeline failed unexpectedly: 'list' object has no attribute 'get'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 676, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 653, in main
    corpus = stream_and_sample(seed=42, target_non_ml=50)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 613, in stream_and_sample
    if source_config.get('domain') == 'non_ml':
       ^^^^^^^^^^^^^^^^^
AttributeError: 'list' object has no attribute 'get'

- python code/02_pattern_mapping.py -> rc=1

INFO - Seed set to 42
INFO - Starting Pattern Mapping Pipeline
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/02_pattern_mapping.py", line 217, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/02_pattern_mapping.py", line 180, in main
    raise FileNotFoundError(f"Corpus not found at {corpus_path}. Run data acquisition first.")
FileNotFoundError: Corpus not found at data/processed/corpus.jsonl. Run data acquisition first.

- python code/03_proposal_generation.py -> rc=1

INFO - Starting proposal generation with batch processing...
ERROR - Power analysis config not found: data/results/power_analysis_config.json

- python code/04_evaluation_loader.py --blind    # writes blinded_batches.csv (incl. alignment rubric in instructions) -> rc=2

usage: 04_evaluation_loader.py [-h] [--generate-mock] [--seed SEED]
                               [--num-ratings NUM_RATINGS]
04_evaluation_loader.py: error: unrecognized arguments: --blind # writes blinded_batches.csv (incl. alignment rubric in instructions)

- python code/04_evaluation_loader.py --mock     # deterministic dry-run ratings -> rc=2

usage: 04_evaluation_loader.py [-h] [--generate-mock] [--seed SEED]
                               [--num-ratings NUM_RATINGS]
04_evaluation_loader.py: error: unrecognized arguments: --mock # deterministic dry-run ratings

- python code/05_statistical_analysis.py -> rc=1

CRITICAL - Analysis failed: Ratings file not found: data/results/ratings_real.csv or data/results/ratings_filled.csv

- python -m pytest tests/ -v -> rc=2
xec(co, module.__dict__)
tests/unit/test_update_state.py:24: in <module>
    from utils.update_state import (
E   ImportError: cannot import name 'ensure_state_dir' from 'utils.update_state' (/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/update_state.py)
=========================== short test summary info ============================
ERROR tests/unit/test_config_seed_pinning.py
ERROR tests/unit/test_data_dirs_and_checksum.py
ERROR tests/unit/test_evaluation_workflow.py
ERROR tests/unit/test_logging_infrastructure.py
ERROR tests/unit/test_logging_integration.py
ERROR tests/unit/test_model_classes.py
ERROR tests/unit/test_pairing_validation.py
ERROR tests/unit/test_pattern_mapping_validation.py
ERROR tests/unit/test_preprocessing_validation.py - FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/tests/code/01_data_acquisition.py'
ERROR tests/unit/test_update_state.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 2.41s ==============================


- python code/05_statistical_analysis.py --dry-run -> rc=1

CRITICAL - Analysis failed: Ratings file not found: data/results/ratings_real.csv or data/results/ratings_filled.csv


## Declared deliverables still missing

- data/results/power_analysis_config.json
- data/results/ratings_filled.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/power_analysis_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_proposal_generation.py` — IS a run-book command
  Make ONE of these WRITE `data/results/power_analysis_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/ratings_filled.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_evaluation_loader.py` — IS a run-book command
    - `code/04_evaluation_recruitment.py` — NOT invoked by the run-book
    - `code/05_statistical_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/results/ratings_filled.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
