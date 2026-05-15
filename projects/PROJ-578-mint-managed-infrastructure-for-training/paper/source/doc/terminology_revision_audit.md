# MinT Terminology Revision Audit

Date: 2026-05-11

This note records the terminology cleanup applied while reviewing Pony's `pony_mint` branch. The edit keeps MinT's main framing while replacing internal or overloaded wording with terms that name the concrete object: adapter files, exported adapter revisions, training checkpoints, CPU cache, GPU batch, cache misses, and cold loading.

## Terms Intentionally Retained

| Term | Reason |
| --- | --- |
| `adapter lifecycle` | The paper follows the adapter across update, export, serving, eviction, reload, and rollback. `Adapter workflow` does not name this lifespan. |
| `Resource admission` | In the architecture figure, the service admits work onto existing workers. It does not allocate new resources per request, so `resource allocation` would be wrong there. |
| `addressable catalog` | Addressability is part of the scale-out claim: many exported policy revisions can be named and selected even though only a small subset is cached or active in a GPU batch. |
| `policy population` | The term names the paper's core object: many trainable, evaluable, rollbackable, and serveable policies over shared bases. |
| `policy record` | The term names MinT's durable service record connecting base compatibility, training checkpoint, rollout records, exported revisions, and adapter cache state. |

## Preferred Replacements

| Previous wording | Preferred wording | Rationale |
| --- | --- | --- |
| `serving residency` | `adapter cache state`, `where the adapter is cached or loaded` | Names the serving state directly. |
| `host-resident cache/set` | `CPU cache`, `local adapter cache`, `CPU-cached adapters` | Matches common LoRA serving terminology. |
| `GPU-active set/window` | `GPU batch`, `adapters in one GPU batch`, `same-batch adapter limit` | Names the batch-level execution constraint. |
| `first-touch admission`, `cold admission`, `live admission` | `cold load`, `cold loading`, `cache miss`, `live load` | The measured work is adapter loading after a cache miss. |
| `admission path/slope` | `cold-load path`, `load staircase` | Names the loader behavior measured in the scale-out experiments. |
| `artifact` | `adapter file`, `exported adapter`, `PEFT adapter`, `shared storage` | Names the object that moves or is stored. |
| `immutable adapter revision` | `fixed adapter revision`, `exported adapter revision` | Serving and evaluation select a fixed export. |
| `mutable checkpoint/object` | `training checkpoint`, `training state`, `adapter and optimizer state` | Names what the trainer restores. |
| `policy heat` | `adapter popularity`, `traffic locality`, `cache reuse` | Names the workload property that drives cache behavior. |

## Scan Boundary

The cleanup covered `papers/mint/paper.tex`, `papers/mint/sections/*.tex`, `papers/mint/figures/*.tex`, and `papers/mint/tables/mint/verified_capabilities.tex`.

Remaining `admission` uses are intentional:

- `Resource admission` in Figure 3 and nearby architecture prose means admitting work onto existing workers.
- `admit $L_r$` in Figure 5 means inserting the selected LoRA into an engine slot after the adapter file has been fetched into the CPU cache.
