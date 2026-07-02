---
action_items:
- id: b263e92b0839
  severity: writing
  text: The 'Existing Assets and Tool Terms' table (Tab. 1 in Appendix) lists several
    datasets (e.g., SpatialVID-HQ, DL3DV) and models (e.g., Pi3X, LTX-2) with non-commercial
    (NC) or gated access terms. The paper claims the model is 'open-source' and 'accessible'
    but does not explicitly state whether the final trained weights or the generated
    benchmark data are subject to these same NC restrictions. Clarify the licensing
    status of the released artifacts to prevent legal ambiguity for downstream users.
- id: e2d96c19abd4
  severity: writing
  text: The 'Broader Impact' section (Sec. 7.1) acknowledges risks of deepfakes and
    simulation misuse but lacks a concrete mitigation strategy for the specific 'minute-scale'
    capability. Given the high fidelity and long duration, the risk of generating
    convincing disinformation is elevated. Explicitly state if the model weights will
    include watermarking (e.g., SynthID, Stable Signature) or if a usage policy prohibiting
    political/defamatory generation will be enforced upon release.
- id: 9b9ce05ebb46
  severity: writing
  text: The data pipeline relies on 'public video sources' (Sec. 4) and automated
    filtering. While the paper mentions filtering for 'visual quality,' it does not
    address the potential for the training data to contain sensitive personal information
    (PII), faces, or copyrighted material that was not explicitly consented to for
    AI training. Add a statement confirming whether a PII scrubbing or face-blurring
    step was included in the annotation pipeline to mitigate privacy risks.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:45:44.294489Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses safety and ethics primarily in the "Broader Impact" section (Sec. 7.1) and the "Existing Assets and Tool Terms" table (Tab. 1 in Appendix). While the authors correctly identify the dual-use risks associated with high-fidelity video generation (e.g., deepfakes, simulation over-interpretation), the review identifies three specific areas where the safety and ethical disclosure requires strengthening before the paper can be considered fully compliant with responsible AI release standards.

First, there is a potential licensing conflict regarding the "open-source" claim. The paper states the model is open-source and accessible (Abstract, Sec. 1), yet the data pipeline relies heavily on assets with restrictive terms, such as SpatialVID-HQ (CC-BY-NC-SA 4.0), DL3DV (Custom terms), and Pi3X (CC BY-NC 4.0 for weights). The "Existing Assets" table lists these restrictions but does not explicitly clarify if the final released model weights or the generated benchmark data inherit these Non-Commercial (NC) constraints. If the model is trained on NC data, releasing it for commercial use could violate the source licenses. The authors must explicitly state the license of the final artifact and whether it is restricted to non-commercial research use only.

Second, the mitigation strategies for the identified risks are generic. The "Broader Impact" section mentions the need for "watermarks or other provenance signals" but does not confirm if the authors have implemented them. Given the model's capability to generate minute-long, 720p videos with precise camera control, the potential for creating convincing disinformation is significant. The review requires a definitive statement on whether the released model includes embedded watermarking (e.g., SynthID, as mentioned for the benchmark images) or if a specific usage policy (e.g., prohibiting political manipulation) will be enforced.

Third, the data privacy aspect of the "Robust Annotation Pipeline" (Sec. 4) is under-specified. The pipeline processes "public video clips" from sources like SpatialVID and MiraData. While the paper details filtering for aesthetic quality and motion, it does not mention any steps taken to detect and remove Personally Identifiable Information (PII), such as faces, license plates, or private locations, which are common in internet video datasets. Training on such data without consent or scrubbing poses privacy risks. The authors should clarify if a PII scrubbing or face-blurring step was integrated into the data preparation process.

Addressing these points will ensure the paper provides a complete picture of the ethical and legal implications of releasing such a powerful world model.
