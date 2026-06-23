---
action_items:
- id: dd1c64438b89
  severity: writing
  text: "The statement in the abstract and introduction that \u201Cexisting MDMs do\
    \ not support multi\u2011turn masking and denoising\u201D is presented without\
    \ citation and may over\u2011state the prior art (e.g., RemeDi\u202F\\citep{huang2025don}\
    \ already explores multi\u2011turn remasking). Add a citation or qualify the claim\
    \ to avoid factual inaccuracy."
- id: ff068cbad12c
  severity: writing
  text: "Experimental results claim superiority over \u201Cstandard masking\u2011\
    based baselines\u201D but only compare against Lumina and its SFT variant. To\
    \ substantiate the claim, include comparisons to other recent multi\u2011turn\
    \ or remasking MDM approaches (e.g., Wang\u202F2025\u202F\\citep{wang2025remasking},\
    \ Huang\u202F2025\u202F\\citep{huang2025don}) or explicitly state that such baselines\
    \ were not evaluated."
- id: d784d5f08619
  severity: writing
  text: "The paper asserts that the proposed method \u201Crequires no architectural\
    \ changes\u201D while introducing the History Reference mechanism that adds a\
    \ per\u2011position accumulated embedding and rotation operations. Clarify that\
    \ this is a purely algorithmic addition without new learnable parameters, and\
    \ cite the relevant implementation details (Appendix\u202F\\ref{app:rope-engineering})\
    \ to support the claim."
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:21:57.339357Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript’s factual statements are largely supported by the cited literature, and the theoretical results (Theorems 1–2, Propositions 1–3) correctly reference standard sources such as Gneiting 2007 for proper scoring rules and Devroye et al. 2013 for excess‑risk bounds. The derivations in the appendix are internally consistent, and the experimental tables are clearly linked to the described metrics.

However, three specific claims require clarification to ensure factual accuracy:

1. **Over‑generalized claim about prior MDMs** – The abstract and introduction assert that “existing MDMs do not support multi‑turn masking and denoising.” This is not substantiated with a citation and conflicts with recent work (e.g., RemeDi \citep{huang2025don} and Wang 2025 \citep{wang2025remasking}) that already explore multi‑turn remasking. The authors should either qualify the statement (e.g., “most existing MDMs lack native multi‑turn revision”) or provide appropriate citations.

2. **Baseline comparison scope** – The experiments repeatedly claim “consistent improvement over standard masking‑based baselines,” yet only Lumina and its SFT variant are reported. To back this claim, the paper should either add comparisons to other state‑of‑the‑art multi‑turn or remasking approaches (such as the aforementioned RemeDi and Wang 2025) or explicitly limit the claim to the baselines evaluated.

3. **Architectural‑change assertion** – The manuscript emphasizes that the method “requires no architectural changes,” while introducing the History Reference mechanism that adds an accumulated embedding and rotation operations (see Appendix \ref{app:rope-engineering}). Although no new learnable parameters are introduced, this is an algorithmic extension. The authors should clarify that the change is purely procedural and cite the implementation details to avoid misinterpretation.

No other factual inaccuracies were detected; all other citations correctly support the statements they accompany. Addressing the three points above will tighten the claim accuracy and align the manuscript with the existing literature.
