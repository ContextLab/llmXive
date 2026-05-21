# Contract — `paper_publisher` agent

## Trigger

Runs in the same `llmxive run` scheduler tick as the implementer. Picks
projects whose `current_stage == paper_accepted` (FR-021). `paper_accepted`
is removed from `scheduler._NEVER_PICK` as part of this spec.

## Inputs

| Field | Source | Required |
|-|-|-|
| `project_id` | `Project.id` | yes |
| `paper/metadata.json` | filesystem | yes |
| `paper/revision_history.yaml` | filesystem | optional (if missing → "Auto-Reviewed | Published" status; if present with ≥1 successful round → "Auto-Reviewed | Auto-Revised | Published") |
| `paper/reviews/*.md` | filesystem | yes — used to build the post-paper appendix |
| Zenodo API token | `llmxive.credentials.load_zenodo_token()` (`[zenodo].api_token` in `~/.config/llmxive/credentials.toml` OR `ZENODO_API_TOKEN` env var) | yes |
| acceptance timestamp | the most recent run-log entry that set `current_stage = paper_accepted` | yes |

## Determinism

This agent is **deterministic** — no LLM calls. Inputs fully determine
outputs. Re-running the publisher on the same inputs (with identical
Zenodo state) produces identical `publication.yaml` content (modulo the
`zenodo_id` returned by the API).

## Steps

1. **Derive volume/issue** from the acceptance timestamp:
   `volume = YY`, `issue = MM` (FR-024). Store in `metadata.json`.
2. **Pre-reserve a DOI** via `POST /api/deposit/depositions` with
   `prereserve_doi: true` in the metadata block. Extract the reserved DOI
   from `response.metadata.prereserve_doi.doi`. (research.md §1.)
3. **Determine status badge** (FR-022):
   - read `paper/revision_history.yaml`
   - if file missing OR `rounds == []` → status = `"Auto-Reviewed | Published"`
   - else if `any(round.tasks_done > 0 for round in rounds)` → status = `"Auto-Reviewed | Auto-Revised | Published"`
   - else → status = `"Auto-Reviewed | Published"` (rounds existed but all failed)
4. **Regenerate the PDF** via the existing LaTeX build pipeline, with
   `\paperstatus{<badge>}`, `\paperdoi{<reserved-DOI>}`,
   `\papervolume{<YY>}`, `\paperissue{<MM>}` set on the main `.tex`
   preamble (FR-022, FR-023).
5. **Generate the post-paper appendix** (FR-034..FR-036): call
   `gen_appendix.py` against the project; the produced fragment is
   `\input{...}`'d before `\end{document}` of the main `.tex`. The
   compile in step 4 already includes this; we just verify the spacer
   page + reviews + revision changelog made it in.
6. **Upload the PDF** to the deposition's `bucket` URL via `PUT`.
7. **Publish** the deposition: `POST /api/deposit/depositions/<id>/actions/publish`.
   On success the DOI activates with DataCite.
8. **Write `paper/publication.yaml`** (FR-032) with all fields (see
   `publication-yaml.md` contract).
9. **Mirror** `doi`, `doi_url`, `zenodo_id`, `volume`, `issue` into
   `paper/metadata.json` (FR-025, FR-032).
10. **Emit an activity-log entry** (FR-028): `agent_name:
    paper_publisher`, `outcome: success`, `outputs: [<new PDF path>,
    <DOI URL>]`.
11. **Transition** the project: `paper_accepted → posted` (FR-021).

## Re-publication (DOI versioning, FR-027)

If `metadata.json::zenodo_id` is already set when the publisher runs
(i.e., this project was previously `posted` and is now returning to
`paper_accepted` after a new revision round):

- Call `POST /api/deposit/depositions/<existing_zenodo_id>/actions/newversion`.
- The response includes `links.latest_draft` — fetch the new draft id.
- Repeat steps 2 (DOI is auto-issued for the new version), 4 (PDF
  regen with new DOI baked in), 6 (upload), 7 (publish).
- Append the new DOI to `metadata.json::doi_versions` (append-only) and
  to `publication.yaml::doi_versions`.
- Update `metadata.json::doi`, `metadata.json::doi_url`,
  `metadata.json::zenodo_id` to the new version's values.

## Outputs

| Path | Written | Notes |
|-|-|-|
| `projects/<PROJ-ID>/paper/publication.yaml` | always (on first publication) / mutated (on re-publication) | **authoritative** publication metadata |
| `projects/<PROJ-ID>/paper/metadata.json` | always | mirror of publication.yaml; authors untouched |
| `projects/<PROJ-ID>/paper/pdf/main.pdf` | always | regenerated PDF with new byline |
| Zenodo deposition (remote) | always | published — DOI activates |
| run-log entry | always | agent_name=paper_publisher, outcome=success |

## Failure modes

| Failure | Detection | Response |
|-|-|-|
| Zenodo token missing | credential loader raises | abort run, no transition; log error |
| Zenodo API unreachable | `requests.exceptions.ConnectionError` | stay at `paper_accepted`, retry on next tick (FR-030) |
| Zenodo API returns 4xx | `response.status_code >= 400` | log error, stay at `paper_accepted`, retry on next tick (FR-030); on 5 consecutive failures → `publish_blocked` |
| PDF compile fails | build pipeline exits nonzero | stay at `paper_accepted`, log error, retry |
| Spacer/appendix missing from PDF | post-compile verification | log warning, continue (PDF still uploaded — appendix is decorative not blocking) |

## Operator escape hatch

`llmxive project republish <PROJ-ID>` (FR-030) rolls a `publish_blocked`
project back to `paper_accepted` and resets the failure counter. The
CLI is implemented in `scripts/publish_paper.py`.
