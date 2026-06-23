---
action_items:
- id: 9854b27eda8c
  severity: fatal
  text: "Many in\u2011text citations (e.g., beyondmimic25, asap25, twist25, unitracker25,\
    \ gmt25, sonic25, motionx++25, phuma25, motionmillion25, gmr25) are not present\
    \ in the bibliography. Add proper bibliography entries or correct the citation\
    \ keys."
- id: e453c0c6b3ab
  severity: science
  text: "The claim that \u201Cvideo\u2011estimated motion can materially improve tracking\
    \ when the model and the training set are scaled appropriately\u201D is not supported\
    \ by any ablation or quantitative analysis in the paper. Provide experimental\
    \ evidence or remove the claim."
- id: 3d276720b590
  severity: science
  text: "The statement \u201CWe are the first motion tracker with zero\u2011shot ability\
    \ trained on a 2B\u2011frame data set\u201D and \u201Cover 200\xD7 larger than\
    \ prior trackers\u201D are presented as novelty claims without clear comparison\
    \ to all existing works. Verify these claims against the literature and cite any\
    \ relevant prior large\u2011scale trackers (e.g., SONIC, any other >100M\u2011\
    frame works)."
- id: 79c0a2d5bfb8
  severity: writing
  text: "Table\u202F1 lists several prior methods with check\u2011marks for \u201C\
    Agile\u201D and \u201CZero\u2011shot\u201D but provides no source or definition\
    \ for these attributes. Clarify the criteria and ensure the table accurately reflects\
    \ the cited papers."
- id: ebb34e39ad92
  severity: writing
  text: "The scaling\u2011law analysis (Fig.\u202F5, Fig.\u202F6) claims monotonic\
    \ improvement up to 2\u202FB tokens, yet the marginal gains between 200\u202F\
    M and 2\u202FB are described as \u201Cslight\u201D while still being presented\
    \ as a strong scaling law. Re\u2011phrase to accurately reflect the observed diminishing\
    \ returns."
- id: 65ed57672518
  severity: writing
  text: "The latency claim (\u22641.5\u202Fms on RTX\u202F4090) is shown in Fig.\u202F\
    7 but lacks details on batch size, precision (FP16 vs FP32), and whether TensorRT\
    \ optimizations were applied uniformly across baselines. Add a brief description\
    \ of the measurement setup."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:58:59.982610Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: full_revision
---

The manuscript makes a large number of factual claims that are either insufficiently supported or improperly cited. Throughout the introduction and related‑work sections the authors refer to many recent works using citation keys ending in “25” (e.g., beyondmimic25, asap25, twist25, unitracker25, gmt25, sonic25, motionx++25, phuma25, motionmillion25, gmr25). None of these keys appear in the provided bibliography, which means the reader cannot verify the existence or relevance of the cited papers. This undermines the credibility of the comparative claims in Table 1 and the narrative that the proposed system fills a clear gap.

A central scientific claim is that “video‑estimated motion can materially improve tracking when the model and the training set are scaled appropriately.” The paper never presents an ablation that isolates video‑estimated data from purely mocap data, nor does it quantify the improvement attributable to this source. Without such evidence the claim is speculative and should be either substantiated with experiments or removed.

The novelty statements—being the first zero‑shot tracker trained on 2 B frames and being >200× larger than prior work—are presented without exhaustive comparison. While the table shows prior trackers using up to 100 M frames, the bibliography does not include any works that might have approached this scale, and the “200×” factor is only roughly accurate (2 B/7.2 M ≈ 278×, but 2 B/100 M ≈ 20×). The authors should explicitly cite all large‑scale baselines and justify the novelty claim.

Table 1 also uses check‑marks for “Agile” and “Zero‑shot” without defining the metrics or thresholds used to assign these labels. This makes the comparison ambiguous; the authors should either provide a clear definition or replace the table with quantitative metrics that are directly comparable.

The scaling‑law discussion (Figures 5 and 6) suggests a continuous performance gain with data and model size, yet the text acknowledges “slight” marginal gains at the highest scale. The narrative should be adjusted to reflect the observed diminishing returns rather than implying unbounded improvement.

Finally, the latency claim (≤1.5 ms on RTX 4090) is illustrated but lacks methodological detail (e.g., batch size, precision mode, whether the same TensorRT optimizations were applied to baselines). Providing this information would allow readers to assess the fairness of the comparison.

Addressing these citation gaps, providing missing experimental evidence, and clarifying the comparative tables will substantially improve the factual reliability of the paper.
