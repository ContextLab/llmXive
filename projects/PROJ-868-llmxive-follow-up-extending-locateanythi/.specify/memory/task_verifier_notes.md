# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
- **T002** — Requested task execution failed; rerun successfully: code/data/preprocess.py exit=1
- **T003** — The `code/model/sparsity.py` file exists, but the unit test `tests/unit/test_sparsity.py` fails for the `window_size=1` case: the generated mask is not the identity matrix as required. The mask construction swaps row/column indices, causing the identity‑mask test to error. The implementation must be corrected so that `window_size=1` yields an exact diagonal (identity) mask and all tests pass.
- **T004** — The wrapper implementation (`code/model/locateany.py`) exists and meets the basic functional spec, but the required integration test `tests/unit/test_model_wrapper.py` is missing, so the verification step cannot be performed. Adding the test file (which runs a forward pass with `window_size=32` and asserts the presence of `prediction`, `latency_ms`, and `torch.get_num_threads() == 2`) is needed to complete the task.
- **T005** — Requested task execution failed; rerun successfully: src/cli/run_experiment.py exit=1
