# Phase 1 Data Model — Pipeline Convergence Protocol

All entities are pydantic v2 models (project convention). New models live in `src/llmxive/convergence/types.py` unless noted. Reused existing models are cited with file:line.

## Convergence core (`convergence/types.py`)

### Severity (enum)
Widened from the existing `ActionItem.severity` (`types.py:285-301`, currently `Literal["writing","science","fatal"]`).
`trivial < code < writing < requirement < methodology < science < fatal` (ordered; used for "worst unresolved severity" routing). A mapping table keeps back-compat with stored `writing|science|fatal` records.

### Concern
A single critical finding raised in R1 (or a new one raised in R3). Maps onto/extends `ActionItem`.
| field | type | notes |
|-|-|-|
| id | str (12-hex) | stable across re-flags (reuses `ActionItem.id`) |
| reviewer | str | panel lens name (e.g. `plan.methodology`) |
| severity | Severity | drives kickback routing |
| artifact | str | repo-relative path of the reviewed artifact |
| location | str | section/line/anchor within the artifact |
| text | str | the concern, evidence-bearing |
| round | int | R1=1, subsequently the round it was raised |

### ConcernResponse
The reviser's per-concern reply (R2). One per addressed concern.
| field | type | notes |
|-|-|-|
| concern_id | str | FK → Concern.id |
| response | str | how it was addressed |
| what_changed | str | the concrete change (file + nature) |
| artifacts_changed | list[str] | repo-relative paths touched |

### Verdict
A panelist's R3 judgment of its own concern.
| field | type | notes |
|-|-|-|
| concern_id | str | FK → Concern.id |
| reviewer | str | lens name |
| status | Literal["pass","fail"] | resolved without new breakage? |
| new_concerns | list[Concern] | present iff status=="fail" |
| stale | bool | true if judged against a since-changed artifact (must not count as pass) |
| self_review | bool | true if reviewer == producer (must be prevented; fixes `_produced_by` stub) |

### ProgressRecord
Per-kickback progress snapshot (enables no-cap-but-inspectable iteration).
| field | type | notes |
|-|-|-|
| kickback_index | int | 0-based |
| unresolved_concern_ids | list[str] | the set at this kickback |
| improved | bool | did the unresolved set shrink/change vs the prior kickback? |

### ConvergenceResult
The engine's outcome for one step.
| field | type | notes |
|-|-|-|
| stage | str | the reviewable stage |
| converged | bool | **always reflects reality** (FR-016) |
| rounds_used | int | within the 3-round per-step cap |
| concern_history | list[Concern] | every concern raised |
| response_history | list[ConcernResponse] | every R2 response |
| verdict_history | list[Verdict] | every R3 verdict |
| next_stage | str \| None | set iff converged |
| kickback | KickbackRecord \| None | set iff not converged |
| inspection_path | str | where the per-round trail was persisted |

### ReviewSpec
Per-step configuration the engine consumes (one per reviewable stage; registry in `convergence/reviewspecs.py`).
| field | type | notes |
|-|-|-|
| stage | str | the stage this spec governs |
| artifacts | list[str] | repo-relative reviewable artifact paths (templated by project) |
| reviewers | list[Reviewer] | panel lenses (R1/R3 callables) |
| reviser | Reviser | R2 callable (author/refiner) |
| kickback_routing | dict[Severity, str] | worst-severity → prior stage |
| overflow_goal | str | preservation contract passed to `summarize` for this step |
| constitution_input | bool | True from `specified` onward (FR-030) |
| max_rounds | int = 3 | per-step cap |
| exempt | bool = False | mechanical steps set True (no loop) |

`Reviewer` and `Reviser` are typed Protocols (callables), not data — see `contracts/convergence-engine.md`.

### KickbackRecord
| field | type | notes |
|-|-|-|
| from_stage | str | the non-converged stage |
| to_stage | str | adaptive target (worst unresolved severity) |
| worst_severity | Severity | |
| unresolved_concerns | list[Concern] | |
| artifact_links | list[str] | all artifacts + reviews involved |
| reason | str | plain-language "why it failed to converge" |
| created_at | datetime | |

