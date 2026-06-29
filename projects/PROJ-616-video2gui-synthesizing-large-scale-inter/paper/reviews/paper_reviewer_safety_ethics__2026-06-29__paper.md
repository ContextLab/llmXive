---
action_items:
- id: a934f29d43b7
  severity: writing
  text: The Impact Statement (Section 8) is insufficient. The paper describes a pipeline
    that scrapes 500M YouTube videos and synthesizes 12M interaction trajectories.
    This raises significant dual-use risks (e.g., training agents for automated credential
    stuffing, phishing, or bypassing CAPTCHAs) and privacy concerns regarding the
    source videos. The authors must explicitly discuss these risks and mitigation
    strategies rather than stating 'none of which we feel must be specifically highlighted.'
- id: 06be58412262
  severity: writing
  text: The methodology relies on scraping 500 million YouTube videos (Section 3.1).
    The paper lacks a clear statement on compliance with YouTube's Terms of Service
    and the legal/ethical implications of mass-scraping user-generated content for
    commercial or research training data. Authors must clarify the legal basis for
    this data collection and whether any opt-out mechanisms or content filtering for
    sensitive/private data were implemented.
- id: 94ac44bce4bb
  severity: writing
  text: The human evaluation study (Section 5.4) involves five expert participants
    but does not mention IRB approval or informed consent procedures. While the task
    (rating data quality) is low-risk, standard ethical guidelines for human subjects
    research require documentation of consent and ethical oversight, especially when
    the paper is submitted to a major conference.
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:18:33.171298Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a large-scale data synthesis pipeline (Video2GUI) that processes 500 million YouTube videos to create a dataset of 12 million GUI interaction trajectories. From a safety and ethics perspective, the current manuscript lacks necessary disclosures regarding the dual-use potential of the technology and the legal/ethical sourcing of the data.

First, the **Impact Statement** (Section 8) is inadequate. The authors state that "none of which we feel must be specifically highlighted here." This is a critical oversight. A dataset of this scale, derived from real-world user interactions, can be used to train agents capable of automating malicious tasks, such as credential stuffing, automated phishing, or bypassing security controls (e.g., CAPTCHAs) at scale. The authors must expand this section to explicitly acknowledge these dual-use risks and describe any safeguards or limitations they have considered or implemented.

Second, the **data sourcing** methodology (Section 3.1) involves scraping 500 million YouTube videos. The paper does not address compliance with YouTube's Terms of Service or the legal/ethical implications of mass-scraping user-generated content. There is no mention of filtering for sensitive or private information that may appear in these videos (e.g., personal data, financial information, or proprietary software interfaces). The authors must clarify the legal basis for this collection and describe any privacy-preserving measures taken to ensure no personally identifiable information (PII) is included in the final dataset.

Finally, the **human evaluation** study described in Section 5.4 involves five expert participants rating data quality. While the risk is low, the manuscript does not mention whether this study received Institutional Review Board (IRB) approval or if informed consent was obtained from the participants. Standard ethical guidelines for research involving human subjects require these disclosures. The authors should add a brief statement confirming that the study was conducted in accordance with relevant ethical guidelines and that participants provided informed consent.
