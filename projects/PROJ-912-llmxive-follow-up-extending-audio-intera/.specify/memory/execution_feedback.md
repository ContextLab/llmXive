# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data/subtle_cue_builder.py  --datasets esc50,urban_sound_8k  --method composite  --threshold-freq 8000  --threshold-amp -40  --split-first`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/models/compress.py  --teacher facebook/wav2vec2-base-960h  --configs int,int4  --pruning-ratios,0.2  --distill  --calibration-data data/processed/subtle_cue_manifest.json; 5 command(s) failed: python code/data/subtle_cue_builder.py  --datasets esc50,urban_sound_8k  --method composite  --threshold-freq 8000  --threshold-amp -40  --split-first (rc=1); python code/inference/runner.py  --model-dir models/checkpoints/  --testbed data/processed/subtle_cue_manifest.json  --thresholds,0.05,0.1 (rc=1); python code/analysis/robustness_curve.py --input results/metrics.csv --output results/robustness_curve.png (rc=1); 5 declared deliverable(s) absent: data/processed/ablation_logits.parquet; data/processed/breaking_point.json; data/processed/robustness_curve.png

## Failing / missing run-book commands

- python code/data/subtle_cue_builder.py  --datasets esc50,urban_sound_8k  --method composite  --threshold-freq 8000  --threshold-amp -40  --split-first -> rc=1
    port Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?
- python code/models/compress.py  --teacher facebook/wav2vec2-base-960h  --configs int,int4  --pruning-ratios,0.2  --distill  --calibration-data data/processed/subtle_cue_manifest.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/models/compress.py': [Errno 2] No such file or directory
- python code/inference/runner.py  --model-dir models/checkpoints/  --testbed data/processed/subtle_cue_manifest.json  --thresholds,0.05,0.1 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/inference/runner.py", line 26, in <module>
    from inference.metrics import get_peak_ram_mb, check_constraints
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/inference/metrics.py", line 20, in <module>
    from utils.logger import get_logger, EvaluationError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/utils/logger.py", line 113, in <module>
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/utils/logger.py", line 48, in setup_logging
    log_dir = PathConfig().logs_dir
              ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'PathConfig' object has no attribute 'logs_dir'. Did you mean: 'code_dir'?
- python code/analysis/robustness_curve.py --input results/metrics.csv --output results/robustness_curve.png -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/robustness_curve.py", line 8, in <module>
    from utils.logger import get_logger, LlmXiveError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/utils/logger.py", line 113, in <module>
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/utils/logger.py", line 48, in setup_logging
    log_dir = PathConfig().logs_dir
              ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'PathConfig' object has no attribute 'logs_dir'. Did you mean: 'code_dir'?
- python code/analysis/sensitivity.py --input results/metrics.csv --output results/sensitivity_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/sensitivity.py", line 19, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/utils/logger.py", line 113, in <module>
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/utils/logger.py", line 48, in setup_logging
    log_dir = PathConfig().logs_dir
              ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'PathConfig' object has no attribute 'logs_dir'. Did you mean: 'code_dir'?
- python code/analysis/ablation.py --input results/metrics.csv --output results/ablation_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/ablation.py", line 15, in <module>
    from models.student import clone_model, freeze_attention_heads, prune_ffn_layers
ModuleNotFoundError: No module named 'models'

## Declared deliverables still missing

- data/processed/ablation_logits.parquet
- data/processed/breaking_point.json
- data/processed/robustness_curve.png
- data/processed/robustness_metrics.csv
- data/processed/sensitivity_report.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `PathConfig` (in `code/config.py`) — accessed via method/attribute names this round: `logs_dir`

`PathConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `PathConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`PathConfig.logs_dir` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/ablation_logits.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/inference/metrics.py` — NOT invoked by the run-book
    - `code/analysis/ablation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ablation_logits.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/breaking_point.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/utils/linters.py` — NOT invoked by the run-book
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
    - `code/analysis/robustness_curve.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/breaking_point.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_curve.png` is declared but was NOT written. Scripts referencing it:
    - `code/utils/linters.py` — NOT invoked by the run-book
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_curve.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/inference/integrate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
    - `code/analysis/robustness_curve.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/robustness_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/linters.py` — NOT invoked by the run-book
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
