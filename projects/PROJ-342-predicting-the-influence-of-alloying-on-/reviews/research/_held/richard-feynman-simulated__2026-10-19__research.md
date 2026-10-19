---
action_items: []
artifact_hash: 05440e5b118aaddc5a5a5886d6eebd3dc83ef71a3110b829b5c8e094a8043354
artifact_path: projects/PROJ-342-predicting-the-influence-of-alloying-on-/specs/001-predicting-the-influence-of-alloying-on/spec.md
backend: dartmouth
feedback: "Two things bother me, and one of them would embarrass us badly if we didn't\
  \ catch it now. First, the easy one: FR-009 computes correlations only among the\
  \ three predictors (predictor-vs-predictor), yet FR-008 sells the FDR correction\
  \ as controlling false positives in the 'linear dependency analysis' that's supposed\
  \ to answer the research question. Picture it: you end up with p-values telling\
  \ you radius mismatch correlates with VEC \u2014 which is a collinearity check,\
  \ fine \u2014 but nowhere does the spec"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-19T22:08:00.697217Z'
reviewer_kind: llm
reviewer_name: richard-feynman-simulated
score: 0.0
verdict: minor_revision
---

Two things bother me, and one of them would embarrass us badly if we didn't catch it now. First, the easy one: FR-009 computes correlations only among the three predictors (predictor-vs-predictor), yet FR-008 sells the FDR correction as controlling false positives in the 'linear dependency analysis' that's supposed to answer the research question. Picture it: you end up with p-values telling you radius mismatch correlates with VEC — which is a collinearity check, fine — but nowhere does the spec require correlating the descriptors against Tg itself. The core question ('which descriptors track Tg?') has no specified statistical test. The pipeline can pass every acceptance scenario and still never test the thing the project is about. Second, the data sources. The spec names a 'Metallic Glass Database' by Pauly et al. at Zenodo DOI 10.5281/zenodo.10043838, with a fallback 'MatNVP Metallic Glass' at 10.5281/zenodo.11023456. Neither the idea document nor the literature search mentions either of these, the fallback name looks like a placeholder, and the idea's own source (Materials Project) doesn't curate glass transition temperatures for metallic glasses in any dataset I can verify from what's shown here. Before anything else gets built, someone should actually resolve those DOIs and confirm record counts and family labels — otherwise US-1's 'retention rate' is a retention rate of nothing. Also worth noticing: the edge case 'What occurs if the Zenodo DOI provided in the idea is invalid' is raised but never answered, while the spec simultaneously hard-codes specific DOIs — the doubt is written down and then ignored.

---

> *Note: this contribution was authored by **Richard Feynman (simulated)** — a simulated AI persona shaped from the public-record writings of Richard Feynman, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Richard Feynman.*
