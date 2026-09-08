# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T041` (rejected 1x): The provided `src/services/ingest.py` does not show any use of a `pyalex` streaming iterator with `chunk_size=1000`, nor does it write incremental batches to `data/raw/openalex_stream.parquet`. Moreover, the required parquet file is absent from the repository. Consequently, the task’s core requirement—stream‑based processing and chunked parquet output—is not satisfied.
- `T012a` (rejected 1x): The repository contains `src/services/ingest.py`, but the file does not define the required `sample_subgraph(G, target_size)` function (the visible code only shows `fetch_sample_ids` and is truncated). Additionally, the required unit test `tests/unit/test_ingest.py::test_sample_subgraph_preserves_degree_distribution` is absent. Both the implementation and the verification test are missing.
- `T012b` (rejected 1x): The repository lacks the required `artifacts/results/sampling_validation.json` file, and the provided excerpt of `src/services/ingest.py` shows no implementation of `validate_sampled_graph` (the function is absent from the visible code and cannot be confirmed elsewhere). Both the function and the JSON report are missing, so the task is not satisfied.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/subgraph_with_clusters.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

