# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006a` (rejected 1x): No `research/data_sources.md` file was presented, and there is no evidence that the implementer verified pycalphad open databases or listed NIST APT accession IDs for the four Fe‑based binary systems. The required markdown log is missing.
- `T006b` (rejected 1x): No actual artifact (e.g., the downloaded `TCFE.tdb` file, verification logs, or code that performs the fetch and validates the presence of all required ternary parameters) was provided. Without the file and the accompanying implementation that fails loudly on missing parameters, the task’s core requirement cannot be confirmed. The implementer must supply the fetched database file and the code/logs demonstrating the required error handling.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

