# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No unit test code file or snippet was provided; the claim lacks any artifact showing a test (expected to fail) for the aromaticity index calculation on benzene (“c1ccccc1”). The required test code is missing.
- `T011` (rejected 1x): No unit test code file was supplied; the only evidence is a generic project specification unrelated to the requested test. The required artifact—a failing unit test that checks conjugation path length for butadiene versus butane—is missing.
- `T012` (rejected 1x): The implementer did not provide any unit‑test code or file containing the tests; the response only repeats the task description and specifications without any actual artifact. Consequently, the required test code (expected to fail) is missing.
- `T017` (rejected 1x): No code, configuration, or documentation implementing the required fallback logic (logging a warning and substituting topological proxies when quantum descriptors are missing) was provided. The evidence lacks any artifact demonstrating that this behavior exists, so the task is not satisfied.
- `T018` (rejected 1x): No code, tests, or documentation were provided showing that error handling for invalid SMILES strings or missing conductivity values was added. The claim cannot be verified because the required artifact (implementation changes or evidence thereof) is absent.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

