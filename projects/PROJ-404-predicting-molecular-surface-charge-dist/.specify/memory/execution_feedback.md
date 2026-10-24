# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/data/loader.py --sample-size 50000 --seed 42 (rc=1); python code/data/loader.py --validate (rc=1); python code/train.py --epochs 100 --early-stopping-patience 10 --batch-size 32 (rc=1)

## Failing / missing run-book commands

- python code/data/loader.py --sample-size 50000 --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py", line 18, in <module>
    from data.dataset import MoleculeData
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/__init__.py", line 2, in <module>
    from .loader import create_streaming_loader, validate_data_integrity
ImportError: cannot import name 'validate_data_integrity' from 'data.loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py)

- python code/data/loader.py --validate -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py", line 18, in <module>
    from data.dataset import MoleculeData
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/__init__.py", line 2, in <module>
    from .loader import create_streaming_loader, validate_data_integrity
ImportError: cannot import name 'validate_data_integrity' from 'data.loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py)

- python code/train.py --epochs 100 --early-stopping-patience 10 --batch-size 32 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/train.py", line 17, in <module>
    from models.schnet import SchNet, create_schnet_model
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/models/__init__.py", line 3, in <module>
    from .baseline_atom import AtomTypeAverageBaseline, create_atom_baseline_model
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/models/baseline_atom.py", line 7, in <module>
    from data.dataset import MoleculeData
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/__init__.py", line 2, in <module>
    from .loader import create_streaming_loader, validate_data_integrity
ImportError: cannot import name 'validate_data_integrity' from 'data.loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py)

- python code/eval.py --model-path artifacts/models/schnet.pt --baseline -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/eval.py", line 24, in <module>
    from data.dataset import MoleculeData
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/__init__.py", line 2, in <module>
    from .loader import create_streaming_loader, validate_data_integrity
ImportError: cannot import name 'validate_data_integrity' from 'data.loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py)

- python -m pytest tests/ -v -> rc=2
404-predicting-molecular-surface-charge-dist/code/eval.py)
_ ERROR collecting projects/PROJ-404-predicting-molecular-surface-charge-dist/tests/test_model.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/tests/test_model.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_model.py:9: in <module>
    from models.schnet import SchNet, build_schnet_model
E   ImportError: cannot import name 'build_schnet_model' from 'models.schnet' (/home/runner/work/llmXive/llmXive/projects/PROJ-404-predicting-molecular-surface-charge-dist/code/models/schnet.py)
=========================== short test summary info ============================
ERROR tests/test_baseline_2d.py
ERROR tests/test_checksum.py
ERROR tests/test_eval.py
ERROR tests/test_model.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 1.95s ===============================


