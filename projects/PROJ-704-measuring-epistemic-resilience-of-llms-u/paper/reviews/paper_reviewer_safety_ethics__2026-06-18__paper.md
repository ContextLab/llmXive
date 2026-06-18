---
action_items:
- id: f86141531827
  severity: science
  text: "The release of a large corpus of fabricated medical statements (the misleading\u2011\
    context injections) creates a clear dual\u2011use risk; malicious actors could\
    \ repurpose the dataset to train or fine\u2011tune models that generate persuasive\
    \ medical misinformation. Require a detailed risk\u2011mitigation plan (e.g.,\
    \ restricted access, watermarking, usage\u2011license clauses) before public distribution."
- id: 1e9c51380955
  severity: writing
  text: "The manuscript mentions a 14\u2011member clinician panel but does not provide\
    \ evidence of Institutional Review Board (IRB) or equivalent ethical approval\
    \ for the human\u2011subject review process. Add a statement confirming IRB/ethics\u2011\
    committee approval or an exemption justification."
- id: 05b9549c1939
  severity: writing
  text: "Although the source questions are from public benchmarks, verify that no\
    \ patient\u2011identifiable information (PHI) is present in any of the injected\
    \ contexts or in the original vignettes. Include an explicit data\u2011privacy\
    \ audit statement."
- id: 84eaafc2d0e6
  severity: science
  text: "The benchmark could inadvertently be used to improve adversarial attacks\
    \ on medical LLMs. Discuss safeguards such as limiting the release to research\u2011\
    only licenses, providing guidance on responsible use, and encouraging the community\
    \ to develop defensive techniques alongside the benchmark."
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:47:09.562251Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper introduces **MedMisBench**, a benchmark that systematically injects misleading medical context into existing multiple‑choice questions to evaluate “epistemic resilience” of large language models (LLMs). From a safety and ethics perspective, the work raises several important concerns that need to be addressed before the manuscript can be accepted.

**Dual‑use risk.**  
The core contribution is a large, publicly released set of fabricated medical statements (≈ 48 k misleading‑context option pairs). While the authors intend the dataset to expose model vulnerabilities, the same resource could be repurposed by malicious actors to train or fine‑tune LLMs that generate persuasive medical misinformation. The manuscript does not discuss this dual‑use potential in depth, nor does it outline concrete mitigation measures (e.g., restricted distribution, licensing, watermarking, or a controlled‑access repository). A responsible‑use statement and a concrete risk‑mitigation plan are essential.

**Human‑subject review ethics.**  
The clinician panel that validates benchmark items and assesses response harm involves 14 clinicians from seven countries. The paper states that reviewers evaluated items but provides no documentation of Institutional Review Board (IRB) or ethics‑committee approval, nor does it describe consent procedures for the reviewers. Even though the data are de‑identified, formal ethical oversight is required for any study involving human participants, including expert reviewers. The authors should include an IRB approval number or a clear exemption rationale.

**Data privacy.**  
All source questions are drawn from public medical QA datasets, but the manuscript does not explicitly confirm that no protected health information (PHI) is present in any vignette or injected sentence. Given the medical domain, a brief audit confirming the absence of PHI (or a statement that the data were screened for PHI) should be added to satisfy privacy standards.

**Potential for harm in downstream use.**  
The benchmark’s evaluation shows that many state‑of‑the‑art LLMs flip from correct to harmful answers when exposed to a single misleading sentence. While this is valuable for research, the release of the benchmark without accompanying defensive guidelines could enable developers to benchmark and subsequently improve the very attacks the paper highlights. The discussion should be expanded to include recommendations for responsible deployment, such as: (1) releasing the dataset under a research‑only license, (2) encouraging the development of detection and mitigation techniques alongside the benchmark, and (3) providing a “red‑team/blue‑team” framework for future work.

**Mitigation experiments.**  
The paper presents two mitigation case studies (search‑based verification and a defensive prompt). These are promising but limited in scope. It would strengthen the safety contribution to (a) evaluate additional, more robust defenses (e.g., factuality‑checking models, chain‑of‑thought prompting with external verification), and (b) report any trade‑offs in terms of latency or computational cost, as these affect real‑world deployment decisions.

**Overall assessment.**  
The manuscript makes a novel technical contribution by defining “epistemic resilience” and providing a benchmark that reveals a critical blind spot in current medical LLM evaluation. However, the safety and ethics implications of releasing a large corpus of plausible‑looking medical misinformation are not sufficiently addressed. The authors should incorporate a thorough discussion of dual‑use risks, provide evidence of ethical oversight for the clinician review, confirm the absence of PHI, and outline concrete responsible‑use policies. Addressing these points will mitigate the primary safety concerns and make the work suitable for publication.
