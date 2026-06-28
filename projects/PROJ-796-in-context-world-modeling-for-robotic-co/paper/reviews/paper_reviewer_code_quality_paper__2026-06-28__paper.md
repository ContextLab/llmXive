---
action_items:
- id: 375bad1d4939
  severity: writing
  text: The \checkdata metadata in paper.tex points to 'MOSS-Transcribe-Diarize' (a
    different project). Update these links to point to the ICWM code repository or
    remove them if code is not yet public.
- id: f40289c52672
  severity: writing
  text: Add a direct link to the ICWM code repository (e.g., GitHub/HuggingFace) in
    the Abstract or Introduction to ensure reproducibility of the method.
- id: ddce66379a85
  severity: writing
  text: Clarify the technical implementation of context prepending in Section 4.1
    (e.g., tokenization of interaction clips, KV cache usage) to aid reproduction.
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T05:50:07.787696Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates good modularity in its LaTeX structure, splitting content into logical files (`010-intro.tex`, `030-method.tex`, etc.), which aids maintainability. However, from a reproducibility and code quality perspective, there are critical omissions.

First, the `paper.tex` file contains `\checkdata` metadata lines (lines 13-15) that reference `mosi.cn/models/moss-transcribe-diarize` and a HuggingFace space for "MOSS-Transcribe-Diarize". These are clearly placeholder links from a different project and must be updated to reflect the actual ICWM code repository or removed if the code is not yet public. Leaving these as-is undermines the paper's credibility regarding artifact availability.

Second, while Section 4.1 ("Implementation Details") provides hyperparameters (learning rate, batch size, backbone), it lacks a direct link to the source code. For a method relying on specific architectural modifications (e.g., how interaction context $\mathcal{T}$ is prepended to the Transformer), a code repository is essential for verification. The current text describes the *what* but not the *how* of the implementation details (e.g., specific tokenization of action clips, handling of variable-length context).

Finally, the LaTeX preamble includes a large number of packages (e.g., `tcolorbox`, `pgfplots`, `siunitx`). While standard for papers, ensure that the `llmxive` class file (referenced in `main-llmxive.tex`) is available to the reader, as custom classes can break compilation if not bundled.

To improve reproducibility, please provide a working code link and ensure the metadata links are accurate.
