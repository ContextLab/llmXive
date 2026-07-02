---
action_items:
- id: 176451045d88
  severity: writing
  text: The manuscript relies on Qwen3-VL and Gemini 3.1 Pro for prompt generation
    and evaluation (Sections 3.2.1, 4.1). Explicitly disclose the data privacy policies
    of these third-party APIs regarding the reference videos and generated prompts
    to ensure no sensitive content is inadvertently transmitted or stored.
- id: 5410af3eb73e
  severity: writing
  text: The training dataset comprises 1.8M internet videos (Section 4.1) without
    mentioning IRB approval, consent procedures, or copyright compliance. Add a statement
    clarifying the legal and ethical basis for using this data, specifically addressing
    potential copyright infringement and the exclusion of personally identifiable
    information (PII).
- id: afa6790338ac
  severity: writing
  text: The "emergent" capability to clone camera motion from raw RGB videos (Section
    4.3) lowers the barrier for generating deepfakes or misleading content. Include
    a dedicated "Ethical Considerations" subsection discussing potential dual-use
    risks (e.g., misinformation, non-consensual content) and proposed mitigation strategies.
artifact_hash: a65d314d17ec7712e12f1ec0ba7f4dba5e22b080c532708ee9eae2b427ffd22c
artifact_path: projects/PROJ-708-omnidirector-general-multi-shot-camera-c/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T06:47:26.306523Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework for camera motion cloning but lacks sufficient disclosure regarding data privacy, third-party API usage, and potential dual-use risks.

**Data Privacy and Third-Party APIs:**
The methodology relies heavily on external Large Multimodal Models (LMMs) for critical tasks. Specifically, Section 3.2.1 describes using Qwen3-VL to refine camera prompts, and Section 4.1 utilizes Gemini 3.1 Pro for quantitative evaluation (GSB comparisons). The paper does not state whether these API calls involve transmitting the reference video frames or generated content to external servers. Given that the input videos are sourced from the internet (Section 4.1), there is a risk of inadvertently processing copyrighted material, PII, or sensitive content through these third-party services. The authors must explicitly disclose the data handling policies of these APIs and confirm that no sensitive data is retained or used for further training by the API providers.

**Dataset Ethics and Copyright:**
The training set consists of 1.8M internet videos (Section 4.1). The manuscript does not mention any Institutional Review Board (IRB) approval, consent mechanisms, or copyright clearance procedures. In the context of generative AI, the use of uncurated internet-scale datasets raises significant ethical concerns regarding the rights of content creators and the potential inclusion of non-consensual or harmful content. A statement clarifying the legal basis for data usage, the filtering of PII, and adherence to copyright laws is required.

**Dual-Use and Misinformation Risks:**
The "emergent" capability described in Section 4.3, where the model can clone camera motion from raw RGB videos without explicit parameter extraction, significantly lowers the technical barrier for generating realistic video manipulations. This capability could be misused for creating deepfakes, spreading misinformation, or generating non-consensual content. The paper currently lacks a discussion on these dual-use risks. The authors should add a dedicated "Ethical Considerations" section outlining the potential for misuse and any safeguards implemented (e.g., watermarking, usage restrictions) to mitigate these risks.
