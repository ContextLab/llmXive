---
action_items:
- id: c65e0476019b
  severity: writing
  text: Add an explicit statement confirming EywaBench construction complies with
    source dataset licenses and introduces no new human subject data, especially for
    'clinic' and 'drug' domains.
- id: e28a3d95dada
  severity: writing
  text: Include a clear disclaimer that Eywa is not for clinical decision-making and
    that utility scores do not validate safety for real-world patient care in medical
    sub-domains.
- id: 68ae2e4bd403
  severity: writing
  text: Clarify the provenance of 'gpt-5-nano' and 'gpt-5-mini'. If unreleased, replace
    with verifiable models to ensure reproducibility and safety auditing.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T23:51:19.816226Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a novel framework for integrating domain-specific foundation models into agentic systems. However, from a safety and ethics perspective, several areas require clarification.

First, the construction of **EywaBench** involves aggregating data from sources including "clinic" and "drug" domains (Appendix `1_appendix/data_analysis.tex`). The paper lacks an explicit statement confirming that this aggregation complies with original data licenses and introduces no new human subject data. An explicit confirmation is necessary to ensure ethical compliance.

Second, the inclusion of **medical tasks** raises dual-use risks. The paper must explicitly state that the system is not intended for clinical decision-making. The current evaluation metrics (utility scores) do not validate safety or reliability for real-world patient care. A dedicated disclaimer in the "Limitations" section is required to mitigate misuse risks.

Third, the use of **hypothetical model names** like "gpt-5-nano" (Section 5.2) is concerning. If these are internal or unreleased models, their use obscures potential safety issues. The authors must clarify their provenance or replace them with verifiable public models to ensure reproducibility and independent safety auditing.

Finally, the paper does not address the **safety of the "Tsaheylu" interface**. If an LLM is misaligned, it could instruct foundation models to perform harmful actions. A brief discussion on safeguards or constraints within the interface to prevent such misuse would strengthen the safety profile of the work.
