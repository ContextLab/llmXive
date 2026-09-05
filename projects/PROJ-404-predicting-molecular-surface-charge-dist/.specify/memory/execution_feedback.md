# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data/loader.py --sample-size 50000 --seed 42 (rc=1); python code/data/loader.py --validate (rc=1); python code/train.py --epochs 100 --early-stopping-patience 10 --batch-size 32 (rc=1)

## Failing / missing run-book commands

- python code/data/loader.py --sample-size 50000 --seed 42 -> rc=1
    port Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?
- python code/data/loader.py --validate -> rc=1
    port Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?
- python code/train.py --epochs 100 --early-stopping-patience 10 --batch-size 32 -> rc=1
    port Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?
- python code/eval.py --model-path artifacts/models/schnet.pt --baseline -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/eval.py", line 14, in <module>
    from utils import get_logger, set_seed
ImportError: cannot import name 'get_logger' from 'utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/utils/__init__.py)
