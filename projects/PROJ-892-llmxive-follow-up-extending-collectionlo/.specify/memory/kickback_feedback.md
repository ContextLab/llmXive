# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The repository lacks the required `config.yaml` file that should contain the fixed list of seeds and prompts, and the provided `code/generator.py` only defines a single `generate_reference_image` helper (truncated) without any implementation that reads a prompt list from `config.yaml` and generates images for each entry using the FP16 LoRA adapter. Both essential artifacts are missing or incomplete.
- `T011b` (rejected 1x): The `data/references/baseline_ref.png` file does not exist, and the provided `code/generator.py` is truncated before the image generation completes, so the function cannot actually produce and save the required reference image. The task’s core output is missing.
- `T013` (rejected 1x): The repository lacks the required `data/references/baseline_ref.png` file, and `code/metrics.py` does not contain a function that iterates over the generated FP16 images and the full set of FP16 reference images to compute LPIPS distances as specified (only a single‑image `compute_lpips_distance` is shown). These missing artifacts prevent the task from being fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

