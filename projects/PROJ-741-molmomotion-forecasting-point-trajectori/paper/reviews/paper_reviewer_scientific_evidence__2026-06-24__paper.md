---
action_items:
- id: ae2dca22f43a
  severity: science
  text: "Quantify the noise introduced by the automatic 3\u2011D annotation pipeline\
    \ (e.g., by reporting per\u2011clip error distributions or a validation set with\
    \ ground\u2011truth motion captured by a motion\u2011capture system) and assess\
    \ how this noise propagates to the benchmark results."
- id: d873230b3697
  severity: science
  text: Provide statistical significance testing (e.g., paired bootstrap or permutation
    tests) for the reported improvements over baselines on the PointMotionBench benchmark,
    including confidence intervals for ADE/FDE/PWT.
- id: a033a12873cc
  severity: science
  text: "Add an additional held\u2011out evaluation set that is sourced from a completely\
    \ different domain (e.g., indoor robotics videos not seen in the pre\u2011training\
    \ corpora) to demonstrate that the model\u2019s performance generalizes beyond\
    \ the three benchmark sources."
- id: e8e9dd854676
  severity: science
  text: "Report the variance across multiple random seeds for the training of both\
    \ the autoregressive and flow\u2011matching variants, to show that the observed\
    \ gains are robust to initialization and data shuffling."
- id: ec52775a93ed
  severity: science
  text: Include an ablation that directly compares trajectories obtained from the
    automatic pipeline against manually annotated trajectories on a small subset,
    to validate that the pipeline does not systematically bias motion direction or
    magnitude.
- id: 5fd129431e2b
  severity: writing
  text: "Clarify the exact split of training/validation/test clips in PointMotionBench\
    \ (e.g., number of clips per category and per motion type) and provide a table\
    \ of per\u2011category performance to rule out that gains are driven by a few\
    \ easy categories."
- id: dd1bf379e512
  severity: writing
  text: "Document the random seed and any nondeterministic operations (e.g., K\u2011\
    means clustering for query point selection) used during data generation and model\
    \ training to enable exact replication."
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:40:16.652413Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling new task—goal‑conditioned 3‑D point motion forecasting—and a large‑scale data pipeline (MolmoMotion‑1M) plus a benchmark (PointMotionBench) to evaluate it. The experimental section reports strong quantitative gains over a wide range of baselines on ADE, FDE, and PWT metrics, and includes qualitative visualizations. However, from a scientific‑evidence perspective several aspects limit the robustness of the central claims:

1. **Annotation Noise and Ground‑Truth Validity** – The core training and benchmark data are generated automatically from unconstrained videos using a multi‑stage pipeline (LLM phrase extraction, MolmoPoint, SAM‑3, AllTracker, ViPE, filtering). While the authors describe filtering heuristics, there is no systematic quantification of residual error in the resulting 3‑D trajectories. Without a validation set with high‑precision ground‑truth (e.g., motion‑capture or manually annotated 3‑D tracks), it is unclear how much annotation noise may inflate or deflate the reported performance.

2. **Statistical Significance** – The tables (e.g., Table 1) present point estimates of ADE/FDE/PWT but lack confidence intervals or hypothesis‑testing. Given the modest size of the benchmark (742 clips), random variation could explain part of the observed improvements, especially for the flow‑matching variant where gains are smaller.

3. **Replication Across Random Seeds** – Training of large multimodal models can be sensitive to initialization and data shuffling. The paper reports a single training run per variant; no variance across seeds is provided, making it difficult to assess the stability of the reported numbers.

4. **Benchmark Diversity and Potential Over‑fitting** – PointMotionBench aggregates three datasets (HOT3D, WorldTrack, DAVIS). While the authors claim no clip‑level overlap with pre‑training data, the benchmark still draws heavily from indoor manipulation and egocentric videos, which are also prominent in the pre‑training corpus. An additional out‑of‑distribution test set would strengthen the claim of generalization.

5. **Ablation of Annotation Pipeline** – The authors perform model‑level ablations (e.g., removing language, 2‑D point features) but do not ablate the data generation steps. A direct comparison of trajectories derived from the automatic pipeline versus a small manually curated set would reveal systematic biases (e.g., under‑estimation of fast motions due to depth smoothing).

6. **Reporting Details for Replicability** – The split ratios (train/val/test) for PointMotionBench, per‑category clip counts, and random seeds used in K‑means clustering for query‑point selection are not fully disclosed. Precise documentation is needed for exact replication.

Overall, the experimental evidence is promising but requires additional quantitative validation and clearer reporting to fully substantiate the central claims. Addressing the points above will considerably strengthen the scientific rigor of the work.
