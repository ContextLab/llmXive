# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
- **T002** — Requested task execution failed; rerun successfully: code/data/preprocess.py exit=1
- **T003** — The provided `code/model/sparsity.py` defines `SparsityConfig` with a `mask(num_tokens)` method, but the tests expect a constructor accepting `num_patches` and a `get_mask()` method. Moreover, the mask logic does not produce a global mask for window sizes larger than the grid (e.g., `window_size=16` on a 16×16 grid) as required by the test cases. The API mismatch and incorrect masking behavior mean the task’s requirements are not satisfied.
- **T004** — The `code/model/locateany.py` file defines the wrapper, but the integration test cannot run: the test fails during import because the `torch` package is not installed, and the wrapper’s constructor signature (`__init__(self, model, sparsity_config)`) does not match the test’s usage (`LocateAnythingSparsityWrapper(sparsity_config=config)`). Consequently the required forward‑pass check and thread‑limit assertion are never exercised. The task needs a working environment with `torch` available and a wrapper API that matches the test expectations.
- **T005** — Requested task execution failed; rerun successfully: src/cli/run_experiment.py exit=1
