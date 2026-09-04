# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The `code/preprocess.py` file is truncated and does not contain a full implementation of the two‑pass streaming Markov surprisal calculation (the function ends mid‑docstring and no transition counting or entropy computation is shown). Moreover, the required input file `data/processed/streamed_temp.csv` is absent, so the streaming step cannot be performed. The task therefore remains unfinished.
- `T017b` (rejected 1x): No evidence of `data/processed/transition_probs.json` or `data/processed/markov_state.json` (or any equivalent files) was provided; thus the required versioned artifacts are missing. The task is not satisfied.
- `T023` (rejected 1x): No code implementing Bonferroni or Benjamini‑Hochberg correction, no conditional logic checking `num_tests > 1`, and no `analysis/results.json` containing an `adjusted_pvalues` list are present in the provided artifacts. The required files and functionality are missing.
- `T024` (rejected 1x): No code, script, notebook, or output file implementing Cohen's d with a 95 % confidence interval using the `pingouin` library is present; the claim lacks any tangible artifact to verify the required functionality. The implementer must provide the actual implementation (e.g., a Python function or analysis script) and its output demonstrating the calculation.
- `T025` (rejected 1x): No code, script, notebook, or output implementing a sensitivity analysis that computes the Minimum Detectable Effect for power = 0.80 is provided, nor is there any logic that checks “observed effect < MDE” and reports it as a limitation. The required artifact is missing.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/standardized.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

