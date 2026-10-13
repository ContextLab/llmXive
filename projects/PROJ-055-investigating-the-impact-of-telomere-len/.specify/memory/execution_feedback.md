# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/04_sensitivity.py; 5 command(s) failed: python code/01_discover_data.py (rc=1); python code/02_ingest_data.py (rc=1); python code/03_clean_merge.py (rc=1)

## Failing / missing run-book commands

- python code/01_discover_data.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/01_discover_data.py", line 153, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/01_discover_data.py", line 115, in main
    logger = setup_logging(LOG_FILE)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/logging_config.py", line 55, in setup_logging
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
                                     ^^^^^^^^^^^^^^^
AttributeError: 'PosixPath' object has no attribute 'upper'

- python code/02_ingest_data.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/02_ingest_data.py", line 13, in <module>
    _config = get_config()
              ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/config.py", line 133, in get_config
    return init_config()
           ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/config.py", line 118, in init_config
    validate_config(env_vars)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/config.py", line 84, in validate_config
    raise ConfigError(f"Missing or empty required configuration key: {key}")
config.ConfigError: Missing or empty required configuration key: DRYAD_API_KEY

- python code/03_clean_merge.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/03_clean_merge.py", line 14, in <module>
    _config = get_config()
              ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/config.py", line 133, in get_config
    return init_config()
           ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/config.py", line 118, in init_config
    validate_config(env_vars)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/config.py", line 84, in validate_config
    raise ConfigError(f"Missing or empty required configuration key: {key}")
config.ConfigError: Missing or empty required configuration key: DRYAD_API_KEY

- python code/04_model_pglS.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/04_model_pglS.py", line 9, in <module>
    import rpy2.robjects as ro
ModuleNotFoundError: No module named 'rpy2'

- python code/04_sensitivity.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/04_sensitivity.py': [Errno 2] No such file or directory

- python code/05_visualize.py -> rc=1
2026-10-13 21:09:36 - telomere_pipeline - INFO - Logging infrastructure initialized
2026-10-13 21:09:36 - telomere_pipeline - INFO - Memory Status: RSS=166,391,808B, Threshold=6,442,450,944B, Exceeds: False

Unexpected error during plot generation: log_memory_status() missing 1 required positional argument: 'logger'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/05_visualize.py", line 159, in main
    log_memory_status()
TypeError: log_memory_status() missing 1 required positional argument: 'logger'

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
