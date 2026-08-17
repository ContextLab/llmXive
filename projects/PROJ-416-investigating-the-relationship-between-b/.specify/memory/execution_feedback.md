# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analysis/verify_power_analysis.py --effect-size 0.15 --alpha 0.05 --power 0.8`
- `python code/data/validate.py --dataset "openneuro" --check-variables "pre_treatment_score,post_treatment_score,anxiety_instrument"`
- `python code/main.py --mode analysis --correction "fdr" --sweep-motion "2.0,3.0" --sweep-pval "0.01,0.05,0.1" --sweep-outcome "change,residual,raw"`
- `python code/main.py --mode full --max-subjects 20 --atlas "Schaefer-100"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data/validate.py --dataset "openneuro" --check-variables "pre_treatment_score,post_treatment_score,anxiety_instrument" (rc=1); python code/analysis/verify_power_analysis.py --effect-size 0.15 --alpha 0.05 --power 0.8 (rc=1); python code/main.py --mode full --max-subjects 20 --atlas "Schaefer-100" (rc=1); 3 declared deliverable(s) absent: data/metrics/network_metrics.csv; data/metrics/power_analysis.json; data/verified_sources.json

## Failing / missing run-book commands

- python code/data/validate.py --dataset "openneuro" --check-variables "pre_treatment_score,post_treatment_score,anxiety_instrument" -> rc=1
    Verified sources file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/data/verified_sources.json
Pipeline halted: Missing verified dataset source. Run T001a first.
- python code/analysis/verify_power_analysis.py --effect-size 0.15 --alpha 0.05 --power 0.8 -> rc=1
    2026-08-17 18:13:40,387 - __main__ - INFO - Starting T048 verification: Power Analysis and Report Reference
2026-08-17 18:13:40,387 - __main__ - ERROR - Verification FAILED with unexpected error: 'Config' object has no attribute 'POWER_ANALYSIS_PATH'
- python code/main.py --mode full --max-subjects 20 --atlas "Schaefer-100" -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/code/main.py", line 13, in <module>
    from code.analysis.network import run_analysis as run_network_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/code/analysis/__init__.py", line 19, in <module>
    from .stats import calculate_vif, apply_fdr_correction, run_ancova_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/code/analysis/stats.py", line 45, in <module>
    def run_power_analysis(n_obs: int, effect_size: float, alpha: float) -> Dict[str, Any]:
                                                                                      ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?
- python code/main.py --mode analysis --correction "fdr" --sweep-motion "2.0,3.0" --sweep-pval "0.01,0.05,0.1" --sweep-outcome "change,residual,raw" -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/code/main.py", line 13, in <module>
    from code.analysis.network import run_analysis as run_network_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/code/analysis/__init__.py", line 19, in <module>
    from .stats import calculate_vif, apply_fdr_correction, run_ancova_analysis
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/code/analysis/stats.py", line 45, in <module>
    def run_power_analysis(n_obs: int, effect_size: float, alpha: float) -> Dict[str, Any]:
                                                                                      ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?

## Declared deliverables still missing

- data/metrics/network_metrics.csv
- data/metrics/power_analysis.json
- data/verified_sources.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/network_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/report.py` — NOT invoked by the run-book
    - `code/analysis/network.py` — NOT invoked by the run-book
    - `code/analysis/plots.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/analysis/save_results.py` — NOT invoked by the run-book
    - `code/analysis/save_metrics.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/network_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report.py` — NOT invoked by the run-book
    - `code/analysis/verify_power_analysis.py` — IS a run-book command
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/verified_sources.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/analysis/report.py` — NOT invoked by the run-book
    - `code/data/validate.py` — IS a run-book command
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/scripts/verify_openneuro_source.py` — NOT invoked by the run-book
    - `code/scripts/verify_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/verified_sources.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/data/verified_sources.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/report.py`, `code/scripts/verify_openneuro_source.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-416-investigating-the-relationship-between-b/data/verified_sources.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/config.py`, `code/analysis/report.py`, `code/data/validate.py`, `code/data/download.py`, `code/scripts/verify_openneuro_source.py`, `code/scripts/verify_gate.py`.
