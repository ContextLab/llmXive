---
action_items:
- id: 404d5703e7fd
  severity: science
  text: "Expand the safety evaluation suite beyond HarmBench (\u2193) and XSTest.\
    \ Include adversarial jailbreak tests, red\u2011team probing, and robustness checks\
    \ for code\u2011generation misuse."
- id: 2c04e7398f55
  severity: writing
  text: "Provide a detailed discussion of dual\u2011use risks associated with open\u2011\
    weight code\u2011generation, tool\u2011use, and long\u2011context capabilities,\
    \ and outline concrete mitigation strategies (e.g., usage policies, content filters)."
- id: 90efdead25d0
  severity: science
  text: "Explain the observed safety regression after RL (HarmBench score rising from\
    \ 8.4\u202F% to 23.1\u202F%). Include analysis of reward shaping effects and any\
    \ corrective steps taken (e.g., KL anchoring, safety\u2011oriented reward terms)."
- id: b6592e8dc599
  severity: writing
  text: "Document any post\u2011training safety mitigations (e.g., refusal modules,\
    \ alignment checks) that will be deployed in the released checkpoints, and provide\
    \ evidence of their effectiveness."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:36:24.787602Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents Mellum 2, a 12 B‑parameter MoE model with advanced long‑context and tool‑use capabilities. From a safety and ethics standpoint, several concerns arise that need to be addressed before the work can be accepted.

**Safety regression after RL** – The authors report a marked increase in HarmBench violations after the reinforcement‑learning stage (from 8.4 % to 23.1 %). This regression is noted only in a single sentence (see Table \ref{tab:posttrain-eval-instruct-repr}) without any analysis of why the RL reward shaping caused the model to become less safe. Given that RLVR is used with no KL‑anchoring to the SFT policy, the model may drift toward unsafe behaviours. A thorough investigation (e.g., ablation of the concision penalty, inspection of generated unsafe content) is required, and any remedial measures should be documented.

**Limited safety evaluation** – The paper evaluates safety on only two benchmarks (HarmBench and XSTest). Modern safety assessments typically include a broader suite (jailbreak robustness, red‑team adversarial prompts, toxicity, privacy leakage, and code‑generation misuse). The current evaluation does not provide confidence that the model is safe for open release, especially given its strong code‑generation and tool‑use abilities.

**Dual‑use and release policy** – Mellum 2 is released under Apache 2.0 with no explicit usage restrictions. The model’s ability to generate executable code, perform tool‑use, and handle very long contexts can be leveraged for malicious purposes (e.g., automated exploit generation, large‑scale phishing, or facilitating cyber‑attacks). The manuscript lacks a discussion of these dual‑use risks, responsible‑AI guidelines, or any technical safeguards (content filters, refusal modules) that will accompany the public checkpoints.

**Reward shaping and safety** – The RL stage introduces a “conciseness penalty” that reduces reward for trigger words (e.g., “wait”, “actually”). While this improves brevity, it may inadvertently suppress safety‑related warnings or refusals. The paper does not analyze potential conflicts between this penalty and safety behaviours, nor does it describe any safety‑specific reward terms.

**Transparency of safety mitigations** – The release notes state that checkpoints are provided “publicly,” but there is no mention of any post‑training safety fine‑tuning, alignment checks, or monitoring infrastructure that would be required for a model with these capabilities. Stakeholders need assurance that the released model will not be deployed in contexts where it could cause harm without appropriate safeguards.

**Recommendations** – To satisfy safety‑ethics criteria, the authors should (1) broaden the safety evaluation, (2) provide a detailed post‑RL safety analysis and remediation plan, (3) discuss dual‑use implications and outline a responsible release strategy, and (4) disclose any safety‑oriented fine‑tuning or runtime filters that will accompany the model. Addressing these items will substantially improve the manuscript’s ethical robustness.
