---
action_items:
- id: 3e43c4a723a7
  severity: writing
  text: "Clarify the description of the Index Branch architecture \u2013 it uses one\
    \ query head per GQA group and a single shared key head, not a single lightweight\
    \ head as stated in the abstract (Fig.\u202F1)."
- id: 047b306fea65
  severity: writing
  text: "Temper the claim that 1\u202FM\u2011token context is the \u2018binding deployment\
    \ constraint\u2019 for all production settings; provide empirical context or rephrase\
    \ to avoid overgeneralisation."
- id: 03d09410904b
  severity: writing
  text: "In the conclusion, the statement that MSA \u2018preserves capability across\
    \ most pretraining and agentic benchmarks\u2019 should be qualified to acknowledge\
    \ the few benchmarks (e.g., MMMU, RULER\u201132K for PT) where performance is\
    \ modestly lower than the full\u2011attention baseline."
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:26:54.186188Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript largely stays within the scope of its experimental evidence, but there are a few instances where the wording stretches beyond what the presented data directly support.

1. **Index Branch description (Abstract & Fig. 1)** – The abstract claims the Index Branch “scores the full causal context with a single lightweight head.” However, Section 3.1 (Eq. 2) defines one query head per GQA group (i.e., \(H_{kv}\) heads) and a single shared key head. This is more than a single head and should be described accurately to avoid misinterpretation.

2. **Binding deployment constraint** – The statement in the abstract and conclusion that “1 M‑token context … becomes the binding deployment constraint” is a strong generalisation. The paper provides speed‑up measurements at 1 M tokens but does not present deployment‑level cost analyses across varied hardware or application scenarios. Re‑phrasing to indicate that 1 M tokens are a *common* or *representative* long‑context regime would keep the claim grounded.

3. **“Preserves capability across most benchmarks”** – Table 4 shows that on several benchmarks (e.g., MMMU, RULER‑32K for the PT variant) the sparse models fall slightly behind the full‑attention baseline. While the overall trend is competitive, the claim should be qualified (e.g., “remains competitive on the majority of evaluated tasks”) to acknowledge these exceptions.

4. **KL‑alignment and gradient detachment** – The paper correctly explains that the KL loss is detached from the backbone (Eq. 7) and that this prevents gradient leakage. The experimental ablations (Fig. 7, Fig. 8) support the necessity of this design, so no over‑claim is identified here.

5. **Efficiency numbers** – The FLOP reduction of 28.4× at 1 M tokens (Fig. 13) matches the reported theoretical analysis. The wall‑clock speed‑ups (14.2× prefill, 7.6× decode) are also demonstrated, so the efficiency claims are well‑substantiated.

Overall, the paper’s central contributions are supported by the presented experiments and analyses. Addressing the three writing‑level issues above will eliminate the minor over‑reach concerns and improve the manuscript’s precision.
