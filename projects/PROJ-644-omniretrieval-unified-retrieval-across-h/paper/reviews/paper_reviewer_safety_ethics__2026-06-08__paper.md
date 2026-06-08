---
action_items:
- id: ee77b4aec547
  severity: writing
  text: "Add a dedicated discussion of privacy and personally identifying information\
    \ (PII) handling, especially given that the benchmark includes unfiltered document\
    \ corpora (see Appendix\u202FA, \xA7\u202FA.1)."
- id: c40851b66be6
  severity: science
  text: "Provide an evaluation of content\u2011filtering or toxicity\u2011mitigation\
    \ mechanisms for the retrieved evidence across all backends (document, SQL, SPARQL,\
    \ Cypher)."
- id: 5f9c84365bc3
  severity: writing
  text: "Explicitly state the licensing terms of each of the 13 datasets and 309 knowledge\
    \ bases, and describe how the system respects copyright and data\u2011use restrictions."
- id: 4a13953ea81a
  severity: writing
  text: "Discuss dual\u2011use risks: the ability to issue native queries to heterogeneous\
    \ backends could be abused to extract disallowed or harmful information, and outline\
    \ mitigation strategies (e.g., rate\u2011limiting, query sanitisation, access\u2011\
    control policies)."
artifact_hash: f1ba0d06b47034bb9ae781a67854dde745b8b5c42ceeefcb523795f3179180a0
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T07:47:31.570598Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

**Safety & Ethics Review (200‑500 words)**  

The manuscript introduces *OmniRetrieval*, a framework that routes a natural‑language question to multiple heterogeneous knowledge sources (document collections, relational databases, RDF graphs, property graphs) and executes native queries on each. While the technical contribution is clear, the paper’s treatment of safety, privacy, and ethical considerations is insufficient for a system that can potentially surface any content stored in the registered backends.

1. **Privacy and PII** – In Appendix A.1 the authors explicitly state that they “do not perform additional filtering for personally identifying information or offensive content” and defer to upstream dataset policies. This admission is concerning because several of the included corpora (e.g., medical abstracts in NFCorpus, web passages in MS MARCO) may contain sensitive personal data. The manuscript lacks a concrete strategy for detecting or redacting PII before returning results, nor does it discuss compliance with regulations such as GDPR or HIPAA. A privacy‑by‑design discussion (e.g., anonymisation pipelines, audit logs) is required.

2. **Content Moderation & Harmful Outputs** – The *Ethical Considerations* section (Section 7) acknowledges the risk of “private, harmful, or biased content” but only recommends “standard safeguards and filtering” without any empirical evaluation. Given that the system can query arbitrary backends, it could retrieve disallowed or extremist material (e.g., hate speech in web corpora, malicious code snippets in code‑related databases). The paper should include experiments measuring the prevalence of toxic or disallowed content in retrieved evidence and demonstrate that a mitigation layer (e.g., toxicity classifier, safe‑completion constraints) reduces such outputs.

3. **Licensing & Data Use** – The benchmark aggregates 13 public datasets and 309 knowledge bases, each with its own license (some are CC‑BY, others may be non‑commercial). The manuscript does not document how these licenses are respected when the system indexes, stores, or redistributes content. This omission could lead to inadvertent copyright violations, especially when the framework consolidates results across sources.

4. **Dual‑Use Risks** – By exposing a unified query interface, OmniRetrieval lowers the barrier for non‑experts to issue sophisticated native queries (SQL joins, SPARQL graph traversals) across many backends. An adversary could exploit this to harvest proprietary data, enumerate schema details, or craft queries that trigger denial‑of‑service conditions in the backends. The paper should discuss threat models, access‑control mechanisms (authentication, per‑backend permissions), and rate‑limiting to mitigate abuse.

5. **IRB/IACUC Concerns** – The work does not involve human subjects or animal studies, so IRB/IACUC approvals are not needed. However, the authors should confirm that no human‑subject data (e.g., user‑generated queries) were collected beyond the public benchmark, and that any such data would be handled under appropriate consent.

**Summary** – The core idea is promising, but the manuscript must address privacy, content‑moderation, licensing compliance, and dual‑use considerations before it can be accepted. The requested revisions are primarily textual (adding discussion) and experimental (evaluating filtering), thus classified as *writing* and *science* severity items. Once these concerns are resolved, the paper will be better aligned with responsible AI deployment standards.
