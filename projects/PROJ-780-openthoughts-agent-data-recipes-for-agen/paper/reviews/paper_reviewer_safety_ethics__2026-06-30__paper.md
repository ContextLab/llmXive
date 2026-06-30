---
action_items:
- id: d4762bc58de8
  severity: writing
  text: The paper lacks a formal statement regarding Institutional Review Board (IRB)
    or equivalent ethics committee approval for the use of human-generated data (e.g.,
    StackExchange, GitHub issues). While the data is public, the aggregation and use
    for training agentic models require explicit discussion of consent, privacy, and
    terms of service compliance.
- id: f3ee0a1da8fe
  severity: writing
  text: The 'Broader Impacts' section (Section 6) is insufficiently detailed regarding
    dual-use risks. Agentic models capable of autonomous code execution and tool use
    pose significant safety risks (e.g., automated vulnerability exploitation, unauthorized
    system access). The paper must expand on specific mitigation strategies, such
    as sandboxing protocols, human-in-the-loop requirements, and refusal mechanisms
    for harmful tasks.
- id: 257a154745fd
  severity: writing
  text: The paper mentions using 'LLM-based task filters' and 'GPT-5' for data curation
    (Section 4.4, Table 4). There is no discussion of the potential for these filters
    to introduce bias or inadvertently filter out valid but complex edge cases, nor
    is there an assessment of the safety of the generated synthetic data (e.g., ensuring
    synthetic tasks do not encode harmful instructions).
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:22:48.973355Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a significant contribution to open-source agentic model training but requires specific additions to address safety and ethical considerations before publication.

**Data Privacy and Consent:**
The dataset construction relies heavily on public repositories and forums, specifically citing `stackexchange-superuser`, `stackexchange-tezos`, and `swe-smith` (derived from GitHub issues) in Section 4.1 and Table 1. While these sources are publicly available, the paper does not explicitly address the ethical implications of repurposing user-generated content for training high-capability agentic models. There is no mention of whether the authors considered the Terms of Service of these platforms regarding automated scraping and model training, nor is there a discussion of user consent or the potential for re-identification of users from their code contributions. A statement clarifying compliance with platform policies and the handling of potentially sensitive user data is required.

**Dual-Use and Safety Risks:**
The "Broader Impacts" paragraph in Section 6 is currently too brief. The paper demonstrates that the resulting models can execute complex, multi-turn tasks in terminal environments (Section 5, Table 3). This capability introduces substantial dual-use risks, including the potential for automated cyberattacks, exploitation of software vulnerabilities, or unauthorized system manipulation. The authors must expand this section to explicitly acknowledge these risks. Furthermore, the paper should detail any safety measures implemented during the training or evaluation phases, such as the use of the `Harbor` sandbox (mentioned in Appendix E) to prevent model actions from affecting host systems, and whether the models were evaluated for their ability to refuse harmful instructions.

**Filtering and Bias:**
The methodology relies on LLM-based filtering (e.g., using GPT-5 to select tasks based on response length, Section 4.4) to curate the dataset. The paper does not discuss the potential for these filters to introduce systematic biases or to inadvertently exclude valid but difficult tasks that do not fit the "longer is better" heuristic. Additionally, there is no analysis of whether the synthetic augmentation (Section 4.5) or the filtering process could inadvertently amplify harmful patterns present in the source data. A brief discussion on the safety and bias implications of these curation steps is necessary.

**Recommendation:**
The authors should revise the manuscript to include a dedicated subsection on "Ethical Considerations and Safety" that addresses data provenance, consent, dual-use risks, and specific mitigation strategies employed. This will ensure the paper meets the necessary ethical standards for research involving powerful agentic systems.
