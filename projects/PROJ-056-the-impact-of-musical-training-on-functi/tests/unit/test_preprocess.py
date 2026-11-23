import pathlib
import pandas as pd
import pytest

from data.preprocess import preprocess_subjects

def test_preprocess_verification(tmp_path):
    """
    Verify that the verification mode produces the expected artefacts
    and meets the SC‑005 validity threshold (≥90 % valid labels).
    """
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    # Run preprocessing in verification mode (synthetic data)
    df_matched = preprocess_subjects(
        df=None,
        mode="verification",
        synthetic_count=100,
        output_dir=str(out_dir),
    )

    # 1️⃣ Cleaned CSV & Parquet exist
    cleaned_csv = out_dir / "subjects_cleaned.csv"
    cleaned_parquet = out_dir / "subjects_cleaned.parquet"
    assert cleaned_csv.is_file()
    assert cleaned_parquet.is_file()

    # 2️⃣ Exclusion report exists and contains expected keys
    excl_report = out_dir / "exclusion_report.txt"
    assert excl_report.is_file()
    content = excl_report.read_text()
    assert "missing years_of_training" in content.lower()
    assert "corrupted nifti" in content.lower()

    # 3️⃣ Matching balance report exists and contains SMD columns
    balance_report = out_dir / "matching_balance_report.csv"
    assert balance_report.is_file()
    df_balance = pd.read_csv(balance_report)
    assert {"covariate", "pre_smd", "post_smd", "diff"}.issubset(df_balance.columns)

    # 4️⃣ Validity: at least 90 % of final rows have a non‑null group label
    final_df = pd.read_csv(cleaned_csv)
    valid_labels = final_df["group"].notna().mean()
    assert valid_labels >= 0.90

    # 5️⃣ Sample‑size guard – ensure both groups have ≥50 after matching
    group_counts = final_df["group"].value_counts()
    assert all(group_counts >= 50)

    # 6️⃣ Returned DataFrame matches the written CSV
    pd.testing.assert_frame_equal(
        final_df.reset_index(drop=True),
        df_matched.reset_index(drop=True),
        check_dtype=False,
    )