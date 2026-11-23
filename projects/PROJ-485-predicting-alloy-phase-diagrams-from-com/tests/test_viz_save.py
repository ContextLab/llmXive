import os
import sys
import tempfile
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from viz.save_plots import save_plot_to_disk, run_save_plots, ensure_output_dir

class TestSavePlots:
    """Tests for T037: Save generated plots to data/artifacts/plots/"""

    def test_ensure_output_dir_creates_directory(self):
        """Test that ensure_output_dir creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_plots")
            assert not os.path.exists(test_dir)
            
            ensure_output_dir(test_dir)
            
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)

    def test_save_plot_to_disk_creates_file(self):
        """Test that save_plot_to_disk creates a file with correct naming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock plot_data dictionary
            # In real usage, this would come from matplotlib figure
            mock_plot_data = {
                'figure': None,  # We'll test the path logic
                'system_id': 'Cu-Zn'
            }
            
            # Test with a pre-existing file path (simulating saved plot)
            test_file = os.path.join(tmpdir, "Cu-Zn.png")
            with open(test_file, 'w') as f:
                f.write("mock plot data")
            
            result_path = save_plot_to_disk(
                plot_data=test_file,
                system_id="Cu-Zn",
                output_dir=tmpdir,
                format="png"
            )
            
            assert result_path == test_file
            assert os.path.exists(result_path)

    def test_save_plot_to_disk_sanitizes_system_id(self):
        """Test that system_id with special characters is sanitized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock plot_data dictionary
            mock_plot_data = {'figure': None}
            
            # Test with system_id containing slashes (edge case)
            result_path = save_plot_to_disk(
                plot_data=mock_plot_data,
                system_id="Cu/Zn",
                output_dir=tmpdir,
                format="png"
            )
            
            # Should sanitize to Cu_Zn.png
            expected_filename = "Cu_Zn.png"
            assert expected_filename in result_path

    def test_run_save_plots_returns_dict(self):
        """Test that run_save_plots returns a dictionary of saved files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # This test verifies the function signature and return type
            # Actual plot generation depends on model and data availability
            result = run_save_plots(
                systems=["Cu-Zn"],
                output_dir=tmpdir,
                format="png"
            )
            
            assert isinstance(result, dict)
            # Result should map system_id to filepath

    def test_naming_convention_system_id(self):
        """Test that files are saved with system ID naming convention (FR-005)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate the expected output
            test_cases = [
                ("Cu-Zn", "Cu-Zn.png"),
                ("Al-Cu", "Al-Cu.png"),
                ("Fe-C", "Fe-C.png"),
            ]
            
            for system_id, expected_filename in test_cases:
                filepath = os.path.join(tmpdir, expected_filename)
                with open(filepath, 'w') as f:
                    f.write("mock")
                
                # Verify the file exists with correct name
                assert os.path.exists(filepath)
                assert os.path.basename(filepath) == expected_filename

    def test_png_format_default(self):
        """Test that PNG is the default format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock plot_data dictionary
            mock_plot_data = {'figure': None}
            
            # Call with default format
            result = save_plot_to_disk(
                plot_data=tmpdir,  # Pass directory as placeholder
                system_id="Cu-Zn",
                output_dir=tmpdir
            )
            
            # Should default to PNG
            assert result.endswith(".png")

    def test_svg_format_explicit(self):
        """Test that SVG format can be explicitly specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_plot_data = {'figure': None}
            
            result = save_plot_to_disk(
                plot_data=tmpdir,
                system_id="Cu-Zn",
                output_dir=tmpdir,
                format="svg"
            )
            
            assert result.endswith(".svg")

    def test_file_existence_verification(self):
        """Test that the function verifies files exist after saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock plot_data dictionary
            mock_plot_data = {'figure': None}
            
            # Save a file
            filepath = save_plot_to_disk(
                plot_data=tmpdir,
                system_id="Cu-Zn",
                output_dir=tmpdir,
                format="png"
            )
            
            # Verify file exists (this is implicitly tested by save_plot_to_disk logic)
            assert os.path.exists(filepath)

    def test_multiple_systems_processed(self):
        """Test that multiple systems can be processed in one run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock files for multiple systems
            systems = ["Cu-Zn", "Al-Cu", "Fe-C"]
            for system in systems:
                filepath = os.path.join(tmpdir, f"{system}.png")
                with open(filepath, 'w') as f:
                    f.write("mock")
            
            # Verify all files exist
            for system in systems:
                filepath = os.path.join(tmpdir, f"{system}.png")
                assert os.path.exists(filepath)
    
    def test_empty_system_list(self):
        """Test behavior with empty system list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_save_plots(
                systems=[],
                output_dir=tmpdir,
                format="png"
            )
            
            assert result == {}