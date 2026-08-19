import pytest
from code.enrichment import load_background_peaks
from pathlib import Path
import tempfile
import os

def test_union_aggregation(tmp_path):
    """
    Test that background generation correctly aggregates (unioning) Peak Regions 
    from the other 4 cell types.
    Covers: US2-FR-004 (Background model must be union of other cell types)
    
    This test simulates having peak files for 5 cell types and verifies that
    when generating background for one cell type, the union of the other 4 is used.
    """
    # Create temporary directory structure
    interim_dir = tmp_path / "interim"
    interim_dir.mkdir()

    cell_types = ["GM", "K562", "HepG2", "H1-hESC", "IMR90"]
    target_cell_type = "GM"

    # Create mock peak files for each cell type
    # Format: chrom, start, end, name (standard BED-like)
    peak_data = {
        "GM": "chr1\t100\t200\tpeak_gm1\nchr1\t300\t400\tpeak_gm2",
        "K562": "chr1\t150\t250\tpeak_k562_1\nchr2\t100\t200\tpeak_k562_2",
        "HepG2": "chr1\t180\t280\tpeak_hepg2_1\nchr3\t100\t200\tpeak_hepg2_2",
        "H1-hESC": "chr1\t120\t220\tpeak_h1_1\nchr4\t100\t200\tpeak_h1_2",
        "IMR90": "chr1\t190\t290\tpeak_imr_1\nchr5\t100\t200\tpeak_imr_2",
    }

    for ct, data in peak_data.items():
        file_path = interim_dir / f"{ct}_peaks.bed"
        file_path.write_text(data)

    # Load background for target cell type (should exclude target)
    # The function load_background_peaks should take the target cell type
    # and load peaks from all OTHER cell types
    background_peaks = load_background_peaks(target_cell_type, str(interim_dir), cell_types)

    # Verify that background contains peaks from K562, HepG2, H1-hESC, IMR90
    # but NOT from GM
    assert len(background_peaks) > 0, "Background should contain peaks from other cell types"
    
    # Check that GM peaks are NOT in the background
    gm_peak_names = ["peak_gm1", "peak_gm2"]
    bg_names = [p.get("name", "") for p in background_peaks]
    for gm_name in gm_peak_names:
        assert gm_name not in bg_names, f"GM peak {gm_name} should not be in background for GM"

    # Check that other cell type peaks ARE in the background
    other_peak_names = [
        "peak_k562_1", "peak_k562_2",
        "peak_hepg2_1", "peak_hepg2_2",
        "peak_h1_1", "peak_h1_2",
        "peak_imr_1", "peak_imr_2"
    ]
    for name in other_peak_names:
        assert name in bg_names, f"Background should contain peak from other cell type: {name}"

def test_union_aggregation_empty_others(tmp_path):
    """
    Test behavior when other cell types have no peaks.
    """
    interim_dir = tmp_path / "interim"
    interim_dir.mkdir()

    cell_types = ["GM", "K562"]
    target_cell_type = "GM"

    # Create only target cell type file
    (interim_dir / "GM_peaks.bed").write_text("chr1\t100\t200\tpeak_gm1")
    # K562 file is missing or empty

    background_peaks = load_background_peaks(target_cell_type, str(interim_dir), cell_types)
    
    # Background should be empty or only contain what's available from others
    assert len(background_peaks) == 0, "Background should be empty when no other peaks exist"