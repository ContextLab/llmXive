---
action_items:
- id: 9e6550f6ae56
  severity: writing
  text: "Provide a top\u2011level README that documents the repository layout, required\
    \ Python/R environment (e.g., conda env.yml or requirements.txt), and step\u2011\
    by\u2011step instructions to reproduce the full minWM pipeline from data preparation\
    \ to inference."
- id: 4f6c155b9d5f
  severity: fatal
  text: "Add the actual training and inference scripts (e.g., data preprocessing,\
    \ camera\u2011control fine\u2011tuning, AR diffusion training, distillation, and\
    \ inference) to the repository; currently only LaTeX sources are present, making\
    \ reproducibility impossible."
- id: 6c70ef7ffb8f
  severity: writing
  text: 'Refactor the LaTeX preamble: the custom \textbf redefinition interferes with
    standard bold formatting and may break packages; replace it with a dedicated macro
    (e.g., \mybf) or remove it entirely.'
- id: c912f2419651
  severity: writing
  text: "Trim the massive macro block in math_commands.tex \u2013 many symbols (e.g.,\
    \ \\rva\u2026\\rvz, \\rmA\u2026\\rmZ) are never used in the paper, inflating the\
    \ source and risking name collisions. Keep only the symbols actually referenced."
- id: 683dfe7599ce
  severity: writing
  text: Introduce a build script (e.g., a Makefile or a simple bash script) that runs
    pdflatex/biber with the correct flags, ensuring the PDF can be regenerated automatically
    from the source.
- id: b89a2cfd7ca9
  severity: writing
  text: "Add unit\u2011style tests for any Python utilities (e.g., data loaders, camera\u2011\
    parameter injection functions) using pytest, and include them in CI to catch regressions."
- id: 42e3645e00fa
  severity: writing
  text: Provide explicit version pins for all external dependencies (e.g., PyTorch,
    transformers, diffusion libraries) in a requirements.txt or conda environment
    file to avoid hidden incompatibilities.
- id: 2477575f6ac0
  severity: writing
  text: Remove unused bibliography entries (e.g., classic ML textbooks) that are not
    cited in the manuscript; this reduces clutter and improves citation relevance.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:33:38.984546Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The submitted artifact consists almost entirely of LaTeX source files (`main.tex`, section inputs, figure includes, `preamble.tex`, and a very large `math_commands.tex`). While the LaTeX is reasonably modular—sections are split into separate `.tex` files and figures are kept in a dedicated folder—the overall code quality of the repository is insufficient for reproducible research.

**Readability & Modularity**  
The `preamble.tex` redefines the core `\textbf` command, which can break downstream packages and makes the source harder to understand for readers unfamiliar with the custom macro. A safer approach is to introduce a new macro (e.g., `\mybf`) rather than overwriting a fundamental LaTeX command. The `math_commands.tex` file defines hundreds of symbols (random vectors, matrices, tensors, etc.) most of which are never referenced in the manuscript. This bloat hampers readability and increases the risk of name collisions. Pruning unused definitions would make the source leaner and easier to maintain.

**Reproducibility & Dependency Hygiene**  
The repository lacks any code that implements the minWM pipeline described in the paper (data construction, camera‑control fine‑tuning, AR diffusion training, distillation, inference). Consequently, a reviewer cannot run the experiments from scratch. There is no `README`, no environment specification (`requirements.txt` or `environment.yml`), and no build script to compile the PDF automatically. Without these, the claim of an “open‑source, reproducible framework” is unsupported.

**Testing**  
No test suite is present. Any Python utilities that would accompany the pipeline (e.g., data loaders, camera‑parameter injection functions) should be covered by unit tests (e.g., using `pytest`) and integrated into continuous integration to catch regressions early.

**Documentation & Bibliography**  
The bibliography contains many classic machine‑learning textbook entries that are never cited in the text, adding unnecessary noise. Cleaning the `.bib` file to retain only cited works would improve clarity. Additionally, the manuscript does not provide explicit instructions on how to obtain the released checkpoints, scripts, or how to invoke the inference code, which are essential for reproducibility.

**Overall Assessment**  
From a code‑quality perspective, the current artifact is a collection of LaTeX files without the accompanying implementation code, build automation, or testing infrastructure required for a reproducible open‑source framework. Addressing the action items above—especially adding the missing pipeline scripts, a clear README, environment specifications, and a lightweight build system—will bring the repository in line with standard reproducibility expectations.
