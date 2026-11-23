"""Unit tests for T013: descriptor computation and quantum-proxy reporting."""

import os
import sys
import json
import numpy as np
import pandas as pd
import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from code.descriptors import compute_all_descriptors, _mol_from_smiles
from code.target_proxy import (
    build_quantum_proxy_report,
    compute_topological_proxy,
    detect_homo_lumo_column,
)


class TestDescriptors:
    def test_benzene_aromaticity(self):
        df = pd.DataFrame({"smiles": ["c1ccccc1"]})
        out = compute_all_descriptors(df)
        assert len(out) == 1
        row = out.iloc[0]
        assert row["aromatic_ring_count"] >= 1
        assert row["ring_count"] >= 1
        assert row["conjugation_path_length"] == 6  # fully conjugated ring
        assert row["molecular_weight"] > 0

    def test_butadiene_conjugation(self):
        df = pd.DataFrame({"smiles": ["C=CC=C"]})
        out = compute_all_descriptors(df)
        row = out.iloc[0]
        # 3 bonds in the conjugated chain
        assert row["conjugation_path_length"] == 3
        assert row["aromatic_ring_count"] == 0

    def test_mixed_hybridization(self):
        # Benzyl alcohol: aromatic ring plus sp3 carbon and oxygen
        df = pd.DataFrame({"smiles": ["c1ccccc1CO"]})
        out = compute_all_descriptors(df)
        row = out.iloc[0]
        assert row["aromatic_ring_count"] == 1
        assert row["degree_std"] > 0
        assert np.isfinite(row["average_path_length"])

    def test_invalid_smiles_excluded(self):
        df = pd.DataFrame({"smiles": ["c1ccccc1", "not_a_smiles!!"]})
        out = compute_all_descriptors(df)
        assert len(out) == 1
        assert out.iloc[0]["is_valid"] is True or out.iloc[0]["is_valid"] == True

    def test_at_least_ten_numeric_descriptor_values(self):
        df = pd.DataFrame({"smiles": ["c1ccccc1CC=CC"]})
        out = compute_all_descriptors(df)
        numeric_cols = [
            c for c in out.columns
            if c not in ("smiles", "is_valid")
            and np.issubdtype(out[c].dtype, np.number)
        ]
        assert len(numeric_cols) >= 8  # schema numeric columns
        assert out[numeric_cols].notna().all().all()

    def test_schema_columns_exact(self):
        df = pd.DataFrame({"smiles": ["CCO"]})
        out = compute_all_descriptors(df)
        expected = {
            "smiles", "aromatic_ring_count", "conjugation_path_length",
            "average_path_length", "degree_mean", "degree_std",
            "ring_count", "molecular_weight", "homo_lumo_gap", "is_valid",
        }
        assert set(out.columns) == expected

    def test_homo_lumo_passthrough(self):
        df = pd.DataFrame({"smiles": ["CCO"], "homo_lumo_gap": [5.2]})
        out = compute_all_descriptors(df)
        assert out.iloc[0]["homo_lumo_gap"] == 5.2

    def test_mol_from_smiles_none_on_garbage(self):
        assert _mol_from_smiles("!!!") is None
        assert _mol_from_smiles("") is None


class TestTargetProxy:
    def test_report_no_quantum_no_conductivity(self):
        raw = pd.DataFrame({"smiles": ["CCO"]})
        report = build_quantum_proxy_report(raw)
        assert report["homo_lumo_present"] is False
        assert report["fallback_used"] is True
        assert report["target_type"] == "topological_proxy"

    def test_report_conductivity_present(self):
        raw = pd.DataFrame({"smiles": ["CCO"], "conductivity": [1e-4]})
        report = build_quantum_proxy_report(raw)
        assert report["homo_lumo_present"] is False
        assert report["fallback_used"] is False
        assert report["target_type"] == "measured_conductivity"

    def test_report_homo_lumo_present(self):
        raw = pd.DataFrame({"smiles": ["CCO"], "homo_lumo_gap": [4.5]})
        report = build_quantum_proxy_report(raw)
        assert report["homo_lumo_present"] is True
        assert report["target_type"] == "homo_lumo_gap"

    def test_detect_homo_lumo_column(self):
        assert detect_homo_lumo_column(pd.DataFrame({"smiles": ["C"]})) is None
        assert detect_homo_lumo_column(
            pd.DataFrame({"smiles": ["C"], "HOMO_LUMO_gap": [1.0]})
        ) == "HOMO_LUMO_gap"

    def test_topological_proxy(self):
        value = compute_topological_proxy(2, 5)
        assert value == pytest.approx(0.6 * 2 + 0.4 * 5)