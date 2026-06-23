---
action_items:
- id: fbc825832fe2
  severity: writing
  text: "The manuscript inherits the teacher\u2019s biases and the dataset\u2019s\
    \ spurious correlations without any mitigation strategy; add a dedicated bias\u2011\
    analysis section and discuss mitigation (e.g., debiasing prompts, safety\u2011\
    aligned fine\u2011tuning)."
- id: bfe6ef3c2a3c
  severity: writing
  text: "The reward signal optimises only for answer correctness and explicitly states\
    \ it does not address safety or fairness; incorporate at least one safety\u2011\
    oriented evaluation (e.g., toxicity, harmful content) to demonstrate that ZPPO\
    \ does not exacerbate unsafe behaviours."
- id: f8322551ac81
  severity: writing
  text: "Potential dual\u2011use risk: improving small VLM/LLM capabilities can lower\
    \ the barrier for malicious actors; include a brief discussion of misuse scenarios\
    \ and recommended safeguards for deployment."
- id: d2431d288fcd
  severity: writing
  text: "The data used for ZPPO\u201177K multimodal RL corpus is not described in\
    \ detail; verify that no personally identifiable information (PII) or copyrighted\
    \ content is present, and add a data\u2011privacy statement."
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:02:56.823714Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper introduces Zone of Proximal Policy Optimization (ZPPO), a novel RL‑based distillation technique that places teacher knowledge inside prompts (BCQ/NCQ) rather than gradients. From a safety‑and‑ethics perspective the work raises several concerns that should be addressed before acceptance.

First, the authors acknowledge that “ZPPO builds on publicly released Qwen3.5 models; any upstream biases are inherited” (Section 7). However, no systematic analysis of these biases is provided, nor are any mitigation strategies explored. Given that the teacher model is large (27 B) and trained on massive web corpora, it likely encodes harmful stereotypes and misinformation. The BCQ/NCQ prompts could inadvertently amplify such biases when the student learns to imitate teacher responses. A bias‑analysis (e.g., measuring gender, racial, or toxic content leakage) and a discussion of mitigation (prompt filtering, safety‑aligned fine‑tuning) are essential.

Second, the reward function is defined purely in terms of answer correctness (Section 6, “Rule‑based reward grader”). The authors explicitly state that “the reward signal targets answer correctness only and does not mitigate safety or fairness concerns.” This design choice leaves open the possibility that ZPPO‑trained students may produce more fluent but equally unsafe outputs. Adding a safety‑oriented evaluation—such as toxicity scoring, refusal rates on harmful queries, or alignment with a safety‑aligned judge—would demonstrate that the method does not worsen unsafe behaviour.

Third, the paper does not discuss dual‑use implications. By enabling compact VLM/LLM models (0.8 B–9 B) to approach the performance of a 27 B teacher, ZPPO lowers the computational barrier for deploying capable multimodal agents. This could be exploited for disinformation, automated phishing, or other malicious applications. A brief “Broader Impact / Misuse” paragraph outlining plausible threats and recommended safeguards (e.g., controlled release, usage monitoring) would align the work with community standards.

Finally, the dataset used for training (ZPPO‑77K multimodal RL corpus) is mentioned only in passing (Appendix A). The manuscript should confirm that the corpus contains no PII, copyrighted material, or other privacy‑sensitive content, and provide a data‑privacy statement consistent with IRB/IACUC expectations for non‑human data.

Addressing these points—bias analysis, safety evaluation, misuse discussion, and data‑privacy clarification—will substantially improve the ethical robustness of the submission without requiring new experimental pipelines.
