---
action_items:
- id: 72aef1aeb4b9
  severity: writing
  text: The dataset generation procedure (Sec 3.3, Appx Sec 2) relies on GAPartNet
    annotations but lacks a formal license declaration for the derived 277 trajectories.
    Explicitly state the license (e.g., CC-BY, MIT) and confirm compatibility with
    the GAPartNet source license to ensure legal reproducibility.
- id: 3b7489848f66
  severity: writing
  text: The paper references external resources (GAPartNet, Isaac Gym, SAPIEN) and
    code (GitHub) but does not include a 'Data Availability' or 'License' section.
    Add a dedicated section or table listing the provenance, version, and license
    of all external datasets and simulation backends used.
- id: f6ccb21534b4
  severity: writing
  text: The reference trajectories are stored as JSON files (Sec 3.3), but the schema
    (field names, coordinate frames, units) is not formally defined in the text or
    an appendix table. Provide a schema definition to prevent ambiguity in data interpretation.
- id: 9ef00009f4cd
  severity: science
  text: The evaluation relies on specific damping multipliers (x1, x2, x4) applied
    to the physics engine. The exact physics engine version (e.g., Isaac Gym Preview
    4) and the specific damping parameter names/units used in the simulation are not
    specified, hindering exact replication of the OOD conditions.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T13:51:45.101705Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper provides a detailed description of the heuristic trajectory generation process (Section 3.3, Appendix Section 2) and the resulting dataset of 277 trajectories. However, from a data quality and provenance perspective, several critical elements are missing or insufficiently documented.

First, **licensing and provenance** are not explicitly addressed. The dataset is derived from GAPartNet geometry and annotations. While GAPartNet has its own license, the paper does not state the license under which the *newly generated* 277 trajectories are released. Without a clear license statement (e.g., CC-BY 4.0, MIT), the "pure-geometry dexterous interaction resource" claimed in the abstract cannot be legally reused by the community. The authors must add a "Data Availability" section specifying the license for the generated dataset and confirming its compatibility with the source GAPartNet license.

Second, the **data schema** for the released JSON trajectories is undefined. Section 3.3 mentions the files contain "per-frame wrist poses and finger configurations," but does not specify the coordinate frame (e.g., world, object, hand base), the rotation representation (quaternion, Euler, axis-angle), or the units (meters, radians). This ambiguity makes the data difficult to integrate into other pipelines. A schema definition or a sample JSON snippet in the appendix is required.

Third, **simulation environment versioning** is critical for reproducibility given the heavy reliance on physics dynamics (damping). The paper mentions using Isaac Gym and SAPIEN but does not specify the exact versions or commit hashes. Since damping behavior can vary between physics engine versions, the lack of version control for the simulation backend makes the "OOD damping" results difficult to verify exactly.

Finally, the **external source stability** is a concern. The paper links to a GitHub repository and a website. While standard for arXiv submissions, the review process should note that if these links rot, the data and code become inaccessible. The authors should consider archiving the dataset on a persistent repository (e.g., Zenodo, Hugging Face) with a DOI to ensure long-term availability, as the current reliance on a GitHub link is a potential point of failure for data quality.
