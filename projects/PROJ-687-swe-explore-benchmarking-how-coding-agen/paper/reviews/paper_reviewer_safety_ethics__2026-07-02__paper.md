---
action_items:
- id: 049e76f973ea
  severity: writing
  text: The 'Dual-Use Considerations' section (Appendix) is currently a single sentence
    recommending access controls. Given the benchmark's focus on automated code analysis
    and vulnerability discovery, expand this to explicitly detail the specific risks
    (e.g., automated vulnerability scanning, supply chain attack generation) and the
    concrete mitigation strategies implemented (e.g., data sanitization protocols,
    release restrictions).
- id: c6746278f414
  severity: writing
  text: The ground truth derivation relies on trajectories from proprietary models
    (GPT-5.4, Gemini-3-Pro, etc.). While the data is public, the methodology section
    should explicitly state whether any PII, secrets, or sensitive configuration data
    were present in the original trajectories and describe the specific sanitization
    process used to remove them before benchmark release.
- id: d1d1728d00a5
  severity: writing
  text: The selection bias limitation (requiring two successful trajectories) is acknowledged,
    but the ethics statement should briefly address whether this exclusion of unsolvable/complex
    issues might inadvertently bias the development of agents toward only 'easy' vulnerabilities,
    potentially leaving critical, hard-to-find bugs unaddressed by future tools trained
    on this data.
artifact_hash: d01bf725e90093797f2151085112b0bd34f0dac442648b3b22aae07b0ee791b3
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:44:58.359419Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses safety and ethics primarily through a brief "Ethics Statement" and a single sentence in the Appendix regarding "Dual-Use Considerations." While the authors correctly identify that the data comes from public repositories and is released under a permissive license, the current treatment of safety risks is insufficient for a benchmark explicitly designed to evaluate automated code analysis and exploration capabilities.

**Dual-Use Risks:** The benchmark isolates the "exploration" phase of software engineering, which is a critical precursor to both bug fixing and vulnerability discovery. As noted in the Appendix, there are dual-use implications. However, the current text ("Recommended access controls and monitoring") is too vague. The review requires a more robust discussion on how this benchmark could be misused to automate the discovery of zero-day vulnerabilities or to generate targeted supply chain attacks. The authors should elaborate on the specific safeguards they recommend for users of the benchmark and whether they intend to implement any access controls on the dataset itself (e.g., requiring registration or usage agreements) to prevent malicious actors from using it to train vulnerability scanners.

**Data Privacy and Sanitization:** The ground truth is derived from agent trajectories that read code files. While the source repositories are public, the trajectories themselves might have inadvertently exposed sensitive information (e.g., API keys, internal IP addresses, or PII) if the agents were not perfectly constrained or if the repositories contained such data. The "Ethics Statement" mentions data was "sanitized," but the methodology (Section 3.3 and Appendix B) lacks detail on *how* this sanitization was performed. Did the authors manually audit the trajectories? Did they use automated tools to scrub secrets? Without this detail, there is a risk that the released benchmark could inadvertently leak sensitive information that was present in the original agent logs.

**Selection Bias and Societal Impact:** The paper acknowledges a "Selection Bias Limitation" where only instances with at least two successful trajectories are included. From an ethics perspective, this creates a dataset that only represents "solvable" problems. If future agents are trained or evaluated primarily on this benchmark, they may become optimized for finding easy-to-locate bugs while failing to address more complex, critical, or obscure vulnerabilities. The authors should briefly discuss this potential societal impact in the ethics statement, acknowledging that the benchmark's design might skew the development of coding agents toward less critical issues.

The paper is generally sound in its scientific approach, but the safety and ethics sections require expansion to meet the standards expected for a benchmark with significant dual-use potential.
