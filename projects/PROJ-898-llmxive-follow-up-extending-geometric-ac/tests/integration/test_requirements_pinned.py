"""Integration test for T002: verify requirements.txt is present and
contains all required pinned dependencies."""

import os
import unittest

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
REQUIREMENTS_PATH = os.path.join(REPO_ROOT, "requirements.txt")

REQUIRED_PACKAGES = [
    "pybullet",
    "torch",
    "cvxpy",
    "diff-taichi",
    "scipy",
    "pandas",
    "numpy",
    "pytest",
]


class TestRequirementsPinned(unittest.TestCase):
    def setUp(self):
        with open(REQUIREMENTS_PATH, "r") as f:
            self.lines = [
                ln.strip()
                for ln in f
                if ln.strip() and not ln.strip().startswith("#")
            ]

    def test_file_exists(self):
        self.assertTrue(
            os.path.isfile(REQUIREMENTS_PATH),
            "requirements.txt must exist at the repository root",
        )

    def test_all_packages_present(self):
        for pkg in REQUIRED_PACKAGES:
            found = any(
                ln.split("==")[0].strip().lower() == pkg
                for ln in self.lines
            )
            self.assertTrue(
                found,
                f"Package '{pkg}' missing from requirements.txt",
            )

    def test_packages_pinned(self):
        # torch is pinned with a local version + extra index URL
        torch_line = next(
            ln for ln in self.lines if ln.startswith("torch")
        )
        self.assertIn("==2.0.0+cpu", torch_line)
        self.assertIn(
            "--index-url https://download.pytorch.org/whl/cpu",
            torch_line,
        )
        for pkg in REQUIRED_PACKAGES:
            if pkg == "torch":
                continue
            line = next(
                ln
                for ln in self.lines
                if ln.split("==")[0].strip().lower() == pkg
            )
            self.assertIn(
                "==",
                line,
                f"Package '{pkg}' must be version-pinned (==)",
            )


if __name__ == "__main__":
    unittest.main()