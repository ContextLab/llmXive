# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015b` (rejected 1x): The repository contains `code/data/generator.py`, but the required output file `data/raw/golden_fixture.json` is absent, and the provided snippet does not show a CLI entry point that writes the JSON to that path. The task’s core deliverable – a script that generates and saves the 10 scenario traces to `data/raw/golden_fixture.json` – is therefore not satisfied.
- `T015c` (rejected 1x): The required artifact `data/raw/golden_fixture.json` is absent; without the file the existence, non‑emptiness, label distribution, and checksum checks cannot be performed. The implementer must run `code/data/generator.py` to create the JSON file in the specified location.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

