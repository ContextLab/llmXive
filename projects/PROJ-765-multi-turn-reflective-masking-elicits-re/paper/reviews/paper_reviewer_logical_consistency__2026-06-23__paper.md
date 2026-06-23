---
action_items:
- id: ee2773bbe603
  severity: writing
  text: "The paper states that no architectural changes are required, yet it introduces\
    \ History Reference (HR) and History Embedding Rotation (HER), which add a per\u2011\
    position accumulated embedding and modify the model\u2019s input. This contradicts\
    \ the \u201Cno architectural changes\u201D claim. Clarify whether HR/HER are considered\
    \ architectural changes and adjust the claim accordingly."
- id: 1e5bdb457750
  severity: science
  text: "Eq.\u202F1\u2019s inference rule re\u2011masks a token whenever p(MASK) >\
    \ p(current token). The manuscript does not discuss that this can trigger re\u2011\
    masking for correct but uncertain tokens, potentially causing loops. Explain how\
    \ the rule avoids such spurious revisions or add a confidence safeguard."
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:21:37.325164Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a coherent theoretical framework: Theorem 1 shows that minimizing the per‑position cross‑entropy loss recovers the conditional distribution of the oracle revision action, and Theorem 2 bounds the excess 0‑1 risk by twice the total‑variation distance. Proposition 3 correctly argues that conditioning on additional history cannot increase Bayes risk, and the empirical sections (image editing, Sudoku, text reasoning) report results that are consistent with these claims.

Nevertheless, a logical inconsistency arises around the “no architectural changes” claim. While the abstract and introduction (Section 1) emphasize that the method can be applied to existing Mask Diffusion Models without modifying their architecture, the proposed History Reference (HR) mechanism (Section 3.2) requires computing an accumulated embedding (Eq. 2) and feeding it to the model at each step. Even though HER is parameter‑free, it changes the model’s input pipeline and adds a new computational component, which constitutes an architectural modification in the broader sense. This contradiction weakens the paper’s positioning and should be resolved by either redefining what is meant by “no architectural changes” or revising the claim.

A second logical gap concerns the inference rule (Eq. 1 in Section 3.1). The rule re‑masks a token whenever the model assigns higher probability to the MASK token than to the current token. The paper does not discuss the scenario where a correct token is simply uncertain, leading to unnecessary re‑masking and possible loops, especially in early denoising steps. While the History Reference is later presented as a stabilizing factor, the manuscript should explicitly state why the rule does not cause spurious revisions, or introduce a confidence threshold to prevent re‑masking of merely uncertain tokens.

Overall, the theoretical arguments are internally consistent and the experiments support the hypotheses. Addressing the architectural‑change claim and clarifying the robustness of the inference rule will eliminate the remaining logical inconsistencies.
