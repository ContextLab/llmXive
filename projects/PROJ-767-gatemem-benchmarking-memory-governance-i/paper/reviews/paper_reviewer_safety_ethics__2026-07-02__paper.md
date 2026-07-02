---
action_items:
- id: 976a7edd83ce
  severity: writing
  text: The dataset contains sensitive simulated PII (medical diagnoses, household
    codes). Explicitly detail the IRB/ethics approval status or the specific de-identification/synthetic
    generation protocols used to ensure no real individuals are represented, as required
    for human-subject-adjacent benchmarks.
- id: d9098d814021
  severity: writing
  text: The 'Active Forgetting' evaluation relies on LLM judges to detect 'leaks'
    of deleted data. Add a specific safety warning in the appendix regarding the risk
    of the judge model itself hallucinating or inadvertently reproducing the 'leak_targets'
    it is supposed to audit, potentially creating a feedback loop of exposure.
- id: bb9c4d1cd966
  severity: writing
  text: The benchmark includes 'social engineering' and 'authority pressure' attack
    vectors (Appendix A1). Clarify that these are strictly simulated within the dataset
    generation pipeline and that the evaluation protocol does not involve real-world
    adversarial testing against live agents to prevent accidental deployment of harmful
    prompts.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:07:25.280049Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses a critical safety gap: the governance of shared memory in multi-principal LLM agents. The focus on access control and active forgetting is highly relevant to preventing privacy violations in institutional settings. However, several ethical and safety documentation gaps must be addressed before the benchmark can be safely adopted or the results fully trusted.

First, the dataset construction involves generating "realistic" episodes containing sensitive information such as medical diagnoses (e.g., STI charts, Hepatitis C), household access codes, and financial details. While the authors state the data is generated, there is no explicit statement regarding Institutional Review Board (IRB) approval or the specific ethical framework used to generate this synthetic data. Given the sensitivity of the topics, the authors must clarify whether the generation process involved human annotators who were exposed to these sensitive prompts, and if so, what protections were in place. If the data is purely synthetic, a statement confirming that no real-world data was used and that the content is entirely fabricated to avoid representing actual individuals is required.

Second, the evaluation methodology relies heavily on an LLM-as-a-judge to detect "leaks" of protected information (Section 3.3, Appendix A3). There is a non-trivial safety risk that the judge model, when prompted with "leak_targets" to check for their presence, might inadvertently reproduce or "hallucinate" these targets in its own output (the `notes` field), effectively leaking the sensitive data it is supposed to be auditing. The prompt template in Appendix A3 includes a "CRITICAL SAFETY FOR THE JUDGE" instruction, but the authors should explicitly discuss the results of any self-consistency checks or red-teaming performed on the judge itself to ensure it does not become a vector for data leakage during the evaluation process.

Finally, the benchmark includes "social engineering" and "authority pressure" attack vectors (Appendix A1). While these are necessary for a robust evaluation, the paper should explicitly state that these prompts are strictly confined to the offline benchmarking environment. There must be a clear disclaimer that these prompts are not intended for, and should not be used in, live adversarial testing against deployed agents without further safety alignment, to prevent the accidental release of harmful prompt engineering techniques into the wild.

Addressing these points will ensure the benchmark is ethically sound and that the evaluation process itself does not introduce new safety risks.
