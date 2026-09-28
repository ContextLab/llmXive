# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The repository lacks the required `data/raw/fao_land_use.csv` file, and the `download.py` script does not contain a concrete implementation that calls `fetch_fao_fra_data` with the exact indicator `AG.LND.FRST.ZS`, processes the early‑21st‑century years, uses chunked handling, or writes the resulting DataFrame to that CSV path. Consequently the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

