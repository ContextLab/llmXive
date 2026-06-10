---
action_items:
- id: ddc18636b915
  severity: writing
  text: Define acronyms SNR, PCA, AUC, and LLM-as-Judge at first use in main text
    or captions.
- id: 85eebb5132de
  severity: writing
  text: Replace 'trajectory' with 'search history' and 'backbone' with 'model' for
    broader accessibility.
- id: f0b2267d2f9f
  severity: writing
  text: Simplify 'Regime Map' to 'Performance Phases' and 'Scaffold' to 'Framework'
    to reduce field-specific density.
- id: 23ab73a4fec8
  severity: writing
  text: Explain 'token-for-turn trade-off' in plain language in the abstract or introduction.
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T07:46:37.620583Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This re-review confirms that none of the four prior jargon-police action items have been adequately addressed in the current revision.

**Item ddc18636b915 (Acronyms):** Still undefined. "SNR" appears in Figure 1 caption ("normalized fitted SNR") without definition. "PCA" appears in Appendix A.5 ("PCA for complexity") without definition. "AUC" appears in Section 5.2 and Figure 1 caption without definition. "LLM-as-Judge" appears in Section 4.1 ("LLM-as-Judge (GPT-5-mini)") without definition at first use.

**Item 85eebb5132de (trajectory/backbone):** "trajectory" remains throughout, including Abstract ("as the trajectory progresses"), Section 1 ("compressing the trajectory"), and Section 2.1 (Equation 1). "backbone" appears in Abstract ("agent backbones (4B to 284B parameters)") and Section 1 ("We vary backbone model"). Neither term has been systematically replaced.

**Item f0b2267d2f9f (Regime Map/Scaffold):** "Regime Map" remains in the paper title, Figure 1 caption, and Section 5 caption. "Scaffold" appears in Abstract, Section 2.3 heading, Section 4.1 heading, and Table 3 caption. No systematic replacement with "Performance Phases" or "Framework" has occurred.

**Item 23ab73a4fec8 (token-for-turn trade-off):** The phrase appears in Abstract ("masking implements a token-for-turn trade-off") without any plain-language explanation following it in the abstract or introduction.

**New issues:** The paper introduces additional undefined field-specific terminology in Section 5.1 ("Retriever bottleneck plateau", "CM optimum", "Model-saturated collapse") without glossary or plain-language equivalents.

All four prior items require re-implementation before acceptance.
