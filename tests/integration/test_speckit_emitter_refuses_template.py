"""T028: integration test — speckit emitter refuses to commit template artifacts.

Verifies FR-009 + FR-010 + SC-004 end-to-end:
  (a) when the emitter writes a template-classified file, the guard raises
  (b) the file is removed from disk (no stub left behind)
  (c) actionable error names the missing context
  (d) project progression points NOT incremented (we verify by inspecting
      the test's seeded project state)

Constitution III: real filesystem write + real auditor classification.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from llmxive.speckit._real_only_guard import (
    TemplateRefused,
    guard_emit,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / ".specify" / "templates"
FIXTURE_TEMPLATE = REPO_ROOT / "tests" / "fixtures" / "audit" / "speckit_template" / "spec.md"
FIXTURE_REAL = REPO_ROOT / "tests" / "fixtures" / "audit" / "speckit_real" / "spec.md"


class TestEmitterRefusesTemplate(unittest.TestCase):
    """Simulates the emitter pattern: write file -> guard_emit -> on fail, file gone."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="emitter_refuse_"))
        self.proj = self.tmp / "projects" / "PROJ-TEST-001" / "specs" / "001-x"
        self.proj.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_guard_emit_removes_template_file_on_fail(self):
        # Simulate emitter writing a template-style stub
        spec = self.proj / "spec.md"
        shutil.copy(FIXTURE_TEMPLATE, spec)
        self.assertTrue(spec.exists())

        with self.assertRaises(TemplateRefused):
            guard_emit(spec, repo_root=self.tmp, templates_dir=TEMPLATES_DIR)

        # File is gone — no stub left in the tree
        self.assertFalse(spec.exists(), "guard should have unlinked the rejected file")

    def test_guard_emit_keeps_real_file(self):
        spec = self.proj / "spec.md"
        shutil.copy(FIXTURE_REAL, spec)
        guard_emit(spec, repo_root=self.tmp, templates_dir=TEMPLATES_DIR)
        self.assertTrue(spec.exists())

    def test_actionable_error_for_template(self):
        spec = self.proj / "spec.md"
        shutil.copy(FIXTURE_TEMPLATE, spec)

        with self.assertRaises(TemplateRefused) as cm:
            guard_emit(spec, repo_root=self.tmp, templates_dir=TEMPLATES_DIR)

        exc = cm.exception
        # Error must mention progression points (SC-004)
        self.assertIn("progression points", str(exc))
        # And name the missing context
        self.assertIn("Fix by supplying", str(exc))

    def test_unlink_disabled_keeps_file(self):
        # When clarify_cmd uses unlink_on_fail=False, the file stays so a
        # maintainer can inspect what regressed.
        spec = self.proj / "spec.md"
        shutil.copy(FIXTURE_TEMPLATE, spec)
        with self.assertRaises(TemplateRefused):
            guard_emit(spec, repo_root=self.tmp, templates_dir=TEMPLATES_DIR,
                       unlink_on_fail=False)
        self.assertTrue(spec.exists())


class TestProgressionNotIncremented(unittest.TestCase):
    """Verifies that on guard refusal, no project state is mutated.

    This is the SC-004 invariant: spurious progressions == 0. We simulate it
    by checking that the project state file is unchanged after a refused emit.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="prog_test_"))
        self.proj_dir = self.tmp / "projects" / "PROJ-TEST-001"
        self.spec_dir = self.proj_dir / "specs" / "001-x"
        self.spec_dir.mkdir(parents=True)
        # Simulate a project state file
        self.state_file = self.proj_dir / "state.json"
        self.state_file.write_text('{"stage": "ideated", "progression_points": 0}')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_state_unchanged_on_guard_refusal(self):
        before = self.state_file.read_text()
        spec = self.spec_dir / "spec.md"
        shutil.copy(FIXTURE_TEMPLATE, spec)

        # Simulate emitter pattern: write -> guard -> on success, update state.
        # Guard raises -> we abort before updating state.
        try:
            guard_emit(spec, repo_root=self.tmp, templates_dir=TEMPLATES_DIR)
            self.fail("expected TemplateRefused")
        except TemplateRefused:
            pass  # correct path; state must NOT be touched

        after = self.state_file.read_text()
        self.assertEqual(before, after, "project state must not change on guard refusal")


if __name__ == "__main__":
    unittest.main()
