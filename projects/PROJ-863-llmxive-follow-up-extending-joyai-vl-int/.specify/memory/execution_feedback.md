# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/utils/validation.py --check-cpu; python code/feature_extraction/extractor.py --model-path ./models/joyai-vl-int --batch-size 100; 5 command(s) failed: python code/src/data_synthesis/generator.py --duration 10 --seed 42 --inject-noise (rc=1); python code/src/baseline/visual_detector.py --manifest data/manifest.jsonl (rc=1); python code/src/scheduler/train.py --epochs 10 --lr 1e-4 (rc=1)

## Failing / missing run-book commands

- python code/utils/validation.py --check-cpu -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/utils/validation.py': [Errno 2] No such file or directory

- python code/src/data_synthesis/generator.py --duration 10 --seed 42 --inject-noise -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/data_synthesis/generator.py", line 276, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/data_synthesis/generator.py", line 235, in main
    get_required_env_vars(required_vars)
TypeError: get_required_env_vars() takes 0 positional arguments but 1 was given

- python code/src/baseline/visual_detector.py --manifest data/manifest.jsonl -> rc=1
2026-10-16 15:28:27,855 | INFO     | NoisyVisualDetector-Runner | Starting Noisy Visual Detector (T026b)
2026-10-16 15:28:27,856 | ERROR    | NoisyVisualDetector-Runner | Input file not found: data/baseline/deterministic_predictions.jsonl

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/baseline/visual_detector.py", line 272, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/baseline/visual_detector.py", line 229, in main
    raise FileNotFoundError(f"Missing deterministic predictions at {input_path}. Run T026a first.")
FileNotFoundError: Missing deterministic predictions at data/baseline/deterministic_predictions.jsonl. Run T026a first.

- python code/feature_extraction/extractor.py --model-path ./models/joyai-vl-int --batch-size 100 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/feature_extraction/extractor.py': [Errno 2] No such file or directory

- python code/src/scheduler/train.py --epochs 10 --lr 1e-4 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/scheduler/train.py", line 364, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/scheduler/train.py", line 315, in main
    env_config = load_environment_config()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/utils/env_config.py", line 59, in load_environment_config
    raise ValueError(error)
ValueError: Missing required environment variables: JOYAI_VL_MODEL_PATH, DATA_SEED

- python code/src/scheduler/eval.py --checkpoint models/scheduler_checkpoint.pth --baseline data/baseline/ -> rc=1
2026-10-16 15:28:30,122 | INFO     | __main__ | Starting scheduler evaluation...
2026-10-16 15:28:30,122 | INFO     | __main__ | Evaluating scheduler with predictions: /home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/data/scheduler/predictions.jsonl
2026-10-16 15:28:30,122 | INFO     | __main__ | Using ground truth: /home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/data/raw/manifest.jsonl
2026-10-16 15:28:30,122 | ERROR    | __main__ | File not found: Predictions file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/data/scheduler/predictions.jsonl


- python -m pytest tests/ -> rc=2
.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validation.py:17: in <module>
    from src.utils.validation import (
E   ImportError: cannot import name 'validate_jsonl_schema' from 'src.utils.validation' (/home/runner/work/llmXive/llmXive/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int/code/src/utils/validation.py)
=========================== short test summary info ============================
ERROR tests/integration/test_feature_pipeline.py
ERROR tests/integration/test_training_pipeline.py
ERROR tests/unit/test_ambiguous_event_resolver.py
ERROR tests/unit/test_exporter.py
ERROR tests/unit/test_feature_extractor.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_pytest_config.py - Failed: 'memory_limit' not found in ...
ERROR tests/unit/test_streaming.py
ERROR tests/unit/test_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 9 errors in 1.61s =========================


