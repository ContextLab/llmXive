---
action_items:
- id: 43478b97e303
  severity: writing
  text: The paper reports a significant safety regression in the RL-trained 'Instruct'
    variant (HarmBench score increases from 8.4% to 23.1%, Section Post-Training Evaluation).
    The authors must explicitly discuss the mechanism of this degradation and provide
    a mitigation strategy or a clear warning for users deploying the RL variant in
    sensitive environments.
- id: 6a5a30235828
  severity: writing
  text: The 'Thinking' variant is trained on a mix including 'Reasoning' and 'Math'
    with RLVR. The paper does not address the risk of these models generating harmful
    content within their 'reasoning traces' (chain-of-thought) which might be visible
    to users or logged, potentially bypassing standard safety filters that only inspect
    final outputs.
- id: 2f486c25178e
  severity: writing
  text: The RL data mix includes 'Agentic tool use' and 'Code' with programmatically
    verifiable rewards. The authors must clarify if the code execution sandbox used
    for reward verification is fully isolated to prevent the model from executing
    malicious payloads (e.g., data exfiltration, system compromise) during the training
    loop itself.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:31:14.635823Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a technical report on the Mellum2 model, an open-weight MoE language model. From a safety and ethics perspective, the paper is generally transparent about its training pipeline and evaluation metrics, including specific safety benchmarks (HarmBench, XSTest). However, there are critical omissions regarding the interpretation of safety results and the potential risks associated with the model's specific capabilities.

First, the "Post-Training Evaluation" section (Section 5) explicitly notes a safety regression: the HarmBench refusal rate drops significantly (score increases from 8.4% to 23.1%) after Reinforcement Learning (RL) is applied to the Instruct variant. While the authors report this number, they do not provide an analysis of *why* this degradation occurred or how it impacts the model's deployment safety. Given that the model is released under Apache 2.0, users need a clear warning that the RL-tuned variant may be more susceptible to jailbreaking or generating harmful content compared to the SFT-only base. This requires a dedicated discussion in the safety section or a prominent disclaimer in the model card.

Second, the paper introduces a "Thinking" variant that emits reasoning traces. The RLVR process involves optimizing for these traces. There is a potential dual-use risk where the model might learn to generate harmful reasoning steps (e.g., planning a cyberattack or detailing a chemical synthesis) that are technically "correct" according to the reward function but ethically problematic. The paper does not discuss whether the safety filters or the reward model specifically penalize harmful content *within* the reasoning trace, or if the "Thinking" variant is more prone to leaking such content than standard models.

Third, the RL infrastructure relies on a "Verification stack" that includes code execution (Section 4.3.2). While the paper mentions a "decoupled" stack, it lacks details on the security of the execution environment. If the model is rewarded for generating code that passes tests, there is a risk it could generate code that performs malicious actions (e.g., network calls, file system manipulation) if the test harness is not strictly sandboxed. The authors should confirm that the code execution environment is air-gapped or strictly sandboxed to prevent the training loop itself from being a vector for harm.

Finally, the data composition includes "Identity examples (oversampled 3x to prevent misidentification as Google AI)" (Section 4.1.1). While this addresses a specific identity issue, the paper does not discuss the broader data privacy implications of the pre-training corpus (10.6T tokens) or the SFT data, particularly regarding the potential inclusion of personally identifiable information (PII) or copyrighted code. A brief statement on data filtering for PII and copyright compliance would strengthen the ethical standing of the report.
