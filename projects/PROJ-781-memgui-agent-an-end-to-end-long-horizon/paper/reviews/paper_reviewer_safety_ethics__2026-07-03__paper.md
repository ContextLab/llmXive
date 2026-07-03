---
action_items:
- id: 0018978e8aa7
  severity: writing
  text: The paper describes generating 2,956 trajectories via a 'teacher' model (Qwen3-VL-235B)
    and filtering for 'reasonableness' (Sec 3, e000). Explicitly state the safety
    guidelines used to filter harmful or privacy-violating actions during this synthetic
    data generation to ensure the dataset does not encode unsafe behaviors.
- id: a30b2d2b7965
  severity: writing
  text: The system performs autonomous actions on mobile devices (Sec 2, e000). The
    'Limitations' section (e000) mentions platform scope but omits safety constraints.
    Add a statement clarifying that the agent is restricted to non-destructive actions
    and includes a 'human-in-the-loop' or 'kill-switch' mechanism for real-world deployment.
- id: 41990fc2c6e3
  severity: writing
  text: The dataset (MemGUI-3K) and benchmarks (MemGUI-Bench) likely contain screenshots
    of real or simulated mobile interfaces (Sec 3, e000). Confirm in the 'Data Availability'
    section that all user data, PII, and sensitive credentials in the training trajectories
    have been redacted or synthesized to prevent privacy leakage.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:53:02.474345Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents MemGUI-Agent, an end-to-end mobile GUI agent with proactive context management. From a safety and ethics perspective, the work is generally sound but lacks explicit declarations regarding the safety protocols used in data generation and deployment constraints.

**Data Generation and Safety Filtering:**
In Section 3 (e000), the authors describe constructing the MemGUI-3K dataset by rolling out a teacher model (Qwen3-VL-235B-Thinking) and filtering for "step-level reasonableness" (75.7% reasonable steps). While the term "reasonableness" is used, the specific criteria for this filter are not detailed. Given that the agent operates on mobile devices, there is a risk that the synthetic data could inadvertently include sequences of actions that are technically valid but unsafe (e.g., unauthorized data deletion, bypassing security prompts, or interacting with sensitive apps). The authors should explicitly state the safety guidelines or reward models used to filter these trajectories to ensure the dataset does not propagate harmful behaviors.

**Deployment Constraints and Dual-Use:**
The system is designed for autonomous execution of long-horizon tasks on mobile devices (Section 2, e000). While the paper focuses on performance, it does not address the potential for misuse (e.g., automated spamming, credential harvesting, or bypassing user consent mechanisms). The "Limitations" section (e000) currently only addresses platform scope (Android vs. iOS). It is recommended to add a paragraph clarifying that the agent is intended for benign automation tasks and includes inherent constraints (e.g., read-only modes, confirmation steps for destructive actions) or that the authors have implemented a "kill-switch" mechanism for real-world testing to prevent uncontrolled execution.

**Privacy and Data Handling:**
The dataset and benchmarks rely on screenshots and UI states (Section 3, e000; Figure 3). Even if synthetic, these interfaces may mimic real applications containing Personally Identifiable Information (PII) or sensitive data patterns. The authors should confirm in the "Data & Code Availability" section (e002) that all user data, credentials, and PII in the training trajectories have been rigorously redacted or that the data is entirely synthetic to prevent privacy leakage upon public release.

**Conclusion:**
The paper does not present immediate fatal ethical flaws, but the lack of explicit safety protocols in the data generation pipeline and deployment constraints requires clarification to meet standard safety ethics guidelines for autonomous agent research.
