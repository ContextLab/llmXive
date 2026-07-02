---
action_items:
- id: 76630c84c84d
  severity: writing
  text: The 'Ethics Statements' section (Section 'Ethics Statements') claims data
    was 'sampled and validated' to avoid offensive content but lacks specific details
    on the validation protocol, sample size, or human-in-the-loop review process.
    Explicitly describe the annotation guidelines and validation steps taken to ensure
    the retail dataset contains no PII or harmful content.
- id: 364260504b0d
  severity: writing
  text: The 'Model Usage' subsection notes the use of proprietary APIs (GPT-5.4, Gemini)
    and local open-source models. Clarify the data privacy implications of sending
    user queries and intermediate tool states to third-party API providers, and confirm
    that no sensitive user data is being processed or stored by these external services.
- id: 2dbcc125cc3c
  severity: writing
  text: The benchmark simulates 'blocking' and 'noisy tools' (Section 3.2) to test
    robustness. While currently in a retail domain, explicitly address the potential
    for dual-use if this framework were adapted to simulate attacks on real-world
    financial or medical systems (e.g., testing how agents handle manipulated API
    responses in critical infrastructure).
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:34:07.383167Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a benchmark for evaluating LLM agents in large-scale tool ecosystems, focusing on planning under unreliable tool access. From a safety and ethics perspective, the paper is generally sound but requires specific clarifications to fully address data privacy, validation rigor, and potential dual-use risks.

First, the **Ethics Statements** section (located after the abstract) asserts that the retail-focused benchmark is unlikely to contain offensive material and that data was "sampled and validated." However, it lacks the necessary granularity to verify this claim. The authors should explicitly detail the validation protocol: Was there a human review step? What were the specific criteria for "offensive content" or "PII" in a retail context? How many samples were reviewed? Without these details, the claim of "minimal societal risk" remains unsubstantiated. This is a standard requirement for datasets involving generated or curated text.

Second, regarding **Data Privacy and Model Usage**, the paper notes the use of proprietary models (GPT-5.4, Gemini) via APIs and local open-source models. When evaluating agents that process queries and tool states, there is an implicit risk of data leakage to third-party API providers. The authors should add a statement confirming that the benchmark queries do not contain real-world Personally Identifiable Information (PII) and that the synthetic nature of the data mitigates privacy risks when sent to external APIs. If any real-world data was used for construction, a formal IRB or data usage agreement statement is required.

Third, while the current application is in the **retail domain**, the methodology involves simulating "blocking," "implicit failures," and "misleading tools." This framework has potential **dual-use** implications. If adapted to critical infrastructure (e.g., financial trading, medical diagnosis, or industrial control systems), the ability to test how agents handle manipulated or failing APIs could be used to identify vulnerabilities in real-world systems. The authors should include a brief discussion in the Limitations or Ethics section acknowledging this potential for misuse and emphasizing that the benchmark is intended for defensive robustness testing only.

Finally, the paper mentions that "All annotations were performed by the authors." If these annotations involved human judgment on the quality or safety of the generated tasks, the authors should briefly mention the qualifications of the annotators and any inter-annotator agreement metrics to ensure the safety validation is rigorous.

Addressing these points will strengthen the paper's ethical standing and ensure transparency regarding data handling and potential risks.
