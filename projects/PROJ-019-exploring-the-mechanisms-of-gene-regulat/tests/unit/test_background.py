"""
Unit tests for background model aggregation logic.
Specifically tests the union aggregation of peak regions from other cell types.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from typing import List, Tuple

# Add project root to path if running standalone, though pytest usually handles this
# via PYTHONPATH or conftest. We assume standard project structure.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess import aggregate_background_model
from code.config import DATA_INTERIM_DIR


def write_temp_bed_file(path: Path, regions: List[Tuple[str, int, int, str]]):
    """Helper to write a mock BED file to disk."""
    with open(path, 'w') as f:
        for chrom, start, end, name in regions:
            f.write(f"{chrom}\t{start}\t{end}\t{name}\n")


@pytest.fixture
def temp_interim_dir():
    """Create a temporary directory mimicking the interim data structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the DATA_INTERIM_DIR structure
        # We expect subdirectories for each cell type containing 'peaks.bed'
        # Or flat files. Based on T014, we assume process_cell_type_peaks creates
        # a standardized file. Let's assume the structure is:
        # DATA_INTERIM_DIR / {cell_type} / "peaks_standardized.bed"
        # or simply DATA_INTERIM_DIR / "{cell_type}_peaks.bed"
        # Given T014 description: "store in data/interim/", let's assume a flat structure
        # for simplicity in this test, or a specific naming convention.
        # Let's assume the function expects a dict of {cell_type: path_to_bed_file}
        # or it scans a directory.
        
        # Looking at T014: "aggregate_background_model... using pybedtools to map... and aggregate"
        # The test description says: "assert background generation correctly aggregates (unioning) Peak Regions from the other 4 cell types."
        
        # We need to mock the input state.
        # Let's assume aggregate_background_model takes a list of cell types to exclude
        # and scans DATA_INTERIM_DIR for the remaining ones.
        
        # Create mock directories and files for 5 cell types
        cell_types = ["GM", "K562", "HepG2", "H1-hESC", "IMR90"]
        mock_files = {}
        
        # Define distinct peaks for each to verify union logic
        # GM: chr1:100-200
        # K562: chr1:150-250 (overlaps GM)
        # HepG2: chr1:500-600
        # H1-hESC: chr1:100-200 (same as GM)
        # IMR90: chr2:100-200 (different chromosome)
        
        data = {
            "GM": [("chr1", 100, 200, "GM_peak1")],
            "K562": [("chr1", 150, 250, "K562_peak1")],
            "HepG2": [("chr1", 500, 600, "HepG2_peak1")],
            "H1-hESC": [("chr1", 100, 200, "H1_peak1")],
            "IMR90": [("chr2", 100, 200, "IMR90_peak1")]
        }

        for ct, regions in data.items():
            ct_dir = Path(tmpdir) / ct
            ct_dir.mkdir(parents=True, exist_ok=True)
            bed_path = ct_dir / "peaks_standardized.bed"
            write_temp_bed_file(bed_path, regions)
            mock_files[ct] = bed_path

        # Temporarily override the config or pass the path explicitly?
        # The function likely uses the global DATA_INTERIM_DIR.
        # We will monkeypatch the config or pass the temp dir if the function signature allows.
        # If not, we might need to mock the config variable.
        # Let's assume the function signature is: aggregate_background_model(target_cell_type, base_dir=None)
        # or it uses the global constant.
        
        # To be safe and test the logic, let's check the import of aggregate_background_model.
        # If it hardcodes DATA_INTERIM_DIR, we can mock it.
        
        yield tmpdir, data


