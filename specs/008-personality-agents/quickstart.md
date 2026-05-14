# Quickstart — Simulated Personality Agents

How to drive the feature end-to-end, locally and on the cron.

## 0. Preconditions

- `DARTMOUTH_CHAT_API_KEY` is set (same as every other LLM-using workflow).
- `pip install -e ".[dev]"` from repo root.
- A clean working tree on `008-personality-agents` (or main after merge).

## 1. Add or inspect a personality

Each persona lives in one file at `agents/prompts/personalities/<slug>.md`. The file is plain Markdown with a YAML front-matter header.

```markdown
---
display_name: "Daniel Kahneman"
summary: "Israeli-American psychologist, Princeton; Nobel laureate, heuristics and biases."
sources:
  - "Thinking, Fast and Slow (FSG 2011)"
  - "Noise (Kahneman/Sibony/Sunstein 2021)"
  - "Nobel Memorial Lecture: Maps of Bounded Rationality (2002)"
  - "Tversky & Kahneman, Judgment under Uncertainty: Heuristics and Biases, Science (1974)"
version: "1.0.0"
---

## Voice & tone
Quiet, precise, deliberate — every word chosen. Unhurried, concrete sentences;
favors a small worked example before any abstraction. Mildly self-effacing; …

## Vocabulary & focus
System 1, System 2, heuristic, bias, anchoring, availability,
representativeness, WYSIATI, …

## Mannerisms (well-attested)
- Personifies System 1 / System 2 as characters …
- "What You See Is All There Is" / WYSIATI …
- …
```

The schema for the front-matter is in [`contracts/personality-prompt-frontmatter.schema.yaml`](./contracts/personality-prompt-frontmatter.schema.yaml). The full grounding cards for the v1 ten personas are in [`research.md` § R5](./research.md).

**Adding an 11th persona** is a one-file PR: drop `agents/prompts/personalities/richard-feynman.md` in place, open a PR, merge. The next cron tick after merge picks it up (FR-020).

## 2. Run a tick locally

```bash
# Local single-shot — picks the next persona in the rotation, makes one
# LLM call, dispatches the contribution to the right pipe, commits state.
# Exits with the chosen persona's slug printed.
python -m llmxive run --max-tasks 1 --agent personality
```

By default this hits the real Dartmouth Chat backend. To dry-run with a
canned response (the test fixture), set:

```bash
LLMXIVE_PERSONALITY_FIXTURE=tests/fixtures/personality_action_comment.json \
  python -m llmxive run --max-tasks 1 --agent personality
```

Inspect what changed:

```bash
git status
git --no-pager diff state/personality_rotation.yaml
ls -la state/run-log/$(date -u +%Y-%m)/
```

## 3. Force a specific personality (for testing voice / debugging)

```bash
# Pretend the previous tick selected `aristotle`; the next one will pick
# the lex-next persona after `aristotle`. To run a specific persona, edit
# `state/personality_rotation.yaml` to set `last_used` to the *previous*
# slug in rotation order (so the next selection lands on the one you want).
python -m llmxive run --max-tasks 1 --agent personality --personality daniel-kahneman
```

The `--personality` flag bypasses the rotation pointer (does NOT update it on success) — strictly for testing.

## 4. View the registry on the website

After the website data is rebuilt:

```bash
python -c "from llmxive.web_data import write_payload; from pathlib import Path; write_payload(Path('.'))"
cp web/data/projects.json docs/data/projects.json   # local-only; the pages.yml workflow does this on push
```

Open `web/index.html` (or the deployed site after push) → About → "Simulated personalities" section → "Personality registry" button → modal lists every persona with their summary; click a row → markdown body renders with Prism syntax highlighting + "View on GitHub" footer.

## 5. Run the cron from GitHub Actions (manual)

```bash
gh workflow run pipeline-personality.yml --ref main
gh run watch  # tail the just-fired run
```

