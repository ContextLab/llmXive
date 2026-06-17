---
action_items:
- id: 1491b06210d3
  severity: science
  text: "Provide a rigorous quantitative evaluation of generative fidelity. Use a\
    \ single, well\u2011defined ground\u2011truth set for all baselines, report the\
    \ number of samples, compute confidence intervals or standard deviations for FID/KID,\
    \ and perform statistical significance testing."
- id: 556db790ea85
  severity: science
  text: Detail the dataset split and sample sizes used for training, validation, and
    testing of the generative model. Include statistics on the geographic diversity
    (e.g., number of cities, total area, distribution of urban vs. natural scenes).
- id: c9d334d309f0
  severity: science
  text: "Add ablation studies for each major component (native 3DGS generative framework,\
    \ multi\u2011LOD decoder, sliding\u2011window inference, cross\u2011domain conditioning).\
    \ Show how performance (FID/KID, runtime, memory) changes when each is removed\
    \ or altered."
- id: 773bfa9da7cb
  severity: science
  text: "Report precise runtime measurements for the claimed 10\u2011minute per km\xB2\
    \ generation speed. Include hardware specifications, variation across dense urban\
    \ vs. sparse rural tiles, and breakdown of preprocessing, inference, and post\u2011\
    processing times."
- id: 3b9a05de9dbf
  severity: science
  text: "Replace the informal visual comparisons (Fig.\u202F9, Fig.\u202F10) with\
    \ quantitative system\u2011level metrics (e.g., coverage percentage, storage cost,\
    \ latency) and include error bars or confidence intervals where appropriate."
- id: 5a1a3cf88f4a
  severity: science
  text: Make the training code, model checkpoints, and evaluation scripts publicly
    available or provide a reproducibility checklist to allow independent verification
    of the reported results.
artifact_hash: 889d5a8e39acbdaa7baa4d1b8f93a551383f0dbc1ede3c36f50fc7a5e7bb8167
artifact_path: projects/PROJ-693-abot-earth-0-5-generative-3d-earth-model/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T06:18:10.124177Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The manuscript presents **ABot‑Earth 0.5**, a generative 3D Earth model that claims state‑of‑the‑art fidelity (FID 16.1, KID 0.006) and planetary‑scale efficiency (≤10 min per km²). However, the **scientific evidence supporting these claims is insufficient**.

1. **Generative fidelity metrics (Sec. 5.1, Table 2)**: The reported FID/KID scores are compared to baselines that use *different* ground‑truth image sets and view sampling strategies (footnote in Table 2). This makes the comparison non‑comparable. Moreover, the paper does not disclose the number of generated samples, the size of the reference set, or any variance measures (e.g., confidence intervals). Without such statistical detail, the claim of “substantial improvement” cannot be substantiated.

2. **Dataset description (Sec. 2.1, Table 1)**: While a list of source datasets is provided, the manuscript lacks quantitative information on the **total training volume** (e.g., total number of 3DGS tiles, geographic area covered, distribution of urban vs. natural scenes). There is no clear train/validation/test split, making it impossible to assess over‑fitting or generalization.

3. **Ablation of core innovations (Sec. 3‑4)**: The paper introduces several novel components (native 3DGS generation, inherent multi‑LOD decoder, seamless sliding‑window inference, VLM‑based conditioning). Yet no ablation experiments isolate the contribution of each component. Consequently, the reported performance could be driven by a single dominant factor rather than the integrated system.

4. **Runtime and scalability claims (Sec. 4.1)**: The claim of “under 10 minutes per km²” is presented without empirical evidence. No hardware configuration, per‑tile runtime distribution, or analysis of how scene complexity (dense city vs. sparse countryside) impacts latency is given. This undermines the reproducibility of the efficiency claim.

5. **System‑level comparisons (Sec. 5.2, Fig. 9, Fig. 10, Table 3)**: The evaluation against Google Earth and Marble relies on qualitative visual snapshots and high‑level tables lacking concrete numbers (e.g., exact coverage percentages, storage size per area, latency). Such anecdotal evidence does not rigorously support the asserted superiority in coverage or openness.

6. **Reproducibility**: No code, model checkpoints, or detailed hyper‑parameter settings are provided. The absence of a reproducibility checklist prevents independent verification of any of the reported results.

To elevate the manuscript to a scientifically robust contribution, the authors must **provide statistically sound quantitative evaluations**, **fully describe dataset composition and splits**, **conduct thorough ablations**, **report detailed runtime analyses**, and **share reproducible artifacts**. Only with these additions can the central claims be credibly validated.
