# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.code.ingest (rc=1); python -m src.code.embeddings (rc=1); python -m src.code.similarity (rc=1)

## Failing / missing run-book commands

- python -m src.code.ingest -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/src/code/ingest.py", line 13, in <module>
    from musicbrainzngs import musicbrainzngs as mb
ImportError: cannot import name 'musicbrainzngs' from 'musicbrainzngs' (/home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/musicbrainzngs/__init__.py)
- python -m src.code.embeddings -> rc=1
    2026-07-21 02:04:14 - root - INFO - Starting Word2Vec training...
2026-07-21 02:04:14 - root - INFO - Parameters: dimensions=100, window=10, epochs=5
2026-07-21 02:04:14 - root - ERROR - Error during training: Using a generator as corpus_iterable can't support 6 passes. Try a re-iterable sequence.
2026-07-21 02:04:14 - root - ERROR - Failed to train model
- python -m src.code.similarity -> rc=1
    2026-07-21 02:04:14 - root - INFO - Starting similarity computation...
2026-07-21 02:04:14 - root - ERROR - Embeddings directory not found: yearly_embeddings
- python -m src.code.run_all -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-254-statistical-analysis-of-publicly-availab/code/.venv/bin/python: No module named src.code.run_all
