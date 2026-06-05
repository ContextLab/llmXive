---
action_items:
- id: 0ddd287db7df
  severity: writing
  text: The paper lacks a conflict of interest statement. Multiple authors are affiliated
    with ByteDance Seed, and Seed 2.0 is used extensively for data synthesis (Sec
    4.1-4.2). Disclose commercial relationships and potential bias from proprietary
    model usage."
- id: cabcfb75efe6
  severity: writing
  text: Data provenance and privacy concerns are not addressed. The 1.5M document
    pool includes academic papers, books, and manuals (Sec 4.1) but no discussion
    of copyright licensing, personal data filtering, or how sensitive information
    was removed from training data."
- id: 95940b4dbf7e
  severity: writing
  text: The Broader Impact section (app:broader_impact) discusses benefits but omits
    potential misuse scenarios. Long-context VQA models could enable automated extraction
    of sensitive information from large document collections. Add discussion of dual-use
    risks and mitigation strategies."
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T10:56:20.350415Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This paper raises several safety and ethics concerns that require attention before publication:

**1. Conflict of Interest (Section 1, Authors)**
Multiple authors are affiliated with ByteDance Seed, and the paper extensively uses Seed 2.0 for data synthesis (Sections 4.1-4.2). No conflict of interest statement is provided. Given the commercial nature of the models used and the training recipe potentially benefiting ByteDance's products, this disclosure is necessary for transparency.

**2. Data Provenance and Privacy (Section 4.1)**
The 1.5M PDF document pool includes "academic papers, books, manuals (engineering, medicine, etc.)" but there is no discussion of:
- Copyright/licensing status of source documents
- Whether personally identifiable information (PII) was filtered
- How medical or proprietary documents were handled to avoid privacy violations

The paper mentions "Filter overlap with benchmarks via SHA-256" but this only addresses benchmark contamination, not privacy concerns.

**3. Human Verification Process (Appendix: Human Verification)**
Manual verification of 100 QA pairs was conducted. While this involves minimal human labor, no IRB approval or consent process is mentioned. For complete ethical compliance, this should be documented even for small-scale human annotation tasks.

**4. Dual-Use Risks (Broader Impact Section)**
The Broader Impact section (app:broader_impact) focuses exclusively on benefits. Long-context vision-language models could enable:
- Automated extraction of sensitive information from large document collections (e.g., medical records, legal documents)
- Surveillance applications analyzing extensive visual-textual data
- Privacy-violating information retrieval from public/private document repositories

A more balanced discussion of potential misuse scenarios and recommended safeguards would strengthen the ethical framework.

**5. Evaluation Bias**
The paper uses LLM-based judging for evaluation (Appendix: Evaluation Details). No discussion of potential bias introduced by using proprietary models (Seed 2.0, GPT-5) for evaluation, which could favor certain model families or introduce systematic errors.

These issues are primarily documentation gaps that can be addressed through manuscript revisions without requiring new experiments.
