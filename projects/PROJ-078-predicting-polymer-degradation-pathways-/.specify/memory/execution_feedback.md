# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…List[Dict]:     """     Generate synthetic data as a fallback if AP…”
- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…le):         # Fallback: generate synthetic data if T013 hasn't run…”
- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…e} not found. Generating synthetic seed data.")         # Generate a…”
- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…c seed data.")         # Generate a small synthetic dataset for T013 to simu…”
- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…a)         logger.info(f"Generated synthetic seed data at {input_file…”
- code/model.py: synthetic/fake INPUT data not authorized by the spec — “…led.")          # Create dummy data         num_nodes = 20…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…List[Dict]:     """     Generate synthetic data as a fallback if AP…”; code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…le):         # Fallback: generate synthetic data if T013 hasn't run…”; code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…e} not found. Generating synthetic seed data.")         # Generate a…”; 11 run-book script(s) missing (plan/impl path mismatch): python code/label_validation.py  --input data/raw/combined.parquet  --output data/processed/records.parquet; python code/create_external_validation.py  --input data/processed/records.parquet  --output data/external/validation.parquet  --min-curated 30; python code/evaluate_external.py  --model code/models/model.pt  --external data/external/validation.parquet  --output state/external_metrics.json; 8 command(s) failed: python -m pytest -q (rc=2); python code/ingest.py  --polymer-genome-url https://huggingface.co/datasets/PolymerGenome/polymer_degradation/resolve/main/data.parquet  --materials-url https://materialsproject.org/rest/v2/materials  --output data/raw/combined.parquet (rc=1); python code/preprocess.py  --input data/processed/records.parquet  --graph-dir data/processed/graphs/ (rc=1)

## Failing / missing run-book commands

- python -m pytest -q -> rc=2
lt argument 'edge_ind...
ERROR tests/unit/test_data_models.py - TypeError: non-default argument 'edge_...
ERROR tests/unit/test_evaluate.py - TypeError: non-default argument 'edge_ind...
ERROR tests/unit/test_ingest.py - TypeError: get_logger() takes 0 positional ...
ERROR tests/unit/test_logging.py - TypeError: get_logger() takes 0 positional...
ERROR tests/unit/test_model.py - TypeError: get_logger() takes 0 positional a...
ERROR tests/unit/test_power_analysis.py
ERROR tests/unit/test_preprocess.py - TypeError: non-default argument 'edge_i...
ERROR tests/unit/test_preprocess_save.py - TypeError: non-default argument 'e...
ERROR tests/unit/test_preprocess_t017b.py - TypeError: non-default argument '...
ERROR tests/unit/test_reporting.py - TypeError: non-default argument 'edge_in...
ERROR tests/unit/test_subsampling.py - TypeError: non-default argument 'edge_...
ERROR tests/unit/test_train.py - TypeError: get_logger() takes 0 positional a...
ERROR tests/unit/test_training.py - TypeError: get_logger() takes 0 positiona...
!!!!!!!!!!!!!!!!!!! Interrupted: 27 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 27 errors in 7.02s ==============================


- python code/ingest.py  --polymer-genome-url https://huggingface.co/datasets/PolymerGenome/polymer_degradation/resolve/main/data.parquet  --materials-url https://materialsproject.org/rest/v2/materials  --output data/raw/combined.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/ingest.py", line 14, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

- python code/label_validation.py  --input data/raw/combined.parquet  --output data/processed/records.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/label_validation.py': [Errno 2] No such file or directory

