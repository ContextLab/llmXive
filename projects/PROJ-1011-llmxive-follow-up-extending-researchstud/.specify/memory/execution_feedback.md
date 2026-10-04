# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/04_evaluation_recruitment.py: self-declared fabricated metric — “…e rows (commented out or with placeholder values)         # to guide the user…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…source_name)          # Mock record for structure validation…”
- code/models/pattern_card.py: synthetic/fake INPUT data not authorized by the spec — “…., 'Transfer Learning', 'Synthetic Data'     key_components: Lis…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/04_evaluation_recruitment.py: self-declared fabricated metric — “…e rows (commented out or with placeholder values)         # to guide the user…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…source_name)          # Mock record for structure validation…”; code/models/pattern_card.py: synthetic/fake INPUT data not authorized by the spec — “…., 'Transfer Learning', 'Synthetic Data'     key_components: Lis…”; 7 command(s) failed: python code/01_data_acquisition.py (rc=1); python code/02_pattern_mapping.py (rc=1); python code/02_pattern_validation.py (rc=1); 4 declared deliverable(s) absent: data/results/power_analysis_config.json; data/results/power_analysis_report.json; data/results/ratings_filled.csv

## Failing / missing run-book commands

- python code/01_data_acquisition.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/01_data_acquisition.py", line 15, in <module>
    from utils.config import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/config.py", line 15, in <module>
    from utils.logging_config import log_model_switch, log_memory_error, log_fallback_success, log_fallback_failure
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/02_pattern_mapping.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/02_pattern_mapping.py", line 14, in <module>
    from utils.config import get_model_config, set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/config.py", line 15, in <module>
    from utils.logging_config import log_model_switch, log_memory_error, log_fallback_success, log_fallback_failure
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/02_pattern_validation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/02_pattern_validation.py", line 14, in <module>
    from utils.logging_config import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/03_proposal_generation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/03_proposal_generation.py", line 16, in <module>
    from utils.config import set_seed, get_model_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/config.py", line 15, in <module>
    from utils.logging_config import log_model_switch, log_memory_error, log_fallback_success, log_fallback_failure
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/04_evaluation_loader.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/04_evaluation_loader.py", line 19, in <module>
    from utils.logging_config import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/05_statistical_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/05_statistical_analysis.py", line 40, in <module>
    from utils.logging_config import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/05_statistical_analysis.py --dry-run -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/05_statistical_analysis.py", line 40, in <module>
    from utils.logging_config import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1011-llmxive-follow-up-extending-researchstud/code/utils/logging_config.py", line 86, in <module>
    def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
                                      ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

## Declared deliverables still missing

- data/results/power_analysis_config.json
- data/results/power_analysis_report.json
- data/results/ratings_filled.csv
- data/results/validity_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/power_analysis_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_proposal_generation.py` — IS a run-book command
  Make ONE of these WRITE `data/results/power_analysis_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_statistical_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/results/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/ratings_filled.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_evaluation_recruitment.py` — NOT invoked by the run-book
    - `code/04_evaluation_loader.py` — IS a run-book command
    - `code/05_statistical_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/results/ratings_filled.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/validity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_statistical_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/results/validity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
