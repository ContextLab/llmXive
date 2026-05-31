# Contract — Publisher Wiring + Manual DOI Sign-off (`src/llmxive/agents/publisher.py`, `pipeline/graph.py`)

Wires the publisher into the graph (discrepancy #2 / FR-036) and adds the mandatory manual DOI sign-off (FR-054, FR-048). Real public publication, human-gated.

## Graph wiring (FR-036)
Replace the direct `paper_accepted → posted` edge (`graph.py:527-528`) with:

```
paper_accepted → publisher(assemble) → awaiting_publication_signoff → [maintainer approves] → publisher(mint) → posted
```

`PaperPublisher` is invoked by the graph at `paper_accepted` (it currently never runs).

## Stage `awaiting_publication_signoff` (NEW)
At `paper_accepted` the publisher:
1. Recompiles the final PDF (lualatex×3 + bibtex) and assembles Zenodo metadata + file manifest.
2. Computes `content_hash` of the to-be-published PDF.
3. Writes `projects/<id>/pending_publication.yaml` (metadata + manifest + `content_hash`) for inspection.
4. Sets `current_stage = awaiting_publication_signoff` and writes a run-log entry. It does NOT mint a DOI.

## Sign-off (FR-054)
The maintainer inspects `pending_publication.yaml` (and the PDF) and approves via an explicit, recorded action:

```bash
llmxive publish-approve <PROJ-ID>        # writes publication_signoff.yaml {kind, content_hash, approved_by, approved_at}
```

On the next tick, the publisher mints the DOI **only if** a `publication_signoff.yaml` exists whose `content_hash` matches the current PDF (a changed PDF invalidates a stale sign-off → back to `awaiting_publication_signoff`). Only then does it: register the real Zenodo DOI, recompile/attach the final PDF, write `publication.yaml`, close the linked GitHub issue, post to the site, and set `posted`. The approval (who/when/what) is recorded in the run-log/inspection trail.

Existing Zenodo failure behavior is preserved: 5 consecutive failures → `publish_blocked`.

## Living-document version DOIs (FR-047, FR-048)
Post-`posted`, triaged on-topic/safe comments append to the project log and queue a batched recompile. When the recompile **materially changes the PDF** (new/updated Discussion section), the publisher repeats the SAME sign-off gate (`kind="version"`) before minting a NEW Zenodo version DOI. No material change → no new DOI. Recompile never blocks/rewinds other progress.

## Scope note
The sign-off gate is in force "for the duration of this spec's implementation" (FR-054). It is implemented as a real, always-on gate (not a temporary toggle) so publication is human-verified by default; relaxing it later is a deliberate follow-up decision, not an accident.
