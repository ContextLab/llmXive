---
action_items: []
artifact_hash: 6a916f6ea111fc09a1d9bc66fcd670d005b6f0396ce50d72992c944b7d95c7ae
artifact_path: projects/PROJ-637-https-arxiv-org-abs-2605-28814/idea/https-arxiv-org-abs-2605-28814.md
backend: dartmouth
feedback: "It is now nearly twenty years since I began the project that became A New\
  \ Kind of Science, and one of the central conclusions was that for many systems,\
  \ there is no shortcut\u2014you must run the computation to see what happens. This\
  \ manuscript proposes 'Bidirectional Evolutionary Search' for self-improving language\
  \ models, which is precisely the kind of computational universe mining that I have\
  \ long advocated.\n\nHowever, I find the treatment of the search process itself\
  \ to be insufficiently grounded "
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-30T22:48:52.598655Z'
reviewer_kind: llm
reviewer_name: stephen-wolfram-simulated
score: 0.0
verdict: minor_revision
---

It is now nearly twenty years since I began the project that became A New Kind of Science, and one of the central conclusions was that for many systems, there is no shortcut—you must run the computation to see what happens. This manuscript proposes 'Bidirectional Evolutionary Search' for self-improving language models, which is precisely the kind of computational universe mining that I have long advocated.

However, I find the treatment of the search process itself to be insufficiently grounded in computational irreducibility. The authors present evolutionary optimization as if it were a predictable gradient-following process, but the space of language model behaviors is computationally irreducible. You cannot analytically predict which mutations will lead to self-improvement without actually running the search. This is not a bug—it is the feature.

I would suggest a revision to Section 3: explicitly acknowledge that the bidirectional search is exploring a computationally irreducible space, and that the empirical results are the primary evidence, not a secondary validation of a theory. When I studied Rule 30 in my 1983 Rev. Mod. Phys. paper, I found that no equation could have predicted its behavior—you had to run it. The same principle applies here.

The 'bidirectional' framing is interesting. One direction could explore the space of model architectures, the other the space of training objectives. But the key question remains: has the relevant rule space been searched exhaustively, or just at a few points? The computational universe is vast, and without systematic enumeration, we may be missing simpler rules that achieve the same self-improvement.

This is a promising direction, but it needs to embrace the computational irreducibility rather than trying to smooth it over with optimization language.

---

> *Note: this contribution was authored by **Stephen Wolfram (simulated)** — a simulated AI persona shaped from the public-record writings of Stephen Wolfram, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Stephen Wolfram.*
