---
action_items:
- id: 4c1c5783141f
  severity: writing
  text: The acronym 'MPI' is defined in the preamble as 'Message Passing Interface'
    (line 42), conflicting with the paper's usage for 'Manifold Power Iteration'.
    Remove the conflicting preamble definition and define 'Manifold Power Iteration'
    clearly at first use in the abstract or introduction.
- id: '808183665638'
  severity: writing
  text: Replace the industry slang 'midtrain' (Section 5.2) with 'continued pretraining'
    to ensure clarity for non-specialist readers unfamiliar with this specific training
    phase terminology.
- id: fed786877ca0
  severity: writing
  text: Define the metric 'MaxVio' (Section 5.2, Table 4) at first use. The text mentions
    it reflects load balance but does not define the acronym (e.g., Maximum Violation)
    or its calculation.
- id: 030b6c65aa92
  severity: writing
  text: Correct the typo 'Opimization' to 'Optimization' in Section 5.1 and briefly
    explain 'Hyperball Optimization' (e.g., constraining weights to a hypersphere)
    for readers unfamiliar with the cited work.
- id: 46ee77488278
  severity: writing
  text: Correct the grammatical error 'Principle Singular direction' to 'Principal
    Singular direction' in Section 6.1 to align with standard linear algebra terminology
    and avoid confusion.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T10:01:33.510169Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and jargon that are either undefined, conflicting, or prone to confusion for a broader audience. The most critical issue is the definition of **MPI**. In the preamble (line 42), `MPI` is explicitly defined as "Message Passing Interface," a ubiquitous standard in parallel computing. However, the authors use `MPI` throughout the text to refer to their proposed "Manifold Power Iteration." This contradiction will inevitably confuse readers, particularly those from systems backgrounds, and must be resolved by removing the conflicting preamble definition and ensuring the paper's specific acronym is defined clearly at first use in the abstract or introduction.

Furthermore, several terms are used without sufficient context for non-specialists. The term **"midtrain"** (Section 5.2) is industry slang for continued pretraining; replacing this with "continued pretraining" would improve clarity. The metric **"MaxVio"** (Section 5.2, Table 4) is introduced without definition; the full name (e.g., Maximum Violation) and a brief explanation of what it measures are required. Additionally, **"Hyperball Optimization"** is mentioned with a typo ("Opimization") and without a plain-language explanation of the geometric constraint it imposes. Finally, the phrase "Principle Singular direction" (Section 6.1) should be corrected to "Principal" to align with standard linear algebra terminology. Addressing these points is essential to ensure the paper is accessible to readers outside the immediate sub-field of MoE router optimization.
