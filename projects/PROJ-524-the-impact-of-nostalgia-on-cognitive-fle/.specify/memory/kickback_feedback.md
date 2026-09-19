# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`data/raw/`, `data/processed/`, `data/results/`, `data/stimuli/`, `contracts/`, `code/`, `tests/`, `paper/`) actually exist; the claim alone is insufficient. The implementer must supply proof (e.g., a directory tree snapshot) that these directories have been created and are non‑empty.
- `T020b` (rejected 1x): No evidence of a file at `specs/001-nostalgia-cognitive-flexibility/data-model.md` is provided, nor any excerpt showing the required documentation of entities, relationships, and the optional `MMSE` field. The implementer must create and supply this markdown file with the specified content.
- `T020a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T020c` (rejected 1x): No `specs/001-nostalgia-cognitive-flexibility/quickstart.md` file was presented, nor any excerpt of its contents showing installation steps, dependency installation, and a “Hello World” ingestion example. Without the required markdown artifact, the task is not satisfied.
- `T012d` (rejected 1x): The required file `data/processed/cleaned_score_filtered.csv` is missing, so the presence and non‑null status of the `MMSE` column cannot be verified. Consequently the generated `mmse_flag.json` (which unconditionally reports `true`) is not based on any actual check, and no error log (`ERR_MMSE_MISSING`) is provided. The implementer must supply the CSV file and generate the flag (and optional error log) based on a real column inspection.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

