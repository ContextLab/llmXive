# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-864-llmxive-follow-up-extending-improved-lar/state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/micro_corpus_train.jsonl, data/processed/micro_corpus_test.jsonl
- `T021` (rejected 1x): No `autoregressive.py` file (or any non‑empty implementation) was presented in the evidence, and there is no code content to verify that a causal LM model was implemented. The required artifact is missing, so the task is not satisfied.
- `T022` (rejected 1x): No `diffusion.py` file (or any code) was presented for the specified path, and there is no evidence that the required bidirectional MDM implementation with large‑scale parameters and matching embedding/heads exists. The task’s core artifact is missing.
- `T023` (rejected 1x): No `train_loop.py` file (or any code) is presented in the provided evidence, and there is no indication that an implementation using `torch.compile` on CPU exists in the specified directory. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

