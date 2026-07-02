---
action_items:
- id: b8156fdb5ef6
  severity: writing
  text: The paper describes collecting 450 real-world robot trajectories via human
    teleoperation (Sec. Real-World Experiments) but lacks explicit IRB/ethics approval
    statements or consent protocols for the human operators. Given the use of human
    data for training AI, a statement on ethical clearance and informed consent is
    required.
- id: 9e88492fdbde
  severity: writing
  text: The data engine relies on large-scale human egocentric video (Ego4D, EPIC-Kitchens).
    The manuscript does not address potential privacy risks, such as the presence
    of identifiable faces, license plates, or sensitive locations in the source videos,
    nor does it detail the anonymization or blurring procedures applied before training.
- id: aa764ed6814f
  severity: writing
  text: The system is designed to learn 'affordance and safety' (Tab. QA families)
    and execute actions on physical objects (vegetables). The paper lacks a discussion
    on safety constraints, failure modes, or human-in-the-loop safeguards required
    when deploying a model that might generate unsafe physical actions in unstructured
    real-world environments.
artifact_hash: bf25ed8c32843a89226c47ca4dcbfcdb0c63d6720d9c7d52a55697f1d16cf9dc
artifact_path: projects/PROJ-600-https-arxiv-org-abs-2605-15298/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:27:35.364823Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel approach to training Vision-Language-Action (VLA) models using human egocentric video to derive physical commonsense priors. From a safety and ethics perspective, the paper raises several concerns regarding data privacy, human subject protection, and the potential for physical harm during deployment that require clarification before acceptance.

**Human Subject Data and Consent**
In Section "Real-World Experiments" (lines 430-445), the authors describe collecting 450 demonstration trajectories using a SpaceMouse to control a Franka robot arm. While this involves human operators, the manuscript does not mention Institutional Review Board (IRB) approval or informed consent procedures. Even if the operators are the authors or lab members, standard ethical guidelines for research involving human participants (especially when data is used to train public models) require explicit documentation of consent and ethical clearance. The authors should add a statement confirming that the data collection protocol was reviewed and approved by an ethics committee and that all participants provided informed consent.

**Privacy in Egocentric Video Sources**
The data engine relies heavily on large-scale public datasets like Ego4D, EPIC-Kitchens, and EgoDex (Section "Data Sources and Staged Construction"). These datasets often contain uncurated, real-world footage that may include identifiable faces, private residences, license plates, or other sensitive information. The paper does not describe any privacy-preserving measures, such as face blurring, license plate redaction, or filtering of sensitive content, applied to the training data. Given the trend of models memorizing training data, there is a risk that the model could inadvertently reproduce private information. The authors must detail the privacy safeguards implemented during the data preprocessing and annotation pipeline.

**Physical Safety and Dual-Use Risks**
The system is explicitly trained to understand "affordance and safety" (Table "QA families") and is evaluated on real-world manipulation tasks involving physical objects (vegetables). While the current experiments are benign, the capability to learn physical interaction from video could theoretically be adapted for harmful purposes (e.g., learning to manipulate dangerous objects or bypass safety protocols). The paper lacks a discussion on the safety constraints embedded in the model's action space or the deployment of "guardrails" to prevent the generation of unsafe physical actions. Furthermore, the "Real-World Experiments" section describes a robot operating in a physical space; there is no mention of emergency stop mechanisms, human supervision protocols, or safety zones used during the data collection and evaluation phases to prevent physical injury to operators or damage to property.

**Recommendation**
The authors should revise the manuscript to include:
1. A statement on IRB approval and informed consent for the real-world data collection.
2. A description of privacy-preserving techniques applied to the egocentric video datasets.
3. A discussion on safety mechanisms, failure modes, and potential dual-use risks associated with the learned physical priors.

These additions are necessary to ensure the research adheres to ethical standards for AI development and deployment.
