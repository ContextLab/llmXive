---
action_items:
- id: f8e99afeac2a
  severity: writing
  text: The paper describes using 'WorldPlay' to generate synthetic training videos
    from OpenVid images (Sec 4.3). As this involves generating realistic video content
    from potentially uncurated internet images, the authors must explicitly state
    the data filtering protocols used to prevent the model from learning from or reproducing
    harmful, biased, or copyrighted content present in the source images.
- id: 9d0607516e7f
  severity: writing
  text: The framework enables 'real-time interactive' video generation with camera
    control (Abstract, Sec 1). This capability carries dual-use risks for generating
    deepfakes or disinformation. The manuscript currently lacks a dedicated 'Ethical
    Considerations' or 'Limitations' section discussing potential misuse, mitigation
    strategies (e.g., watermarking), and responsible release guidelines for the open-source
    code.
- id: 885c6c1ee0d7
  severity: writing
  text: The ablation study in Sec 4.3 notes that models trained on 'SpatialVid' (perception-estimated
    poses) failed, while those trained on 'DL3DV' (reconstructed scenes) succeeded.
    The authors should clarify the provenance and consent status of the DL3DV dataset,
    specifically whether the 3D reconstructions were performed on data with appropriate
    usage rights for training generative models.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:44:46.935288Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents minWM, a framework for converting video diffusion models into interactive world models. From a safety and ethics perspective, the paper is largely descriptive of a technical pipeline but lacks necessary disclosures regarding the potential for misuse and data provenance.

First, the paper highlights the generation of synthetic training data using WorldPlay on images from OpenVid (Section 4.3, "Training data"). OpenVid is a large-scale dataset scraped from the internet. The authors do not specify any filtering mechanisms applied to these source images to remove harmful, illegal, or copyrighted content before using them to train the video generation model. Without explicit confirmation of data curation and safety filtering, there is a risk that the resulting world models could inadvertently learn and reproduce biases or harmful content present in the raw internet data.

Second, the core contribution is a "real-time interactive" video generation system (Abstract, Introduction). Such technology has significant dual-use potential, including the creation of realistic deepfakes, disinformation campaigns, or non-consensual synthetic media. The manuscript currently treats the technology purely as a scientific advancement without addressing these societal risks. Standard practice for such frameworks requires a dedicated section on "Ethical Considerations" or "Broader Impacts" that discusses potential misuse, the authors' stance on responsible use, and any technical safeguards (e.g., watermarking, usage policies) implemented or recommended for the open-source release.

Finally, while the authors mention using DL3DV for 3D reconstruction to create ground-truth camera trajectories (Section 4.3), they do not explicitly confirm the licensing and consent status of the source videos used for reconstruction. Given the sensitivity of 3D reconstruction and generative training, a brief statement confirming that the source data was used in accordance with its license and privacy guidelines would be prudent.

The paper should be revised to include a discussion on data safety filtering, potential misuse scenarios, and responsible release guidelines before it can be considered fully compliant with safety and ethics standards.
