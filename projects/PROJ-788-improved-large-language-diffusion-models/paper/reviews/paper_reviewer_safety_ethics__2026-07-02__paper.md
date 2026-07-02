---
action_items:
- id: 0c19c4ae3bb5
  severity: writing
  text: The manuscript lacks a dedicated 'Ethics Statement' or 'Safety Considerations'
    section. Given the model's strong performance on code generation (HumanEval, MBPP)
    and reasoning benchmarks, authors must explicitly discuss potential dual-use risks
    (e.g., generating malicious code, phishing, or disinformation) and mitigation
    strategies employed during training or inference.
- id: c4aab4beea35
  severity: writing
  text: The paper mentions training on a 12T token corpus and a 25B token instruction
    set but does not specify the data sources, filtering criteria for harmful content,
    or whether human data privacy/consent was considered. A brief description of data
    curation protocols regarding safety and privacy is required.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T10:45:16.085532Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents iLLaDA, a large-scale diffusion language model, but currently lacks sufficient transparency regarding safety and ethical considerations, which is critical for models with demonstrated capabilities in code generation and complex reasoning.

**Data Privacy and Curation:**
The paper states in Section 2.1 and 2.2 that the model was pre-trained on 12 trillion tokens and fine-tuned on a 25 billion token instruction corpus. However, it does not disclose the provenance of these datasets, the methods used to filter out personally identifiable information (PII), or the protocols for handling copyrighted or sensitive data. Without a description of data curation pipelines (e.g., deduplication, PII redaction, or exclusion of harmful content), it is impossible to assess compliance with data privacy norms or the risk of the model memorizing and regurgitating sensitive information.

**Dual-Use and Harm Potential:**
The results in Table 1 and Table 2 demonstrate significant improvements in code generation (HumanEval, MBPP) and mathematical reasoning. These capabilities inherently carry dual-use risks, such as the automated generation of malware, exploit code, or sophisticated social engineering prompts. The manuscript currently treats these benchmarks purely as performance metrics without addressing the safety implications. The authors should include a discussion on how the model might be misused and what safeguards (e.g., RLHF for safety, refusal mechanisms, or output filtering) are planned or implemented.

**Missing Ethics Statement:**
There is no dedicated section (e.g., "Ethics Statement," "Broader Impact," or "Safety Considerations") in the main text or appendix. Standard practice for large language model papers requires an explicit statement addressing potential harms, bias mitigation, and the responsible release of model weights. The absence of this section prevents a full evaluation of the authors' commitment to safe AI development.

To proceed, the authors must add a section detailing their data safety protocols, potential dual-use risks, and mitigation strategies.
