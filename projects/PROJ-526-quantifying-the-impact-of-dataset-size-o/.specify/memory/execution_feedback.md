# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download_data.py --output data/raw/ (rc=1); python code/generate_descriptors.py --input data/raw/ --output data/processed/ (rc=1); python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv (rc=1)

## Failing / missing run-book commands

- python code/download_data.py --output data/raw/ -> rc=1
    2026-09-29 18:38:19 | INFO     | __main__ | Starting data download with chunked loading and memory optimization.
2026-09-29 18:38:19 | WARNING  | __main__ | Could not load config: get_config() takes 0 positional arguments but 1 was given. Using default datasets.
2026-09-29 18:38:19 | ERROR    | __main__ | No datasets specified. Please provide --datasets or configure in config.yaml.
- python code/generate_descriptors.py --input data/raw/ --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/generate_descriptors.py", line 25, in <module>
    from matminer.featurizers.composition import MagpieData
ImportError: cannot import name 'MagpieData' from 'matminer.featurizers.composition' (/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/.venv/lib/python3.11/site-packages/matminer/featurizers/composition/__init__.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/generate_descriptors.py", line 27, in <module>
    raise ImportError(
ImportError: The 'matminer' package is required for Magpie descriptor generation. Please install it via 'pip install matminer' and ensure 'pymatgen' is also installed.
- python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv -> rc=1
    2026-09-29 18:38:22 | INFO     | __main__ | Starting learning curve generation
2026-09-29 18:38:22 | ERROR    | __main__ | Error during learning curve generation: Feature file not found: data/processed/magpie_features.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/train_learning_curves.py", line 257, in main
    df = load_master_dataset(args.features)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/train_learning_curves.py", line 45, in load_master_dataset
    raise FileNotFoundError(f"Feature file not found: {features_path}")
FileNotFoundError: Feature file not found: data/processed/magpie_features.csv
- python code/fit_scaling_laws.py --input data/processed/learning_curves.csv --output data/processed/scaling_results.csv -> rc=1
    2026-09-29 18:38:23 | INFO     | __main__ | Starting scaling law fitting process

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/fit_scaling_laws.py", line 312, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/fit_scaling_laws.py", line 258, in main
    data_dir = require_data_dir(config)
               ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: require_data_dir() takes 0 positional arguments but 1 was given
- python code/analyze_physics.py --input data/processed/scaling_results.csv --output data/processed/final_analysis.csv -> rc=1
    Error in physical metrics analysis: 'Config' object has no attribute 'get'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/analyze_physics.py", line 479, in main
    data_dir = config.get('data_dir', 'data')
               ^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'get'
- python code/visualize_results.py --input data/processed/final_analysis.csv --output figures/ -> rc=1
    native files...
2026-09-29 18:38:27,549 - __main__ - ERROR - Data file missing: Learning curve file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/data/processed/learning_curves.csv
2026-09-29 18:38:27,549 - __main__ - ERROR - Ensure T019 (learning curves) and T020 (scaling laws) have run successfully.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 335, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 304, in main
    lc_df = load_learning_curve_data()
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 79, in load_learning_curve_data
    raise FileNotFoundError(f"Learning curve file not found: {lc_path}")
FileNotFoundError: Learning curve file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/data/processed/learning_curves.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `require_data_dir` — defined in `code/config.py`; called 3 way(s):

- code/consolidate_data.py: data_dir = require_data_dir()
- code/fit_scaling_laws.py: data_dir = require_data_dir(config)
- code/visualize_results.py: data_dir = require_data_dir()

Make `require_data_dir` in `code/config.py` accept ALL of the above.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `get`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.get` call sites (16):
- code/generate_final_summary.py: permutation_p_value = stats_data.get('permutation_test', {}).get('p_value', np.nan)
- code/generate_final_summary.py: class_comparison = stats_data.get('comparison', 'unknown')
- code/analyze_physics.py: positions = structure_data.get('positions', [])
- code/analyze_physics.py: lattice = structure_data.get('lattice', None)
- code/analyze_physics.py: data_dir = config.get('data_dir', 'data')
- code/download_data.py: files_to_download = metadata.get('siblings', [])
- code/download_data.py: token = config.get('huggingface_token')
- code/download_data.py: default_datasets = config.get('datasets', [])
- code/models.py: structure_available=data.get("structure_available", False),
- code/models.py: metadata=data.get("metadata", {})
- code/validate_properties.py: data_dir = Path(config.get('data_dir', 'data'))
- code/validate_properties.py: state_dir = Path(config.get('state_dir', 'state'))
- code/utils/integrity.py: if r.get("file_path") == file_str
- code/utils/integrity.py: latest_record = max(matching_records, key=lambda x: x.get("timestamp", ""))
- code/utils/integrity.py: expected_checksum = latest_record.get("checksum")
- code/utils/integrity.py: f_path = record.get("file_path")

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/data/processed/learning_curves.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train_learning_curves.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/data/processed/learning_curves.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train_learning_curves.py`, `code/visualize_results.py`.
