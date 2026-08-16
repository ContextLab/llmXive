# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required output file `data/processed/micro_corpus_full.jsonl` does not exist, and there is no evidence that `tokenize_and_stream.py` was created or executed to produce it. Without the generated JSONL corpus (or the script that creates it), the task’s core requirement is unmet.
- `T024` (rejected 1x): No `callbacks.py` file (or its contents) was presented for the path `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/training/`, and therefore there is no evidence that epoch, train_loss, val_loss, gap, time, and RAM are being logged as required. The implementer must supply a non‑empty `callbacks.py` implementing the specified logging.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

