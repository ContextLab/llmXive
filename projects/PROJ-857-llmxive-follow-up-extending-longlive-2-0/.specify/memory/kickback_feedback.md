# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The required file `projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/requirements.txt` does not exist, even though a similarly named `code/requirements.txt` with the correct dependencies is present elsewhere. The task specifically demanded the file at the given project path, which is missing.
- `T003` (rejected 1x): No configuration files (e.g., pyproject.toml, .flake8, .isort.cfg, or pre‑commit hooks) or any other artifact showing that black, flake8, and isort have been set up is present. Without such files, the requirement to configure the linting/formatting tools is not satisfied. The implementer must add the appropriate configuration files and demonstrate they are active.
- `T004` (rejected 1x): No `config.py` file or its contents were provided; therefore the required constants for seeds, the three bit‑width values, and the path configurations are missing, so the task is not satisfied.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: data/loader.py
- `T005a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/downsampler.py
- `T007` (rejected 1x): No `simulation/quantization_emulator.py` file or any code implementing stochastic rounding is provided; without the file we cannot verify that the required core logic, bit‑width handling, or KL‑divergence validation exists. The implementer must add the actual Python module with the specified functionality.
- `T008` (rejected 1x): No `simulation/student_model.py` file or any code implementing the CPU‑only wrapper is present in the provided evidence; without the actual file we cannot confirm that a functional wrapper for the simplified diffusion model exists. The required artifact is missing.
- `T009` (rejected 1x): No `evaluation/clip_evaluator.py` file or its contents were provided; without the script we cannot confirm that a frozen CLIP‑ViT model is loaded without gradients or that it produces temporal coherence scores as required. The required artifact is missing.
- `T038` (rejected 1x): declared artifact(s) missing/empty/invalid: data/discontinuity_generator.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/downsampler.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

