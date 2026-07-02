---
action_items:
- id: e968d48b60b3
  severity: writing
  text: 'The paper addresses a critical safety issue in Document Intelligence: the
    risk of "Attribution Hallucination" where models provide correct answers based
    on incorrect evidence, which is particularly dangerous in high-stakes domains
    like law and medicine. The proposed benchmark, CiteVQA, is a significant step
    toward safer AI deployment. However, several ethical and safety concerns regarding
    data provenance, privacy, and labor practices require clarification before acceptance.
    First, regarding data'
artifact_hash: 567bb319ad9aec08be02c875d29027d6ab5aa636652eb3a41f2a0b1e3b7ef794
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:16:07.195806Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses a critical safety issue in Document Intelligence: the risk of "Attribution Hallucination" where models provide correct answers based on incorrect evidence, which is particularly dangerous in high-stakes domains like law and medicine. The proposed benchmark, CiteVQA, is a significant step toward safer AI deployment. However, several ethical and safety concerns regarding data provenance, privacy, and labor practices require clarification before acceptance.

First, regarding **data copyright and provenance**, Section 3.1 states that 711 documents were sourced from Common Crawl. While the authors cite adherence to the Robots Exclusion Protocol and a takedown policy in Appendix A, this is insufficient for a benchmark intended for public release. The paper must explicitly confirm that the specific 711 documents selected do not violate copyright laws or that their use falls under fair use for research. The current "takedown upon request" model is reactive and does not guarantee the safety of the dataset at the time of publication. A proactive statement on the legal basis for using these specific documents is required.

Second, **privacy concerns** are not adequately addressed. The dataset includes documents from "Medical & Health" and "Gov & Legal" domains (Table 1, Appendix 5.2). There is no mention of whether these documents were screened for Personally Identifiable Information (PII) or Protected Health Information (PHI). Releasing a benchmark containing unredacted medical records or legal documents could lead to severe privacy violations. The authors must confirm that all PII/PHI has been removed or that the documents are strictly public records with no privacy implications.

Third, **labor ethics** need more transparency. Appendix 5.1 mentions that human experts were compensated with an honorarium exceeding the local minimum wage. However, it does not specify the exact rate, the currency, or the total hours worked. To ensure fair labor practices and allow for reproducibility of the ethical standard, these specific details must be included in the manuscript.

Finally, the **environmental impact** of the data construction pipeline is overlooked. The automated pipeline uses multiple LLM passes (masking ablation, template distillation, verification) to generate ground truth for 1,897 samples. The computational cost and associated carbon footprint of this process are significant. An environmental impact statement or an estimate of the energy consumption is necessary to align with modern sustainability standards in AI research.

Addressing these points will ensure the benchmark is not only technically robust but also ethically sound and legally defensible.
