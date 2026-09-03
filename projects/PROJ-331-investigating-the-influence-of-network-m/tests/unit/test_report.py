import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np

# Import functions from the project's report module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from report import load_results, generate_correlation_plot, extract_methods_from_log, generate_methods_section, generate_pdf


class TestLoadResults:
    """Unit tests for load_results function."""

    def test_loads_correlation_results(self):
        """Verify loading correlation results from JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'motif_M1': {
                    'pearson_r': 0.5,
                    'pearson_p': 0.01,
                    'bonferroni_p': 0.13
                },
                'motif_M13': {
                    'pearson_r': -0.3,
                    'pearson_p': 0.04,
                    'bonferroni_p': 0.52
                }
            }, f)
            temp_path = f.name
        
        try:
            results = load_results(temp_path)
            assert isinstance(results, dict)
            assert 'motif_M1' in results
            assert results['motif_M1']['pearson_r'] == 0.5
        finally:
            os.unlink(temp_path)

    def test_handles_missing_file(self):
        """Verify the function raises an error for missing files."""
        with pytest.raises(FileNotFoundError):
            load_results("nonexistent_file.json")


class TestGenerateCorrelationPlot:
    """Unit tests for generate_correlation_plot function."""

    def test_creates_plot(self):
        """Verify the function creates a plot object."""
        # Create sample data
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r = 0.9
        p = 0.01
        
        fig = generate_correlation_plot(x, y, r, p, "Test Motif")
        
        assert fig is not None
        # Check that it's a matplotlib figure
        import matplotlib.pyplot as plt
        assert isinstance(fig, plt.Figure)

    def test_handles_zero_variance(self):
        """Verify the function handles zero variance gracefully."""
        x = np.array([1, 1, 1, 1, 1])  # Zero variance
        y = np.array([2, 4, 6, 8, 10])
        
        # Should not crash
        fig = generate_correlation_plot(x, y, 0.0, 1.0, "Zero Variance Motif")
        assert fig is not None


class TestExtractMethodsFromLog:
    """Unit tests for extract_methods_from_log function."""

    def test_parses_log_file(self):
        """Verify the function extracts statistical parameters from log."""
        log_content = """
        [INFO] Pipeline started
        [STATS] Bonferroni alpha: 0.003846 (13 motifs)
        [STATS] Permutation count: 1000
        [STATS] Random seed: 42
        [STATS] numpy version: 1.24.0
        [STATS] scipy version: 1.10.0
        [STATS] statsmodels version: 0.14.0
        [INFO] Pipeline completed
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_path = f.name
        
        try:
            methods = extract_methods_from_log(temp_path)
            assert isinstance(methods, dict)
            assert methods['bonferroni_alpha'] == 0.003846
            assert methods['permutation_count'] == 1000
            assert methods['random_seed'] == 42
            assert 'numpy' in methods['library_versions']
        finally:
            os.unlink(temp_path)

    def test_handles_missing_log(self):
        """Verify the function handles missing log files."""
        with pytest.raises(FileNotFoundError):
            extract_methods_from_log("nonexistent.log")


class TestGenerateMethodsSection:
    """Unit tests for generate_methods_section function."""

    def test_generates_methods_text(self):
        """Verify the function generates methods section text."""
        methods_data = {
            'bonferroni_alpha': 0.003846,
            'permutation_count': 1000,
            'random_seed': 42,
            'library_versions': {
                'numpy': '1.24.0',
                'scipy': '1.10.0',
                'statsmodels': '0.14.0'
            }
        }
        
        text = generate_methods_section(methods_data)
        
        assert isinstance(text, str)
        assert 'Bonferroni' in text
        assert '1000' in text
        assert '42' in text
        assert 'numpy' in text

    def test_handles_missing_data(self):
        """Verify the function handles missing data gracefully."""
        text = generate_methods_section({})
        assert isinstance(text, str)
        assert len(text) > 0