- python code/preprocess.py  --input data/processed/records.parquet  --graph-dir data/processed/graphs/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/preprocess.py", line 22, in <module>
    from data_models import PolymerRecord, MolecularGraph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/data_models.py", line 73, in <module>
    @dataclass
     ^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/dataclasses.py", line 1232, in dataclass
    return wrap(cls)
           ^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/dataclasses.py", line 1222, in wrap
    return _process_class(cls, init, repr, eq, order, unsafe_hash,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/dataclasses.py", line 1027, in _process_class
    _init_fn(all_init_fields,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/dataclasses.py", line 545, in _init_fn
    raise TypeError(f'non-default argument {f.name!r} '
TypeError: non-default argument 'edge_index' follows default argument

- python code/power_analysis.py  --records data/processed/records.parquet  --output state/power_analysis.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/power_analysis.py", line 125, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/power_analysis.py", line 121, in main
    input_path = paths['processed'] / 'processed_graph_dataset.csv'
                 ~~~~~^^^^^^^^^^^^^
KeyError: 'processed'

- python code/augment.py  --graph-dir data/processed/graphs/  --output data/augmented/graphs/  --method bond_rotation_atom_masking  --factor 2 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/augment.py", line 15, in <module>
    logger = setup_logging("augment")
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/utils.py", line 17, in setup_logging
    _logger.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'augment'

- python -c "import pyarrow.parquet as pq; n_pre = len(pq.read_table('data/processed/records.parquet')); n_aug = len(pq.read_table('data/augmented/records.parquet')); assert n_aug == 2*n_pre" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pyarrow'

- python code/create_external_validation.py  --input data/processed/records.parquet  --output data/external/validation.parquet  --min-curated 30 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/create_external_validation.py': [Errno 2] No such file or directory

- python code/train.py  --graph-dir data/augmented/graphs/  --folds 5  --epochs 100  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/train.py", line 26, in <module>
    from model import PolymerGNN, create_model_from_config, validate_model_constraints
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/model.py", line 24, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

- python code/evaluate_external.py  --model code/models/model.pt  --external data/external/validation.parquet  --output state/external_metrics.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/evaluate_external.py': [Errno 2] No such file or directory

- python code/attribution.py  --model code/models/model.pt  --graph-dir data/augmented/graphs/  --output data/attribution/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/attribution.py': [Errno 2] No such file or directory

- python code/mcnemar_test.py  --predictions data/attribution/predictions.parquet  --labels data/external/validation.parquet  --output state/mcnemar_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/mcnemar_test.py': [Errno 2] No such file or directory

- python code/null_distribution.py  --attribution-dir data/attribution/  --iterations 1000  --output state/null_distribution.npy -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/null_distribution.py': [Errno 2] No such file or directory

- python code/permutation_test.py  --null state/null_distribution.npy  --attribution data/attribution/  --output data/reports/perm_test_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/permutation_test.py': [Errno 2] No such file or directory

- python code/confounding_assessment.py  --attribution-dir data/attribution/  --output state/confounding_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/confounding_assessment.py': [Errno 2] No such file or directory

- python code/ablation.py  --graph-dir data/processed/graphs/  --external data/external/validation.parquet  --output state/ablation_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/ablation.py': [Errno 2] No such file or directory

- python code/visualization.py  --motif-importance data/output/model_output.json  --output data/reports/visualizations/top5_pathways.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/visualization.py': [Errno 2] No such file or directory

- python code/report.py  --metrics state/training_metrics.json  --external state/external_metrics.json  --mcnemar state/mcnemar_results.json  --perm_test data/reports/perm_test_results.json  --confounding state/confounding_report.json  --ablation state/ablation_results.json  --output docs/reports/final_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -q -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.3, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-078-predicting-polymer-degradation-pathways-
configfile: pytest.ini
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/


- python -m llmxive.reference_validator  --files plan.md research.md quickstart.md  --log state/reference_validator.log -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-078-predicting-polymer-degradation-pathways-/bin/python: Error while finding module specification for 'llmxive.reference_validator' (ModuleNotFoundError: No module named 'llmxive')


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pubchempy` to the project's `requirements.txt` and `pip install pubchempy`.
- **Verified**: this loads **1** real records with fields: _record, _atoms, _bonds.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pubchempy as pcp

results = pcp.get_compounds('benzene', 'name')
print(f'RECORDS={len(results)}')
if results:
    sample = results[0]
    fields = ','.join(sample.__dict__.keys())
    print(f'FIELDS={fields}')
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
