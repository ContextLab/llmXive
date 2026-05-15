# Story Alignment To-do After Main Sync

Date: 2026-05-12

Branch: `pony_mint`

This note tracks the story-alignment pass after syncing `origin/main` into `pony_mint`. The current manuscript story is:

1. Post-training is becoming a recurring infrastructure workload over many variants, not a single final checkpoint.
2. LoRA can carry trained behavior while shared dense or MoE base models remain resident.
3. MinT is a Tinker-compatible managed LoRA RL service that connects rollout, update, export, serving, evaluation, and rollback.
4. The paper should read through three scaling axes:
   - Scale Up: LoRA RL on large dense and MoE bases.
   - Scale Down: adapter-only training-serving handoff.
   - Scale Out: a large addressable policy catalog separated from bounded host-resident and GPU-active working sets.
5. The evidence boundary must stay explicit: million-scale means addressable catalog capacity, and under-0.2s means the packed live engine-load slice, not end-to-end cold-request latency.

## Completed In This Pass

### P0. Re-anchor Introduction

Status: done.

Changes:

- Rewrote the opening to start from post-training as a recurring infrastructure workload.
- Added citations for agent-environment interaction, learning from experience, frontier-model agentic training/evaluation reports, LoRA, LoRA Without Regret, Tinker, and multi-LoRA serving.
- Reframed LoRA as a behavior carrier and MinT as the managed service that turns that carrier into an end-to-end training-serving lifecycle.
- Rewrote the Scale Up / Scale Down / Scale Out paragraph so it maps directly to the abstract.

Files:

- `papers/mint/sections/1_introduction.tex`

### P0. Clarify Adapter Revision vs Policy Record

Status: done.

Current terminology:

- `adapter revision`: the fixed exported LoRA payload used by rollout, evaluation, serving, and rollback.
- `policy record`: the durable service state that ties the compatible base, adapter shape, training checkpoint, rollout records, exported revisions, and cache state together.
- `LoRA policy`: the deployable behavior over a resident base model.

Changes:

- Reframed Section 2 opening around many trained behaviors over a few resident base models.
- Added an explicit sentence defining a deployable LoRA policy as the LLM behavior that MinT trains, evaluates, serves, and rolls back.
- Kept the principle that the abstraction is not an implementation trick: the adapter is the behavior-carrying payload, while the policy record is the service state that preserves lifecycle correctness.

Files:

- `papers/mint/sections/2_system_overview.tex`

### P0. Keep Claim Boundaries For 1%, 10^6, And 0.2s

Status: done.

Current wording:

- `1%`: Section 4 explains measured rank-32 Qwen3-4B adapter size and the rank-linear estimate for rank-1 under the same target-module pattern.
- `10^6`: Abstract, Section 4, Evaluation, and Conclusion now describe this as an addressable policy catalog or million-scale catalog, not simultaneous GPU residency.
- `0.2s`: Section 4 and Evaluation identify this as the packed live engine-load slice after tensor packing, not the full cold-request path.

Files:

- `papers/mint/paper.tex`
- `papers/mint/sections/4_scaling.tex`
- `papers/mint/sections/5_capabilities.tex`
- `papers/mint/sections/7_conclusion.tex`

### P1. Align System Design With The Service Story

Status: done.

Changes:

- Section 3 now points to both Figure 1 (`fig:mint_overview`) and the handoff figure (`fig:mint_handoff_paths`).
- The opening now states the two things the runtime must preserve: a simple service interface and an adapter-only handoff.
- Figure caption wording now uses policy records and exported revisions consistently.

Files:

- `papers/mint/sections/3_architecture.tex`

### P1. Make Evaluation Read As Evidence For The Three Scaling Axes

Status: done.

Changes:

- Evaluation opening now maps Scale Down, Scale Up, and Scale Out to the measured evidence.
- Added an explicit evidence boundary for the million-scale claim: MinT manages a million-scale catalog while training and serving selected revisions through bounded resident working sets.

Files:

- `papers/mint/sections/5_capabilities.tex`

### P1. Mirror Abstract In Conclusion

Status: done.

Changes:

- Conclusion now follows problem -> MinT -> Scale Up/Down/Out evidence -> implication.
- The final paragraph now says multi-train/multi-serve means many LoRA policy revisions managed over shared trillion-parameter base deployments, with selected revisions active in bounded working sets.

Files:

- `papers/mint/sections/7_conclusion.tex`

## Remaining To-do

### P1. Polish Introduction For Style After Visual Inspection

The Introduction now has the correct logic and citation support, but it should be read in the rendered PDF to check whether the two top figures interrupt the flow. If the first two pages feel too figure-heavy, consider moving only the handoff figure later or shortening the paragraph before Figure 1.

### P1. Decide Whether To Keep Commented Chinese Draft Blocks

`sections/1_introduction.tex` still contains a long commented Chinese drafting block. It does not affect compilation, but it adds source noise. Remove it before submission if the team no longer needs it for provenance.

### P2. Tighten The Title/Body Relationship

The title says "Training and Serving Millions of LLMs" while the technical body correctly speaks about LoRA policies, adapter revisions, and addressable catalogs. The current Section 2 bridge explains the relationship, but another future polish pass could make the title-body connection even more explicit in the last sentence of the Introduction.

### P2. Optional Figure Caption Polish

Figure 1 now says "policy records" and "exported revisions." This is aligned, but after visual inspection the caption may benefit from a shorter version if it occupies too much space.

## Validation Target

After each future source edit:

```bash
cd papers/mint
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
grep -c "LaTeX Warning: Citation" paper.log
grep -ci "undefined references\\|undefined citations" paper.log
grep -c "File .* not found" paper.log
grep -c "Overfull" paper.log
pdfinfo paper.pdf | grep Pages
```
