# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/interpret/pca_correlation.py --report_out interpretability_report.md; 6 command(s) failed: python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv (rc=1); python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 (rc=1); python src/training/evaluate.py --metrics_out data/results_composition_only.json (rc=1)

## Failing / missing run-book commands

- python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv -> rc=1
/loader.py", line 127, in load_and_clean
    sample = pd.read_csv(input_path, nrows=0)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/materials.csv'

- python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 18, in <module>
    from src.graphs.composition import build_composition_graph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/graphs/composition.py", line 30, in <module>
    from pymatgen.core import Composition
ModuleNotFoundError: No module named 'pymatgen'

- python src/training/evaluate.py --metrics_out data/results_composition_only.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 22, in <module>
    from src.graphs.composition import build_composition_graph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/graphs/composition.py", line 30, in <module>
    from pymatgen.core import Composition
ModuleNotFoundError: No module named 'pymatgen'

- python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 14, in <module>
    from src.graphs.composition import build_composition_graph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/graphs/composition.py", line 30, in <module>
    from pymatgen.core import Composition
ModuleNotFoundError: No module named 'pymatgen'

- python src/interpret/extract_embeddings.py --out outputs/node_embeddings.npy -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py", line 17, in <module>
    from src.graphs.composition import build_composition_graph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/graphs/composition.py", line 30, in <module>
    from pymatgen.core import Composition
ModuleNotFoundError: No module named 'pymatgen'

- python src/interpret/pca_correlation.py --report_out interpretability_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py': [Errno 2] No such file or directory

- python -m pytest -q tests/ -> rc=2

==================================== ERRORS ====================================
_ ERROR collecting projects/PROJ-033-predicting-material-properties-from-comp/tests/unit/test_graph_builder.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/tests/unit/test_graph_builder.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_graph_builder.py:17: in <module>
    from src.graphs.composition import build_composition_graph
src/graphs/composition.py:30: in <module>
    from pymatgen.core import Composition
E   ModuleNotFoundError: No module named 'pymatgen'
=========================== short test summary info ============================
ERROR tests/unit/test_graph_builder.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 2.97s


