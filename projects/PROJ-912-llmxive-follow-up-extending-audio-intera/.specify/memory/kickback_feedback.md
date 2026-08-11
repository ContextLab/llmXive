# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021a` (rejected 1x): The required `data/processed/class_config_subtle.yaml` file is missing, and the provided `subtle_cue_builder.py` is truncated before showing any logic that classifies classes or writes the YAML configuration. Without the YAML output, the task’s second requirement is not satisfied.
- `T014a` (rejected 1x): The `compress.py` file does not contain a knowledge‑distillation training loop, does not load a quantized student model, does not stream the required Parquet dataset, nor compute or save the KD loss curve. Additionally, the required data file `data/processed/subtle_cue_subset.parquet` is missing, and `config.py` is truncated and does not expose the expected `KD_ALPHA`/`KD_TEMP` constants. These missing/incorrect artifacts prevent the task from being fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

