---
action_items:
- id: 368b909ec438
  severity: writing
  text: Explicitly state the software and model weight license (e.g., MIT, Apache
    2.0) in the Abstract or Conclusion. Currently, the GitHub link is provided without
    legal terms (Abstract, line 28).
- id: 071fead716d0
  severity: writing
  text: Provide a specific commit hash or version tag for the released code repository
    to ensure reproducibility. The GitHub URL lacks a pinned version (Author info,
    line 12).
- id: 4ac0e48abda2
  severity: writing
  text: Clarify the licensing constraints of the synthetic training data derived from
    Wan2.1-T2V-14B. The base model's license dictates permissible use of generated
    data (Sec 5.1, Implementation Details).
artifact_hash: 005685aa9007ed1eda2f5c52307bec525988ac42fa3e5edf385819b15a2b3366
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T17:04:29.565778Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility metadata within the manuscript. While the experimental methodology is sound, critical data governance information is missing from the text.

First, the paper states "Code is released at https://github.com/NVLabs/AnyFlow" in the Abstract (line 28) and Author block (line 12), but no license is specified. Without an explicit license (e.g., MIT, Apache 2.0, CC-BY), the legal status of the code and weights remains ambiguous, hindering safe adoption. This is a standard requirement for open-source AI artifacts.

Second, regarding version control, the manuscript relies on external baselines and a self-hosted repository. For the Wan2.1 base model, only the arXiv link is provided (Sec 5.1). For the AnyFlow repository, no commit hash or release tag is cited. This creates a risk of link rot and version drift; reviewers cannot verify that the reported results correspond to the specific code snapshot available at publication time.

Third, the training data provenance requires clarification. The authors note training on a "synthetic dataset of 256K prompt--video pairs generated from Wan2.1-T2V-14B" (Sec 5.1). The legal and ethical implications of synthetic data depend heavily on the base model's license and terms of service. If Wan2.1 restricts derivative works, the AnyFlow model's distribution rights could be contested. The paper should explicitly address whether the synthetic data generation complies with the base model's usage policy.

Finally, the evaluation relies on "official VBench augmented prompts" (Sec 5.2). The specific version or file hash of these prompts is not provided. Since benchmark performance can vary with prompt engineering, omitting the exact prompt set reduces the reproducibility of the evaluation data.

To resolve these issues, the authors should add a license declaration, pin repository versions, and clarify synthetic data provenance constraints. These are textual fixes that do not require re-running experiments.
