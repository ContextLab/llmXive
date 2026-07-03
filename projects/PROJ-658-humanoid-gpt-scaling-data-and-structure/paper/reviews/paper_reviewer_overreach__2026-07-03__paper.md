---
action_items:
- id: 87385b94c643
  severity: writing
  text: The paper makes several claims that extend beyond the provided evidence, particularly
    regarding the magnitude of generalization, the existence of a formal scaling law,
    and the specific contribution of data modalities. First, the abstract and introduction
    repeatedly use the term "unprecedented" to describe the zero-shot generalization
    capabilities (Abstract, Sec 1). However, the empirical evidence for this is limited
    to a small set of four specific dance clips (Table 3) and a few teleoperation
    de
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:27:20.348517Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the provided evidence, particularly regarding the magnitude of generalization, the existence of a formal scaling law, and the specific contribution of data modalities.

First, the abstract and introduction repeatedly use the term "unprecedented" to describe the zero-shot generalization capabilities (Abstract, Sec 1). However, the empirical evidence for this is limited to a small set of four specific dance clips (Table 3) and a few teleoperation demonstrations (Fig 4, 5). The paper does not present a comprehensive zero-shot benchmark covering a wide variety of unseen motion categories, styles, or dynamic regimes that would be necessary to support such a strong superlative claim against existing baselines like SONIC. The evaluation appears cherry-picked to demonstrate success rather than stress-test the limits of generalization.

Second, Section 5 is titled "Scaling Laws" and claims to "derive a scaling law" for humanoid motion tracking. However, the section lacks the mathematical rigor expected of such a claim. The authors present qualitative plots (Fig 6, 7) and state that "marginal gains decrease slightly," but they do not provide a fitted power-law equation, exponents, or statistical analysis to validate a specific scaling relationship. Without a formal derivation or quantitative fit, describing this as a "scaling law" is an overreach; it is merely an observation of scaling trends.

Third, the authors claim to provide "the first systematic evidence that video-estimated motion can materially improve tracking" (Sec 1, Summary). While the dataset includes video-derived motions, the paper does not isolate this variable. There is no ablation study comparing training on the full 2B corpus versus a subset excluding video-estimated data to quantify the specific marginal gain attributable to this modality. The improvement is conflated with the overall scale of the dataset.

Finally, the claim of "real-time performance" based on a 1.5ms inference latency on an NVIDIA RTX 4090 (Sec 4.5) is misleading in the context of the deployed system. The Unitree-G1 humanoid typically relies on onboard compute (e.g., Jetson Orin) which is significantly less powerful than a desktop 4090. Without reporting latency measurements on the actual onboard hardware, the claim that the system maintains real-time performance in deployment is unsupported.
