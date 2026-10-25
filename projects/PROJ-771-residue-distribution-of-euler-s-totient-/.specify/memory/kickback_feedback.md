# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): The provided `code/stats.py` defines `calculate_chi_squared_statistic` and a `run_chi_squared_test` that returns a dict matching the required schema, but it lacks a public `exact_multinomial_test` function and does not expose a `method="monte_carlo"` option. Moreover, the repository’s `tests/unit/test_stats.py` does not contain the three chi‑squared sub‑tests described in the task specification, so the required verification is missing. The next implementer must add the missing test cases (uniform, biased, and small‑N exact cases) and ensure the API supports the exact‑multinomial fallback and o

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

