---
action_items:
- id: 0342f13f4d68
  severity: writing
  text: The claim of 'director-level control' (Abstract, Intro) is overreaching. The
    paper demonstrates camera motion cloning but lacks evidence for controlling narrative
    depth or emotional atmosphere. Qualify this claim to 'camera motion control' or
    provide metrics for narrative alignment.
- id: 1313e5e2fe0b
  severity: science
  text: The 'Emergent Camera Understanding' section (Section 5.3) overstates generalization.
    Claiming the model executes dolly zooms 'without requiring explicitly curated
    training data' (lines 430-435) is unsupported, as Figure 2 shows these were rendered
    in training. Clarify that this is learned behavior, not zero-shot emergence.
- id: 4381eec1b4b9
  severity: writing
  text: The assertion that the Prompt Expansion Agent 'completely decouples' camera
    signals (Section 4.2, lines 330-332) is absolute and unsupported. Table 1 shows
    a 3.38% leakage rate. Replace 'completely decouples' with 'significantly reduces
    leakage' to align with quantitative evidence.
artifact_hash: a65d314d17ec7712e12f1ec0ba7f4dba5e22b080c532708ee9eae2b427ffd22c
artifact_path: projects/PROJ-708-omnidirector-general-multi-shot-camera-c/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T06:47:10.829958Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the scope and capabilities of OmniDirector that exceed the evidence provided in the experiments.

First, the term "director-level control" is used repeatedly in the Abstract, Introduction, and Conclusion to describe the framework's capabilities. While the paper successfully demonstrates high-fidelity cloning of camera trajectories and shot transitions, the term "director-level" implies control over narrative structure, emotional tone, and character performance. The current evaluation metrics (RRE, RTE, leakage rate) only measure geometric and content fidelity, not narrative or emotional alignment. Without specific experiments or metrics addressing these higher-level cinematic attributes, the claim of "director-level control" is an overreach. The authors should qualify this claim to reflect the specific scope of camera motion and shot transition control demonstrated.

Second, the "Emergent Camera Understanding" section (Section 5.3) presents a significant over-interpretation of the results. The authors claim that the model can clone complex effects like the "Hitchcock zoom" (dolly zoom) and fisheye distortion "without requiring explicitly curated training data for such specific trajectories" (lines 430-435). However, Figure 2 explicitly shows that the training data generation process includes rendering dolly zooms and fisheye distortions. Therefore, the model's ability to reproduce these effects is a result of exposure to these specific patterns during training, not an emergent zero-shot capability. The claim of "emergent" behavior is misleading and contradicts the methodology described in Section 3.1.2. The text should be revised to accurately reflect that these capabilities are learned from the curated training distribution.

Finally, the claim that the Prompt Expansion agent "completely decouples" the camera signal from the reference video (Section 4.2, lines 330-332) is too absolute. The quantitative results in Table 1 show a non-zero leakage rate of 3.38% for the proposed method. While this is a significant improvement over baselines, it is not "complete" decoupling. The language should be adjusted to "significantly reduces" or "effectively decouples" to maintain scientific rigor and align with the reported metrics.
