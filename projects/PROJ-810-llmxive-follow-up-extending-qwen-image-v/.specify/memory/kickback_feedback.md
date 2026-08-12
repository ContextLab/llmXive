# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): The `src/analysis/separability.py` script correctly implements the power‑analysis logic and would write the required fields, but the expected output file `data/results/power_analysis.json` is absent, so the deliverable is not present. The missing JSON file must be generated (e.g., by running the script) and contain `N_required`, `effect_size`, `power`, and `N_audit`.
- `T001` (rejected 1x): The provided `vae_loader.py` checks a different model (`Qwen/Qwen2-VL-2B-Instruct`) instead of `Qwen-Image-VAE-2.0`, and the required `data/results/model_availability.json` file is absent. Consequently the task’s core validation and deliverable are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

