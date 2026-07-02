---
action_items:
- id: 95f53f51073d
  severity: science
  text: 'The paper exhibits critical data quality and provenance issues that block
    verification of the central claims. First, there is a direct contradiction in
    the code provenance. The Abstract states: "Our code is available at: [anonymous
    link]" and immediately repeats "Our code is available at: [non-anonymous GitHub
    link]". This inconsistency suggests a lack of rigorous version control or a copy-paste
    error in the final manuscript. For a paper claiming a "plug-and-play" acceleration
    method, the inabil'
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:09:47.862449Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The paper exhibits critical data quality and provenance issues that block verification of the central claims.

First, there is a direct contradiction in the **code provenance**. The Abstract states: "Our code is available at: [anonymous link]" and immediately repeats "Our code is available at: [non-anonymous GitHub link]". This inconsistency suggests a lack of rigorous version control or a copy-paste error in the final manuscript. For a paper claiming a "plug-and-play" acceleration method, the inability to definitively locate the source code prevents independent verification of the `EffOPD` implementation. The authors must resolve this to a single, valid, and accessible URL (or a valid anonymous submission link if under review) and ensure the repository contains the exact scripts used to generate the results in Figures 1-6.

Second, the **dataset provenance** is insufficiently documented. While the paper mentions using datasets like `DeepMath-103K` and `MATH-12K`, it fails to specify the exact version, commit hash, or license for these resources. In the context of LLM post-training, dataset versions can vary significantly in quality and composition. Without explicit versioning or license declarations (e.g., "DeepMath-103K v1.0, CC-BY-4.0"), the reproducibility of the training dynamics is compromised. Furthermore, Table 1 in the Appendix lists several teacher models (e.g., `Qwen3-14B-Base-DAPO`) as "No" for Open-Source. The paper does not explain how these closed-source models were obtained or under what license they were used for training. If these models are proprietary or require specific internal access, the paper's claim of reproducibility is invalid unless the authors provide a clear path to access these assets or release the weights.

Finally, the **bibliographic integrity** is questionable. The metadata flags the arXiv URL (2605.11739) as unreachable, which is expected for a future-dated paper, but the text does not provide an alternative stable identifier (like a DOI or a specific commit hash for the code) that would allow a reviewer to verify the work's existence and state at the time of submission. The reliance on "unreachable" or future-dated links undermines the scientific record.

To proceed, the authors must: (1) unify and validate the code repository link; (2) explicitly list the license and version for all datasets and models used; and (3) clarify the access method for any closed-source models referenced in the experiments. Until these data quality issues are resolved, the results cannot be considered reproducible or verifiable.
