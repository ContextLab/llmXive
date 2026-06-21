---
action_items:
- id: 8478bcd7657f
  severity: writing
  text: "Replace repeatedly used abbreviations such as \u201COPSD\u201D, \u201CdLLM\u201D\
    , \u201CRLVR\u201D, \u201CAR\u201D, and \u201CKL\u201D with plain language on\
    \ first mention or add brief parenthetical explanations."
- id: 816631e9aa84
  severity: writing
  text: "Define \u201CKL\u201D (Kullback\u2011Leibler divergence) at its first appearance;\
    \ many readers unfamiliar with information\u2011theoretic terms will be lost."
- id: 298c3ed3a5e6
  severity: writing
  text: "Substitute \u201Cprivileged information\u201D with a clearer phrase like\
    \ \u201Cextra context\u201D or \u201Cadditional guidance\u201D throughout Sections\u202F\
    1\u20113."
- id: 8865f49dcda6
  severity: writing
  text: "Rephrase \u201Cdense token\u2011level supervision\u201D and \u201Cdense step\u2011\
    level supervision\u201D to \u201Crich token\u2011level guidance\u201D and \u201C\
    stepwise guidance\u201D to improve readability."
- id: 4cf476504d2b
  severity: writing
  text: "The phrase \u201Cself\u2011future\u2011experience\u201D (Section\u202F3.1)\
    \ is opaque; replace with \u201Cfuture self\u201D or \u201Cfuture answer\u201D\
    \ for clarity."
- id: a84f50b3c8b1
  severity: writing
  text: "Avoid the jargon\u2011heavy term \u201Cpolicy collapse\u201D (Section\u202F\
    4.5); use \u201Ctraining collapse\u201D or \u201Cperformance degradation\u201D\
    \ and briefly explain the phenomenon."
- id: 66d3f3431da6
  severity: writing
  text: "The term \u201Con\u2011policy nature\u201D appears multiple times (e.g.,\
    \ Sections\u202F1,\u202F3.1,\u202F3.3); simplify to \u201Cusing its own generated\
    \ data\u201D."
- id: 632d930e58e0
  severity: writing
  text: "Clarify \u201Cstep\u2011level KL divergence\u201D by adding a short description\
    \ of what the KL is measuring at each denoising step."
- id: 9d64e53e38a8
  severity: writing
  text: "The acronym \u201CSFT\u201D is introduced without a clear definition of the\
    \ underlying method; add a brief description of \u201Csupervised fine\u2011tuning\u201D\
    \ when first used."
- id: 39693c446195
  severity: writing
  text: "In Table\u202F3 and related discussion, replace \u201Csample efficiency\u201D\
    \ with \u201Ctraining efficiency\u201D and explain why fewer optimization steps\
    \ matter."
- id: b687e6f7028d
  severity: writing
  text: "The phrase \u201Cteacher\u2011specific privileged information\u201D (Section\u202F\
    2) is redundant; simplify to \u201Cteacher\u2019s extra context\u201D."
- id: 17298db0d8c8
  severity: writing
  text: "Throughout the manuscript, replace \u201Cautoregressive\u2011centric\u201D\
    \ with \u201Cfocused on left\u2011to\u2011right models\u201D."
- id: 3f051b25d2ed
  severity: writing
  text: "The term \u201Cstep\u2011level divergence supervision\u201D is repeated;\
    \ consider a single term like \u201Cstepwise divergence loss\u201D and use it\
    \ consistently."
- id: f13527889737
  severity: writing
  text: "Explain the abbreviation \u201CLoRA\u201D (Low\u2011Rank Adaptation) at its\
    \ first mention in Appendix\u202FA.3."
- id: 236262cd8bcb
  severity: writing
  text: "The phrase \u201Cmodel\u2011seeking behavior\u201D vs. \u201Cmodel\u2011\
    covering behavior\u201D (Section\u202F4.4) is jargon\u2011heavy; replace with\
    \ \u201Cfocuses on high\u2011probability predictions\u201D and \u201Ccovers a\
    \ broader distribution\u201D, respectively."
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:43:20.130675Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is technically solid, but it is littered with specialist jargon that hampers accessibility. In the abstract and Section 1, terms such as “OPSD”, “dLLM”, “RLVR”, and “AR” are introduced without sufficient plain‑language explanations, forcing readers to constantly flip to the bibliography. Throughout Sections 2–3, phrases like “privileged information”, “dense token‑level supervision”, and “step‑level divergence supervision” are used repeatedly; these could be replaced with simpler alternatives (“extra context”, “rich token‑level guidance”, “stepwise guidance”) and defined once. The novel concept of “self‑future‑experience” (Section 3.1) is obscure; a more intuitive wording such as “future self” would convey the idea immediately.

Several acronyms appear without definition (e.g., “KL” in Eq. 4, “LoRA” in Appendix A.3). Adding brief parenthetical definitions would aid non‑expert readers. The discussion of “policy collapse” in Section 4.5 uses reinforcement‑learning terminology that is unnecessary for the core contribution; rephrasing it as “training collapse” and providing a short description would improve clarity.

Redundant wording also reduces readability. Phrases like “teacher‑specific privileged information” and “on‑policy nature” recur across multiple sections; consolidating them into a single, clearer expression (“teacher’s extra context” and “using its own generated data”) would streamline the narrative. The manuscript frequently switches between “step‑level KL divergence” and “step‑level divergence supervision”; adopting a consistent term such as “stepwise divergence loss” would avoid confusion.

Finally, the tables and figures use terms like “sample efficiency” without contextual explanation. Replacing this with “training efficiency” and briefly stating why fewer optimization steps are beneficial would make the results more interpretable.

Addressing these language issues will make the paper much more approachable to a broader audience while preserving its technical contributions.
