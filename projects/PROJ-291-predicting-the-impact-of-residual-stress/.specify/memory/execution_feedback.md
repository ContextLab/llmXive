# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 command(s) failed: python -m src.ingest.ingest          # downloads (real) data, verifies checksum (rc=1); python -m src.preprocess.preprocess   # unit conversion, imputation, proxy calc, checksum propagation, contract validation (rc=1); python -m src.models.train --feature-set A   # process‑only (rc=1); 1 declared deliverable(s) absent: data/processed/unified_fatigue.csv

## Failing / missing run-book commands

- python -c "import hashlib, pandas as pd; df = pd.read_csv('data/raw/synthetic_fatigue.csv');  print('Checksum OK' if hashlib.sha256(df.to_csv(index=False).encode()).hexdigest() ==  open('state/projects/PROJ-291-predicting-the-impact-of-residual-stress.yaml').read().split('synthetic_fatigue_checksum: ')[1].strip() else 'Checksum MISMATCH')" -> rc=1
^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/synthetic_fatigue.csv'

- python -m src.ingest.ingest          # downloads (real) data, verifies checksum -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.ingest.ingest' (ModuleNotFoundError: No module named 'src')

- python -m src.preprocess.preprocess   # unit conversion, imputation, proxy calc, checksum propagation, contract validation -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.preprocess.preprocess' (ModuleNotFoundError: No module named 'src')

- python -m src.models.train --feature-set A   # process‑only -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src')

- python -m src.models.train --feature-set B   # process + measured stress (if any) -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src')

- python -m src.models.train --feature-set C   # process + material props -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src')

- python -m src.models.evaluate --compare A B   # paired t‑test (full set) + sensitivity on measured subset -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src')

- python -m src.models.evaluate --cross-material  # transfer learning evaluation -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src')

- python -m src.mediation.bootstrap_mediation --resamples 10000 -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/.venv/bin/python: Error while finding module specification for 'src.mediation.bootstrap_mediation' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q -> rc=1
y'
            else:
                return _repr(o)
    
            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))
    
            return text
    
    
        if (_one_shot and c_make_encoder is not None
                and self.indent is None):
            _iterencode = c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        else:
            _iterencode = _make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot)
>       return _iterencode(o, 0)
E       ValueError: Out of range float values are not JSON compliant

/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py:258: ValueError
=========================== short test summary info ============================
FAILED tests/test_ingest.py::test_run_ingest_creates_unified_csv - ValueError...
1 failed in 0.70s



## Declared deliverables still missing

- data/processed/unified_fatigue.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/unified_fatigue.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_fatigue.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
