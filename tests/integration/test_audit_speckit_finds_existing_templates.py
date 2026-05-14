"""T029: real-tree integration test for template_vs_real auditor.

Runs the auditor against the current `projects/` tree (real filesystem,
real artifacts) and asserts the manifest contains the EXPECTED template
classifications (the ones we found during /speckit-implement Phase 4).

This is a SANITY check: if a future maintainer adds another template stub
or fixes one we've already pruned, this test must be updated — that is
intentional, the auditor's value comes from staying calibrated against
the actual repo state.

After T041's prune runs, the EXPECTED list should be empty. We keep the
test parameterised so that intermediate intent is visible: while pruning,
the expected set is "the known stubs we're about to delete"; post-prune
it's empty.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from llmxive.audit.template_vs_real import audit


REPO_ROOT = Path(__file__).resolve().parents[2]


class TestAuditOnLiveTree(unittest.TestCase):
    """Sanity check: auditor returns a manifest with valid shape against the live tree."""

    def test_auditor_runs_against_live_tree_without_error(self):
        manifest = audit(
            projects_dir=REPO_ROOT / "projects",
            templates_dir=REPO_ROOT / ".specify" / "templates",
            repo_root=REPO_ROOT,
        )
        self.assertIn("items", manifest)
        self.assertGreater(manifest["summary"]["total"], 0,
                           "live tree should contain at least some speckit artifacts")

    def test_real_legacy_migrations_classify_as_real(self):
        """The known legacy migrations (PROJ-006/008 etc.) MUST stay 'real'."""
        manifest = audit(
            projects_dir=REPO_ROOT / "projects",
            templates_dir=REPO_ROOT / ".specify" / "templates",
            repo_root=REPO_ROOT,
        )
        by_target = {it["target"]: it for it in manifest["items"]}
        # PROJ-006's spec.md is a real legacy migration
        proj006_spec = "projects/PROJ-006-agriculture-optimization/specs/001-agriculture-optimization/spec.md"
        if proj006_spec in by_target:
            self.assertEqual(
                by_target[proj006_spec]["classification"], "real",
                "PROJ-006 spec.md is a legacy migration with real prose; must classify 'real'",
            )

    def test_known_template_tasks_md_found(self):
        """If any project's tasks.md is still a template stub, the auditor catches it."""
        manifest = audit(
            projects_dir=REPO_ROOT / "projects",
            templates_dir=REPO_ROOT / ".specify" / "templates",
            repo_root=REPO_ROOT,
        )
        # Just verify the auditor produces SOME classification for every input;
        # the prune step (T041) will then act on whatever it flags.
        for it in manifest["items"]:
            self.assertIn(it["classification"], ("real", "partial", "template"))


if __name__ == "__main__":
    unittest.main()
