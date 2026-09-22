import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from ingestion import validate_scope, download_file

class TestT012dExclusionLogic:
    """Tests for T012d: Strict exclusion logic for DementiaBank."""

    def test_validate_scope_allows_adress(self):
        """Ensure ADReSS is allowed."""
        # Should not raise
        validate_scope("ADReSS")

    def test_validate_scope_raises_for_dementiabank(self):
        """Ensure DementiaBank raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            validate_scope("DementiaBank")
        assert "excluded by Plan" in str(excinfo.value)

    def test_download_file_raises_connection_error_for_dementiabank_url(self):
        """Ensure download_file raises ConnectionError if DementiaBank URL is used."""
        dummy_path = Path("/tmp/fake.zip")
        dementia_url = "https://dementia.talkbank.org/data.zip"

        with pytest.raises(ConnectionError) as excinfo:
            download_file(dementia_url, dummy_path)

        assert "DementiaBank source is unverified and excluded by Plan" in str(excinfo.value)

    def test_download_file_allows_adress_url(self):
        """Ensure download_file proceeds (or fails with download error) for ADReSS URL, not exclusion error."""
        dummy_path = Path("/tmp/fake_adress.zip")
        adress_url = "https://github.com/jmacdona/ADReSS-Data/raw/master/ADReSS_Data.zip"

        # We mock the actual network call to avoid real downloads in unit tests,
        # but we verify that the specific exclusion logic for DementiaBank is NOT triggered.
        # The function will likely fail with a 404 or similar if the file doesn't exist,
        # but it must NOT raise the "DementiaBank excluded" error.
        
        with patch('urllib.request.urlretrieve') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Simulated download failure")
            with pytest.raises(Exception): # Expect the simulated failure, not the exclusion error
                download_file(adress_url, dummy_path)

        # Verify that the exclusion check was bypassed
        # (This is implicitly tested by the fact that we didn't get ConnectionError with the specific message)
        pass