# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T070` (rejected 1x): No evidence was provided that `specs/001-evaluating-the-impact-of-llm-generated-c/research.md` exists, contains the three required sections, or that its SHA256 hash was written to `state/research_protocol.sha256`. The implementer must add the appendix with the specified content and store its hash as proof.
- `T073b` (rejected 1x): The repository contains `code/recruitment/tracker.py` and a populated `data/raw/participants_raw.json`, but the required schema file `contracts/participant.schema.yaml` is missing, so the schema cannot be verified. Moreover, the JSON file’s structure (a plain list) does not match the tracker’s expected schema (metadata + participants array), violating the “matches contracts/participant.schema.yaml” requirement. The task therefore remains incomplete.
- `T001a` (rejected 1x): declared artifact(s) missing/empty/invalid: state/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c.yaml
- `T010b` (rejected 1x): No `state/run_metadata.json` file or its contents were provided; thus we cannot confirm the file exists, contains valid JSON, or includes a `RUN_ID` UUID as required. The implementer must supply the actual file with the specified fields.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

