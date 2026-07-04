---
action_items:
- id: dc4891449243
  severity: writing
  text: 'Section 4.1 (Hardware-Aware Fast Top-p Decoding Kernel): The term ''CTA''
    (Compute Thread Array) is used without definition. While standard in CUDA programming,
    it is not universally known to all adjacent-field PhDs (e.g., those in NLP or
    statistics). Define it at first use: ''CTA (Compute Thread Array, the basic execution
    unit in CUDA)''.'
- id: 5fdbe6456aa1
  severity: writing
  text: "Section 4.1: The symbol $p_\text{top}$ appears in the text ('cumulative attention\
    \ mass reaches $p_\text{top}$') without prior definition. The parameter is referred\
    \ to as 'Top-$p$' or 'p' elsewhere (e.g., Table 1, Section 3.2). Define $p_\t\
    ext{top}$ explicitly as the cumulative probability threshold (e.g., 0.9) where\
    \ it first appears in Section 4.1."
- id: 4afa5e3a6e74
  severity: writing
  text: "Section 4.1: The term 'log-sum-exp pair $(m_b, \ell_b)$' is used without\
    \ defining the variables $m_b$ and $\ell_b$. An adjacent-field reader may not\
    \ know these represent the maximum and log-sum-exp values used in the stable softmax\
    \ computation. Add a brief clause: '...reduces it to a block-level log-sum-exp\
    \ pair $(m_b, \ell_b)$, where $m_b$ is the block maximum and $\ell_b$ is the log-sum-exp\
    \ value.'"
- id: 29aa34f72b71
  severity: writing
  text: 'Section 4.1: The term ''SM'' is used (''allows the SM to maximize concurrent
    CTAs'') without definition. In CUDA context, this stands for Streaming Multiprocessor.
    Define it at first use: ''...allows the SM (Streaming Multiprocessor) to maximize...'''
- id: 25cdb8fec9e4
  severity: writing
  text: "Section 4.1: The term 'half2' is used ('vectorized $\texttt{half2}$ instructions')\
    \ without explanation. While common in GPU optimization, it refers to a 2-element\
    \ vector of 16-bit floats. A reader from a non-systems adjacent field might not\
    \ know this. Add a brief gloss: '...via vectorized $\texttt{half2}$ (2-element\
    \ 16-bit float vector) instructions...'"
- id: 8c56fd0a2dbf
  severity: writing
  text: 'Section 3.2: The term ''attention sinks'' is used in the phrase ''sliding
    window with attention sinks'' without definition. While ''streamingLLM'' is cited,
    the concept of ''sinks'' (specific tokens that attract attention to stabilize
    the distribution) is not explained. Add a brief parenthetical: ''...sliding window
    with attention sinks (specific tokens that attract attention to stabilize the
    distribution)...'''
artifact_hash: 898687640cf9d8b6eab95a3e688a2f4f6333ec4f1546846934c46563afd8ae37
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:59:43.902524Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-written and avoids excessive in-group slang, but it relies on several CUDA-specific and systems-level terms that are undefined, creating barriers for a competent reader from an adjacent field (e.g., NLP, statistics, or general ML) who may not be familiar with GPU architecture internals.

Specifically, Section 4.1 introduces a dense string of CUDA terminology without glossing. Terms like "CTA" (Compute Thread Array), "SM" (Streaming Multiprocessor), and "half2" are used as if they are common knowledge. While standard for GPU kernel developers, they are not standard vocabulary for a general ML researcher. Similarly, the mathematical notation in the kernel description, specifically the "log-sum-exp pair $(m_b, \ell_b)$" and the variable $p_\text{top}$, lacks explicit definition in the text where they first appear. The reader is forced to infer the meaning of $m_b$ and $\ell_b$ from context or prior knowledge of stable softmax implementations, which violates the self-containment requirement.

Additionally, the term "attention sinks" in Section 3.2 is used without a brief operational definition, relying solely on a citation to "streamingLLM". While the concept is central to the method, a reader unfamiliar with that specific prior work would not know what a "sink" is in this context.

These are minor, text-only fixes. Adding one-sentence definitions or parenthetical glosses for these terms would make the paper fully accessible to the target audience without altering the scientific content.
