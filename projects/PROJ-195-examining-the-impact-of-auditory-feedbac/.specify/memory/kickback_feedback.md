# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No Docker configuration file, script, or documentation for `fmriprep` memory and process limits is present in the provided evidence. The task required a concrete artifact (e.g., a Dockerfile, docker‑compose.yml, or command‑line options) that sets appropriate resource limits, but none was supplied.
- `T016` (rejected 1x): The submission provides no code, configuration, or `preprocessing.log` file showing that logging of preprocessing deviations was added. Without any artifact demonstrating the new logging behavior, the task requirement is not satisfied. The implementer must add the logging implementation and supply the resulting log (or code changes) as evidence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

