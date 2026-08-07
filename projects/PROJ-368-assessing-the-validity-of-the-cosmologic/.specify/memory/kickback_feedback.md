# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No updated `spec.md` file was provided, nor any diff or excerpt showing that the phrase “Benjamini-Hochberg correction” was replaced with “Maximum Statistic approach (max of N/S and E/W asymmetries)”. Without this concrete artifact, we cannot confirm the required change was made. The implementer must supply the modified `spec.md` (or a clear before‑after snippet) demonstrating the replacement.
- `T002` (rejected 1x): No updated `spec.md` file is provided or shown; without the actual document we cannot verify that the phrase “Benjamini-Hochberg correction applied” was replaced with “Maximum Statistic approach applied”. The required artifact is missing.
- `T003` (rejected 1x): No actual `spec.md` file or its contents were provided, so we cannot verify that the acceptance scenario text was changed from “Benjamini‑Hochberg” to “Maximum Statistic.” The required artifact is missing.
- `T004` (rejected 1x): No directory listings or screenshots were provided to show that the `code`, `tests`, `data/raw`, `data/processed`, `data/simulations`, `data/reports`, and `docs` folders actually exist; without concrete evidence the claim cannot be verified. The implementer must supply proof (e.g., a directory tree output) that these directories were created.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

