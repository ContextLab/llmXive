# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success`
  - script usage: `ingest.py [-h] [--output OUTPUT] [--input-csv INPUT_CSV] [--rows ROWS]`
  - argparse error: `ingest.py: error: unrecognized arguments: # downloads, checksums, merges, proxy calc; exits 0 on success`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: bash scripts/env_check.sh (rc=1); python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success (rc=2); python -m src.preprocess.preprocess   # unit conversion, imputation, contract validation (rc=1); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- bash scripts/env_check.sh -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: No module named src.env_check

- python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success -> rc=2

usage: ingest.py [-h] [--output OUTPUT] [--input-csv INPUT_CSV] [--rows ROWS]
ingest.py: error: unrecognized arguments: # downloads, checksums, merges, proxy calc; exits 0 on success

- python -m src.preprocess.preprocess   # unit conversion, imputation, contract validation -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.preprocess.preprocess' (ModuleNotFoundError: No module named 'src.preprocess')

- python -m src.models.train --feature-set A   # process‑only -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.train --feature-set B   # process + measured stress (balanced subset) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.train --feature-set C   # process + material props (+ proxy stress) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.evaluate --compare A B   # Wilcoxon signed‑rank test (≥10 % MAPE improvement required) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.evaluate --cross-material  # transfer learning ΔMAPE + permutation test -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src.models')

- python -m src.mediation.bootstrap_mediation --resamples 10000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.mediation.bootstrap_mediation' (ModuleNotFoundError: No module named 'src.mediation')

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
1 failed in 0.76s



## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/ingest.py` — NOT invoked by the run-book
    - `code/src/env_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
