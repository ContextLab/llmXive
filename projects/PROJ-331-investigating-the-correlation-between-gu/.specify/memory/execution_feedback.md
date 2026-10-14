# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.pipeline.ingest (rc=1); python -m src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m src.pipeline.run_permutation --iterations 1000 --seed 42 (rc=1); 5 declared deliverable(s) absent: data/processed/clr_abundances.parquet; data/processed/filtered_samples.parquet; data/processed/patient_outcome_slopes.parquet

## Failing / missing run-book commands

- python -m src.pipeline.ingest -> rc=1

2026-10-14 11:15:12,994 INFO __main__: === PPMI input validation (FR-001) ===
2026-10-14 11:15:12,995 INFO __main__: ASV table not found at PPMI name; using alternate open‑dataset name: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv
2026-10-14 11:15:12,995 ERROR __main__: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_clinical.parquet nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_clinical.parquet exist. Place the researcher‑supplied clinical metadata at one of these locations.
2026-10-14 11:15:12,995 ERROR __main__: Input validation FAILED: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_clinical.parquet nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_clinical.parquet exist. Place the researcher‑supplied clinical metadata at one of these locations.

- python -m src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 -> rc=1

2026-10-14 11:15:13,139 ERROR __main__: Required input files not found. Expected either:
  /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv
  /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_clinical.parquet
or:
  /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv
  /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_clinical.parquet

- python -m src.pipeline.run_permutation --iterations 1000 --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-331-investigating-the-correlation-between-gu/bin/python: No module named src.pipeline.run_permutation

- python -m pytest -q src/tests -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: src/tests



## Declared deliverables still missing

- data/processed/clr_abundances.parquet
- data/processed/filtered_samples.parquet
- data/processed/patient_outcome_slopes.parquet
- data/processed/patient_taxon_slopes.parquet
- data/raw/open_clinical.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clr_abundances.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/__main__.py` — NOT invoked by the run-book
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_preprocess_default.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clr_abundances.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_preprocess_default.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_correlation_adj.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess_default_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_outcome_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_outcome_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_taxon_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_taxon_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/open_clinical.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/__main__.py` — NOT invoked by the run-book
    - `code/src/pipeline/ingest.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/tests/test_correlation_adj.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/open_clinical.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
