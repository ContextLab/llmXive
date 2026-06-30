---
action_items:
- id: 2d0ca12253ce
  severity: writing
  text: The paper demonstrates a strong focus on data quality in its methodology,
    particularly in the construction of the SFT and RL datasets (Appendix e000). However,
    critical gaps in data provenance and versioning prevent full reproducibility.
    First, the provenance and licensing of the training data are insufficiently detailed.
    Section e000 states the SFT corpus (2,954 examples) is generated from "Sonnet
    4.6 exploration traces." As Sonnet is a proprietary model, the legal basis for
    using its outputs f
artifact_hash: 535aae0d1a0e0d57b4a24f48088ceb2c0ca892fe3b86ecd68f902e6d0b3a9865
artifact_path: projects/PROJ-716-fastcontext-training-efficient-repositor/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T04:11:01.695096Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates a strong focus on data quality in its methodology, particularly in the construction of the SFT and RL datasets (Appendix e000). However, critical gaps in data provenance and versioning prevent full reproducibility.

First, the **provenance and licensing** of the training data are insufficiently detailed. Section e000 states the SFT corpus (2,954 examples) is generated from "Sonnet 4.6 exploration traces." As Sonnet is a proprietary model, the legal basis for using its outputs for training a new model (FastContext) is unclear. The "Artifact Use and Intended Use" section (e001) is too generic, merely stating adherence to "underlying dataset licenses" without specifying the license for the derived Sonnet traces or the 400 RL prompts. A clear statement on the license of the released artifacts (models, prompts, trajectories) is required.

Second, **external source versioning** is missing. The paper relies on tools like `ripgrep` (cited via URL in e000) and `SGLang` (e000) for data generation and rollout. No version numbers, commit hashes, or release tags are provided. Given that tool behavior (e.g., regex matching in ripgrep) can change between versions, the exact data generation pipeline cannot be reconstructed. This is a significant risk for reproducibility.

Third, the **data availability** for the evaluation subset is incomplete. Appendix e002 lists instance IDs for the "SWE-bench Pro Subset" but does not provide a direct link to a downloadable manifest file or a script to retrieve these specific 200 instances from the SWE-bench repository. Without this, independent researchers cannot verify the "51.5%" score reported in Table 1 (e001) against the exact same test set.

Finally, the **schema** for the SFT data is described textually (e.g., `instance_id`, `messages`) but lacks a formal schema definition (e.g., JSON Schema) or a sample data file in the supplementary materials. This makes it difficult for others to format their own data for training.

To address these issues, the authors should: (1) explicitly state the license for all derived training data; (2) pin all external tool versions; (3) provide a downloadable manifest for the evaluation subset; and (4) include a sample data file or schema definition.
