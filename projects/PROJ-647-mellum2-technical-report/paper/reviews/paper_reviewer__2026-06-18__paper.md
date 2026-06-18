---
action_items:
- id: 63695720459c
  severity: writing
  text: 'Verify that every cited reference in the bibliography has `verification_status:
    verified`. Add missing verification entries or remove unverified citations.'
- id: a16dae493a3b
  severity: science
  text: "Expand the discussion of the safety regression observed after RL (HarmBench\
    \ score rising from 8.4\u202F% to 23.1\u202F%). Explain possible causes and any\
    \ mitigation steps taken or planned."
- id: cf0ecab154ba
  severity: writing
  text: "Provide more detailed reproducibility information: random seed values, exact\
    \ optimizer hyper\u2011parameters (e.g., \u03B21/\u03B22 for Muon), and any data\
    \ preprocessing scripts or versioned data splits used for pre\u2011training, long\u2011\
    context extension, SFT, and RL."
- id: c6161d9e6577
  severity: writing
  text: "Clarify the evaluation methodology for the \u201CThinking\u201D variant,\
    \ especially how multi\u2011turn conversations are unfolded and how the final\
    \ turn loss is computed. Include a brief pseudo\u2011code or algorithm box."
- id: c2fe56ed3ad8
  severity: writing
  text: "Add a limitation paragraph acknowledging the weaker performance on broad\
    \ knowledge benchmarks (e.g., MMLU\u2011Redux) and outline future work to address\
    \ this gap."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: "minor issues \u2013 citation verification, safety regression discussion,\
  \ reproducibility details"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:35:38.936146Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- **Comprehensive system description** – The paper details the architecture, long‑context extension, supervised fine‑tuning, and reinforcement‑learning stages with clear diagrams and tables.
- **Strong empirical results** – On coding (EvalPlus, LiveCodeBench) and tool‑use benchmarks the Mellum 2 variants outperform comparable 4–14 B dense baselines. The long‑context ablation is well‑supported by RULER scores.
- **Efficiency focus** – The authors demonstrate that Mellum 2 matches the per‑token compute of a 2.5 B dense model while delivering higher throughput on a single H100, which is a valuable contribution for practical deployments.
- **Open‑source release** – All checkpoints and the technical report are released under Apache 2.0, facilitating community verification and reuse.

## Concerns
- **Citation verification** – The bibliography contains many references, but the review input does not include a `verification_status` for any of them. For an accepted manuscript all citations must be verified.
- **Safety regression** – HarmBench scores increase markedly after RL (from 8.4 % to 23.1 %). The paper reports the numbers but does not analyse why the RL stage degrades safety or propose mitigation.
- **Reproducibility gaps** – While most hyper‑parameters are listed, critical details such as random seeds, exact Muon β parameters, and data‑version identifiers are missing, which hampers exact replication.
- **Knowledge performance** – Mellum 2 lags behind larger baselines on knowledge‑heavy benchmarks (e.g., MMLU‑Redux 78 % vs. 91 % for Qwen3.5‑9B). A brief discussion of this limitation would improve transparency.
- **Methodological clarity for “Thinking”** – The description of multi‑turn unfolding and loss computation for the Thinking variant could benefit from a concise algorithmic summary.

## Recommendation
The manuscript presents a solid engineering effort with strong results on code‑centric tasks and an innovative long‑context extension. However, the missing citation verification, limited analysis of the observed safety regression, and a few reproducibility omissions prevent it from being publication‑ready. I recommend **minor revision** focused on the action items listed above. Addressing these points will bring the paper to the required standard for acceptance.
