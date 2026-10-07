# Execution failures — fix these before the analysis can run

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/main.py --action download --config config.yaml`
- `python code/main.py --action estimate_noise --config config.yaml`
- `python code/main.py --action generate_synthetic --config config.yaml`
- `python code/main.py --action analyze --config config.yaml`
- `python code/main.py --action report --config config.yaml`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --action download --config config.yaml (rc=1); python code/main.py --action estimate_noise --config config.yaml (rc=1); python code/main.py --action generate_synthetic --config config.yaml (rc=1); 2 declared deliverable(s) absent: data/aggregated/convergence_log.json; data/aggregated/split_half_results.json

## Failing / missing run-book commands

- python code/main.py --action download --config config.yaml -> rc=1
    datasets - INFO - TensorFlow version 2.21.0 available.

WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373560.242533    3087 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373562.681464    3087 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 36, in <module>
    from analysis.split_half_validator import main as split_half_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/analysis/split_half_validator.py", line 23, in <module>
    from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
ModuleNotFoundError: No module named 'utils.data_leakage_guard'
- python code/main.py --action estimate_noise --config config.yaml -> rc=1
    datasets - INFO - TensorFlow version 2.21.0 available.

WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373568.688018    3098 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373570.436863    3098 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 36, in <module>
    from analysis.split_half_validator import main as split_half_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/analysis/split_half_validator.py", line 23, in <module>
    from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
ModuleNotFoundError: No module named 'utils.data_leakage_guard'
- python code/main.py --action generate_synthetic --config config.yaml -> rc=1
    datasets - INFO - TensorFlow version 2.21.0 available.

WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373575.180933    3108 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373576.965243    3108 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 36, in <module>
    from analysis.split_half_validator import main as split_half_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/analysis/split_half_validator.py", line 23, in <module>
    from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
ModuleNotFoundError: No module named 'utils.data_leakage_guard'
- python code/main.py --action analyze --config config.yaml -> rc=1
    datasets - INFO - TensorFlow version 2.21.0 available.

WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373581.800377    3120 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373583.589713    3120 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 36, in <module>
    from analysis.split_half_validator import main as split_half_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/analysis/split_half_validator.py", line 23, in <module>
    from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
ModuleNotFoundError: No module named 'utils.data_leakage_guard'
- python code/main.py --action report --config config.yaml -> rc=1
    datasets - INFO - TensorFlow version 2.21.0 available.

WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373588.468828    3130 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791373590.202640    3130 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 36, in <module>
    from analysis.split_half_validator import main as split_half_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/analysis/split_half_validator.py", line 23, in <module>
    from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
ModuleNotFoundError: No module named 'utils.data_leakage_guard'

## Declared deliverables still missing

- data/aggregated/convergence_log.json
- data/aggregated/split_half_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/aggregated/convergence_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/utils/convergence_monitor.py` — NOT invoked by the run-book
    - `code/analysis/convergence_logger.py` — NOT invoked by the run-book
    - `code/analysis/glm_fitter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/convergence_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/aggregated/split_half_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/split_half_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
