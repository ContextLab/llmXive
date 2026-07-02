---
action_items:
- id: b80868b230c2
  severity: writing
  text: The Impact Statement (Section Impact Statement) is generic and fails to address
    specific dual-use risks of autonomous GUI agents, such as unauthorized automation,
    credential theft, or bypassing security controls. A detailed discussion of potential
    misuse and mitigation strategies is required.
- id: c2dc351cd760
  severity: writing
  text: The data collection pipeline relies on scraping 500 million YouTube videos.
    The manuscript lacks explicit confirmation of compliance with YouTube's Terms
    of Service, copyright laws, and the specific licenses of the source videos. Clarification
    on legal basis for data usage and redistribution is needed.
- id: 74392152c0fa
  severity: writing
  text: The human evaluation study (Section Data Quality Check) involves five expert
    participants but does not mention IRB approval, informed consent procedures, or
    how participant anonymity and data privacy were protected during the study.
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:11:04.804782Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a large-scale framework for synthesizing GUI interaction data from internet videos. While the technical contribution is significant, the paper currently lacks sufficient depth regarding safety, ethics, and legal compliance, which are critical for datasets intended to train autonomous agents.

**Dual-Use and Societal Impact:**
The current "Impact Statement" (Section Impact Statement) is a boilerplate declaration that does not address the specific risks associated with training agents to autonomously control user interfaces. GUI agents possess significant dual-use potential; they could be weaponized for automated credential theft, bypassing CAPTCHAs, executing unauthorized financial transactions, or automating spam and fraud campaigns. The authors must expand this section to explicitly discuss these risks, potential misuse scenarios, and the specific safeguards or limitations they propose (e.g., watermarking synthetic data, restricting release of certain high-risk subsets, or providing usage guidelines).

**Data Privacy and Copyright:**
The dataset "WildGUI" is constructed from 500 million YouTube videos. The paper does not address the legal and ethical implications of scraping and redistributing this content.
1.  **Terms of Service:** The authors must confirm that their scraping and processing pipeline complies with YouTube's Terms of Service and the robots.txt policies of the source platforms.
2.  **Copyright:** The manuscript should clarify the copyright status of the source videos and the legal basis for creating a derivative dataset (WildGUI). Are the videos used under fair use, or are they licensed? If the dataset is released, does it include copyrighted material?
3.  **PII:** The pipeline extracts screenshots and trajectories. The authors should describe any automated or manual processes used to detect and redact Personally Identifiable Information (PII), such as user names, email addresses, or sensitive documents visible in the screenshots, to prevent privacy violations.

**Human Subjects Research:**
Section "Data Quality Check" describes a user study involving five expert participants. The manuscript does not state whether this study received Institutional Review Board (IRB) approval or if informed consent was obtained from the participants. Given that the study involves human evaluation of data, standard ethical protocols for human subjects research should be followed and documented.

**Recommendation:**
The paper requires a minor revision to address these ethical and safety gaps. The authors should add a dedicated subsection in the "Impact Statement" or "Ethical Considerations" to discuss dual-use risks, legal compliance regarding data scraping, PII handling, and IRB approval for the human study.
