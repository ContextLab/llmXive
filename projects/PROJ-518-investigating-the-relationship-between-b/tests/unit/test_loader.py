import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from data.loader import fetch_hcp_data, validate_caq_availability, DataMissingCreativityError

class TestFetchHcpData:
    def test_fetch_hcp_data_verifies_ca_q(self):
        """Test that fetch_hcp_data checks for CAQ before downloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup manifest
            manifest = {
                "subjects": {
                    "100307": {
                        "behavioral": {
                            "CAQ": 50.0
                        }
                    }
                }
            }
            manifest_path = Path(tmpdir) / "raw" / "manifest.json"
            manifest_path.parent.mkdir(parents=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Mock the download function to avoid actual network calls
            with patch('data.loader.urllib.request.urlretrieve') as mock_download:
                with patch('data.loader.Path.mkdir'):
                    with patch('data.loader.os.path.exists', return_value=True):
                        with patch('data.loader.os.path.getsize', return_value=100):
                            # We need to mock the config to point to our temp dir
                            with patch('data.loader.get_config') as mock_config:
                                mock_config.return_value.DATA_PATH = Path(tmpdir)
                                
                                # This should not raise an error because CAQ is present
                                # It will try to download, which is mocked
                                result = fetch_hcp_data("100307")
                                
                                assert result is not None
                                mock_download.assert_called() # Verify download logic was triggered

    def test_fetch_hcp_data_raises_on_missing_ca_q(self):
        """Test that fetch_hcp_data raises DataMissingCreativityError if CAQ is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup manifest without CAQ
            manifest = {
                "subjects": {
                    "100307": {
                        "behavioral": {
                            "IQ": 100
                        }
                    }
                }
            }
            manifest_path = Path(tmpdir) / "raw" / "manifest.json"
            manifest_path.parent.mkdir(parents=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            with patch('data.loader.get_config') as mock_config:
                mock_config.return_value.DATA_PATH = Path(tmpdir)
                
                with pytest.raises(DataMissingCreativityError):
                    fetch_hcp_data("100307")

    def test_fetch_hcp_data_raises_on_missing_subject(self):
        """Test that fetch_hcp_data raises FileNotFoundError if subject not in manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "subjects": {
                    "100307": {
                        "behavioral": {
                            "CAQ": 50.0
                        }
                    }
                }
            }
            manifest_path = Path(tmpdir) / "raw" / "manifest.json"
            manifest_path.parent.mkdir(parents=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            with patch('data.loader.get_config') as mock_config:
                mock_config.return_value.DATA_PATH = Path(tmpdir)
                
                with pytest.raises(FileNotFoundError):
                    fetch_hcp_data("999999")

    def test_fetch_hcp_data_uploads_files(self):
        """Test that files are saved to the correct directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "subjects": {
                    "100307": {
                        "behavioral": {
                            "CAQ": 50.0
                        }
                    }
                }
            }
            manifest_path = Path(tmpdir) / "raw" / "manifest.json"
            manifest_path.parent.mkdir(parents=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Create a fake downloaded file to simulate success
            subject_dir = Path(tmpdir) / "raw" / "hcp_100307"
            subject_dir.mkdir(parents=True)
            fmri_file = subject_dir / "100307_task-rest_bold.nii.gz"
            fmri_file.write_text("fake nifti")
            
            with patch('data.loader.urllib.request.urlretrieve') as mock_download:
                with patch('data.loader.Path.mkdir'):
                    with patch('data.loader.os.path.exists', return_value=True):
                        with patch('data.loader.os.path.getsize', return_value=100):
                            with patch('data.loader.get_config') as mock_config:
                                mock_config.return_value.DATA_PATH = Path(tmpdir)
                                
                                result = fetch_hcp_data("100307")
                                
                                assert "fmri" in result
                                assert "behavioral" in result
                                # Verify the path contains the subject directory
                                assert "hcp_100307" in result["fmri"]