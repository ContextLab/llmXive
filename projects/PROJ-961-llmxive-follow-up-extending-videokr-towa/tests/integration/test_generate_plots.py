import json
import os
import csv
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.generate_plots import plot_binned_accuracy, plot_continuous_accuracy, load_binned_accuracy_data, load_raw_annotated_data
from utils.config import get_project_root, ensure_dir

def test_plot_generation_integration():
    """
    Integration test: Ensure plot generation scripts run without error
    given valid input data files.
    """
    # Setup temporary directories for this test
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir) / 'data' / 'processed'
        figures_dir = Path(tmp_dir) / 'figures'
        ensure_dir(data_dir)
        ensure_dir(figures_dir)

        # 1. Create mock binned_accuracy.json (T019 output)
        binned_data = {
            "1": {"accuracy": 0.85, "count": 100},
            "2": {"accuracy": 0.60, "count": 80},
            "3+": {"accuracy": 0.25, "count": 40}
        }
        binned_file = data_dir / 'binned_accuracy.json'
        with open(binned_file, 'w') as f:
            json.dump(binned_data, f)

        # 2. Create mock annotated_videokr.csv (T013/T015 output)
        csv_file = data_dir / 'annotated_videokr.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'question', 'answer', 'correctness', 'chain_length'])
            # Add some data points
            for i in range(50):
                writer.writerow([f'id_{i}', 'q', 'a', 'true', 1])
            for i in range(50, 130):
                writer.writerow([f'id_{i}', 'q', 'a', 'true', 2])
            for i in range(130, 150):
                writer.writerow([f'id_{i}', 'q', 'a', 'false', 3]) # Low accuracy for 3
            for i in range(150, 160):
                writer.writerow([f'id_{i}', 'q', 'a', 'true', 3])
            for i in range(160, 170):
                writer.writerow([f'id_{i}', 'q', 'a', 'false', 4]) # 4 hops

        # 3. Run plot generation
        binned_plot_out = figures_dir / 'binned_accuracy.png'
        continuous_plot_out = figures_dir / 'continuous_accuracy.png'

        # Test Binned Plot
        plot_binned_accuracy(binned_data, str(binned_plot_out))
        assert binned_plot_out.exists(), "Binned plot file not created"
        assert binned_plot_out.stat().st_size > 0, "Binned plot file is empty"

        # Test Continuous Plot
        plot_continuous_accuracy(load_raw_annotated_data(str(csv_file)), str(continuous_plot_out))
        assert continuous_plot_out.exists(), "Continuous plot file not created"
        assert continuous_plot_out.stat().st_size > 0, "Continuous plot file is empty"

    print("Integration test passed: Plot generation works with valid inputs.")

if __name__ == '__main__':
    test_plot_generation_integration()
