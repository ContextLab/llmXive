---
action_items:
- id: 1c04da352a64
  severity: writing
  text: "Add a dedicated discussion of privacy and PII handling, especially given\
    \ that the benchmark includes unfiltered document corpora (see Appendix A, \xA7\
    A.1)."
- id: e89af1b736eb
  severity: science
  text: Provide an evaluation of content-filtering or toxicity-mitigation mechanisms
    for the retrieved evidence across all backends (document, SQL, SPARQL, Cypher).
- id: cc63454648ed
  severity: writing
  text: Explicitly state the licensing terms of each of the 13 datasets and 309 knowledge
    bases, and describe how the system respects copyright and data-use restrictions.
- id: 21b54ac18ec9
  severity: writing
  text: 'Discuss dual-use risks: the ability to issue native queries to heterogeneous
    backends could be abused to extract disallowed or harmful information, and outline
    mitigation strategies (e.g., rate-limiting, query sanitisation, access-control
    policies).'
artifact_hash: f1ba0d06b47034bb9ae781a67854dde745b8b5c42ceeefcb523795f3179180a0
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T04:35:12.148675Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This re-review confirms that all four prior safety & ethics action items remain unaddressed in the current revision.

**PII Handling (ee77b4aec547):** The Ethical Considerations section (Section 7) briefly acknowledges that "private, harmful, or biased content present in these resources may carry over to the outputs" but provides no dedicated discussion of PII handling. Appendix A, §A.1 states "we do not perform additional filtering for personally identifying information or offensive content, deferring to the policies of the upstream datasets." This deferral is insufficient for a framework that will be deployed—there must be explicit guidance on how PII should be filtered or redacted in production use, especially given the unfiltered BEIR document corpora (MS MARCO, Natural Questions, etc.).

**Content Filtering Evaluation (c40851b66be6):** No evaluation of content-filtering or toxicity-mitigation mechanisms is provided. The paper mentions "standard safeguards and filtering" in the abstract ethical statement but offers no empirical assessment or description of mechanisms implemented across the four backends. This is a science-class issue requiring either implementation and evaluation or explicit acknowledgment that this is out of scope with justification.

**Licensing Terms (5f9c84365bc3):** The Appendix A, "Use of Existing Artifacts" states artifacts are used "under its respective license and terms" but does not explicitly enumerate the licensing terms for each of the 13 datasets (BEIR, Spider, BIRD, SimpleQuestions, LC-QuAD 2.0, QALD-10, Text2Cypher, etc.) or the 309 knowledge bases. This requires a table or appendix listing each dataset with its license (e.g., CC-BY, Apache 2.0, proprietary) and how compliance is ensured.

**Dual-Use Risks (4a13953ea81a):** There is no discussion of dual-use risks specific to OmniRetrieval's capability to issue native queries across heterogeneous backends. The system could potentially be abused to extract sensitive information from databases, execute harmful queries, or bypass access controls. No mitigation strategies (rate-limiting, query sanitization, access-control policies) are outlined. This is a critical omission for a framework that exposes powerful query capabilities through a natural-language interface.

All four items require revision before acceptance.
