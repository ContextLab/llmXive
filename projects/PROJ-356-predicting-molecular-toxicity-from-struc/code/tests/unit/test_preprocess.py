"""
Unit tests for SMILES standardization and molecular weight filtering (T015, US1).

These tests are written BEFORE the implementation of
``src/data/preprocess.py`` (T020) and are expected to FAIL with an
ImportError until that module is implemented. They define the contract:

- ``canonicalize_smiles(smiles: str) -> str``: RDKit canonical SMILES.
- ``remove_salts(smiles: str) -> str``: strip salt fragments, keep largest
  organic fragment.
- ``filter_by_molecular_weight(molecules, max_mw=1000.0)``: keep entries
  whose computed MW is below ``max_mw``; drop invalid/None entries.
- ``preprocess_dataframe(df, ...)``: full pipeline: canonicalize, remove
  salts, MW filter, deduplicate by canonical SMILES, discard
  label-conflicting groups, and raise ValueError if final N <= 1000.
"""
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

# Ensure the code directory is importable regardless of invocation cwd.
CODE_DIR = Path(__file__).resolve().parent.parent.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


class TestSMILESStandardization:
    def test_canonicalize_smiles(self):
        """Different valid representations canonicalize identically."""
        from src.data.preprocess import canonicalize_smiles

        assert canonicalize_smiles("CCO") == canonicalize_smiles("OCC")
        assert canonicalize_smiles("c1ccccc1") == canonicalize_smiles("C1=CC=CC=C1")

    def test_canonicalize_returns_string(self):
        from src.data.preprocess import canonicalize_smiles

        result = canonicalize_smiles("CCO")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_canonicalize_invalid_raises(self):
        """Invalid SMILES must fail loudly, not silently return input."""
        from src.data.preprocess import canonicalize_smiles

        with pytest.raises(Exception):
            canonicalize_smiles("not_a_valid_smiles")

    def test_remove_salts(self):
        """Salt fragments are stripped; only the organic fragment remains."""
        from src.data.preprocess import remove_salts

        cleaned = remove_salts("CCO.[Na+]")
        assert "." not in cleaned
        assert "Na" not in cleaned

    def test_remove_salts_no_salt_unchanged(self):
        from src.data.preprocess import remove_salts

        cleaned = remove_salts("CCO")
        assert "." not in cleaned

    def test_remove_salts_keeps_largest_fragment(self):
        from src.data.preprocess import remove_salts

        cleaned = remove_salts("CCCC.CC")
        assert "." not in cleaned
        assert len(cleaned) >= 2  # the larger fragment is retained


class TestMolecularWeightFiltering:
    def test_filter_by_molecular_weight(self):
        """Only molecules below the MW cutoff are retained."""
        from src.data.preprocess import filter_by_molecular_weight

        molecules: List[Tuple[str, float]] = [
            ("CCO", 46.07),                      # Ethanol
            ("CCCCCCCCCCCCCCCC", 226.44),        # Octadecane
            ("C1=CC=C(C=C1)C(=O)O", 122.12),     # Benzoic acid
        ]
        filtered = filter_by_molecular_weight(molecules, max_mw=100)
        assert len(filtered) == 1
        assert filtered[0][1] < 100

    def test_filter_default_cutoff_1000(self):
        """Default cutoff enforces the FR-002 MW < 1000 Da rule."""
        from src.data.preprocess import filter_by_molecular_weight

        molecules = [("CCO", 46.07), ("C" * 60, 1500.0)]
        filtered = filter_by_molecular_weight(molecules)
        assert all(mw < 1000 for _, mw in filtered)

    def test_filter_handles_invalid_mw(self):
        """Entries with None/invalid MW are dropped, not crashed on."""
        from src.data.preprocess import filter_by_molecular_weight

        molecules = [("CCO", 46.07), ("INVALID", None)]
        filtered = filter_by_molecular_weight(molecules, max_mw=100)
        assert len(filtered) == 1
        assert filtered[0][0] == "CCO"

    def test_filter_empty_list(self):
        from src.data.preprocess import filter_by_molecular_weight

        assert filter_by_molecular_weight([], max_mw=100) == []


class TestDuplicateHandling:
    def test_conflicting_labels_discarded(self):
        """Groups with >1 unique label are discarded entirely."""
        import pandas as pd
        from src.data.preprocess import preprocess_dataframe

        rows = []
        # 1100 agreeing rows to stay above the N > 1000 threshold
        for i in range(1100):
            rows.append({"smiles": "CCO", "label": 0})
        # conflicting duplicates of one SMILES
        rows.append({"smiles": "CCO", "label": 1})
        rows.append({"smiles": "c1ccccc1", "label": 0})
        rows.append({"smiles": "c1ccccc1", "label": 1})
        df = pd.DataFrame(rows)

        out = preprocess_dataframe(df)
        # all CCO rows share label 0 -> kept as one unique entry
        # c1ccccc1 has conflicting labels -> discarded
        assert "c1ccccc1" not in set(out["smiles"])

    def test_agreeing_duplicates_collapsed(self):
        import pandas as pd
        from src.data.preprocess import preprocess_dataframe

        rows = [{"smiles": "CCO" if i % 2 == 0 else "OCC", "label": 0}
                for i in range(1100)]
        df = pd.DataFrame(rows)
        out = preprocess_dataframe(df)
        assert len(out) == 1
        assert out.iloc[0]["smiles"] == "CCO"

    def test_mw_filter_applied(self):
        import pandas as pd
        from src.data.preprocess import preprocess_dataframe

        rows = [{"smiles": "CCO", "label": 0}] * 1100
        rows.append({"smiles": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC", "label": 1})
        df = pd.DataFrame(rows)
        out = preprocess_dataframe(df)
        assert len(out[out["smiles"] == "CCO"]) == 1

    def test_below_minimum_raises(self):
        """Final N <= 1000 must raise ValueError, not warn and proceed."""
        import pandas as pd
        from src.data.preprocess import preprocess_dataframe

        df = pd.DataFrame(
            [{"smiles": "CCO", "label": 0}] * 500
            + [{"smiles": "c1ccccc1", "label": 1}] * 400
        )
        with pytest.raises(ValueError, match="minimum threshold of 1000"):
            preprocess_dataframe(df)

    def test_preprocessing_log_written(self, tmp_path):
        """Counts of discarded conflicts and final N are reported."""
        import json
        import pandas as pd
        from src.data.preprocess import preprocess_dataframe

        rows = [{"smiles": "CCO", "label": 0}] * 1100
        rows.append({"smiles": "c1ccccc1", "label": 0})
        rows.append({"smiles": "c1ccccc1", "label": 1})
        df = pd.DataFrame(rows)
        out = preprocess_dataframe(df, log_path=tmp_path / "preprocessing_log.json")

        log_file = tmp_path / "preprocessing_log.json"
        assert log_file.exists()
        log = json.loads(log_file.read_text())
        assert "discarded_conflict_count" in log
        assert "final_n" in log
        assert log["final_n"] == len(out)
        assert log["final_n"] > 1000