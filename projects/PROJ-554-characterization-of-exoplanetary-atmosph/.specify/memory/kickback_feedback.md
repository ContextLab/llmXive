# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No code, configuration file, or documentation was presented showing that environment variables for API keys (if needed) and random seeds have been set up or handled. Without any artifact to inspect, we cannot confirm the requirement has been met. The implementer must provide the actual implementation (e.g., a `.env` template, a settings module, or script snippets) that demonstrates the environment variable handling and seed configuration.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/metadata.csv
- `T014` (rejected 1x): No code, configuration, or log output was provided to demonstrate that download progress logging and API response handling have been added. The required artifact (e.g., updated script/module with logging statements and/or sample log files) is missing, so the task is not satisfied.
- `T018c` (rejected 1x): No artifact defining the output schema (e.g., a JSON/YAML/CSV specification listing fields for log10 water mixing ratio, its standard deviation, and an upper‑limit flag) was provided. The claim lacks any concrete file or code that maps these values, so the requirement is not satisfied.
- `T019` (rejected 1x): No code, script, or documentation was presented that implements detection of low‑S/N spectra using SNR/Resolution metadata, nor any logic that produces censored upper‑limit values. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

