# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009a` (rejected 1x): The required adapter file `data/models/adapter_fp16.safetensors` is absent, and the provided `code/data_loader.py` is truncated and does not contain the specified logic for extracting LoRA subspace rank, regex grouping, SVD computation, and buffering of rank data. Both essential artifacts are missing or incomplete.
- `T016` (rejected 1x): The provided `code/data_loader.py` does not contain any function that performs zero‑shot post‑training quantization of LoRA adapters, nor does it save `adapter_int8.safetensors` or `adapter_int4.safetensors`. Both expected output files are absent from `data/quantized/`. Consequently, the required functionality and artifacts are missing.
- `T010b` (rejected 1x): The required `data/models/adapter_fp16.safetensors` file is absent, so the loader cannot actually load the verified FP16 adapter. Moreover, the provided `code/data_loader.py` is truncated and does not contain a complete function that loads both the adapter and the base model into CPU memory. Both the artifact and the implementation are missing/incomplete.
- `T014` (rejected 1x): The provided `code/main.py` is incomplete (truncated mid‑function, missing the rest of the logic for processing images, computing metrics, and saving results). Additionally, the required `data/results.csv` file does not exist. Both the script and the results CSV are essential for the task, so the implementation is not finished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

