---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:47:52.667711Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics explicitly in Section 6 ("Limitations, social impact, and future work") and Appendix Sec "Broader Impact". The authors acknowledge risks regarding misinformation ("Generated videos may be mistaken for real observations") and safety-critical misuse ("over-interpreted as faithful predictions in robotics"). However, there are significant gaps in data licensing compliance and technical mitigation strategies that require attention before public release.

1. **Data Licensing vs. Open-Source Claim:** The abstract claims an "open-source world model," yet Table 11 (Sec Appendix) lists training data sources like SpatialVID-HQ and OmniWorld under CC-BY-NC-SA 4.0 or custom non-commercial terms. Releasing a model trained on NC data as open-source may violate these licenses if the weights enable commercial inference. The authors must clarify whether the model weights inherit these non-commercial restrictions or if the training data was filtered to only include permissive licenses (Sec 4, Tab 11).

2. **Misuse Mitigation:** While the authors recommend documenting provenance (Sec 6), they do not detail technical safeguards for the model weights themselves. The benchmark images use SynthID (App. Sec "Benchmark Details"), but it is unclear if the released model enforces watermarking or detection capabilities for generated outputs. Given the high fidelity (720p, minute-scale), this is a critical dual-use risk that requires specific technical countermeasures beyond policy recommendations.

3. **Bias Acknowledgement:** The paper notes biases from public video sources (Sec 6) but lacks a specific audit of these biases in the evaluation benchmark, which relies on generated initial frames (Nano Banana Pro).

Recommendation: Minor revision to clarify data license compliance for the model weights and specify technical provenance measures for generated outputs.
