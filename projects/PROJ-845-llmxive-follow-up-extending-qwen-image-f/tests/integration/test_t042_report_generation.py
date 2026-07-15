"""
Integration test for T042: Trace Consistency Report Generation.

This test verifies that the report generation script correctly processes
mock DistillationRun files and produces a valid JSON report.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def test_report_generation_with_mock_data():
    """
    Test that the report generator creates a valid report from mock run data.
    """
    # Create a temporary directory for mock data
    temp_dir = tempfile.mkdtemp()
    data_processed_dir = Path(temp_dir)
    
    try:
        # Create mock DistillationRun JSON files
        mock_runs = [
            {
                "run_id": "run_high_001",
                "entropy_subset": "high",
                "status": "converged",
                "samples_processed": 100,
                "samples_kept": 95,
                "filtering_stats": {"discarded": 5, "reason": "entropy_mismatch"}
            },
            {
                "run_id": "run_low_001",
                "entropy_subset": "low",
                "status": "converged",
                "samples_processed": 100,
                "samples_kept": 90,
                "filtering_stats": {"discarded": 10, "reason": "entropy_mismatch"}
            },
            {
                "run_id": "run_target_001",
                "entropy_subset": "target",
                "status": "failed_non_converge",
                "samples_processed": 100,
                "samples_kept": 98,
                "filtering_stats": {"discarded": 2, "reason": "entropy_mismatch"}
            }
        ]
        
        for i, run in enumerate(mock_runs):
            file_path = data_processed_dir / f"distillation_run_{i}.json"
            with open(file_path, 'w') as f:
                json.dump(run, f)
        
        # Import the main function from the script
        # We need to patch the project root path inside the script logic if necessary,
        # but since we added it to sys.path, the import should work.
        # However, the script uses `project_root = Path(__file__).resolve().parent.parent`
        # which might be relative to the script's location, not the temp dir.
        # To test this properly, we will execute the logic directly.
        
        # Simulate the logic of the script
        from training.trace_consistency_report import load_distillation_runs, aggregate_statistics, generate_report
        
        runs = load_distillation_runs(data_processed_dir)
        assert len(runs) == 3, f"Expected 3 runs, got {len(runs)}"
        
        stats = aggregate_statistics(runs)
        
        assert stats['total_samples_processed'] == 300, f"Expected 300 total samples, got {stats['total_samples_processed']}"
        assert stats['total_samples_filtered'] == 17, f"Expected 17 filtered, got {stats['total_samples_filtered']}"
        assert stats['filtered_per_subset']['high_entropy'] == 5
        assert stats['filtered_per_subset']['low_entropy'] == 10
        assert stats['filtered_per_subset']['target_specific'] == 2
        assert stats['overall_status'] == "pass"
        assert "run_target_001" in stats['failed_run_ids']
        
        # Generate report to a temp file
        output_file = data_processed_dir / "trace_consistency_report.json"
        generate_report(stats, output_file)
        
        assert output_file.exists(), "Report file was not created"
        
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        assert report['report_type'] == "trace_consistency_validation"
        assert report['fr_reference'] == "FR-009"
        assert report['statistics']['total_samples_processed'] == 300
        
        print("Test passed: Report generation works correctly with mock data.")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_report_generation_with_mock_data()
    print("All tests passed.")