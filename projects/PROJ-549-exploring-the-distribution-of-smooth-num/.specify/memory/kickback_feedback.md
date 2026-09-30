# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The `code/validate_sieve.py` file is present but its content is truncated and lacks a complete implementation (e.g., the `verify_primes_sample` function is unfinished and there is no entry‑point to execute the script). Moreover, the required input file `data/primes_1e9.csv` is missing, so the script cannot be run or produce the expected validation report. Both the script and the prime list artifact need to be completed and present for the task to be satisfied.
- `T023b` (rejected 1x): The implementer supplied only the task description and user stories but did not provide any actual artifact—such as the grid‑generation script, output files, or validation results—required to verify that the parameter grid was correctly enumerated and that smooth‑number densities were computed. Without these concrete files or evidence, the requirement cannot be confirmed. The next implementer must deliver the executable code and its resulting data (e.g., a CSV or JSON of density measurements) along with verification that the counts match known ground‑truth for at least one test case.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

