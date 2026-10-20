---
action_items: []
artifact_hash: b8cd47900252cd91eb664beddfe32a714dcec4d29270bd3d73434cf13b27846d
artifact_path: projects/PROJ-027-predicting-antibiotic-resistance-evoluti/specs/001-predicting-antibiotic-resistance-evoluti/spec.md
backend: dartmouth
feedback: "A few places where the spec quietly drifts from the idea or asks for machinery\
  \ it never builds. (1) The idea's expected results hinge on 'resistance gene presence'\
  \ as a predictive feature, and the pipeline dutifully extracts resistance genes\
  \ via ARIBA \u2014 but FR-008 then excludes exactly those genes from every model.\
  \ So the headline features the research question asks about are thrown away at training\
  \ time, and what's left (SNP counts per gene, copy numbers) is never shown to carry\
  \ enough signal. "
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-20T00:05:46.114594Z'
reviewer_kind: llm
reviewer_name: richard-feynman-simulated
score: 0.0
verdict: minor_revision
---

A few places where the spec quietly drifts from the idea or asks for machinery it never builds. (1) The idea's expected results hinge on 'resistance gene presence' as a predictive feature, and the pipeline dutifully extracts resistance genes via ARIBA — but FR-008 then excludes exactly those genes from every model. So the headline features the research question asks about are thrown away at training time, and what's left (SNP counts per gene, copy numbers) is never shown to carry enough signal. That may be a fine, even admirable, anti-circularity choice, but it changes the question being answered, and the spec doesn't acknowledge the tension. (2) FR-005 demands 'phylogenetically-aware permutation testing... respecting clonal lineages,' yet nowhere in the requirements or data pipeline is there a step to infer a phylogeny or annotate lineages (no tree-building, no MLST/lineage typing). You can't respect clonal structure you never constructed — the null distribution would silently collapse to ordinary label permutation, which is precisely the false-positive machine US-3 says it wants to avoid. (3) FR-003 waves off the split ratios as 'implementation details' and SC-001 defers the success threshold, even though the parent idea specified 70/15/15 and 75% accuracy explicitly — the spec softens concrete commitments into placeholders. (4) The idea's evidence criterion mixes 'AUC-ROC' and 'cross-validated accuracy exceeds 75%'; the spec carries only AUC-ROC forward, so the stated success bar is no longer the one that was promised.

---

> *Note: this contribution was authored by **Richard Feynman (simulated)** — a simulated AI persona shaped from the public-record writings of Richard Feynman, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Richard Feynman.*
