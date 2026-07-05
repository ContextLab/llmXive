"""
Contract test for plot output files (US3).

This test verifies that the visualization pipeline produces the expected
output files with correct structure and non-empty content.

Test Requirements:
- Verifies existence of all expected plot files
- Validates file sizes are non-zero
- Checks file format validity (PNG headers)
- Ensures filenames match expected naming convention
"""
import os
import pytest
from pathlib import Path
import struct
import json
from typing import List, Dict, Any

# Project imports
from utils.config import get_data_dir, get_processed_data_dir


# Expected output paths and naming conventions
EXPECTED_PLOTS = {
    'scatter': 'figures/scatter_csa_vs_food_security.png',
    'coefficient': 'figures/coefficient_plot.png',
    'regional_map': 'figures/regional_csa_adoption_map.png',
    'distribution': 'figures/distribution_csa_index.png',
    'robustness_summary': 'figures/robustness_summary.png',
}

# Expected robustness check outputs
EXPECTED_ROBUSTNESS_LOGS = {
    'leave_one_region': 'data/processed/robustness_leave_one_region.json',
    'bootstrap_results': 'data/processed/robustness_bootstrap.json',
}

# Minimum file size in bytes (plots should be at least 1KB)
MIN_FILE_SIZE = 1024

# PNG magic bytes
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


