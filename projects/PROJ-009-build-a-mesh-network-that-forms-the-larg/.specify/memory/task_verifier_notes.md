# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/orchestrator/cli.py exit=1
- **T002** — The required `data/raw/physical_node_*.json` files do not exist, and `collect_and_write_metadata` cannot produce them: it calls `validate_schema(metadata, "physical-node")`, but `contract_validator.py` only defines "ExecutionRun" and "RegressionModel" schemas, so it would raise `ValueError: Unknown schema: physical-node` — the schema file `contracts/physical-node.schema.yaml` is an empty stub (`properties: {}`) that is never actually loaded. Additionally, the test suite covers only discovery and the factory; it contains no tests for tool-presence checks, CPU profiling, radio metrics, thermal r
- **T003** — Requested task execution failed; rerun successfully: code/orchestrator/cli.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/orchestrator/cli.py exit=1
