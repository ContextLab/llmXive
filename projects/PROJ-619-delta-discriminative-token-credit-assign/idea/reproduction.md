# Reproduce & validate: DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-619-delta-discriminative-token-credit-assign/external/dlbook_notation/   (clone of https://github.com/goodfeli/dlbook_notation)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** DelTA: Discriminative Token Credit Assignment for Reinforcement Learning from Verifiable Rewards

**Abstract:** Reinforcement learning from verifiable rewards (RLVR) has emerged as a central technique for improving the reasoning capabilities of large language models. Despite its effectiveness, how response-level rewards translate into token-level probability changes remains poorly understood. We introduce a discriminator view of RLVR updates, showing that the policy-gradient update direction implicitly acts as a linear discriminator over token-gradient vectors and thereby determines which token probabilities are increased or decreased during learning. Under standard sequence-level RLVR, this discriminator is constructed from positive- and negative-side centroids formed by advantage-weighted averaging of token-gradient vectors. However, such centroid construction can be dominated by shared high-frequency patterns, such as formatting tokens, diluting sparse yet discriminative directions that better distinguish high-reward responses from low-reward ones. To address this limitation, we propose $\textbf{DelTA}$, a discriminative token credit assignment method that estimates token coefficients to amplify side-specific token-gradient directions and downweight shared or weakly discriminative ones. These coefficients reweight a self-normalized RLVR surrogate, making the effective side-wise centroids more contrastive and thereby reshaping the RLVR update direction. On seven mathematical benchmarks, DelTA outperforms the strongest same-scale baselines by 3.26 and 2.62 average points on Qwen3-8B-Base and Qwen3-14B-Base, respectively. Additional results on code generation, a different backbone, and out-of-domain evaluations further demonstrate the generalization ability of DelTA.

## Shipped code — file tree (`projects/PROJ-619-delta-discriminative-token-credit-assign/external/dlbook_notation/`)

```
.gitignore
README.md
commentary.tex
make.sh
math_commands.tex
natbib.bst
notation.bib
notation.tex
notation_example.pdf
notation_example.tex
settings.tex
venn.pdf
```

## Detected entry points

- (no .py entry scripts auto-detected; see README usage)

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `dlbook_notation` — not re-implementing it.