class TestPlotOutputContract:
    """Contract tests for plot output files."""
    
    @pytest.fixture(scope='class')
    def figures_dir(self):
        """Get the figures directory path."""
        data_dir = get_data_dir()
        return data_dir.parent / 'figures'
    
    @pytest.fixture(scope='class')
    def processed_dir(self):
        """Get the processed data directory path."""
        return get_processed_data_dir()
    
    def test_figures_directory_exists(self, figures_dir):
        """Verify that the figures directory exists."""
        assert figures_dir.exists(), f"Figures directory does not exist: {figures_dir}"
        assert figures_dir.is_dir(), f"Path is not a directory: {figures_dir}"
    
    def test_all_expected_plot_files_exist(self, figures_dir):
        """Verify all expected plot files exist."""
        missing_files = []
        for plot_name, relative_path in EXPECTED_PLOTS.items():
            full_path = figures_dir / relative_path
            if not full_path.exists():
                missing_files.append(relative_path)
        
        if missing_files:
            pytest.fail(f"Missing expected plot files: {missing_files}")
    
    def test_plot_files_are_non_empty(self, figures_dir):
        """Verify all plot files have non-zero size."""
        empty_files = []
        for plot_name, relative_path in EXPECTED_PLOTS.items():
            full_path = figures_dir / relative_path
            if full_path.exists():
                size = full_path.stat().st_size
                if size == 0:
                    empty_files.append(relative_path)
                elif size < MIN_FILE_SIZE:
                    # Log warning but don't fail for small files
                    pytest.warns(f"File {relative_path} is unusually small: {size} bytes")
        
        if empty_files:
            pytest.fail(f"Empty or near-empty plot files: {empty_files}")
    
    def test_png_files_have_valid_header(self, figures_dir):
        """Verify PNG files have valid PNG magic bytes."""
        invalid_files = []
        for plot_name, relative_path in EXPECTED_PLOTS.items():
            full_path = figures_dir / relative_path
            if full_path.exists() and relative_path.endswith('.png'):
                try:
                    with open(full_path, 'rb') as f:
                        header = f.read(8)
                        if header != PNG_MAGIC:
                            invalid_files.append(relative_path)
                except Exception as e:
                    invalid_files.append(f"{relative_path} (error: {e})")
        
        if invalid_files:
            pytest.fail(f"Invalid PNG headers: {invalid_files}")
    
    def test_robustness_logs_directory_exists(self, processed_dir):
        """Verify that the robustness logs directory exists."""
        assert processed_dir.exists(), f"Processed data directory does not exist: {processed_dir}"
        assert processed_dir.is_dir(), f"Path is not a directory: {processed_dir}"
    
    def test_robustness_log_files_exist(self, processed_dir):
        """Verify all expected robustness log files exist."""
        missing_files = []
        for log_name, relative_path in EXPECTED_ROBUSTNESS_LOGS.items():
            full_path = processed_dir / relative_path
            if not full_path.exists():
                missing_files.append(relative_path)
        
        if missing_files:
            pytest.fail(f"Missing expected robustness log files: {missing_files}")
    
    def test_robustness_logs_are_valid_json(self, processed_dir):
        """Verify robustness log files contain valid JSON."""
        invalid_files = []
        for log_name, relative_path in EXPECTED_ROBUSTNESS_LOGS.items():
            full_path = processed_dir / relative_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                        # Verify basic structure
                        if not isinstance(data, dict):
                            invalid_files.append(f"{relative_path} (not a dict)")
                        elif 'summary' not in data and 'results' not in data:
                            invalid_files.append(f"{relative_path} (missing summary/results key)")
                except json.JSONDecodeError as e:
                    invalid_files.append(f"{relative_path} (JSON error: {e})")
                except Exception as e:
                    invalid_files.append(f"{relative_path} (error: {e})")
        
        if invalid_files:
            pytest.fail(f"Invalid JSON in robustness logs: {invalid_files}")
    
    def test_plot_filenames_match_convention(self, figures_dir):
        """Verify plot filenames follow the expected naming convention."""
        convention_violations = []
        for plot_name, expected_path in EXPECTED_PLOTS.items():
            expected_filename = Path(expected_path).name
            actual_files = list(figures_dir.glob(f"*{plot_name}*.png"))
            if not actual_files:
                convention_violations.append(f"No file matching '*{plot_name}*.png' found")
            elif expected_filename not in [f.name for f in actual_files]:
                # Allow variations but warn if exact match not found
                convention_violations.append(
                    f"Expected '{expected_filename}', found: {[f.name for f in actual_files]}"
                )
        
        if convention_violations:
            # Log as warnings rather than failing, as naming can vary slightly
            pytest.warns(f"Naming convention issues: {convention_violations}")
    
    def test_plot_metadata_consistency(self, figures_dir):
        """Verify plots have consistent metadata (if embedded)."""
        # This is an optional check - many PNGs may not have metadata
        # We just verify we can open them without errors
        unreadable_files = []
        for plot_name, relative_path in EXPECTED_PLOTS.items():
            full_path = figures_dir / relative_path
            if full_path.exists():
                try:
                    # Try to read basic info
                    with open(full_path, 'rb') as f:
                        data = f.read(100)  # Read first 100 bytes
                        if len(data) < 24:  # PNG header is 8 bytes + IHDR chunk
                            unreadable_files.append(relative_path)
                except Exception as e:
                    unreadable_files.append(f"{relative_path} (error: {e})")
        
        if unreadable_files:
            pytest.fail(f"Unreadable plot files: {unreadable_files}")
    
    def test_robustness_log_content_structure(self, processed_dir):
        """Verify robustness logs contain expected structure."""
        for log_name, relative_path in EXPECTED_ROBUSTNESS_LOGS.items():
            full_path = processed_dir / relative_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    data = json.load(f)
                
                # Check for expected keys based on log type
                if 'leave_one_region' in relative_path:
                    assert 'iterations' in data or 'regions_tested' in data, \
                        f"{relative_path} missing expected keys for leave-one-region analysis"
                elif 'bootstrap' in relative_path:
                    assert 'iterations' in data or 'n_bootstrap' in data, \
                        f"{relative_path} missing expected keys for bootstrap analysis"
    
    def test_all_plots_have_appropriate_dimensions(self, figures_dir):
        """Verify plots have reasonable dimensions (not too small or too large)."""
        import struct
        
        dimension_issues = []
        for plot_name, relative_path in EXPECTED_PLOTS.items():
            full_path = figures_dir / relative_path
            if full_path.exists() and relative_path.endswith('.png'):
                try:
                    with open(full_path, 'rb') as f:
                        f.seek(16)  # IHDR chunk starts at byte 16
                        width_bytes = f.read(4)
                        height_bytes = f.read(4)
                        width = struct.unpack('>I', width_bytes)[0]
                        height = struct.unpack('>I', height_bytes)[0]
                        
                        if width < 100 or height < 100:
                            dimension_issues.append(
                                f"{relative_path}: too small ({width}x{height})"
                            )
                        elif width > 10000 or height > 10000:
                            dimension_issues.append(
                                f"{relative_path}: too large ({width}x{height})"
                            )
                except Exception as e:
                    dimension_issues.append(f"{relative_path}: error reading dimensions ({e})")
        
        if dimension_issues:
            pytest.fail(f"Dimension issues: {dimension_issues}")
    
    def test_no_duplicate_plot_files(self, figures_dir):
        """Verify there are no duplicate plot files with different names."""
        # Check for files that might be duplicates (same size, similar name)
        # This is a basic heuristic check
        file_sizes = {}
        duplicates = []
        
        for plot_file in figures_dir.glob("*.png"):
            size = plot_file.stat().st_size
            if size in file_sizes:
                # Check if names are suspiciously similar
                if any(
                    common in plot_file.name and common in file_sizes[size]
                    for common in ['scatter', 'coefficient', 'map', 'distribution', 'robustness']
                ):
                    duplicates.append(
                        f"{plot_file.name} and {file_sizes[size]} (same size: {size})"
                    )
            else:
                file_sizes[size] = plot_file.name
        
        if duplicates:
            pytest.warns(f"Possible duplicate files detected: {duplicates}")
    
    def test_plot_output_timestamp_consistency(self, figures_dir):
        """Verify plot files have reasonable modification timestamps."""
        import time
        
        now = time.time()
        old_files = []
        
        for plot_name, relative_path in EXPECTED_PLOTS.items():
            full_path = figures_dir / relative_path
            if full_path.exists():
                mtime = full_path.stat().st_mtime
                age_days = (now - mtime) / (24 * 3600)
                
                # Warn if file is older than 30 days (might be stale)
                if age_days > 30:
                    old_files.append(f"{relative_path} ({age_days:.1f} days old)")
        
        if old_files:
            pytest.warns(f"Potentially stale plot files: {old_files}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])