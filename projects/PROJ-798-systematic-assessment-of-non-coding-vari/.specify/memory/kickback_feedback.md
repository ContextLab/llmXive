# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The required `.gitignore` file at the repository (project) root is not present in the collected evidence at all — no artifact entry exists for it. Without the file, the required exclusion patterns cannot be verified, and the `git check-ignore` verification commands (exit 0 for `data/raw/snps_raw.vcf.gz`, exit 1 for `data/raw/source_log.txt`) cannot pass; the implementer must create `.gitignore` with the exact five specified patterns.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

