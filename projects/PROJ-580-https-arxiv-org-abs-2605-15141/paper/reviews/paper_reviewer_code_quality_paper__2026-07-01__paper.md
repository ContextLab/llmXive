---
action_items:
- id: f4230a0899b4
  severity: science
  text: The LaTeX source lacks a `requirements.txt`, `pyproject.toml`, or `Dockerfile`.
    Without these, the reproducibility of the 3-stage pipeline (AR training, Causal
    CD, Asymmetric DMD) is impossible to verify from scratch. Add a dependency manifest
    and a build script.
- id: 11a418da5dff
  severity: science
  text: The paper claims a 4x reduction in training cost (11,600 vs 2,900 GPU hours)
    and zero storage overhead. However, the code artifacts required to reproduce the
    'Causal CD' online step (specifically the single-step ODE solver integration and
    EMA update logic) are not provided. Include the core training loop implementation
    to validate these efficiency claims.
- id: 43e3eaea249d
  severity: writing
  text: The `src/3-Method.tex` file contains complex mathematical derivations (Eq.
    1-5) but no corresponding pseudocode or algorithm block. For code quality and
    reproducibility, an `algorithm` environment detailing the Causal CD update rule
    and the asymmetric DMD self-rollout loop is required.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:04:24.344821Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The provided LaTeX source for "Causal Forcing++" presents a strong theoretical narrative but fails the code quality and reproducibility lens due to the complete absence of executable artifacts. As an arXiv-ingested paper, the expectation is that the authors provide a link to a repository with a clear entry point, yet the text only lists GitHub URLs without specifying the commit hash, branch, or directory structure required to run the experiments.

Specifically, the claim of reducing Stage 2 training cost from ~11,600 to ~2,900 A800 GPU hours (Section 3.2, Table 1) relies on the "online" nature of Causal CD. However, without the actual training script (e.g., `train_causal_cd.py`) showing how the single-step ODE supervision is computed and integrated into the loss function, this efficiency claim cannot be independently verified. The current text describes the math but not the implementation details (e.g., gradient accumulation, EMA decay rates, or specific solver tolerances) necessary to reproduce the "zero storage" advantage.

Furthermore, the paper describes a complex 3-stage pipeline (AR training, Causal CD initialization, Asymmetric DMD). There is no `Makefile`, `Dockerfile`, or `requirements.txt` included in the source to define the environment. The `math_commands.tex` and `preamble.tex` are well-structured, but the absence of a `src/` directory containing the actual Python code (or a clear `CODE_OF_CONDUCT` and `CONTRIBUTING.md` in the linked repo) makes the "reproducibility from scratch" requirement unmet.

To address this, the authors must either:
1. Provide a `requirements.txt` and a `run_experiment.sh` script in the repository linked in the abstract.
2. Include a detailed Algorithm block in `src/3-Method.tex` that explicitly outlines the data flow and update rules for the Causal CD stage, ensuring the logic is unambiguous for implementation.
3. Clarify the exact commit hash and branch of the referenced GitHub repositories to ensure the code matches the paper's claims.

Without these artifacts, the paper remains a theoretical proposal rather than a reproducible scientific contribution.
