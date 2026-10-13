# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/01_data_ingestion.py exit=1
- **T014** — The test file, raw CSV, and schema all exist and their contents are mutually consistent (CSV has exactly `smiles,logP` columns matching the schema's required fields, and the test logic correctly validates columns, nulls, types, and n≥128). However, the task's verification criterion is that `pytest code/tests/test_dataset_schema.py` passes, and no execution evidence (pytest output, exit code, or run log) was supplied — the passing test is only claimed, not demonstrated. Provide a recorded pytest run showing all tests in the file pass to complete this task.
- **T002** — Requested task execution failed; rerun successfully: code/02_tda_computation.py exit=1
