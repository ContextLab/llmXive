# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T090` (rejected 1x): No updated `research.md` file (or excerpt of Section 4.1) was supplied; thus we cannot confirm that the measurement apparatus definition (argmax over the Born‑rule distribution and observable as the binary ambiguity label) was actually added. The required documentation artifact is missing.
- `T091` (rejected 1x): No `research.md` file or its contents were provided, so we cannot verify that Section 4.2 was updated with the required sentence about locality. The implementer must supply the updated `research.md` showing the new text.
- `T092` (rejected 1x): No updated `research.md` file (or excerpt thereof) was provided, so we cannot verify that Section 4.3 now distinguishes epistemic uncertainty from ontological superposition and frames the model’s superposition as a computational representation of epistemic uncertainty. The required documentation artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

