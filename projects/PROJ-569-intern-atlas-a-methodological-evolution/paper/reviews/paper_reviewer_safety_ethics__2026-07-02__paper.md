---
action_items:
- id: 0af65770525b
  severity: writing
  text: The 'Strata Dataset' (Sec 4.2) includes 'Rejected submissions' from ICLR 2026.
    The authors must explicitly confirm that these rejected papers were obtained via
    public channels (e.g., OpenReview) and that no private reviewer comments or confidential
    author identities were used in the evaluation pipeline to ensure compliance with
    conference data policies.
- id: 298a7f69a910
  severity: writing
  text: The 'Human-Rated Subset' (App D.3) involves 10 AI PhD researchers scoring
    100 ideas. The manuscript lacks a statement confirming that informed consent was
    obtained from these experts, that the study protocol was reviewed by an IRB (or
    equivalent ethics board), and that the data collection adhered to privacy standards
    regarding the experts' identities and scores.
- id: ff8ac50d1edf
  severity: writing
  text: The 'Idea Generation' operator (Sec 3.3) proposes new research ideas based
    on 'structural gaps.' The authors must add a 'Broader Impact' or 'Limitations'
    subsection explicitly addressing the risk of these agents generating harmful,
    unethical, or dual-use research proposals (e.g., biosecurity risks, adversarial
    attacks) and describe any safety filters or human-in-the-loop safeguards implemented
    to prevent such outputs.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:30:36.605202Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents Intern-Atlas, a large-scale infrastructure for mapping methodological evolution in AI. From a safety and ethics perspective, the paper is generally sound in its intent to improve scientific rigor, but it lacks necessary disclosures regarding data provenance, human subject protections, and potential dual-use risks associated with automated idea generation.

First, regarding data privacy and conference policies, Section 4.2 describes the "Strata Dataset," which includes 300 "Rejected submissions" from ICLR 2026. While the text notes that data was obtained from OpenReview, the authors must explicitly clarify the scope of data used. Specifically, they should confirm that the evaluation pipeline relied solely on publicly available metadata and text, and did not utilize confidential reviewer comments, author identities, or private decision rationales. Using rejected papers for training or evaluation without explicit permission or public availability of the full review history can violate conference data policies and author privacy expectations. A brief statement in the "Data Availability" or "Ethics" section confirming adherence to these policies is required.

Second, the study involves human evaluation. Appendix D.3 details a "Human-Rated Subset" where 10 AI PhD researchers scored 100 idea profiles. The manuscript currently lacks any mention of ethical oversight. The authors must state whether this study was reviewed by an Institutional Review Board (IRB) or an equivalent ethics committee. Furthermore, they should confirm that informed consent was obtained from the participating experts, detailing how their identities and scores were anonymized and stored. Without this, the human evaluation component does not meet standard ethical research guidelines.

Third, the "Strategy-Driven Idea Generation" operator (Section 3.3) is designed to propose novel research ideas by identifying "structural gaps" in the literature. While the paper frames this as a positive contribution to scientific discovery, it does not address the potential for these agents to generate harmful or dual-use research proposals (e.g., methods for creating biological weapons, advanced cyber-attacks, or surveillance tools). The "Broader Impact" section (Appendix E) is currently too generic, stating only that risks are "indirect." The authors should expand this section to explicitly discuss the risk of generating harmful ideas and describe any specific safety mechanisms, such as keyword filtering, human-in-the-loop verification, or refusal policies, that are in place to prevent the system from outputting dangerous research directions.

Finally, the extraction process relies on LLMs to classify citation relationships and extract "bottlenecks." While the paper mentions a "deterministic post-checker" for verbatim quotes, there is no discussion of how the system handles potential biases in the underlying literature (e.g., citation bias against certain demographics or institutions) that could be amplified by the graph structure. A brief acknowledgment of this limitation and its potential impact on the fairness of the generated ideas would strengthen the ethical standing of the work.

Addressing these points will ensure the paper meets the necessary ethical standards for publication.
