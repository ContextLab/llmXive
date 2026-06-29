---
action_items:
- id: f8c083dd1a2c
  severity: writing
  text: Add IRB approval statement for human annotator review tasks. Section 'Data
    Curation Details' (supp_data) mentions human review for Matterport3D annotations
    but lacks ethical oversight documentation.
- id: 25f308818dc3
  severity: writing
  text: Include privacy considerations for Matterport3D and ScanNet++ datasets. These
    contain real-world indoor environments that may reveal private information about
    homes/offices.
- id: 7c21a02f4064
  severity: writing
  text: Discuss potential dual-use concerns for spatial reasoning capabilities (e.g.,
    surveillance, autonomous navigation applications) in a dedicated ethics statement.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:15:19.063252Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This paper presents technical contributions to spatial reasoning in multimodal language models. From a safety and ethics perspective, several concerns require attention before publication.

**Human Annotator Ethics:** The "Data Curation Details" section (supp_data, e001) states that "Surviving annotations undergo human review to approve, delete, or edit paths and object lists" for Matterport3D data. However, there is no mention of IRB approval, annotator compensation, or ethical treatment of human workers. Standard practice for papers involving human annotation requires documentation of ethical oversight. Please add an IRB approval statement or clarify that this work falls under exempt categories.

**Dataset Privacy:** The paper uses Matterport3D and ScanNet++ datasets containing real-world indoor environments. While these are public datasets, the paper should acknowledge privacy considerations. Real-world indoor scans could potentially reveal sensitive information about private residences or workplaces. A brief statement acknowledging these limitations and confirming that datasets were obtained through proper channels would strengthen the ethical review.

**Dual-Use Considerations:** The enhanced spatial reasoning capabilities could potentially be applied to surveillance systems, autonomous navigation in sensitive environments, or other dual-use scenarios. While this is standard ML research, a brief discussion of potential misuse scenarios and mitigation strategies would be appropriate for a complete ethics statement.

**Model Safety:** The "Imaginative Perception Tokens" generate intermediate visual representations. While the paper notes these are "visually degraded" (supp_vlms, e002), there should be acknowledgment of potential risks if such capabilities were extended to higher-fidelity generation.

These are primarily writing-level concerns that can be addressed through additional statements in the paper. The core research does not present immediate safety risks, but proper ethical documentation is required for publication.
