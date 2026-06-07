---
action_items:
- id: 0797277bac16
  severity: writing
  text: Explicitly state IRB approval or exemption status for human expert evaluation
    described in Appendix 'Details of Expert Evaluation'.
- id: 6bc26de57319
  severity: writing
  text: Clarify if Personally Identifiable Information (PII) scrubbing was performed
    on Common Crawl documents prior to benchmark construction.
- id: e16b6109c00a
  severity: writing
  text: Provide a direct URL or contact method for the copyright takedown process
    mentioned in Appendix 'Ethical Consideration'.
artifact_hash: 343bba3cbfbb16bee3f79c8a33c3a51555292623f2cdbd016ca7ae51e6fbc39c
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T21:40:57.236082Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety, ethics, and compliance regarding the CiteVQA benchmark.

**Human Subject Compliance**
The Appendix "Details of Expert Evaluation" states that PhD-level experts were recruited for sampling audits and compensated. However, the manuscript does not explicitly reference Institutional Review Board (IRB) approval or exemption status for this human evaluation work. Standard academic ethics require documentation of IRB oversight or a formal exemption determination when human subjects are involved in research, even for expert annotation. This should be added to the Appendix to ensure compliance with institutional and conference review standards.

**Data Privacy and PII**
The "Data Compliance & Ethics Statement" in the Appendix confirms data is sourced from Common Crawl. While adherence to Terms of Use is noted, there is no explicit mention of Personally Identifiable Information (PII) scrubbing or redaction processes for the 711 selected PDF documents. Given that Common Crawl can contain sensitive personal data, and the benchmark targets high-stakes domains (legal, medical), the authors should clarify whether PII was filtered to prevent potential privacy violations in the released metadata or coordinates.

**Copyright and Distribution**
The authors state they distribute "public download links" rather than the PDFs themselves to respect copyright. This is a sound mitigation strategy. However, the text mentions a takedown process ("please contact us") without providing a specific email address or URL in the Appendix. To ensure transparency and enforceability of rights holder claims, a direct contact mechanism should be published in the repository and the paper.

**Evaluation Judges**
The evaluation relies on LLM judges (e.g., Qwen3-VL-235B). While validated against human experts, the Appendix does not discuss potential biases inherent in these proprietary models that could skew safety-related metrics. A brief discussion on the limitations of using LLM judges for safety-critical attribution tasks would strengthen the ethical rigor of the evaluation protocol.

Overall, the paper demonstrates strong ethical awareness but requires specific clarifications on IRB status and data privacy handling to meet full compliance standards.