def test_union_aggregation(temp_interim_dir):
    """
    Test that the background model correctly unions peaks from all cell types
    EXCEPT the target cell type.
    
    Scenario:
    Target = "GM"
    Sources = K562, HepG2, H1-hESC, IMR90
    
    Expected Union:
    - chr1:150-250 (from K562, overlaps GM but GM is excluded)
    - chr1:500-600 (from HepG2)
    - chr1:100-200 (from H1-hESC)
    - chr2:100-200 (from IMR90)
    
    Note: K562 (150-250) and H1-hESC (100-200) overlap.
    The union should merge overlapping regions.
    Interval [100, 200] and [150, 250] -> Union [100, 250].
    So expected regions on chr1: [100, 250] and [500, 600].
    On chr2: [100, 200].
    """
    tmpdir, data = temp_interim_dir
    target_cell_type = "GM"
    
    # We need to ensure the function sees our temp directory.
    # If aggregate_background_model uses the global DATA_INTERIM_DIR constant,
    # we must patch it.
    # Let's assume the function signature allows a base_dir argument or we patch the module.
    
    # Attempt to call the function. If it strictly uses the global constant,
    # we patch the constant in the preprocess module.
    from code import preprocess
    original_dir = preprocess.DATA_INTERIM_DIR
    preprocess.DATA_INTERIM_DIR = Path(tmpdir)
    
    try:
        # Call the function. Assuming it returns a list of BedTool objects or a file path.
        # The task says "aggregate background model... using pybedtools".
        # Let's assume it returns a BedTool object or a list of merged intervals.
        # We need to check the actual return type. If it writes to disk, we check the file.
        # Based on T014: "aggregate_background_model...".
        # Let's assume it returns a pybedtools.BedTool object representing the union.
        
        background_bed = aggregate_background_model(target_cell_type=target_cell_type)
        
        # background_bed should be a BedTool object or similar iterable
        assert background_bed is not None, "Background model should not be None"
        
        # Convert to list of intervals to inspect
        intervals = list(background_bed)
        
        # We expect:
        # 1. chr1:100-250 (Union of H1-hESC [100-200] and K562 [150-250])
        # 2. chr1:500-600 (HepG2)
        # 3. chr2:100-200 (IMR90)
        
        # Sort intervals for deterministic checking
        # BedTool intervals are (chrom, start, end, name, score, strand)
        # We sort by chrom, then start
        intervals.sort(key=lambda x: (x.chrom, x.start))
        
        assert len(intervals) == 3, f"Expected 3 merged regions, got {len(intervals)}: {intervals}"
        
        # Check chr1 merged region
        # H1-hESC: 100-200, K562: 150-250 -> Union 100-250
        assert intervals[0].chrom == "chr1"
        assert intervals[0].start == 100
        assert intervals[0].end == 250
        
        # Check chr1 separate region
        assert intervals[1].chrom == "chr1"
        assert intervals[1].start == 500
        assert intervals[1].end == 600
        
        # Check chr2 region
        assert intervals[2].chrom == "chr2"
        assert intervals[2].start == 100
        assert intervals[2].end == 200

    finally:
        # Restore original config
        preprocess.DATA_INTERIM_DIR = original_dir


def test_union_aggregation_excludes_target(temp_interim_dir):
    """
    Test that the target cell type's peaks are NOT included in the background.
    Target = "HepG2"
    Sources = GM, K562, H1-hESC, IMR90
    
    HepG2 has chr1:500-600.
    If the background is correct, chr1:500-600 should NOT appear unless another cell type has it.
    None of the others have chr1:500-600.
    """
    tmpdir, _ = temp_interim_dir
    target_cell_type = "HepG2"
    
    from code import preprocess
    original_dir = preprocess.DATA_INTERIM_DIR
    preprocess.DATA_INTERIM_DIR = Path(tmpdir)
    
    try:
        background_bed = aggregate_background_model(target_cell_type=target_cell_type)
        intervals = list(background_bed)
        
        # Check that no interval corresponds to HepG2's unique region
        # HepG2: chr1:500-600
        for interval in intervals:
            if interval.chrom == "chr1" and interval.start == 500 and interval.end == 600:
                pytest.fail(f"Target cell type HepG2 region (chr1:500-600) found in background: {interval}")
                
        # Verify we still have other regions
        # GM (100-200), K562 (150-250) -> Union 100-250
        # H1-hESC (100-200) -> already covered
        # IMR90 (chr2:100-200)
        # Expected: chr1:100-250, chr2:100-200
        assert len(intervals) == 2
        
    finally:
        preprocess.DATA_INTERIM_DIR = original_dir