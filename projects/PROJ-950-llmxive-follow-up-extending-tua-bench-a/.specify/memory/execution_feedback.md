# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/run_baseline.py --seed $SEED --output data/baseline_results/seed_${SEED}.json; python code/aggregate_results.py --mode baseline; python code/run_augmented.py --seed $SEED --top_k $K  --output data/augmented_results/k_${K}/seed_${SEED}.json; 2 command(s) failed: python code/generate_synthetic_tasks.py  --num_complex 12 --num_routine 12  --output data/synthetic_tasks.json (rc=1); python -m pytest -q tests/contract/test_execution_result.py (rc=4)

## Failing / missing run-book commands

- python -c "import json, hashlib, pathlib, sys;  manifest = json.load(open('data/manifest.json'));  for f, chksum in manifest.items():  data = pathlib.Path('data', f).read_bytes();  if hashlib.sha256(data).hexdigest() != chksum:  sys.exit(f'Checksum mismatch: {f}');  print('All checksums OK')" -> rc=1

  File "<string>", line 1
    import json, hashlib, pathlib, sys;  manifest = json.load(open('data/manifest.json'));  for f, chksum in manifest.items():  data = pathlib.Path('data', f).read_bytes();  if hashlib.sha256(data).hexdigest() != chksum:  sys.exit(f'Checksum mismatch: {f}');  print('All checksums OK')
                                                                                            ^^^
SyntaxError: invalid syntax

- python code/generate_synthetic_tasks.py  --num_complex 12 --num_routine 12  --output data/synthetic_tasks.json -> rc=1
 401 Unauthorized"
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

The above exception was the direct cause of the following exception:

ImportError: datasets library could not be imported

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/generate_synthetic_tasks.py", line 196, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/generate_synthetic_tasks.py", line 187, in main
    all_tasks = stream_tasks()
                ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/generate_synthetic_tasks.py", line 120, in stream_tasks
    return _load_with_hf_hub()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/generate_synthetic_tasks.py", line 84, in _load_with_hf_hub
    raise FileNotFoundError(
FileNotFoundError: Unable to locate a supported train split file in the 'tua_bench' repo.

- python code/run_baseline.py --seed $SEED --output data/baseline_results/seed_${SEED}.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-950-llmxive-follow-up-extending-tua-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/run_baseline.py': [Errno 2] No such file or directory

- python code/aggregate_results.py --mode baseline -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-950-llmxive-follow-up-extending-tua-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/aggregate_results.py': [Errno 2] No such file or directory

- python code/run_augmented.py --seed $SEED --top_k $K  --output data/augmented_results/k_${K}/seed_${SEED}.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-950-llmxive-follow-up-extending-tua-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/run_augmented.py': [Errno 2] No such file or directory

- python code/aggregate_results.py --mode augmented --top_k $K -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-950-llmxive-follow-up-extending-tua-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/aggregate_results.py': [Errno 2] No such file or directory

- python code/stats.py  --baseline data/baseline_results/aggregated.json  --augmented data/augmented_results/k_3/aggregated.json  --output-dir stats/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-950-llmxive-follow-up-extending-tua-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/stats.py': [Errno 2] No such file or directory

- python code/plot_results.py --stats-dir stats/ --fig-dir figures/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-950-llmxive-follow-up-extending-tua-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-950-llmxive-follow-up-extending-tua-bench-a/code/plot_results.py': [Errno 2] No such file or directory

- python -m pytest -q tests/contract/test_execution_result.py -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/test_execution_result.py


