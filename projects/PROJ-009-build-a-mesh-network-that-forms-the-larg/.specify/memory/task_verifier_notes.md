# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The task requires that `collect_and_write_metadata` produce real JSON files (`data/raw/physical_node_<ip>.json`) validated against the schema, and that the test suite generate these files. However:

1. **Missing schema file**: `contracts/physical-node.schema.yaml` does not exist at the project root. The `contract_validator.py` looks for schemas under `specs/001-build-a-mesh-network-that-forms-the-larg/contracts/`, but the evidence shows the schema file is at `contracts/physical-node.schema.yaml` (project root). The path resolution in `contract_validator.py` will fail to locate it.

2. **No gen
- **T014** — The task requires three categories of artifacts, and the evidence shows critical gaps:

1. **Test file missing**: `code/tests/unit/test_instrumentor.py` does not exist on disk (marked MISSING by the collector), yet the historical execution log shows test runs. The task explicitly requires this artifact to exist and pass `pytest code/tests/unit/test_instrumentor.py` with exit code 0. The execution log shows 2 test failures (test_parse_mpstat_output_basic and test_parse_sensors_output_basic), confirming the tests are broken and the file is not properly committed.

2. **Sample log fixtures missin
- **T003** — The task requires a fully functional scheduler module that passes unit tests and creates valid dropout events. However, the test suite fails catastrophically: 8 of 12 tests error during setup because the test fixtures create `PhysicalNode` objects with an incompatible API. The `PhysicalNode` model in `code/orchestrator/models.py` requires `node_id`, `hostname`, `username`, and `hardware_spec` fields (all mandatory), but the test fixtures attempt to construct nodes with only `ip`, `status`, and `ram_mb` parameters. This causes immediate `ValidationError` exceptions before any test logic execute
- **T016** — **Evidence checked:**

1. **Schema file exists and is correct**: `specs/001-build-a-mesh-network-that-forms-the-larg/contracts/task-chunk.schema.yaml` is present with all required fields (`task_id`, `estimated_ops`, `actual_duration`, `assigned_node_id`, `status`) and the correct enum values. ✓

2. **JSONL data file exists with valid records**: `data/raw/task_chunks/run_001.jsonl` contains 4 records, each with all required fields and valid status values ("completed"). Each line validates against the schema. ✓

3. **TaskChunkStore writer exists but is incomplete**: `code/orchestrator/task_chunk
- **T011** — Requested task execution failed; rerun successfully: code/orchestrator/cli.py exit=1
