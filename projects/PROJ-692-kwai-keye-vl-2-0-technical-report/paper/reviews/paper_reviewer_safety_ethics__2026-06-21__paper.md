---
action_items:
- id: 5b9aafde4cdb
  severity: writing
  text: "Add a dedicated safety and ethics section (\u22481\u202Fpage) that discusses\
    \ potential dual\u2011use risks of the model\u2019s agentic, code\u2011generation,\
    \ and long\u2011video capabilities, and outlines concrete mitigation measures\
    \ (e.g., usage policy, red\u2011team testing, content filters)."
- id: e55a94b44cc2
  severity: science
  text: "Provide a data\u2011privacy audit for the pre\u2011training corpus (DataComp,\
    \ LAION, CC12M, PD12M, COCO) confirming that personal data were removed or consented,\
    \ and cite any relevant IRB or data\u2011use approvals."
- id: 836f14cc382c
  severity: science
  text: "Include quantitative evaluation of harmful content generation (e.g., toxicity,\
    \ disinformation, deep\u2011fake video synthesis) and report failure cases, especially\
    \ for the agentic RL and tool\u2011use pipelines described in Section\u202F4.3\
    \ and the multi\u2011domain service case (Fig\u202F13)."
- id: 2bd9bb46925f
  severity: writing
  text: "Specify a responsible\u2011release plan (e.g., model\u2011card, licensing,\
    \ access controls) and describe how downstream developers are required to enforce\
    \ safety constraints when deploying the model for code or tool use."
- id: a06de2490a0b
  severity: fatal
  text: "Clarify whether any human\u2011in\u2011the\u2011loop data (e.g., user profiles\
    \ used in the multi\u2011domain service case) were collected with informed consent\
    \ and IRB approval; if not, remove or anonymize such examples."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:52:36.587203Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents an impressive multimodal MoE model with 256 K token context and extensive agentic capabilities (Sections 3–5, especially the Cross‑Modal Multi‑Teacher On‑Policy Distillation and the multi‑domain service orchestration case in Figure 13). From a safety‑and‑ethics perspective, several critical gaps need to be addressed before the work can be accepted.

1. **Dual‑use and misuse potential** – The model’s ability to generate code, invoke external APIs, and orchestrate multi‑step transactions (Section 4.3, Figure 13) raises clear dual‑use concerns. An adversary could exploit these capabilities for automated phishing, credential‑stealing, or large‑scale disinformation campaigns. The paper currently lacks any discussion of these risks or of safeguards (e.g., rate‑limiting, API‑access controls, or verification of tool outputs).

2. **Content‑moderation and harmful generation** – While the authors claim “hallucination‑resistance” (Conclusion) and report strong performance on benchmarks, there is no systematic evaluation of toxic or unsafe outputs, especially for the RL‑trained agents that receive reward signals from execution outcomes. A safety‑focused benchmark (e.g., toxicity, privacy leakage, or deep‑fake generation) should be included, and failure cases should be reported.

3. **Data privacy and consent** – The pre‑training data sources (DataComp, LAION, CC12M, PD12M, COCO) are massive web‑scraped corpora that may contain personal information. The manuscript does not mention any privacy audit, de‑identification steps, or IRB/ethical review for handling such data. Given the model’s ability to retrieve and synthesize long‑range contextual information, the risk of unintentionally memorizing and regurgitating private data is non‑trivial.

4. **Responsible release and licensing** – The paper states that “model checkpoints are released” (Abstract) but provides no model‑card, licensing terms, or usage restrictions. Open‑source release of a 30 B‑class agentic model without clear governance can accelerate misuse. The authors should adopt a responsible‑release framework (e.g., a detailed model‑card, restricted API access, or a tiered licensing scheme) and explicitly require downstream users to implement safety filters.

5. **Human‑subject considerations** – The multi‑domain service case includes a user profile and personal preferences (Section Appendix Case VI). It is unclear whether this example is synthetic or derived from real user data. If real, informed consent and IRB approval are required; otherwise, the example should be anonymized or replaced with a fully synthetic scenario.

6. **Alignment verification** – The Cross‑Modal Multi‑Teacher On‑Policy Distillation (Section 4.2) aligns the student to 13 specialized teachers, but the safety of those teachers (e.g., whether they have been vetted for harmful behavior) is not described. A brief audit of teacher models and the alignment loss design would strengthen the safety claim.

In summary, the technical contributions are strong, but the manuscript currently omits essential safety, privacy, and ethical considerations. Addressing the action items above—particularly adding a dedicated safety‑and‑ethics discussion, providing privacy audits, evaluating harmful content generation, and defining a responsible release policy—will bring the work in line with community standards for high‑impact multimodal models.
