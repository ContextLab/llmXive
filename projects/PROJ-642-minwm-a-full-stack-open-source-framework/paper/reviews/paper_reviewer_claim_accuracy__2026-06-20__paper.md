---
action_items:
- id: 3e452b88f664
  severity: fatal
  text: "Numerous in\u2011text citations (e.g., \\cite{zhu2026causal}, \\cite{zhao2026causal},\
    \ \\cite{li2026cameras}, \\cite{wang2025spatialvid}, \\cite{ling2024dl3dv}, \\\
    cite{nan2024openvid}, \\cite{bao2024vidu}, \\cite{feng2025vidarc}, \\cite{ye2025yan},\
    \ \\cite{xiang2025pan}, \\cite{he2025matrix}) have no corresponding entries in\
    \ the bibliography. Add the missing bibliography items or remove/replace the citations."
- id: c84e5a85b6b3
  severity: writing
  text: "Broad statements about the progress of video diffusion models (e.g., \u201C\
    Recent video diffusion foundation models have achieved remarkable progress in\
    \ high\u2011quality video generation\u201D) are made without any supporting references.\
    \ Cite recent benchmark papers or surveys that substantiate these claims."
- id: de827dca8dc7
  severity: writing
  text: "The claim that minWM \u201Csubstantially reduces the first\u2011frame latency\u201D\
    \ is supported only by a single table (Table\u202F1) with single\u2011run numbers.\
    \ Provide statistical evidence (e.g., mean\u202F\xB1\u202Fstd over multiple runs,\
    \ hardware/software configuration details) to justify the magnitude of the speedup\
    \ and avoid overstating the result."
- id: 39663027f92d
  severity: science
  text: "The manuscript asserts that the framework is \u201Carchitecture\u2011general\u201D\
    \ but demonstrates it on only two backbones (Wan2.1 and HY1.5). Either temper\
    \ the claim or add experiments on a third, qualitatively different architecture\
    \ to substantiate generality."
- id: 1dba10677b44
  severity: writing
  text: "The description of PRoPE camera\u2011conditioning cites \\cite{li2026cameras},\
    \ which is absent from the bibliography. Verify that the cited work exists and\
    \ that the equations accurately reflect it; otherwise, provide a correct reference\
    \ or adjust the description."
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:32:36.204827Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: full_revision
---

**Claim‑accuracy assessment**

The paper introduces *minWM*, an end‑to‑end pipeline for converting bidirectional video diffusion models into camera‑controllable few‑step autoregressive world models. While the overall idea is plausible, several factual claims are either unsupported or incorrectly referenced.

1. **Missing bibliography entries** – The text repeatedly cites works that do not appear in `main.bib` (e.g., `zhu2026causal`, `zhao2026causal`, `li2026cameras`, `wang2025spatialvid`, `ling2024dl3dv`, `nan2024openvid`). Without these entries a reviewer cannot verify that the cited methods (Causal Forcing, PRoPE, SpatialVid, DL3DV, WorldPlay) actually contain the described algorithms or datasets. This is a fatal citation error.

2. **Unsubstantiated background claims** – The introductory paragraph claims “remarkable progress in high‑quality video generation” and that “interactive world models require controllable, causal, and low‑latency rollout” but provides no quantitative citations to recent surveys (e.g., *VideoBench* 2024) or benchmark results. The statement is therefore an unsupported assertion.

3. **Latency reduction claim** – Table 1 reports first‑frame latency for multi‑step bidirectional, multi‑step AR, and few‑step AR models on a single A800 GPU. No variance, confidence intervals, or repeatability information is given, and the hardware/software stack (driver version, CUDA, batch inference settings) is omitted. Consequently, the claim of a “223.75×” speedup cannot be verified and may be overstated.

4. **Generality of the framework** – The authors claim the pipeline is “architecture‑general” and demonstrate it on two backbones (Wan2.1 and HY1.5). Two models do not constitute a broad architectural spectrum; a third architecture (e.g., a latent‑diffusion video model or a transformer‑only design) would be needed to substantiate the generality claim. As written, the claim is too strong.

5. **PRoPE description** – Section 3.1 presents the PRoPE injection equations and cites `li2026cameras`. Since this reference is missing, the reader cannot confirm that the formulation matches the original method. This raises doubts about the correctness of the presented equations.

6. **Ablation interpretations** – The paper interprets failure on SpatialVid as “likely due to perception‑estimated camera poses” and presents this as a conclusion. However, no quantitative analysis (e.g., pose error statistics) is provided, making the conclusion speculative.

Overall, the manuscript’s factual backbone is weakened by missing citations and insufficient empirical evidence for its key performance claims. Addressing the citation gaps, providing statistical validation for latency improvements, and tempering or expanding the generality claim are necessary before the paper can be considered for acceptance.
