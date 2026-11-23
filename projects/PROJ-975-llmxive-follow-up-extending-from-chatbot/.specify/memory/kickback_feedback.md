# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The generated `tasks.json` fails schema validation – the required `ground_truth_skills` field is missing (or empty) for tasks, causing `test_schema_compliance` to error. The task records therefore do not conform to `task.schema.yaml`. To complete the task, each task must include a non‑empty `ground_truth_skills` array (3‑5 skill IDs) that satisfies the schema, and the schema files must be present in the `contracts/` directory.
- `T004` (rejected 1x): The pytest run (`code/.tasks/T004.tests_contract_test_schemas.py.log`) exits with failures: `test_real_tasks_schema_compliance` (and also `test_real_skills_schema_compliance`) report “Additional properties are not allowed” (e.g., `edge_case`, `embedding_vector` in tasks). The `fix_tasks_schema.py` script runs without error but does not remove these extra fields, so the JSON files still violate the schemas. Consequently the test suite does not exit successfully, violating the task requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

