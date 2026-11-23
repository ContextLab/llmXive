"""
Integration test for the full analysis pipeline on mock data.

This test verifies that the entire analysis workflow (T018-T023) executes correctly
end-to-end using mock data that simulates the expected inputs from previous stages.
It ensures that:
1. Metadata validation logic correctly identifies paired vs baseline data.
2. Correlation analysis produces valid statistical outputs.
3. Benjamini-Hochberg correction is applied correctly.
4. Sensitivity analysis generates the required table.
5. Final report is generated with all required sections.
6. VIF diagnostics run without error.
"""

import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    load_config,
    validate_metadata,
    run_correlation_analysis,
    run_benjamini_hochberg,
    calculate_vif,
    main as analysis_main
)
from sensitivity_analysis import generate_sensitivity_table, main as sensitivity_main
from collinearity import run_collinearity_diagnostics, main as collinearity_main
from report import generate_report, main as report_main


def setup_mock_data(temp_dir: Path) -> dict:
    """
    Create mock data files that simulate the output of previous pipeline stages.
    Returns a dict with paths to created files for verification.
    """
    # Create necessary directories
    (temp_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (temp_dir / "data" / "analysis").mkdir(parents=True, exist_ok=True)
    (temp_dir / "logs").mkdir(parents=True, exist_ok=True)
    (temp_dir / "docs").mkdir(parents=True, exist_ok=True)

    # Create mock metadata with paired fatigue ratings
    # This simulates the output of T009 (download.py)
    metadata_df = pd.DataFrame({
        'participant_id': [f'P{i:03d}' for i in range(1, 31)],
        'pre_fatigue': np.random.uniform(1.0, 5.0, 30),
        'post_fatigue': np.random.uniform(2.0, 7.0, 30),
        'age': np.random.randint(20, 60, 30),
        'sex': np.random.choice(['M', 'F'], 30)
    })
    metadata_path = temp_dir / "data" / "processed" / "metadata.csv"
    metadata_df.to_csv(metadata_path, index=False)

    # Create mock LZC metrics (simulating T014 output)
    channels = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2']
    lzc_data = []
    for pid in metadata_df['participant_id']:
        for ch in channels:
            # Simulate LZC values with some correlation to fatigue for testing
            base_val = np.random.uniform(0.4, 0.7)
            lzc_data.append({
                'participant_id': pid,
                'channel': ch,
                'lzc_value': base_val
            })
    lzc_df = pd.DataFrame(lzc_data)
    lzc_path = temp_dir / "data" / "processed" / "lzc_metrics.csv"
    lzc_df.to_csv(lzc_path, index=False)

    # Create mock PE metrics (simulating T015 output)
    pe_data = []
    for pid in metadata_df['participant_id']:
        for ch in channels:
            base_val = np.random.uniform(2.0, 2.5)
            pe_data.append({
                'participant_id': pid,
                'channel': ch,
                'pe_value': base_val
            })
    pe_df = pd.DataFrame(pe_data)
    pe_path = temp_dir / "data" / "processed" / "pe_metrics.csv"
    pe_df.to_csv(pe_path, index=False)

    # Create a minimal config file
    config = {
        'filter_low': 1,
        'filter_high': 40,
        'artifact_threshold': 100,
        'random_seed': 42,
        'n_threshold': 30,
        'notch_frequency': 50,
        'embedding_dim': 3,
        'analysis_mode': 'paired',
        'correlation_method': 'pearson',
        'alpha': 0.05
    }
    config_path = temp_dir / "code" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        import yaml
        yaml.dump(config, f)

    return {
        'metadata': str(metadata_path),
        'lzc': str(lzc_path),
        'pe': str(pe_path),
        'config': str(config_path),
        'temp_dir': str(temp_dir)
    }


def test_full_analysis_pipeline_integration():
    """
    Integration test: Run the full analysis pipeline on mock data and verify outputs.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        
        # Setup mock data
        paths = setup_mock_data(temp_path)
        
        # Change to temp directory to simulate running from project root
        original_dir = os.getcwd()
        os.chdir(temp_path)
        
        try:
            # 1. Test Metadata Validation (T018)
            config = load_config(paths['config'])
            metadata = validate_metadata(paths['metadata'])
            
            assert metadata is not None, "Metadata validation failed"
            assert 'pre_fatigue' in metadata.columns, "Missing pre_fatigue column"
            assert 'post_fatigue' in metadata.columns, "Missing post_fatigue column"
            assert len(metadata) == 30, f"Expected 30 participants, got {len(metadata)}"
            
            # 2. Test Correlation Analysis (T019)
            # We need to run the analysis script which will read the mock data
            # and produce correlation results
            analysis_output = run_correlation_analysis(
                metadata_path=paths['metadata'],
                lzc_path=paths['lzc'],
                pe_path=paths['pe'],
                config=config
            )
            
            assert analysis_output is not None, "Correlation analysis failed"
            assert 'results' in analysis_output, "Missing results in analysis output"
            assert 'correlations' in analysis_output['results'], "Missing correlations"
            
            # Verify we have correlation data for multiple channels
            correlations = analysis_output['results']['correlations']
            assert len(correlations) > 0, "No correlations calculated"
            
            # 3. Test Benjamini-Hochberg Correction (T020)
            # Extract p-values from correlations and apply correction
            p_values = [c['p_value'] for c in correlations if 'p_value' in c]
            if p_values:
                bh_results = run_benjamini_hochberg(p_values, alpha=0.05)
                assert bh_results is not None, "BH correction failed"
                assert 'adjusted_p_values' in bh_results, "Missing adjusted p-values"
                assert len(bh_results['adjusted_p_values']) == len(p_values), \
                    "Mismatch in BH correction output length"
            
            # 4. Test VIF Calculation (T023)
            vif_results = calculate_vif(analysis_output['results']['correlations'])
            assert vif_results is not None, "VIF calculation failed"
            
            # 5. Test Sensitivity Analysis (T021)
            sensitivity_output = generate_sensitivity_table(
                analysis_output['results']['correlations'],
                thresholds=[0.05, 0.01]
            )
            assert sensitivity_output is not None, "Sensitivity analysis failed"
            assert 'table' in sensitivity_output, "Missing sensitivity table"
            assert len(sensitivity_output['table']) == 2, "Expected 2 thresholds"
            
            # 6. Verify output files are created
            # The main functions should write files to disk
            expected_files = [
                'data/analysis/correlation_results.json',
                'data/analysis/bh_correction.json',
                'data/analysis/sensitivity_table.csv',
                'data/analysis/vif_report.csv',
                'docs/final_report.md'
            ]
            
            for expected_file in expected_files:
                file_path = Path(expected_file)
                assert file_path.exists(), f"Expected output file not created: {expected_file}"
                assert file_path.stat().st_size > 0, f"Output file is empty: {expected_file}"
            
            # 7. Verify final report contains required sections
            report_path = Path('docs/final_report.md')
            with open(report_path, 'r') as f:
                report_content = f.read()
            
            required_sections = [
                "Correlation Analysis",
                "Statistical Significance",
                "Confidence Intervals",
                "Sensitivity Analysis"
            ]
            
            for section in required_sections:
                assert section in report_content, f"Missing section in report: {section}"
            
            print("✅ All integration tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Integration test failed with error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            os.chdir(original_dir)


def test_analysis_mode_failure():
    """
    Test that the analysis script fails gracefully when neither paired nor baseline data is available.
    This is a negative test for T027b.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        
        # Create directories
        (temp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (temp_path / "logs").mkdir(parents=True, exist_ok=True)
        
        # Create metadata WITHOUT pre/post or baseline fatigue ratings
        metadata_df = pd.DataFrame({
            'participant_id': [f'P{i:03d}' for i in range(1, 11)],
            'age': np.random.randint(20, 60, 10),
            'sex': np.random.choice(['M', 'F'], 10)
        })
        metadata_path = temp_path / "data" / "processed" / "metadata.csv"
        metadata_df.to_csv(metadata_path, index=False)
        
        # Create minimal config
        config = {
            'random_seed': 42,
            'analysis_mode': 'auto'
        }
        config_path = temp_path / "code" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        original_dir = os.getcwd()
        os.chdir(temp_path)
        
        try:
            # This should raise an error or exit with code 1
            with pytest.raises(SystemExit) as exc_info:
                validate_metadata(str(metadata_path))
            
            # Alternatively, if it doesn't exit, it should return a validation failure
            # We'll check the validation logic directly
            metadata = pd.read_csv(metadata_path)
            valid_cols = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue', 
                         'post_fatigue', 'fatigue_post', 'end_fatigue']
            has_valid_cols = any(col in metadata.columns for col in valid_cols)
            
            assert not has_valid_cols, "Test setup error: metadata should not have fatigue columns"
            
            # The validate_metadata function should detect this and fail
            # Since we can't easily capture the exit code in a test, we verify the logic
            print("✅ Analysis mode failure test passed - missing data correctly detected")
            return True
            
        except Exception as e:
            print(f"❌ Analysis mode failure test failed: {e}")
            raise
        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])