# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010b` (rejected 1x): The `code/data_loader.py` file does not contain a function that actually loads the FP16 LoRA adapter and base model with `device_map='cpu'` and `torch_dtype=torch.float16`; it only defines download utilities. Moreover, the required `data/models/collection_lora.safetensors` file is absent. Both the implementation and the necessary model file are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

