# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001g` (rejected 1x): No evidence was provided that a `code/simulation` directory exists in the repository; the response contains no listing, screenshot, or description confirming its creation or contents. The required artifact is missing, so the setup task is not satisfied.
- `T001h` (rejected 1x): The claim provides no evidence that a `code/generation` directory actually exists in the repository; no file list, screenshots, or other artifacts were supplied to confirm its creation. Without such proof, the required setup task cannot be verified as completed.
- `T001i` (rejected 1x): No evidence was provided that a `code/evaluation` directory exists in the repository; the implementer did not supply a directory listing, file manifest, or any content showing the folder was created. The required artifact is therefore missing.
- `T001j` (rejected 1x): No artifact showing the `code/analysis` directory was provided; without a listing, screenshot, or other proof of its existence, we cannot confirm the directory was actually created. The implementer must supply evidence (e.g., a directory tree dump) that the `code/analysis` folder now exists.
- `T001k` (rejected 1x): No evidence of a `code/utils` directory was provided; the claim cannot be verified because the artifact (the directory) is missing from the supplied information. The implementer must create the directory (and optionally add a placeholder file) and present proof that it exists.
- `T001l` (rejected 1x): No evidence was presented showing that a `tests/contract` directory exists in the repository (e.g., a directory listing, file paths, or contents). Without such proof, we cannot confirm the required setup step was performed. The implementer must add the `tests/contract` folder (with at least one file or placeholder) and provide evidence of its presence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

