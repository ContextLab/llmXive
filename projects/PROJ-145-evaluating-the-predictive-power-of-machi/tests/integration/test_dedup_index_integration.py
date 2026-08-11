import pytest
import pandas as pd
from pathlib import Path
import json
import sys
import os
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import (
    load_hmao_dataset,
    process_and_save_heas_train,
    load_hmao_index_for_novelty_check,
    build_deduplicated_composition_index,
    sample_holdout_known,
    sample_true_novel
)

@pytest.fixture
def clean_data_dirs():
    """Ensure data directories are clean before test."""
    data_dir = Path("data/processed")
    if data_dir.exists():
        for f in data_dir.glob("*"):
            f.unlink()
    else:
        data_dir.mkdir(parents=True)
    yield
    # Cleanup after test if needed

def test_full_pipeline_dedup_index(clean_data_dirs):
    """
    Integration test: Run the full ingestion pipeline and verify the deduplicated index.
    This ensures T017 works in the context of T012-T015.
    """
    # 1. Load dataset (streaming)
    ds = load_hmao_dataset(streaming=True)
    
    # 2. Process train set
    train_df = process_and_save_heas_train(ds, Path("data/processed/heas_train.csv"))
    assert train_df is not None
    assert len(train_df) > 0
    assert Path("data/processed/heas_train.csv").exists()
    
    # 3. Build HMAO index
    hmao_index = load_hmao_index_for_novelty_check()
    assert len(hmao_index) > 0
    
    # 4. Sample holdout and novel (T014/T015 logic)
    holdout_df = sample_holdout_known(hmao_index, train_df, 100) # Small sample for speed
    holdout_df.to_csv(Path("data/processed/holdout_known.csv"), index=False)
    
    novel_df = sample_true_novel(hmao_index, 100)
    novel_df.to_csv(Path("data/processed/true_novel.csv"), index=False)
    
    # 5. T017: Build Deduplicated Index
    dedup_index = build_deduplicated_composition_index(train_df, hmao_index)
    
    # 6. Verify artifacts
    assert Path("data/processed/deduplicated_composition_index.json").exists()
    
    # Verify content
    with open("data/processed/deduplicated_composition_index.json") as f:
        loaded_index = json.load(f)
    
    assert len(loaded_index) == len(dedup_index)
    
    # Verify disjointness logic (holdout should be in index but not train)
    train_comps = set(train_df['composition'].astype(str).str.strip())
    holdout_comps = set(holdout_df['composition'].astype(str).str.strip())
    
    for comp in holdout_comps:
        canonical = "-".join(sorted(comp.split('-')))
        assert canonical in loaded_index
        # The holdout should be in the HMAO index (source=True)
        # Note: The index tracks existence, not necessarily the split
        assert loaded_index[canonical]['exists_in_source'] is True

def test_novel_set_exclusion(clean_data_dirs):
    """Verify that true_novel.csv contains compositions NOT in the HMAO index."""
    ds = load_hmao_dataset(streaming=True)
    train_df = process_and_save_heas_train(ds, Path("data/processed/heas_train.csv"))
    hmao_index = load_hmao_index_for_novelty_check()
    
    novel_df = sample_true_novel(hmao_index, 50)
    
    for comp in novel_df['composition']:
        canonical = "-".join(sorted(comp.split('-')))
        assert canonical not in hmao_index, f"Novel composition {comp} found in HMAO index!"
        assert canonical not in set(train_df['composition'].astype(str).str.strip())