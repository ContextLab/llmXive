---
action_items:
- id: 6ef416cde126
  severity: writing
  text: "Add a dedicated \u201CEthical Considerations\u201D or \u201CResponsible Use\u201D\
    \ section that discusses the dual\u2011use nature of camera\u2011controllable\
    \ video generation, potential for disinformation, privacy violations, and outlines\
    \ concrete mitigation strategies (e.g., watermarking, usage licenses, model access\
    \ controls)."
- id: 6def0747d8f8
  severity: writing
  text: Provide clear documentation of the provenance and licensing of all training
    datasets (SpatialVid, DL3DV, OpenVid, WorldPlay). Verify that no personally identifiable
    information (PII) or copyrighted content is inadvertently included, and state
    any filtering steps taken to remove such data.
- id: 9b34cfca9ed2
  severity: writing
  text: "Consider implementing a technical safeguard such as a detectable watermark\
    \ or a model\u2011level classifier that can flag generated content, and describe\
    \ this in the code repository."
- id: c1b9da4eed05
  severity: writing
  text: "If the released checkpoints are made publicly available, include a usage\
    \ policy that restricts malicious applications (e.g., deep\u2011fake creation,\
    \ surveillance) and outlines a process for revoking access if abuse is detected."
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:32:55.672970Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript introduces **minWM**, an open‑source pipeline that converts large text‑to‑video diffusion models into camera‑controllable, few‑step autoregressive world models. From a safety‑and‑ethics perspective, the work raises several concerns that are not addressed in the current text.

**Dual‑use risk.** By enabling real‑time, camera‑controlled video synthesis, the framework can be repurposed to generate highly realistic synthetic footage that mimics real‑world camera motion. This capability could be exploited for disinformation, deep‑fake creation, or privacy‑invasive surveillance simulations. The paper (see Sections 1–4) does not discuss these risks or propose mitigations. A responsible‑use statement is essential for any technology that lowers the barrier to high‑fidelity video generation.

**Data privacy and licensing.** The training data includes SpatialVid (perception‑estimated camera poses), DL3DV (re‑rendered 3D scenes), OpenVid, and WorldPlay‑generated videos. The manuscript (Fig. \ref{fig:ablation-data} and Sec. 4.2) does not clarify whether any of these sources contain personally identifiable information (e.g., faces, location metadata) or copyrighted material. Without explicit verification and filtering, the released models may inadvertently memorize and reproduce such content, violating privacy norms and copyright law.

**Model release safeguards.** The authors plan to release checkpoints, scripts, and documentation (Abstract, line 9). However, no mechanism is described to limit malicious redistribution or to embed provenance information in generated videos. Prior work on diffusion models has shown that watermarking or classifier‑based detection can help trace synthetic media; the authors should at least discuss adopting such techniques.

**IRB/IACUC considerations.** The work does not involve human subjects or animal experiments, so IRB/IACUC approval is not required. Nonetheless, if future extensions incorporate human‑captured video with identifiable subjects, the authors must obtain appropriate consent and ethical review.

**Recommendations.** The paper should be revised to include a concise but thorough “Ethical Considerations” section (≈200 words) covering the points above. Additionally, the code repository should contain a LICENSE file that specifies permissible uses and a CONTRIBUTING guide that enforces the usage policy. Implementing a detectable watermark in the generated videos would further reduce the risk of covert misuse.

Addressing these issues will substantially improve the manuscript’s alignment with responsible AI practices and make the open‑source release safer for the broader community.
