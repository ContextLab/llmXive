# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011b` (rejected 1x): No script, command log, or list of downloaded FASTQ files is present; the implementer provided no artifact showing that they fetched run IDs for SRP053178 or actually downloaded the raw FASTQ data from NCBI SRA. Consequently the requirement to implement Strategy B is not satisfied.
- `T011c` (rejected 1x): The claim provides only the task description and project specifications; there is no Docker command, script, log, or generated OTU table presented. No evidence of running QIIME2/DADA2 with the required parameters or of producing a non‑empty OTU table is available, so the required artifact is missing.
- `T011d` (rejected 1x): No merged OTU‑serology dataset (e.g., a CSV file) or script implementing the merge by `subject_id` is present; the evidence consists only of the task description, so the required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

