"""Tests for T000: pinned requirements, global seed, and checksum manifest."""

import random
from pathlib import Path

import numpy as np
import pytest

from llmxive_toolkit import paths


def test_requirements_are_exactly_pinned():
  req_path = paths.root / "requirements.txt"
  assert req_path.is_file(), "requirements.txt must exist"
  bad = []
  for raw in req_path.read_text(encoding="utf-8").splitlines():
      line = raw.strip()
      if not line or line.startswith("#"):
          continue
      if "==" not in line or line.split("==", 1)[1].strip() == "":
          bad.append(line)
      elif "*" in line.split("==", 1)[1]:
          bad.append(line)
  assert not bad, f"Non-pinned requirement specs found: {bad}"


def test_global_seed_is_42_and_deterministic():
  import src.utils.seeds as seeds

  assert seeds.GLOBAL_SEED == 42
  seeds.set_global_seed(42)
  a = (random.random(), np.random.rand())
  seeds.set_global_seed(42)
  b = (random.random(), np.random.rand())
  assert a == b, "set_global_seed(42) must be deterministic"


def test_checksums_manifest_matches_files():
  manifest = paths.data("checksums.txt")
  assert manifest.is_file(), "data/checksums.txt must exist"

  entries = {}
  for line in manifest.read_text(encoding="utf-8").splitlines():
      line = line.strip()
      if not line:
          continue
      digest, rel = line.split("  ", 1)
      entries[rel] = digest

  assert entries, "checksum manifest is empty"

  import hashlib

  data_root = paths.data()
  for rel, digest in entries.items():
      f = data_root / rel
      assert f.is_file(), f"manifest references missing file {rel}"
      h = hashlib.sha256(f.read_bytes()).hexdigest()
      assert h == digest, f"checksum mismatch for {rel}"

  # Every raw data file (other than the manifest itself) must be listed.
  on_disk = {
      str(p.relative_to(data_root))
      for p in data_root.rglob("*")
      if p.is_file() and p.name != "checksums.txt"
  }
  missing = on_disk - set(entries)
  assert not missing, f"files missing from manifest: {sorted(missing)}"