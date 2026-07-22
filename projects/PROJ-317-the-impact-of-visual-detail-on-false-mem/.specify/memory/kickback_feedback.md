# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The two required files exist, but the source template `docs/ethics/gdpr_consent_template.md` is missing, so the artifacts could not be created “using the template as the base.” Additionally, the consent form does not clearly contain a detailed “GDPR‑compliant Anonymization Workflow” clause as mandated. The next implementer must provide the missing template and regenerate the consent document from it, ensuring the full anonymization workflow clause is present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

