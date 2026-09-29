# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings, `ls` output, or other evidence were provided to show that the required folders under `projects/PROJ-236-exploring-the-influence-of-network-topol/` (e.g., `code/utils`, `code/tests/unit`, `data/raw`, etc.) actually exist. Without such proof the verification condition cannot be satisfied.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`) or command‑line output logs are provided, and there is no evidence that `ruff --quiet` and `black --check` were run successfully on the `code/` directory. The required artifacts and verification results are missing.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T017` (rejected 1x): No CI script or related code was provided; the claim that a verification script exists that reads connectivity metrics and aborts the build when the overall success rate falls below 95% after retries cannot be confirmed. The required artifact is missing.
- `T018` (rejected 1x): The implementer supplied only a unrelated feature specification about network topology and heat transport, with no CI configuration, test results, or any evidence of a “Physical Stability Filter” pass‑rate check. Consequently, the required artifact (CI check ensuring >5 % seed rejection causes failure) is missing.
- `T019` (rejected 1x): The implementer provided only a textual description of the intended verification and did not supply any actual artifact (e.g., CI configuration, unit‑test code, or test output) demonstrating that a CI assertion fails when the distance‑cutoff scaling is incorrect. Without concrete code or results, the requirement for a verifiable CI‑based check is not met.
- `T020` (rejected 1x): The claim provides no actual artifact—no test script, checksum‑recomputation code, or `data/` directory contents are presented. Without concrete files or code that loops over saved artifacts and validates their checksums, the verification task is not satisfied. The implementer must supply the automated test implementation and the relevant data files.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

