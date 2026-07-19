# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/derived/resource_monitoring_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/derived/resource_monitoring_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/data_loader.py --download (rc=1); python code/data_loader.py --verify (rc=1); python code/main.py --config code/config.yaml (rc=1); 3 declared deliverable(s) absent: data/derived/regression_results.json; data/derived/sensitivity_analysis.csv; data/validation/human_annotations.csv

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=1
    download the dataset.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 223, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 202, in main
    librispeech_data = load_librispeech_subset(config)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 61, in load_librispeech_subset
    return fetch_and_verify_librispeech(config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 42, in fetch_and_verify_librispeech
    raise FileNotFoundError(f"LibriSpeech data directory not found at {data_dir}. Please download the dataset.")
FileNotFoundError: LibriSpeech data directory not found at /home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/data/raw/librispeech. Please download the dataset.
- python code/data_loader.py --verify -> rc=1
    download the dataset.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 223, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 202, in main
    librispeech_data = load_librispeech_subset(config)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 61, in load_librispeech_subset
    return fetch_and_verify_librispeech(config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 42, in fetch_and_verify_librispeech
    raise FileNotFoundError(f"LibriSpeech data directory not found at {data_dir}. Please download the dataset.")
FileNotFoundError: LibriSpeech data directory not found at /home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/data/raw/librispeech. Please download the dataset.
- python code/main.py --config code/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/main.py", line 20, in <module>
    from distortion_engine import DistortionEngine, generate_all_distortion_vectors
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/distortion_engine.py", line 4, in <module>
    from typing import List, DistortionConfig, Dict, Tuple, Optional, Any
ImportError: cannot import name 'DistortionConfig' from 'typing' (/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/typing.py)
- python code/analysis.py --validate-sss -> rc=1
    INFO:__main__:Loading sensitivity analysis data...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/analysis.py", line 275, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/analysis.py", line 239, in main
    sensitivity_data = load_sensitivity_analysis(config)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/analysis.py", line 45, in load_sensitivity_analysis
    sensitivity_path = Path(config['derived_path']) / 'sensitivity_analysis.csv'
                            ~~~~~~^^^^^^^^^^^^^^^^
KeyError: 'derived_path'

## Declared deliverables still missing

- data/derived/regression_results.json
- data/derived/sensitivity_analysis.csv
- data/validation/human_annotations.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/human_annotations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/human_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/human_annotations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `sensitivity_analysis.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[derived_path]`
- PRODUCER(s) to edit: `code/analysis.py`
- CONSUMER(s) that read it: `code/analysis.py`
  → Edit the producer so every required name [derived_path] is in `sensitivity_analysis.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
