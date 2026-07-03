---
action_items:
- id: 441b5ed49919
  severity: science
  text: The 'Ethical Considerations' section (sec/6_limitations.tex) states that all
    human motion recordings are obtained with 'informed consent' but fails to specify
    the IRB approval number or the specific consent protocol used for the 'large internally
    captured dataset' mentioned in the Introduction. Given the use of human subjects
    for data collection, explicit IRB documentation is required to verify compliance
    with ethical standards.
- id: 5ab3343ad1b0
  severity: science
  text: The paper describes deploying a high-speed, zero-shot motion tracker on a
    physical humanoid (Unitree-G1) capable of 'collaboratively carrying boxes' and
    executing 'high-dynamic' motions. The safety section mentions an 'emergency stop
    mechanism' but lacks a quantitative risk assessment or a detailed safety protocol
    for human-robot interaction (HRI) in unstructured environments, which is critical
    for preventing physical harm during real-world deployment.
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:27:37.033459Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses safety and ethics primarily in the dedicated "Ethical Considerations" section (sec/6_limitations.tex). While the authors acknowledge potential risks such as physical collisions and misuse, the current disclosure is insufficient for a work involving large-scale human data collection and physical robot deployment.

First, regarding data privacy and consent, the authors claim in sec/6_limitations.tex that "All human motion recordings are obtained with informed consent." However, the paper aggregates a "large internally captured dataset" (Introduction, sec/1_intro.tex) alongside public datasets. For the internal data, the manuscript lacks specific details regarding the Institutional Review Board (IRB) approval process, the specific consent forms used, and how data anonymization was technically enforced beyond "stripping personal identifiers." In the context of motion capture, which can be biometrically identifying, a more rigorous description of the consent protocol and IRB oversight is necessary to ensure compliance with ethical research standards.

Second, the deployment of a zero-shot, high-agility controller on a physical humanoid robot introduces significant safety risks. The "Robot Safety" paragraph acknowledges the risk of collision and falls but relies on a generic "emergency stop mechanism." Given the system's capability to perform complex, dynamic tasks like "collaboratively carrying boxes" (sec/4_experiments.tex, Fig. show1) in real-time, the review requires a more concrete safety framework. This should include a quantitative risk assessment, specific fail-safe logic (e.g., force-limiting, collision detection thresholds), and a clear protocol for human-in-the-loop supervision during the reported real-world experiments. The current text is too vague to assure that the system is safe for the described applications.

Finally, while the "Misuse Potential" paragraph correctly identifies risks like surveillance, it does not propose specific technical mitigations (e.g., watermarking, usage restrictions in the model weights) to prevent the model from being repurposed for malicious imitation or unauthorized surveillance, which is a standard expectation for powerful generative models.