class TestGeneratePdf:
    """Unit tests for generate_pdf function."""

    def test_creates_pdf_file(self):
        """Verify the function creates a PDF file."""
        # Create temporary input files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create correlation results
            corr_results = {
                'motif_M1': {
                    'pearson_r': 0.5,
                    'pearson_p': 0.01,
                    'bonferroni_p': 0.13,
                    'significant': False
                }
            }
            corr_path = tmpdir / 'correlation_results.json'
            with open(corr_path, 'w') as f:
                json.dump(corr_results, f)
            
            # Create permutation results
            perm_results = []
            perm_path = tmpdir / 'permutation_results.json'
            with open(perm_path, 'w') as f:
                json.dump(perm_results, f)
            
            # Create power analysis
            power_results = {
                'min_detectable_r': 0.3,
                'power_level': 0.80,
                'adjusted_alpha': 0.003846,
                'n_subjects': 50
            }
            power_path = tmpdir / 'power_analysis.json'
            with open(power_path, 'w') as f:
                json.dump(power_results, f)
            
            # Create layout template
            layout = {
                'pages': [
                    {
                        'type': 'title',
                        'elements': [{'type': 'text', 'source_field': 'title'}]
                    },
                    {
                        'type': 'correlation',
                        'elements': [
                            {'type': 'plot', 'source_field': 'motif_M1'},
                            {'type': 'text', 'source_field': 'motif_M1'}
                        ]
                    }
                ]
            }
            layout_path = tmpdir / 'report_layout_template.json'
            with open(layout_path, 'w') as f:
                json.dump(layout, f)
            
            # Generate PDF
            pdf_path = tmpdir / 'results.pdf'
            generate_pdf(
                corr_path,
                perm_path,
                power_path,
                layout_path,
                str(pdf_path)
            )
            
            # Verify file exists and has content
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0

    def test_file_size_constraint(self):
        """Verify PDF file size is within limits (<=5MB)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create minimal input files
            corr_path = tmpdir / 'correlation_results.json'
            with open(corr_path, 'w') as f:
                json.dump({'motif_M1': {'pearson_r': 0.5, 'pearson_p': 0.01, 'bonferroni_p': 0.13, 'significant': False}}, f)
            
            perm_path = tmpdir / 'permutation_results.json'
            with open(perm_path, 'w') as f:
                json.dump([], f)
            
            power_path = tmpdir / 'power_analysis.json'
            with open(power_path, 'w') as f:
                json.dump({'min_detectable_r': 0.3, 'power_level': 0.80, 'adjusted_alpha': 0.003846, 'n_subjects': 50}, f)
            
            layout_path = tmpdir / 'report_layout_template.json'
            with open(layout_path, 'w') as f:
                json.dump({'pages': []}, f)
            
            pdf_path = tmpdir / 'results.pdf'
            generate_pdf(corr_path, perm_path, power_path, layout_path, str(pdf_path))
            
            # Check file size (should be <= 5MB = 5 * 1024 * 1024 bytes)
            file_size = pdf_path.stat().st_size
            assert file_size <= 5 * 1024 * 1024

    def test_mandatory_disclaimer(self):
        """Verify the PDF contains the mandatory disclaimer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create input files
            corr_path = tmpdir / 'correlation_results.json'
            with open(corr_path, 'w') as f:
                json.dump({'motif_M1': {'pearson_r': 0.5, 'pearson_p': 0.01, 'bonferroni_p': 0.13, 'significant': False}}, f)
            
            perm_path = tmpdir / 'permutation_results.json'
            with open(perm_path, 'w') as f:
                json.dump([], f)
            
            power_path = tmpdir / 'power_analysis.json'
            with open(power_path, 'w') as f:
                json.dump({'min_detectable_r': 0.3, 'power_level': 0.80, 'adjusted_alpha': 0.003846, 'n_subjects': 50}, f)
            
            layout_path = tmpdir / 'report_layout_template.json'
            with open(layout_path, 'w') as f:
                json.dump({'pages': []}, f)
            
            pdf_path = tmpdir / 'results.pdf'
            generate_pdf(corr_path, perm_path, power_path, layout_path, str(pdf_path))
            
            # Read PDF content (simple text extraction)
            # Note: This is a basic check; a full PDF parser would be more robust
            with open(pdf_path, 'rb') as f:
                content = f.read().decode('latin-1', errors='ignore')
            
            assert "associational only" in content.lower()
            assert "do not imply causation" in content.lower()

    def test_handles_missing_template(self):
        """Verify the function raises an error for missing template."""
        with pytest.raises(FileNotFoundError):
            generate_pdf(
                "nonexistent_corr.json",
                "nonexistent_perm.json",
                "nonexistent_power.json",
                "nonexistent_template.json",
                "output.pdf"
            )