"""
Integration test for full download-and-align flow.
Tests the ingestion and alignment pipeline using mocked FTP responses.
"""
import os
import csv
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

# Import the real implementation functions from the code module
# Note: ingest.py and align.py are not yet implemented, so we mock the behavior
# to simulate what they would do with real data.
from code.ingest import download_goes_data, download_dst_indices, download_kp_indices
from code.align import align_events


def create_mock_goes_response():
    """Generate synthetic but schema-valid GOES flare data."""
    data = []
    base_date = datetime(2010, 1, 1)
    for i in range(100):
        event_time = base_date + timedelta(days=i*3, hours=i%24)
        flux = 1e-6 * (10 ** (i % 5))  # Varying flux levels
        data.append({
            'event_time': event_time.isoformat(),
            'peak_flux': flux,
            'peak_flux_unit': 'W/m^2',
            'class': f'X{i%10}.{i%10}'
        })
    return data


def create_mock_cme_response():
    """Generate synthetic but schema-valid CME data."""
    data = []
    base_date = datetime(2010, 1, 1)
    for i in range(100):
        event_time = base_date + timedelta(days=i*3, hours=i%24)
        data.append({
            'event_time': event_time.isoformat(),
            'speed': 500 + (i % 1000),
            'width': 120 + (i % 240),
            'direction': 'W' if i % 2 == 0 else 'E'
        })
    return data


def create_mock_dst_response():
    """Generate synthetic but schema-valid Dst index data."""
    data = []
    base_date = datetime(2010, 1, 1)
    for i in range(365*10):  # 10 years of hourly data
        event_time = base_date + timedelta(hours=i)
        dst_value = -50 - (50 * ((i % 365) / 365))  # Seasonal variation
        data.append({
            'event_time': event_time.isoformat(),
            'dst_value': dst_value
        })
    return data


def create_mock_kp_response():
    """Generate synthetic but schema-valid Kp index data."""
    data = []
    base_date = datetime(2010, 1, 1)
    for i in range(365*10):  # 10 years of 3-hourly data
        event_time = base_date + timedelta(hours=i*3)
        kp_value = (i % 9) / 3.0  # Values 0.0 to 3.0
        data.append({
            'event_time': event_time.isoformat(),
            'kp_value': kp_value
        })
    return data


def test_full_ingest_align_flow():
    """
    Test the full download-and-align flow using mocked FTP responses.
    Asserts that the aligned CSV is created and contains data.
    """
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define output paths
        goes_csv_path = os.path.join(temp_dir, 'goes_flares.csv')
        cme_csv_path = os.path.join(temp_dir, 'cme_catalog.csv')
        dst_csv_path = os.path.join(temp_dir, 'dst_indices.csv')
        kp_csv_path = os.path.join(temp_dir, 'kp_indices.csv')
        aligned_csv_path = os.path.join(temp_dir, 'aligned_events.csv')

        # Mock the FTP downloads
        with patch('code.ingest.fetch_ftp_data') as mock_fetch:
            # Configure the mock to return our synthetic data
            mock_fetch.side_effect = [
                create_mock_goes_response(),  # GOES data
                create_mock_cme_response(),   # CME data
                create_mock_dst_response(),   # Dst data
                create_mock_kp_response()     # Kp data
            ]

            # Mock the CSV writing to our temp directory
            with patch('code.ingest.write_csv_data') as mock_write:
                # Configure mock_write to actually write to our temp directory
                def write_to_temp(data, path, **kwargs):
                    df = pd.DataFrame(data)
                    df.to_csv(path, index=False)
                    return True

                mock_write.side_effect = write_to_temp

                # Mock the alignment function to use our temp paths
                with patch('code.align.load_csv_data') as mock_load:
                    def load_from_temp(path, **kwargs):
                        return pd.read_csv(path)

                    mock_load.side_effect = load_from_temp

                    # Mock the write_aligned_events function
                    with patch('code.align.write_aligned_events') as mock_write_aligned:
                        def write_aligned_to_temp(data, path):
                            df = pd.DataFrame(data)
                            df.to_csv(path, index=False)
                            return True

                        mock_write_aligned.side_effect = write_aligned_to_temp

                        # Execute the full flow
                        # 1. Download GOES data
                        download_goes_data(goes_csv_path)

                        # 2. Download CME data
                        download_cme_data(cme_csv_path)

                        # 3. Download Dst indices
                        download_dst_indices(dst_csv_path)

                        # 4. Download Kp indices
                        download_kp_indices(kp_csv_path)

                        # 5. Align events
                        align_events(
                            goes_path=goes_csv_path,
                            cme_path=cme_csv_path,
                            dst_path=dst_csv_path,
                            kp_path=kp_csv_path,
                            output_path=aligned_csv_path
                        )

                        # Assertions
                        assert os.path.exists(aligned_csv_path), \
                            "Aligned events CSV was not created"

                        df = pd.read_csv(aligned_csv_path)
                        assert len(df) > 0, \
                            "Aligned events CSV is empty"

                        # Verify schema compliance (basic checks)
                        required_columns = [
                            'storm_time', 'dst_min', 'flare_time',
                            'flare_flux', 'cme_speed', 'is_recurrent'
                        ]
                        for col in required_columns:
                            assert col in df.columns, \
                                f"Required column '{col}' missing from aligned events"

                        print(f"Test passed: Aligned events CSV created with {len(df)} rows")


if __name__ == '__main__':
    test_full_ingest_align_flow()
    print("All integration tests passed!")
