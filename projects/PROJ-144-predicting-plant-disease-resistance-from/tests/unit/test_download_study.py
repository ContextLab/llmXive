import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import io
import zipfile

from data.download_study import (
    get_study_download_url,
    download_study_data,
    load_phenotype_metadata,
    verify_temporal_separation,
    compute_checksums,
    download_study,
    main
)
from utils.exceptions import TemporalVerificationError, DataUnavailableError

# Mock data helpers
def create_mock_zip(temp_dir, intensity_name, phenotype_name):
    zip_path = os.path.join(temp_dir, "mock_study.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Create dummy intensity content
        intensity_content = "sample_id,metabolite_1,metabolite_2\nS1,10.5,20.3\nS2,11.2,21.0\n"
        zf.writestr(intensity_name, intensity_content)
        
        # Create dummy phenotype content with temporal data
        phenotype_content = "sample_id,germplasm_id,condition,time_point\nS1,G1,control,baseline\nS2,G1,pathogen,pre_inoculation\n"
        zf.writestr(phenotype_name, phenotype_content)
    return zip_path

def create_mock_zip_no_temporal(temp_dir, intensity_name, phenotype_name):
    zip_path = os.path.join(temp_dir, "mock_study_no_temporal.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        intensity_content = "sample_id,metabolite_1\nS1,10.5\n"
        zf.writestr(intensity_name, intensity_content)
        
        # Phenotype without temporal keywords
        phenotype_content = "sample_id,germplasm_id,assay_score\nS1,G1,0.8\n"
        zf.writestr(phenotype_name, phenotype_content)
    return zip_path

class TestDownloadStudy:
    
    def test_get_study_download_url(self):
        url = get_study_download_url("ST123456")
        assert "ST123456" in url
        assert "metabolomicsworkbench.org" in url

    @patch('data.download_study.requests.Session')
    def test_download_study_data_valid_zip(self, mock_session, tmp_path):
        mock_response = MagicMock()
        mock_response.headers = {'Content-Type': 'application/zip'}
        
        # Create a real zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("ST123_intensity.csv", "s,m1\n1,10\n")
            zf.writestr("ST123_phenotype.csv", "s,c,t\n1,baseline,pre\n")
        mock_response.content = zip_buffer.getvalue()
        mock_response.raise_for_status = MagicMock()
        
        mock_session.return_value.get.return_value = mock_response
        
        intensity_path, phenotype_path = download_study_data("http://fake/url", tmp_path)
        
        assert os.path.exists(intensity_path)
        assert os.path.exists(phenotype_path)
        assert "ST123_intensity.csv" in intensity_path
        assert "ST123_phenotype.csv" in phenotype_path

    def test_load_phenotype_metadata(self, tmp_path):
        csv_path = tmp_path / "test_phenotype.csv"
        csv_path.write_text("sample_id,condition\nS1,pre-challenge\n")
        
        df = load_phenotype_metadata(str(csv_path))
        assert len(df) == 1
        assert "condition" in df.columns

    def test_verify_temporal_separation_success(self):
        df = pd.DataFrame({
            "sample_id": ["S1", "S2"],
            "time_point": ["baseline", "pre_inoculation"]
        })
        assert verify_temporal_separation(df, "ST001") is True

    def test_verify_temporal_separation_fail(self):
        df = pd.DataFrame({
            "sample_id": ["S1", "S2"],
            "assay_score": [0.5, 0.8]
        })
        with pytest.raises(TemporalVerificationError):
            verify_temporal_separation(df, "ST001")

    def test_compute_checksums(self, tmp_path):
        file1 = tmp_path / "file1.csv"
        file1.write_text("data")
        file2 = tmp_path / "file2.csv"
        file2.write_text("data2")
        
        checksums = compute_checksums([str(file1), str(file2)])
        assert len(checksums) == 2
        assert "file1.csv" in checksums
        assert "file2.csv" in checksums

    @patch('data.download_study.download_study_data')
    @patch('data.download_study.load_phenotype_metadata')
    @patch('data.download_study.verify_temporal_separation')
    @patch('data.download_study.compute_checksums')
    def test_download_study_success(self, mock_checksums, mock_verify, mock_load, mock_download, tmp_path):
        mock_download.return_value = ("intensity.csv", "phenotype.csv")
        mock_load.return_value = pd.DataFrame({"time": ["baseline"]})
        mock_verify.return_value = True
        mock_checksums.return_value = {"intensity.csv": "abc123"}
        
        intensity, phenotype, checksums = download_study("ST001", "http://url")
        
        assert intensity is not None
        assert phenotype is not None
        assert checksums is not None
        mock_verify.assert_called_once()

    @patch('data.download_study.download_study_data')
    @patch('data.download_study.load_phenotype_metadata')
    def test_download_study_temporal_fail(self, mock_load, mock_download, tmp_path):
        mock_download.return_value = ("intensity.csv", "phenotype.csv")
        mock_load.return_value = pd.DataFrame({"score": [1.0]}) # No temporal data
        
        with pytest.raises(TemporalVerificationError):
            download_study("ST001", "http://url")

    @patch('builtins.open', new_callable=MagicMock)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('json.load', return_value=[{"study_id": "ST001", "download_url": "http://test"}])
    @patch('data.download_study.download_study')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_download, mock_load, mock_exists, mock_open):
        mock_download.return_value = ("intensity.csv", "phenotype.csv", {"hash": "123"})
        # Mock os.replace to do nothing
        with patch('os.replace'):
            main()
        
        # Verify print was called with success
        assert any("Successfully processed" in str(call) for call in mock_print.call_args_list)
        
    @patch('builtins.open', new_callable=MagicMock)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('json.load', return_value=[{"study_id": "ST001", "download_url": "http://test"}])
    @patch('data.download_study.download_study')
    @patch('builtins.print')
    def test_main_temporal_fail(self, mock_print, mock_download, mock_load, mock_exists, mock_open):
        mock_download.side_effect = TemporalVerificationError("Temporal check failed")
        
        with pytest.raises(TemporalVerificationError):
            with patch('os.replace'):
                main()
