---
action_items:
- id: 5fb1fda3da17
  severity: science
  text: "The manuscript claims that the teacher\u2019s reasoning\u2011conditioned\
    \ score distribution can be \u201Ceffectively internalized\u201D into a 9B student\
    \ without providing a direct ablation that isolates the contribution of reasoning\
    \ versus the KL distillation loss. Add an experiment that trains the student with\
    \ only KL loss on the teacher\u2019s scalar expectations (no distribution) or\
    \ with a non\u2011reasoning teacher to substantiate the claim."
- id: 3f7bc77f694c
  severity: science
  text: "The paper states that the proposed framework \u201Cgeneralizes to all sequence\u2011\
    to\u2011score tasks\u201D (Section\u202F7) despite only evaluating on text\u2011\
    to\u2011image generation. This is an over\u2011generalization; either remove the\
    \ claim or provide evidence on at least one additional modality (e.g., video or\
    \ captioning)."
- id: '869497645444'
  severity: writing
  text: "The authors report a \u201C41.3\u202F% net human\u2011preference improvement\u201D\
    \ (GSB) over the SFT baseline, yet the GSB metric is defined relative to a baseline\
    \ that already includes human\u2011aligned fine\u2011tuning. The evaluation set\
    \ (400 prompts) is small and may not reflect broader distributions. Clarify the\
    \ statistical significance, confidence intervals, and whether the improvement\
    \ holds across diverse datasets."
- id: b7ff0e4303bf
  severity: science
  text: "The manuscript suggests that score\u2011distribution supervision \u201Caccelerates\
    \ score\u2011scale calibration\u201D without presenting a baseline where only\
    \ pointwise scalar supervision is used. Include a comparison where the teacher\
    \ is trained with only scalar rewards to verify that the distributional loss is\
    \ responsible for the reported gains."
- id: 885d08285c4e
  severity: writing
  text: "Section\u202F4.2 claims that the teacher\u2019s reasoning \u201Chelps decompose\
    \ visual evidence, apply rubric criteria, and allocate probability mass across\
    \ neighboring score bins,\u201D yet no analysis of the reasoning traces is provided\
    \ (e.g., qualitative examples, correlation with performance). Provide evidence\
    \ that the reasoning actually influences the distribution rather than being ignored."
artifact_hash: ea1d74fbe2af288d803689e081136bb19c2463edb4534b816711d1532122572b
artifact_path: projects/PROJ-694-beyond-scalar-rewards-by-internalizing-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T00:49:32.376116Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper’s central narrative repeatedly stretches the evidence beyond what is demonstrated. The authors assert that a large VLM teacher, trained with Group‑wise Direct Score Optimization (GDSO), learns a “calibrated score distribution” and that this distribution can be distilled into a compact student without any reasoning at inference time. However, the experimental section lacks a crucial control: a student trained from a teacher that does **not** use reasoning (or that outputs only scalar expectations). Without this, it is unclear whether the observed performance gain of the 9B RISD student stems from the reasoning‑conditioned distribution, from the KL‑distillation objective itself, or from other confounding factors such as model capacity or training duration. An ablation that removes the reasoning component from the teacher (e.g., a plain SFT teacher) would directly test the claim of “reasoning‑internalized” scoring.

Similarly, the claim of “generalization to all sequence‑to‑score tasks” is unsupported. The manuscript only evaluates on a single internal text‑to‑image benchmark; extending the claim to video, captioning, or other modalities requires at least a proof‑of‑concept experiment. Over‑general statements risk misleading readers about the scope of the method.

The reported 41.3 % GSB improvement is impressive but potentially overstated. The GSB metric is defined on a modest set of 400 prompts, and no statistical analysis (e.g., confidence intervals, p‑values) is provided. Moreover, the baseline SFT model already incorporates human‑aligned fine‑tuning, so the relative gain may be smaller when compared against stronger baselines or on larger, more diverse test sets. The authors should present variance estimates and discuss the robustness of this improvement.

The paper also attributes faster calibration to the distributional loss (Eq. (13)) without comparing to a model trained with only pointwise scalar supervision. A direct comparison would substantiate the claim that distribution‑level supervision is the primary driver of the observed PLCC/SRCC gains.

Finally, the manuscript frequently mentions that the teacher’s reasoning “helps decompose visual evidence … and allocate probability mass,” yet no qualitative analysis of the reasoning traces is offered. Providing example reasoning chains and correlating them with distributional outputs would strengthen the argument that reasoning is essential rather than an auxiliary artifact.

Addressing these points—through targeted ablations, broader evaluation, statistical rigor, and qualitative analysis—will align the paper’s claims with the presented evidence and avoid over‑reaching conclusions.
