#!/usr/bin/env bash
# Single source of truth for the pipeline crons' commit + push.
#
# WHY THIS EXISTS (the bug it fixes)
# ----------------------------------
# ~14 workflows commit to `main` on overlapping schedules. The old inline
# pattern was:
#
#     git commit -m "..."
#     for i in 1..5; do git pull --rebase origin main && git push && break; done
#     echo "pushed=true"
#
# When a CONCURRENT run had already pushed (almost always touching the
# wholesale-regenerated web/data/projects.json), `git pull --rebase` hit a
# conflict and LEFT THE TREE CONFLICTED. Every subsequent retry then died with
# "Pulling is not possible because you have unmerged files", so the loop never
# recovered — the tick's work (e.g. a full in_progress task-batch drain) was
# SILENTLY LOST and the step STILL EXITED 0 (`pushed=true`), masking the loss.
#
# THE FIX
# -------
# * Rebase our single tick-commit onto the latest origin/main with `-X theirs`
#   — during a rebase git reverses ours/theirs, so "theirs" is OUR replayed
#   commit; conflicts resolve toward THIS tick deterministically (no conflict
#   markers ever reach the tree). The only routine conflict is the regenerated
#   web/data/* which is rebuilt next tick regardless.
# * Always `git rebase --abort` before each attempt so we NEVER operate on a
#   conflicted tree.
# * VERIFY the push landed (issue #1139): after a "successful" push, re-fetch
#   origin/main from the server and confirm our commit is contained in it before
#   claiming success — a masked exit code (the git-push-exitcode-mask class) or a
#   concurrent force-update would otherwise report pushed=true while the tick's
#   work was actually lost. A failed verify falls through and re-races.
# * FAIL LOUD (exit 1) if we still can't push after the retries — the project
#   state on origin is then simply unchanged (no corruption); it stays
#   schedulable and a later tick re-does the work. A masked success is worse
#   than a visible miss.
#
# Usage:  bash scripts/ci/commit-and-push.sh "pipeline(implement): 8h tick"
# Emits `pushed=true|false` to $GITHUB_OUTPUT (for the pages-deploy gate).
set -uo pipefail

msg="${1:?usage: commit-and-push.sh <commit-message>}"

emit() { [ -n "${GITHUB_OUTPUT:-}" ] && echo "pushed=$1" >> "$GITHUB_OUTPUT"; return 0; }

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

# Stage every pipeline output present in this fresh CI checkout. -A is safe
# here: the only working-tree changes are what this run produced.
git add -A

# Size guard: GitHub's pre-receive hook HARD-REJECTS any file >100MB, which
# fails the ENTIRE push and loses this worker's whole tick (observed: a 260MB
# pii_findings.csv + a 221MB raw CSV declined the push). Analysis runs emit
# oversized data artifacts that escape the path-scoped .gitignore (data/analysis/*,
# a misplaced projects/data/raw/*, or a tracked file regenerated past the limit).
# Drop any staged blob over 95MB — it is a REGENERABLE analysis/raw artifact, not
# source (the execution gate recomputes it each run). Never silent: log each skip.
# A modified tracked file keeps its committed (smaller) version; a new one is left
# untracked and excluded so a retry can't re-stage it.
git diff --cached --name-only -z | while IFS= read -r -d '' f; do
  [ -f "$f" ] || continue
  sz=$(wc -c < "$f" 2>/dev/null || echo 0)
  if [ "$sz" -gt 95000000 ]; then
    echo "[commit] SKIP oversized $((sz / 1000000))MB file (>95MB GitHub limit): $f" >&2
    git restore --staged -- "$f" 2>/dev/null || git rm --cached -q --ignore-unmatch -- "$f"
    grep -qxF "$f" .git/info/exclude 2>/dev/null || echo "$f" >> .git/info/exclude
  fi
done

if git diff --cached --quiet; then
  echo "no changes to commit"
  emit false
  exit 0
fi

git commit -m "$msg"

# Retry budget: a long-running tick (e.g. the reprocess drain, which holds the
# tree for minutes running review panels) starts its push AFTER many concurrent
# advance-matrix commits have landed, so a short budget loses every rebase race
# and DISCARDS the tick's work. Use a generous attempt count with JITTERED,
# capped backoff so simultaneous runners desync (a fixed schedule makes them
# collide in lockstep) and each gets many chances to land in a gap.
ATTEMPTS="${COMMIT_PUSH_ATTEMPTS:-20}"
for i in $(seq 1 "$ATTEMPTS"); do
  git rebase --abort 2>/dev/null || true   # guarantee a clean, non-conflicted tree
  if ! git fetch origin main --quiet; then
    echo "fetch failed (attempt $i); retrying" >&2; sleep $((2 + RANDOM % 5)); continue
  fi
  if git rebase -X theirs origin/main >/dev/null 2>&1; then
    head_sha="$(git rev-parse HEAD)"
    if git push origin HEAD:main --quiet; then
      # VERIFY the push actually landed (issue #1139 — concurrent persistence
      # loses work; guard against the exit-code-mask class of bug where a push
      # is reported OK but the tick's commit is not on origin/main). Re-fetch
      # origin/main from the SERVER and confirm our commit is contained in it.
      # If it is NOT an ancestor of the refreshed tip, the work did not persist
      # (a concurrent force-update, or a masked failure) — do NOT emit success;
      # fall through and re-race.
      if git fetch origin main --quiet \
         && git merge-base --is-ancestor "$head_sha" FETCH_HEAD; then
        echo "pushed on attempt $i (verified $head_sha landed on origin/main)"
        emit true
        exit 0
      fi
      echo "push reported success but $head_sha is NOT on origin/main (attempt $i) — re-racing" >&2
    fi
  else
    git rebase --abort 2>/dev/null || true
  fi
  echo "push attempt $i failed; retrying..." >&2
  sleep $((2 + RANDOM % 5))   # 2-6s jitter; desyncs concurrent runners
done

echo "ERROR: could not push after ${ATTEMPTS} attempts — this tick's work was NOT persisted." >&2
echo "origin/main is unchanged (no corruption); the project stays schedulable and a later tick re-does the work." >&2
emit false
exit 1
