---
action_items:
- id: 7f852ae62879
  severity: fatal
  text: Remove or replace citations to works that are dated 2025/2026 (e.g., \citep{Lee_2025_CVPR,NEURIPS2025_e5849736,Lee_2026_CVPR_Masters})
    as they cannot provide supporting evidence for the claims made.
- id: 25f556517e14
  severity: science
  text: "Correct the statement in Appendix\u202F\xA7\u202F2 that ZPPO \u201Cexceeds\
    \ the 27B teacher on several LLM benchmarks\u201D \u2013 the presented tables\
    \ show the teacher\u2019s scores are substantially higher; re\u2011phrase to indicate\
    \ that ZPPO narrows the gap on specific benchmarks."
- id: 9b5b55fee2ba
  severity: writing
  text: "Add explicit citations for the claim that \u201CRL avoids logit imitation\
    \ but discards hard questions whose rollouts all fail (zero advantage)\u201D or\
    \ qualify it as an observation rather than a literature\u2011backed fact."
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:02:37.016957Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several factual claims that are not fully supported by the cited literature.  

1. **Future‑dated citations** – Throughout the Related Work (Sec. 2) and elsewhere the authors cite papers with publication years 2025 and 2026 (e.g., \\citep{Lee_2025_CVPR}, \\citep{NEURIPS2025_e5849736}, \\citep{Lee_2026_CVPR_Masters}). These works do not yet exist, so they cannot substantiate statements about knowledge‑distillation brittleness, prompt‑replay methods, or other background. The claim that “prompt replay and hint‑scaffolding methods \\citep{zhan2025exgrpo,zhang2025clpo,li2025staying} lack the teacher‑in‑prompt guidance that ZPPO provides” is therefore unsupported.

2. **Overstated performance relative to the teacher** – In Appendix § 2 the authors write that “ZPPO exceeds the 27B teacher on several LLM benchmarks by +3.1/+2.8/+2.6 pp”. Table \\ref{tab:appendix:teacher_capability:vs_teacher} shows the teacher’s macro‑average LLM score is 71.8 % while ZPPO‑trained 0.8 B–9 B students achieve at most 33.1 %. No benchmark in the presented tables demonstrates a student surpassing the teacher; the correct observation is that ZPPO narrows the gap on certain tasks. This misstatement could mislead readers about the method’s absolute performance.

3. **Uncited RL advantage claim** – The introduction asserts that “RL avoids logit imitation but discards hard questions whose rollouts all fail (zero advantage)”. No reference is provided for this observation, and it is not derived from the experimental analysis (the zero‑advantage phenomenon is discussed later but without a citation). The claim should either be backed by a prior study or presented as an empirical observation from the authors’ own data.

4. **Consistency of reported gains** – The abstract’s claim of “+9.3 pp for 0.8 B VLM benchmarks” matches the difference between Base (41.0 %) and ZPPO (50.3 %) in Table \\ref{tab:hintprefix}, so this is accurate. Other macro‑average improvements (e.g., +7.5 pp in Table \\ref{tab:representative}) are also consistent with the presented numbers.

Overall, the experimental results appear internally consistent, but the manuscript contains unsupported citations and an inaccurate performance claim. Addressing these issues will improve factual reliability without requiring new experiments.
