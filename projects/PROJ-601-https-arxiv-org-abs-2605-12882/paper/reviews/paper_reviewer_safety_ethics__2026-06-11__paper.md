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
reviewed_at: '2026-06-11T04:43:58.075549Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This re-review confirms that the three prior action items regarding safety and ethics compliance remain unaddressed in the current revision. While the manuscript has been updated in other areas, the specific ethical disclosures required for publication standards have not been sufficiently clarified.

1.  **IRB Status (Item 0797277bac16):** In Appendix `Details of Expert Evaluation`, the authors describe inviting PhD-level experts for sampling audits and mention compensation. However, there is still no explicit statement regarding Institutional Review Board (IRB) approval or an exemption status. For research involving human participants (even for evaluation/annotation), standard academic ethics require this declaration to ensure participant protection and ethical compliance. Please add a sentence confirming the IRB status (e.g., "IRB approval was obtained from [Institution]" or "This study was exempt from IRB review because...").

2.  **PII Scrubbing (Item 6bc26de57319):** The `Ethical Consideration` section and `Document Collection` subsection state that documents are sourced from Common Crawl. Common Crawl datasets frequently contain personal information. The manuscript currently lacks a clear statement confirming whether Personally Identifiable Information (PII) was scrubbed or redacted from these documents before inclusion in the CiteVQA benchmark. To mitigate privacy risks, please explicitly state the data cleaning procedures regarding PII (e.g., "All PII was automatically redacted using [Tool] prior to annotation").

3.  **Copyright Takedown Contact (Item e16b6109c00a):** The `Ethical Consideration` section mentions that rights holders should "contact us" regarding takedown requests but does not provide a specific contact method (email address) or a direct URL to a takedown form. This vagueness hinders compliance with copyright holders' rights. Please update the text to include a specific email address (e.g., `copyright@citevqa.org`) or a link to a dedicated takedown page in the repository.

Addressing these points is necessary to ensure the benchmark meets responsible AI and data privacy standards.
