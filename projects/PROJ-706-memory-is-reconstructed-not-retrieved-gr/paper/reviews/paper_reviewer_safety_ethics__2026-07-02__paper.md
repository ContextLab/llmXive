---
action_items:
- id: 1ccb8fb234ec
  severity: writing
  text: The Impact Statement (Section 7) acknowledges privacy risks but lacks specific
    mitigation strategies for the proposed 'active reconstruction' mechanism. Since
    the agent autonomously infers new cues and traverses memory graphs, it may inadvertently
    expose sensitive user data not explicitly queried. The authors should detail how
    the system prevents over-exposure of private information during the multi-step
    reasoning process.
- id: 02664d9f4350
  severity: writing
  text: The paper relies on LLM-based distillation to populate the memory graph (Section
    3.3, Appendix A.1) without mentioning human-in-the-loop verification or consent
    protocols for the source dialogue data. If the system is deployed in real-world
    settings, the automatic extraction of 'semantic aspects' and 'episodic events'
    from user conversations raises significant consent and data governance concerns
    that require explicit discussion.
- id: 1e3ba2f7ff5e
  severity: writing
  text: The 'Binary-Tree Needle-in-a-Haystack' theoretical task (Appendix A.4) and
    the 'Case Study' (Appendix A.5) use synthetic or anonymized examples. However,
    the paper does not address the potential for the active reconstruction mechanism
    to hallucinate or fabricate 'cues' that could lead to the retrieval of false or
    harmful information about real users in a production environment. A discussion
    on the safety of the inference path is needed.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:12:57.151657Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents MRAgent, a framework for active memory reconstruction in LLM agents. From a safety and ethics perspective, the paper is generally sound in its high-level acknowledgment of risks but lacks necessary depth regarding the specific implications of its "active" mechanism.

The **Impact Statement** (Section 7) correctly identifies that persistent memory raises privacy and data governance concerns. However, it treats these as generic issues applicable to all memory systems. The proposed "active reconstruction" mechanism, which allows the agent to infer new cues and traverse graph paths based on accumulated evidence (Section 2.3, Algorithm 1), introduces a specific risk of **information over-exposure**. Unlike passive retrieval, which is bounded by the query, active reconstruction may lead the agent to retrieve sensitive data that was not directly requested but is semantically linked in the graph. The authors should explicitly discuss how the system prevents the agent from traversing into private or sensitive sub-graphs during this autonomous exploration.

Furthermore, the **memory population pipeline** (Section 3.3, Appendix A.1) relies entirely on LLM distillation to extract cues, tags, and semantic facts from raw dialogue. There is no mention of **user consent** mechanisms or **human-in-the-loop verification** for this extraction process. In a real-world deployment, automatically converting user conversations into a structured graph of "semantic aspects" and "episodic events" without explicit user opt-in or the ability to review/delete specific inferred nodes could violate data privacy norms. The authors should clarify the data governance protocols assumed for the training and deployment of this system.

Finally, while the theoretical analysis (Appendix A.4) and case studies demonstrate the power of active reconstruction, they do not address the risk of **hallucinated cues**. If the LLM incorrectly infers a cue during the reconstruction process, it could lead to the retrieval of irrelevant or potentially harmful information, creating a "false memory" effect. The paper should include a brief discussion on the safety implications of this error mode, particularly in high-stakes applications like personal assistants or decision support systems.

Overall, the paper does not present immediate fatal ethical flaws, but the specific risks introduced by the active reconstruction paradigm require more detailed mitigation strategies and ethical considerations in the final version.
