---
action_items:
- id: 5b5b9edccd7b
  severity: science
  text: The manuscript does not describe how subjects in the training data gave informed
    consent; add a detailed discussion of data collection ethics and consent procedures.
- id: b2e88b3203a3
  severity: science
  text: "Potential for generating non\u2011consensual or harmful deepfake videos is\
    \ not mitigated; propose concrete safeguards such as watermarking, usage restrictions,\
    \ and detection tools."
- id: c2f978895085
  severity: science
  text: Bias and fairness analyses of garment representation across demographics are
    missing; include evaluation of demographic bias and steps to mitigate.
- id: f03cf3639f57
  severity: writing
  text: The paper lacks a clear policy for responsible deployment and user access
    control; add a section outlining responsible release practices.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T03:19:00.919487Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper introduces **FashionChameleon**, a real‑time, autoregressive video generation system that can swap garments on a human subject while preserving motion coherence (see Abstract and Fig. 1). While the technical contributions are notable, the manuscript raises several safety and ethical concerns that need to be addressed before acceptance.

1. **Data provenance and consent** – Section 5 (“High‑Quality Data Curation Pipeline”) describes a four‑stage pipeline that harvests “≈ 82 K triplets” from publicly available videos. No information is provided about whether the individuals depicted gave informed consent for their likeness to be used in a generative model. This omission is critical because the resulting system can produce realistic videos of identifiable people wearing arbitrary garments, a classic deep‑fake scenario. The reviewers must require the authors to document the source of the videos, any consent mechanisms employed, and how privacy‑preserving procedures (e.g., face blurring, exclusion of copyrighted material) are applied.

2. **Potential for misuse** – The “Potential Negative Societal Impact” section (near the end) acknowledges risks such as generation of sexual/violent content and misleading realistic videos, but it stops short of proposing concrete mitigations. Given the system’s ability to edit garments on a specific person in real time, there is a high risk of non‑consensual manipulation (e.g., fabricating pornographic or defamatory content). The manuscript should include a mitigation plan: mandatory watermarking of generated frames, integration of detection tools, and a clear usage‑policy that restricts distribution to vetted parties.

3. **Bias and fairness** – The dataset curation pipeline focuses on garment extraction but does not discuss demographic coverage (e.g., gender, skin tone, body type). Without such analysis, the model may perform unevenly across groups, reinforcing stereotypes or excluding minorities. The authors should conduct a bias audit (e.g., measuring garment‑switch fidelity across demographic slices) and describe steps taken to balance the training set or to fine‑tune the model for fairness.

4. **Responsible deployment** – There is no mention of access control, licensing, or community‑governance mechanisms. For a technology with dual‑use potential, the paper should outline a responsible release strategy (e.g., staged rollout, API key gating, audit logs) and discuss how they will monitor and respond to abusive applications.

Addressing these points will substantially improve the ethical robustness of the work and align it with community standards for generative video technologies.
