---
action_items:
- id: 3543fa53122d
  severity: writing
  text: Refactor the LaTeX source into modular files (e.g., separate sections, macros,
    bibliography) and include a build script (e.g., Makefile or latexmk) to ensure
    reproducible compilation.
- id: 46a4204299b2
  severity: writing
  text: "Provide a public code repository containing the actual implementation of\
    \ the Manifold Power\u2011Iteration router (Python/PyTorch), with a clear `requirements.txt`\
    \ or `environment.yml` specifying all dependencies."
- id: 63659f62d267
  severity: writing
  text: "Add unit tests for the core router logic (power iteration step, L2 retraction,\
    \ scaling constant C) and integration tests that verify the model can be trained\
    \ end\u2011to\u2011end on a small synthetic MoE toy problem."
- id: 04fed478bf80
  severity: writing
  text: "Fix typographical errors in the provided pseudo\u2011code (e.g., rename `foward`\
    \ to `forward`, ensure the variable `wg` is defined or passed, and close the parentheses\
    \ on the `R_hat` line)."
- id: 34faa9734080
  severity: writing
  text: Include a reproducibility checklist in the appendix that details random seed
    settings, hardware configuration, and exact hyperparameter values used for each
    experiment, referencing the files in `apx:details`.
- id: cbb784f858ea
  severity: writing
  text: Document the version of the underlying libraries (e.g., PyTorch, MegaBlocks,
    TorchTitan, FSDP) used in the experiments to avoid hidden dependency drift.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:39:31.539629Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The submission consists solely of LaTeX source files (`acl_latex.tex`, `main-llmxive.tex`, `math_commands.tex`) and a bibliography. From a **code‑quality** perspective, the artifacts that underpin the experimental claims are **absent** from the repository, making it impossible for a reviewer (or future researcher) to verify the implementation or reproduce the results.

### Readability & Modularity
- The LaTeX is a single monolithic document (`main-llmxive.tex`) that embeds all sections, figures, and tables. While this is common for short papers, the lack of modularity (e.g., separate `.sty` files for macros, distinct `.tex` files per section) hampers readability and maintenance.
- Custom macros (`\bluebg`, `\pinkbg`, `\name`, `\Name`) are defined both in the original preamble and re‑declared in the shim layer, leading to duplication and potential inconsistencies.

### Dependency Hygiene
- No `requirements.txt`, `environment.yml`, or Dockerfile is provided. The paper mentions several heavy‑weight dependencies (TorchTitan, MegaBlocks, FSDP, Muon optimizer, Hyperball) but does not specify versions. This omission makes it unclear whether the code would run on a fresh environment.

### Reproducibility
- The experimental sections refer to extensive pre‑training runs (up to 11 B parameters, 350 B tokens) but the actual training scripts, data pipelines, and checkpoint loading logic are missing.
- The pseudo‑code in Figure 1 is incomplete and contains obvious bugs (`def foward`, undefined `wg`, missing closing parenthesis). Without a concrete implementation, the “Power‑then‑Retract” algorithm cannot be validated.
- Hyperparameters are listed in tables (e.g., Table 7), but there is no central configuration file that can be consumed by a training script. Random seed settings, hardware topology, and exact data preprocessing steps are not documented.

### Testing
- No test suite is provided. For a method that introduces a non‑trivial update rule on router weights, unit tests (checking that a single power‑iteration step preserves the L2 norm after retraction, that the scaling constant `C` behaves as `Θ(1/√N)`) are essential.
- Integration tests that train a minimal MoE model (e.g., 2 experts, 1 k tokens) and verify loss reduction would give confidence that the method is correctly wired.

### Recommendations
1. **Create a public code repository** (e.g., GitHub) that contains:
   - The full implementation of `MoE_MPI` (extending MegaBlocks’ `MoE`), with clear docstrings.
   - A `requirements.txt` pinning versions of PyTorch, MegaBlocks, TorchTitan, etc.
   - A `README.md` with step‑by‑step instructions to reproduce the 1 B and 3 B experiments on a single GPU (or a minimal multi‑GPU setup).
2. **Add a test suite** under `tests/` that covers:
   - Correctness of the power‑iteration update.
   - Stability of the L2 retraction across many steps.
   - Compatibility with different activation functions (`softmax`, `sigmoid`).
3. **Modularize the LaTeX**:
   - Split each major section into its own `.tex` file and include them via `\input{}`.
   - Move all custom macros to a dedicated `macros.sty`.
   - Provide a `Makefile` or `latexmkrc` to compile the PDF reproducibly.
4. **Document the experimental environment**:
   - Include GPU model, driver/CUDA version, and the exact commit hash of the code used for each table.
   - Provide a reproducibility checklist (random seeds, number of training steps, token counts, checkpoint saving frequency).
5. **Fix the pseudo‑code**:
   - Rename `foward` → `forward`.
   - Ensure `wg` (the expert weight tensor) is passed as an argument or obtained from the MoE module.
   - Close the parentheses on the `R_hat` line and add proper comments explaining each operation.

Addressing these issues will dramatically improve the paper’s **reproducibility** and **usability** for the community, turning the promising theoretical contribution into a verifiable, reusable artifact.
