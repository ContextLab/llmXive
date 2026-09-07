# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directory `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/` is provided; the artifact list is empty, so we cannot confirm the project root was actually created. The implementer must supply a verification that the directory exists (e.g., a file listing or screenshot).
- `T001b` (rejected 1x): No evidence of the required directory `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/` being created is provided; the response only contains project specifications and no filesystem artifacts. The task’s core deliverable—a non‑empty code directory—is missing.
- `T001c` (rejected 1x): No evidence was provided that the required directory `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/` actually exists or contains any files; the implementer’s claim is unsubstantiated.
- `T001d` (rejected 1x): No evidence was provided that a `tests/` directory exists at the specified path, nor any contents within it. Without a visible directory or files, the requirement cannot be confirmed as satisfied.
- `T002a` (rejected 1x): The required file `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/requirements.txt` does not exist, so the specified dependencies are not provided at the correct location (the existing `code/requirements.txt` is in a different directory and also contains extra packages). The task is therefore not fulfilled.
- `T002b` (rejected 1x): No Python version‑check script was provided; there is no file or code snippet demonstrating a runnable script that verifies the interpreter is Python 3.11 or newer. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

