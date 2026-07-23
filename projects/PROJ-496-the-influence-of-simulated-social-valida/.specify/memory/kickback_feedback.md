# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `projects/PROJ-496-the-influence-of-simulated-social-valida/code/` directory (or any files within it) was provided; the implementer did not supply the requested directory structure.
- `T001b` (rejected 1x): No directory listing or proof that `projects/PROJ-496-the-influence-of-simulated-social-valida/data/` was created is provided; the claim lacks any tangible artifact confirming the required folder structure exists.
- `T001c` (rejected 1x): No evidence of the required `projects/PROJ-496-the-influence-of-simulated-social-valida/tests/` directory (or any files within it) is provided; the claim is unsupported by any artifact listing or content. The implementer must create and show the actual directory structure.
- `T001d` (rejected 1x): No evidence of the required `projects/PROJ-496-the-influence-of-simulated-social-valida/docs/` directory (or any files within it) was provided; the claim lacks any artifact to verify that the directory structure was actually created.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/lint.yml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T004` (rejected 1x): No directory structure or `.gitkeep` files are presented in the provided evidence; without visible `data/raw`, `data/processed`, and `data/results` folders (each containing a `.gitkeep`), the requirement cannot be confirmed as satisfied. The implementer must add the actual directory tree and placeholder files as proof.
- `T014` (rejected 1x): No code, script, or in‑memory data structures were provided that implement the required categorization logic or produce the six named lists. Without such artifacts we cannot confirm that the “Eligible”, “Sim‑Only”, “Real‑Only”, “Partial‑EEG”, “Partial‑Anxiety”, and “None” categories are actually generated. The implementer must supply the implementation (e.g., a Python module or notebook) and evidence (e.g., printed lists or unit‑test output) showing the categories populated as specified.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/negative_finding_report_v1.pdf

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