The workflow is otherwise on a 30-minute schedule. Concurrency is enforced via the workflow-level group, so manual + scheduled never collide.

## 6. Verify attribution

After at least one `committed` outcome, check three places:

```bash
# (a) Run-log entry
jq '.[] | select(.agent_name == "personality")' state/run-log/$(date -u +%Y-%m)/*.jsonl | tail -1

# (b) Committed artifact frontmatter (review file path comes from the run-log)
head -10 projects/PROJ-<id>/paper/reviews/<persona-slug>-simulated__*.md

# (c) Website contributor list — the entry MUST appear as "<Display Name> (simulated)"
jq '.contributors[] | select(.name | contains("(simulated)"))' web/data/projects.json
```

Negative invariant — none of these should ever happen:

```bash
# A simulated entry with kind=human → FAIL (FR-010)
jq '.contributors[] | select(.kind == "human" and (.name | contains("(simulated)")))' web/data/projects.json

# A real-person contributor entry that has been merged with a simulated one → FAIL (FR-011)
# (manual check — visually scan the contributor list for any name appearing twice without/with the suffix)
```

## 7. End-to-end test (real LLM)

```bash
LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_personality_per_persona_real.py -v
```

Drives one tick per persona, smoke-checks the dispatch path, prints the LLM output for human voice-eyeballing.

## 8. Adding a new pipe (out of scope for v1)

If a future persona wants to take an action beyond comment / contribute / propose_arxiv (say, "open a discussion thread"), the agent's dispatcher in `src/llmxive/agents/personality.py` is the one place to add the new branch. The action menu in `agents/prompts/personality.md` would also need to be extended. No other touch points.

## 9. Verify SC-005 (voice distinctness) manually

The automated Jaccard check in `tests/real_call/test_personality_per_persona_real.py` is a smoke test, NOT the SC-005 gate. SC-005 is verified manually:

1. After the cron has completed at least one full rotation (≥ 10 ticks producing `committed` outcomes), run:

   ```bash
   # Extract one committed contribution per persona
   for persona_slug in $(ls agents/prompts/personalities/*.md | xargs -n1 basename | sed 's/.md$//'); do
     echo "=== $persona_slug ==="
     jq -r "select(.personality_slug == \"$persona_slug\" and .outcome == \"committed\") | .committed_paths[0]" \
       state/run-log/**/*.jsonl 2>/dev/null | tail -1
   done
   ```

2. Open each cited path, strip the front-matter / disclaimer footer / display name, and present the bodies in a randomized name-stripped order to a human reviewer who knows ≥ 4 of the simulated figures.

3. Ask the reviewer to match each body back to the right persona. Expected: ≥ 50% correct attribution for the figures they know (vs. 10% random-chance baseline for a 10-persona pool).

4. Record the result + reviewer initials in `state/sc-005-voice-distinctness/<YYYY-MM>.yaml`. Spec ratification = first month with ≥ 50% match rate.

If the rate falls below the bar, file an issue against the worst-matched personas' prompts (their voices aren't doing distinguishing work) — typically meaning the grounding card needs a more specific mannerism or vocabulary anchor.

---

## 10. Audit a 7-day window

For SC-007 (≥ 90% scheduled-window completion):

```bash
# Count the run-log entries in the last 7 days where agent_name == "personality"
find state/run-log -name "*.jsonl" -newer "$(date -u -v -7d +%Y-%m-%d)" \
  | xargs jq -c 'select(.agent_name == "personality")' 2>/dev/null \
  | wc -l
# Expected: ≥ 90% of 48 * 7 = 302 ticks → ≥ 272 entries.
```

For SC-002 (rotation balance, ±1 per persona in first 100 ticks):

```bash
jq -r '.personality_slug' state/run-log/**/*.jsonl 2>/dev/null \
  | grep -v null | sort | uniq -c
# Each persona should appear within ±1 of the count.
```
