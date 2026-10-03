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
    NEDNN_OPTS=0`.
I0000 00:00:1791045162.762244    2815 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI AVX512_BF16 AVX512_FP16 AVX_VNNI AMX_TILE AMX_INT8 AMX_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791045164.697807    2815 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1791045164.700487    2815 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 29, in <module>
    from analysis.convergence_monitor import main as convergence_monitor_main
ModuleNotFoundError: No module named 'analysis.convergence_monitor'
- python code/main.py --action estimate_noise --config config.yaml -> rc=1
    NEDNN_OPTS=0`.
I0000 00:00:1791045169.629538    2825 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI AVX512_BF16 AVX512_FP16 AVX_VNNI AMX_TILE AMX_INT8 AMX_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791045170.805986    2825 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1791045170.806282    2825 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 29, in <module>
    from analysis.convergence_monitor import main as convergence_monitor_main
ModuleNotFoundError: No module named 'analysis.convergence_monitor'
- python code/main.py --action generate_synthetic --config config.yaml -> rc=1
    NEDNN_OPTS=0`.
I0000 00:00:1791045174.039371    2836 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI AVX512_BF16 AVX512_FP16 AVX_VNNI AMX_TILE AMX_INT8 AMX_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791045175.201420    2836 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1791045175.201732    2836 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 29, in <module>
    from analysis.convergence_monitor import main as convergence_monitor_main
ModuleNotFoundError: No module named 'analysis.convergence_monitor'
- python code/main.py --action analyze --config config.yaml -> rc=1
    NEDNN_OPTS=0`.
I0000 00:00:1791045178.433592    2846 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI AVX512_BF16 AVX512_FP16 AVX_VNNI AMX_TILE AMX_INT8 AMX_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791045179.565502    2846 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1791045179.565813    2846 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 29, in <module>
    from analysis.convergence_monitor import main as convergence_monitor_main
ModuleNotFoundError: No module named 'analysis.convergence_monitor'
- python code/main.py --action report --config config.yaml -> rc=1
    NEDNN_OPTS=0`.
I0000 00:00:1791045182.829333    2856 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 AVX512F AVX512_VNNI AVX512_BF16 AVX512_FP16 AVX_VNNI AMX_TILE AMX_INT8 AMX_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791045183.974153    2856 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1791045183.974446    2856 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 29, in <module>
    from analysis.convergence_monitor import main as convergence_monitor_main
ModuleNotFoundError: No module named 'analysis.convergence_monitor'

## Declared deliverables still missing

- data/aggregated/convergence_log.json
- data/aggregated/split_half_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/aggregated/convergence_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/convergence_monitor.py` — NOT invoked by the run-book
    - `code/analysis/convergence_logger.py` — NOT invoked by the run-book
    - `code/analysis/glm_fitter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/convergence_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/aggregated/split_half_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/split_half_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
