---
action_items:
- id: e3806d8bfdd4
  severity: writing
  text: The paper lacks an explicit statement regarding IRB approval or ethical review
    for the human-in-the-loop data collection or annotation processes used to construct
    the MemGUI-3K dataset. Please add a statement in Section 3 (Dataset) confirming
    whether human annotators were involved and if their participation was reviewed
    by an ethics board.
- id: 2dcd39ab708b
  severity: writing
  text: The dataset construction involves 'entity substitution' and 'task simplification'
    on seed tasks. The authors must clarify the provenance of these seed tasks. If
    they were scraped from public app stores or user forums, a statement on data privacy,
    terms of service compliance, and the exclusion of PII (Personally Identifiable
    Information) is required.
- id: 1c44207de26a
  severity: writing
  text: The agent is designed to perform autonomous actions (click, type, swipe) on
    mobile devices. The paper should include a 'Safety and Limitations' subsection
    explicitly stating that the agent is not intended for use in environments where
    it could cause financial harm, privacy violations, or unauthorized access, and
    that it lacks a 'human-in-the-loop' safety override mechanism.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:23:13.365329Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

**Safety and Ethics Review**

The manuscript presents MemGUI-Agent, an autonomous mobile GUI agent capable of long-horizon task execution. While the technical contribution is significant, the paper currently lacks sufficient detail regarding the ethical implications of the data used and the potential risks of deploying such an autonomous agent.

**1. Data Provenance and Privacy (Section 3)**
The construction of the **MemGUI-3K** dataset is central to the paper's claims. Section 3.2 mentions expanding 128 seed tasks via "entity substitution" and "task simplification." However, the source of these seed tasks is not explicitly defined.
*   If the seed tasks were derived from real user interactions or scraped from public app stores/forums, the authors must address **data privacy**. Specifically, a statement is needed confirming that all Personally Identifiable Information (PII) (e.g., user names, phone numbers, addresses, financial data) was scrubbed from the trajectories before inclusion in the dataset.
*   If human annotators were involved in creating or verifying the trajectories, the paper must state whether this process received **IRB (Institutional Review Board)** approval or adhered to standard ethical guidelines for human-subject research. Currently, Section 3.2 and the Appendix (Section 4) lack this declaration.

**2. Dual-Use and Autonomous Action Risks (Section 2 & 6)**
The agent is designed to execute actions (`click`, `type`, `swipe`) autonomously on a mobile device. This capability introduces **dual-use risks**:
*   **Malicious Automation:** The agent could theoretically be repurposed to perform unauthorized actions, such as making in-app purchases, sending messages to contacts, or scraping sensitive data from a device without the user's explicit, real-time consent.
*   **Lack of Safety Guardrails:** The current prompt templates (Appendix) and action space do not appear to include explicit "safety checks" or "human-in-the-loop" confirmation steps for high-risk actions (e.g., deleting data, transferring money, or changing system settings).
*   **Recommendation:** The authors should add a dedicated paragraph in the **Limitations** section (Section 5) or a new **Safety Considerations** section. This should explicitly state that the agent is intended for benign research purposes, acknowledge the potential for misuse, and clarify that the current implementation does not include built-in safeguards against malicious deployment.

**3. Benchmark Integrity**
The benchmarks (MemGUI-Bench, MobileWorld) involve interacting with real or simulated apps. The authors should confirm that the evaluation protocol does not involve interacting with live user accounts or sensitive data during the automated testing phase, ensuring that the benchmarking process itself does not violate privacy norms or terms of service of the applications tested.

**Conclusion**
The paper is technically sound but requires minor revisions to address ethical transparency regarding data collection and to explicitly acknowledge the safety risks associated with autonomous mobile agents. Adding the requested statements will ensure the work meets standard ethical publication requirements.