## Review intake (`convergence/triage.py`)

### TriageRecord
| field | type | notes |
|-|-|-|
| source | Literal["human","personality"] | |
| author | str | github handle / persona (persona keeps `(simulated)` suffix) |
| stage_context | str | the project's stage when triaged |
| quality_pass | bool | evidence-based + specific + relevant |
| safe_on_topic | bool | family-friendly + safe + on-topic |
| mapped_lenses | list[str] | reviewer lenses that will receive it (advisory) |
| preserved | bool | included in the publication review log? (quality_pass ∧ safe_on_topic) |
| excluded_reason | str \| None | set iff not preserved |
| review_text | str | the original review (possibly summarized via `tools/summarize`) |

## Summarizer (`tools/summarize.py`)

### SummaryManifest / SummaryEntry (persisted as `manifest.json`)
| SummaryEntry field | type | notes |
|-|-|-|
| element_id | str | ordered id within the manifest |
| kind | Literal["content","pointer"] | pointer → nested manifest (recursion) |
| file | str | on-disk content file or nested manifest path |
| critical | list[str] | verbatim check-critical elements in this entry |
| summary | str | goal-targeted prose summary (semantic checks only) |

`SummaryManifest` = `{root_hash, goal, model, token_budget, entries: list[SummaryEntry], created_at}`. `desummarize` walks entries (optionally filtered by `want`) and follows `pointer` kinds recursively. **Invariant**: the union of all `critical` across all levels == the set of check-critical elements extracted from the source (no loss; tested).

## Calibration (`calibration/`)

### CalibrationCase
| field | type | notes |
|-|-|-|
| case_id | str | |
| domain | str | one of the 9 `LIBRARIAN_DEFAULT_FIELDS` |
| held_out | bool | excluded from prompt tuning (FR-043) |
| polarity | Literal["positive","negative"] | positive=real-paper/backlog/HF; negative=injected-flaw |
| stage | str | which step's panel this targets |
| clean_artifact | str | path to the good artifact |
| injected_artifact | str \| None | negative only |
| injected_flaw_kind | str \| None | e.g. `circular_rq`, `fr_without_task`, `gutted_requirement`, `fabricated_data`, `nonexistent_citation`, `plan_tasks_contradiction` |
| expected_lens | str \| None | the lens that MUST catch the injected flaw |
| anchor_paper | str \| None | positive: DOI/URL of the real peer-reviewed anchor |

### DifferentialResult
| field | type | notes |
|-|-|-|
| case_id | str | |
| injected_caught | bool | injected flaw flagged in the injected review by `expected_lens` |
| injected_absent_in_clean | bool | not flagged in the clean review |
| extra_findings | list[Concern] | additional findings needing manual adjudication |
| adjudication_path | str | markdown report for the maintainer |

## Publication sign-off (`agents/publisher.py`)

### PublicationSignoff (persisted as `publication_signoff.yaml`)
| field | type | notes |
|-|-|-|
| project_id | str | |
| kind | Literal["initial","version"] | initial publish or living-document version |
| content_hash | str | hash of the to-be-published PDF; a changed PDF invalidates the signoff |
| approved_by | str | maintainer identity |
| approved_at | datetime | |
| notes | str | optional |

## Reused existing models (not redefined)
- `ReviewRecord` (`types.py:304-367`) — kept; `score` field retained but no longer read by any gate (R6).
- `ActionItem` (`types.py:285-301`) — `Concern` extends its id/text/severity.
- `RunLogEntry` (`types.py:370`) — every convergence round + sign-off writes one.
- `Project` (`types.py:211`) — `current_stage` gains the new `awaiting_publication_signoff` value.
- `Stage` (`types.py:80-145`) — add `AWAITING_PUBLICATION_SIGNOFF`; reuse existing revision stages for kickback targets.
