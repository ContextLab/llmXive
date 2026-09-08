# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python -m pytest tests/unit/test_data_source.py -v (rc=1); python code/tests/integration/test_ingest_pipeline.py (rc=1); python code/tests/integration/test_embeddings_pipeline.py (rc=1); 2 declared deliverable(s) absent: data/processed/final_analysis_dataset.parquet; data/processed/subgraph_with_clusters.parquet

## Failing / missing run-book commands

- python -m pytest tests/unit/test_data_source.py -v -> rc=1
    ng handling of the above exception, another exception occurred:

    def test_pyalex_basic_query():
        """
        Verify that pyalex can perform a basic search query (e.g., count of works).
    
        This tests the API's ability to handle query parameters, not just ID lookups.
        """
        try:
            # Query for a very common term to ensure a result exists
            # We use a small sample to keep it fast
            result = Works().filter(openalex="W2741809807").sample(1)
    
            assert len(result) == 1, "Sample query did not return exactly 1 result"
            assert result[0]["id"].endswith(SAMPLE_WORK_ID), "Sampled work ID mismatch"
    
        except Exception as e:
>           pytest.fail(f"pyalex basic query failed: {e}")
E           Failed: pyalex basic query failed: object of type 'Works' has no len()

tests/unit/test_data_source.py:74: Failed
=========================== short test summary info ============================
FAILED tests/unit/test_data_source.py::test_pyalex_basic_query - Failed: pyalex basic query failed: object of type 'Works' has no len()
========================= 1 failed, 2 passed in 0.83s ==========================
- python code/tests/integration/test_ingest_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/tests/integration/test_ingest_pipeline.py", line 7, in <module>
    from src.services.ingest import fetch_sample_ids, fetch_and_build_subgraph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/src/services/ingest.py", line 11, in <module>
    from src.lib import config
ImportError: cannot import name 'config' from 'src.lib' (unknown location)
- python code/tests/integration/test_embeddings_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/tests/integration/test_embeddings_pipeline.py", line 14, in <module>
    from src.services.embeddings import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/src/services/embeddings.py", line 10, in <module>
    from src.lib.config import get_config, get_path
ModuleNotFoundError: No module named 'src.lib.config'
- python code/scripts/save_final_dataset.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/scripts/save_final_dataset.py", line 22, in <module>
    from src.lib import config
ImportError: cannot import name 'config' from 'src.lib' (unknown location)
- python code/scripts/save_statistical_metrics.py --correction-method bh -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/scripts/save_statistical_metrics.py", line 13, in <module>
    from src.lib.config import get_artifacts_path
ModuleNotFoundError: No module named 'src.lib.config'
- python code/scripts/generate_analysis_report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/scripts/generate_analysis_report.py", line 7, in <module>
    from src.lib import config
ImportError: cannot import name 'config' from 'src.lib' (unknown location)
- python code/scripts/run_validation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/scripts/run_validation.py", line 23, in <module>
    from src.lib import config
ImportError: cannot import name 'config' from 'src.lib' (unknown location)

## Declared deliverables still missing

- data/processed/final_analysis_dataset.parquet
- data/processed/subgraph_with_clusters.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_analysis_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/save_final_dataset.py` — IS a run-book command
    - `code/scripts/run_validation.py` — IS a run-book command
    - `code/scripts/save_statistical_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/subgraph_with_clusters.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_save_graph.py` — NOT invoked by the run-book
    - `code/scripts/save_final_dataset.py` — IS a run-book command
    - `code/scripts/run_validation.py` — IS a run-book command
    - `code/src/services/save_graph.py` — NOT invoked by the run-book
    - `code/src/services/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/subgraph_with_clusters.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
