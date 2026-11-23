# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.code.ingest (rc=1); python -m src.code.embeddings (rc=1); python -m src.code.similarity (rc=1); 3 declared deliverable(s) absent: data/derived/flagged_low_coverage_years.json; data/derived/partial_metadata_mpd.parquet; data/derived/temp_embeddings.npz

## Failing / missing run-book commands

- python -m src.code.ingest -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/src/code/ingest.py", line 13, in <module>
    from musicbrainzngs import musicbrainzngs as mb
ImportError: cannot import name 'musicbrainzngs' from 'musicbrainzngs' (/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/musicbrainzngs/__init__.py)

- python -m src.code.embeddings -> rc=1
2026-10-09 16:24:31 - root - INFO - Starting Word2Vec training...
2026-10-09 16:24:31 - root - INFO - Parameters: dimensions=100, window=10, epochs=5
2026-10-09 16:24:31 - root - ERROR - Error during training: Using a generator as corpus_iterable can't support 6 passes. Try a re-iterable sequence.
2026-10-09 16:24:31 - root - ERROR - Failed to train model


- python -m src.code.similarity -> rc=1
2026-10-09 16:24:31 - root - INFO - Starting similarity computation...
2026-10-09 16:24:31 - root - ERROR - Embeddings directory not found: yearly_embeddings


- python -m src.code.run_all -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/code/.venv/bin/python: No module named src.code.run_all

- python -m pytest tests/contract/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/code/.venv/bin/python: No module named pytest

- python -m pytest tests/unit/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/derived/flagged_low_coverage_years.json
- data/derived/partial_metadata_mpd.parquet
- data/derived/temp_embeddings.npz

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/flagged_low_coverage_years.json` is declared but was NOT written. Scripts referencing it:
    - `code/embeddings.py` — NOT invoked by the run-book
    - `src/code/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/flagged_low_coverage_years.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/partial_metadata_mpd.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/partial_metadata_mpd.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/temp_embeddings.npz` is declared but was NOT written. Scripts referencing it:
    - `code/embeddings.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/temp_embeddings.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
