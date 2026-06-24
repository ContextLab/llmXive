---
action_items:
- id: 12e1a9633113
  severity: science
  text: "Temper the claim that the learned 3D motion prior \u201Ctransfers well\u201D\
    \ to downstream robotics; the current evidence is limited to simulation and a\
    \ small finetuning study on DROID without closed\u2011loop real\u2011world robot\
    \ experiments."
- id: 17487b1181be
  severity: writing
  text: "Clarify that the performance advantage over baselines is demonstrated on\
    \ the specific benchmark (\benchmarkname{}) and does not necessarily generalize\
    \ to all possible 3D motion forecasting tasks or datasets."
- id: 8d32a33adc13
  severity: writing
  text: "Provide a more precise justification for the statement that MolmoMotion\u2011\
    1M is \u201Cthe largest\u201D corpus of its kind, possibly by citing comparable\
    \ datasets or acknowledging the lack of a formal size comparison."
- id: 7d5a9d2d305a
  severity: science
  text: "Add a discussion of failure cases or scenarios where the model\u2019s predictions\
    \ are inaccurate (e.g., highly deformable objects, severe occlusions), and explain\
    \ how these limitations affect downstream applications."
- id: 71bdecff420e
  severity: science
  text: Include quantitative ablations that isolate the contribution of language conditioning
    versus visual cues on the benchmark, to support the claim that language instructions
    substantially improve forecasting.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:39:55.935107Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript introduces a novel task—goal‑conditioned 3D point motion forecasting—and presents a full data‑model pipeline (MolmoMotion‑1M, \benchmarkname{}, and the \modelname model). While the technical contributions are solid, several claims extend beyond what the presented evidence can fully support.

1. **Downstream Transfer Claims**  
   The paper states that the learned motion prior “transfers well” to robot manipulation and video generation. The robot experiments are limited to a simulated pick‑and‑place benchmark (MolmoSpaces) and a finetuning study on DROID videos; no closed‑loop real‑world robot trials are performed. Consequently, the claim of broad transfer to downstream robotics is overstated. The authors should either temper this language or provide additional real‑world evaluations.

2. **Benchmark‑Specific Superiority**  
   The assertion that \modelname “significantly outperforms all existing motion prediction baselines” is based on results from \benchmarkname{} only. While the table shows clear gains on the three subsets (HOT3D, WorldTrack, DAVIS), it does not cover other possible 3D motion forecasting settings (e.g., dense mesh‑based prediction, multi‑object interactions). The claim should be qualified to reflect the benchmark‑specific nature of the evaluation.

3. **Dataset Size Claim**  
   The authors claim MolmoMotion‑1M is “the largest corpus of action‑described, object‑grounded 3D point trajectories.” No comparative analysis with other large‑scale 3D motion datasets is provided. A brief citation of comparable works (or a statement acknowledging the lack of a formal comparison) would make this claim more defensible.

4. **Limitations and Failure Modes**  
   Section 6 lists a limitation regarding the sparse query‑point setting, but the paper would benefit from a more detailed analysis of failure cases (e.g., highly deformable objects, severe occlusions, ambiguous language). Understanding where the model breaks down is crucial for assessing the realism of the claimed “general motion prior.”

5. **Contribution of Language Conditioning**  
   The ablation study (Table 4) shows a drop when language is removed, but the narrative could more explicitly link this to the claim that language instructions “substantially improve forecasting.” Providing per‑subset statistics (e.g., ADE/FDE on DAVIS with/without language) would strengthen the argument.

6. **Over‑generalization in Abstract**  
   The abstract mentions “significantly outperforms all existing motion prediction baselines” and “improves training efficiency and generalization for robot manipulation.” Both statements should be qualified to avoid implying universal superiority across all tasks and datasets.

Overall, the paper’s core methodology is sound, but the language around generalization and impact needs to be calibrated to the experimental scope. Addressing the points above will align the claims with the presented evidence and improve scientific rigor.
