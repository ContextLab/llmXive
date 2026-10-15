# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T102` (rejected 1x): The unit‑test suite shows that the embedding‑based branch of `link_dataframe` does not behave as required: `test_embedding_path_when_available` fails, returning the wrong `entity_node_id`. Consequently the function does not correctly implement the configurable embedding‑similarity path, and the task’s verification condition (all pytest tests passing) is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

