# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory structure under `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` was provided; the claim lacks any listing, screenshots, or file tree confirming that the implementation plan’s folders have been created. The task cannot be considered done until the actual directories are present and non‑empty.
- `T002` (rejected 1x): No evidence of any `__init__.py` files was presented for the directories under `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`. Without visible files, we cannot confirm that the required initialization modules were created. The implementer must add and show the `__init__.py` files in each new directory.
- `T003` (rejected 1x): The required file `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt` does not exist, so the task of initializing the project with the specified dependencies at that location is not fulfilled. The existing `code/requirements.txt` is irrelevant because it is in the wrong path. The missing file must be created (and contain at least the listed packages).
- `T006b` (rejected 1x): I inspected the path `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/specs/001-context-fidelity-scaling-tradeoff/contracts/` for the three required YAML schema files (Task Instance, Context Configuration, Execution Result) and found no such files present. The task therefore lacks the required entity schema artifacts.
- `T008b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results.csv
- `T012b` (rejected 1x): The `loader.py` file is only partially shown and does not contain any logic that filters instances by line count, writes a versioned Parquet file, or records a checksum in `state/`. Moreover, the expected output file `data/filtered_swe_bench_v1.parquet` is missing, and no checksum file is present. The required artifacts and functionality are therefore absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

