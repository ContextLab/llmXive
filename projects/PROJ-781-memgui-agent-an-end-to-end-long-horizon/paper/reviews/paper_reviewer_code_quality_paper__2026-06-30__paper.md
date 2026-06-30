---
action_items:
- id: 8f33ca82ba42
  severity: science
  text: The paper claims to release code and models (GitHub/HuggingFace links in e002)
    but provides no repository structure, dependency list (requirements.txt/pyproject.toml),
    or Dockerfile. Without a 'reproducibility from scratch' guide, the code quality
    cannot be verified. Add a 'Reproducibility' section or appendix detailing the
    environment setup and entry points.
- id: 03a0035db031
  severity: science
  text: The training setup (e002, Sec. Appendix-Train) specifies 'AdamW fused' and
    'bfloat16' on 8x80GB GPUs. The code artifacts (implied by the GitHub link) must
    explicitly document the specific deep learning framework version (e.g., PyTorch
    2.x) and CUDA version to ensure the 'fused' optimizer and precision modes are
    supported. Missing this causes reproducibility failure.
- id: d4dc1c3c04f2
  severity: science
  text: The dataset construction pipeline (e002, Fig. Data-Pipeline) involves 'MemGUI-Eval
    filtering' and 'Teacher Rollouts'. The code quality review requires the evaluation
    scripts and filtering logic to be modular and testable. The current text describes
    the process but does not reference specific script paths or test suites for the
    data pipeline, making it impossible to verify the '2,956 trajectory' count independently.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:26:16.672816Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The provided manuscript describes a novel agent architecture (MemGUI-Agent) and a dataset (MemGUI-3K), but the **code quality** and **reproducibility** aspects are currently opaque. As a paper-stage review, I am evaluating the *artifacts that produced the paper* based on the claims made in the text.

**1. Reproducibility and Dependency Hygiene**
The paper explicitly links to a GitHub repository (`github.com/kwai/MemGUI-Agent`) and a HuggingFace model (`lgy0404/MemGUI-8B-SFT`) in the metadata (e002). However, the LaTeX source itself contains **no code snippets, configuration files, or dependency lists** (e.g., `requirements.txt`, `pyproject.toml`, or `Dockerfile`).
*   **Issue:** The training setup (Appendix, Sec. Training Setup) mentions specific optimizations like `AdamW fused` and `bfloat16` precision on 8x80GB GPUs. Without a provided `environment.yml` or `Dockerfile` in the supplementary material, it is impossible to verify if the "fused" optimizer is compatible with the claimed PyTorch/CUDA versions.
*   **Requirement:** The authors must include a `reproducibility.md` or an appendix section detailing the exact software stack (PyTorch version, CUDA version, specific library versions for `deepspeed` or `accelerate` if used) and the entry point for the training script.

**2. Modularity and Testability of Data Pipeline**
The dataset construction (Sec. MemGUI-3K Dataset) relies on a complex pipeline: "Task expansion → teacher rollouts → MemGUI-Eval filtering → SFT conversion."
*   **Issue:** The text describes the filtering logic (e.g., removing "abnormal 321-step outlier") but does not reference the specific code modules or unit tests that enforce these rules. In a high-quality codebase, the "MemGUI-Eval" filter should be a distinct, testable module with a corresponding test suite (e.g., `test_data_filtering.py`) to ensure the 2,956 trajectory count is deterministic.
*   **Requirement:** The review cannot confirm the integrity of the dataset without evidence of modular code structure. The authors should cite the specific file paths for the data filtering logic in the appendix or provide a snippet of the filtering code to demonstrate modularity.

**3. Code Artifacts and Truncation**
The paper claims to release code, but the provided LaTeX source does not include any code listings (e.g., via `lstlisting` or `minted`) that show the implementation of the `ConAct` mechanism (the 5-part output structure).
*   **Issue:** While the prompt templates are provided (e01), the actual inference loop and the `Fold` function implementation (Eq. 4) are missing from the text. If the code repository is the primary artifact, the paper must explicitly state the directory structure (e.g., `src/models/`, `src/training/`, `tests/`) to allow reviewers to assess modularity.
*   **Recommendation:** Add a "Code Structure" subsection in the Appendix that outlines the repository layout and points to the specific files implementing the `ConAct` logic and the `Fold` operation. This is critical for verifying that the code is not a monolithic script but a modular system.

**Conclusion**
The paper makes strong claims about performance and dataset size but fails to provide the necessary code-level evidence (dependency lists, modular structure, test suites) to support reproducibility. The verdict is **minor_revision** pending the inclusion of a reproducibility guide and code structure documentation.
