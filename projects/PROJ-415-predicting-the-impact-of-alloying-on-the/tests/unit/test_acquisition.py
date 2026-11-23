import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError, Timeout

# Add project root to path if running standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.acquisition import acquire_and_save_diffusion_data, verify_url_reachability, fetch_real_diffusion_data_from_nist

class TestFailLoudBehavior:
    """Tests to verify that the acquisition module fails loudly on network errors."""

    @patch('code.data.acquisition.requests.head')
    def test_url_unreachable_raises_systemexit(self, mock_head):
        """Test that verify_url_reachability returns False when HEAD request fails."""
        mock_head.side_effect = ConnectionError("Network is unreachable")
        
        # verify_url_reachability should return False
        assert verify_url_reachability("http://fake-url.com") is False

    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_fetch_raises_systemexit_on_connection_error(self, mock_get, mock_head):
        """Test that fetch_real_diffusion_data_from_nist raises SystemExit on connection error."""
        mock_head.return_value.status_code = 200
        mock_get.side_effect = ConnectionError("Failed to connect")

        with pytest.raises(SystemExit) as exc_info:
            fetch_real_diffusion_data_from_nist("http://fake-url.com")
        
        assert "Data Fetch Failed" in str(exc_info.value)

    @patch('code.data.acquisition.VERIFIED_URLS', ['http://fake1.com', 'http://fake2.com'])
    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_acquire_fails_loudly_when_all_urls_fail(self, mock_get, mock_head, mock_urls):
        """Test that acquire_and_save_diffusion_data raises SystemExit after all URLs fail."""
        # Mock all URLs as unreachable
        mock_head.side_effect = [ConnectionError("Fail"), ConnectionError("Fail")]
        mock_get.side_effect = [ConnectionError("Fail"), ConnectionError("Fail")]

        with pytest.raises(SystemExit) as exc_info:
            acquire_and_save_diffusion_data("http://any.com")

        assert "Pipeline cannot proceed without verified real data" in str(exc_info.value)

    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_no_synthetic_fallback_on_network_error(self, mock_get, mock_head):
        """Test that no synthetic data is generated when network errors occur."""
        # Setup mocks to fail
        mock_head.return_value.status_code = 200
        mock_get.side_effect = Timeout("Request timed out")

        # Ensure no data files exist before
        test_file = "data/raw/test_no_synthetic.csv"
        if os.path.exists(test_file):
            os.remove(test_file)

        with pytest.raises(SystemExit):
            fetch_real_diffusion_data_from_nist("http://fake-url.com")

        # Verify no synthetic file was created
        assert not os.path.exists(test_file)

    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_no_mock_generator_called_on_error(self, mock_get, mock_head):
        """Test that mock_generator functions are not called on error."""
        mock_head.return_value.status_code = 200
        mock_get.side_effect = ConnectionError("Connection refused")

        # Patch any potential mock generator to ensure it's not called
        with patch('code.data.acquisition.generate_synthetic_data', side_effect=AssertionError("Mock generator should not be called")):
            with pytest.raises(SystemExit):
                fetch_real_diffusion_data_from_nist("http://fake-url.com")
    
    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_server_error_500_raises_systemexit(self, mock_get, mock_head):
        """Test that a 500 Internal Server Error raises SystemExit immediately."""
        mock_head.return_value.status_code = 200
        
        # Mock GET to return a 500 error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_get.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            fetch_real_diffusion_data_from_nist("http://fake-url.com")
        
        assert "Data Fetch Failed" in str(exc_info.value)

    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_timeout_raises_systemexit(self, mock_get, mock_head):
        """Test that a timeout raises SystemExit immediately."""
        mock_head.return_value.status_code = 200
        mock_get.side_effect = Timeout("Request timed out after 30s")

        with pytest.raises(SystemExit) as exc_info:
            fetch_real_diffusion_data_from_nist("http://fake-url.com")
        
        assert "Data Fetch Failed" in str(exc_info.value)

    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_404_fallback_to_secondary_url(self, mock_get, mock_head):
        """
        Test that the pipeline correctly handles a 404 error from the primary URL
        and successfully falls back to the secondary URL before raising SystemExit.
        This specifically addresses the scenario where the primary source is unavailable
        but a verified fallback exists and is reachable.
        """
        # Setup: Primary URL returns 404, Secondary URL succeeds
        mock_head.side_effect = [
            MagicMock(status_code=404), # Primary HEAD fails
            MagicMock(status_code=200)  # Secondary HEAD succeeds
        ]
        
        # Mock the GET request for the primary to raise 404
        mock_primary_response = MagicMock()
        mock_primary_response.status_code = 404
        mock_primary_response.raise_for_status.side_effect = Exception("404 Not Found")
        
        # Mock the GET request for the secondary to succeed with CSV content
        mock_secondary_response = MagicMock()
        mock_secondary_response.status_code = 200
        mock_secondary_response.text = "host_id,solute_id,concentration,activation_energy,crystal_structure,diffusion_mode\nCu,Ni,0.1,1.5,FCC,self"
        mock_secondary_response.iter_lines = lambda: [b"host_id,solute_id,concentration,activation_energy,crystal_structure,diffusion_mode", b"Cu,Ni,0.1,1.5,FCC,self"]
        
        # Sequence: Primary GET fails, Secondary GET succeeds
        mock_get.side_effect = [mock_primary_response, mock_secondary_response]

        # Mock the save functions to avoid disk I/O in test but verify they were called
        with patch('code.data.acquisition.save_source_metadata') as mock_save_meta, \
             patch('code.data.acquisition.save_fetched_data') as mock_save_data:
            
            # This should NOT raise SystemExit because a fallback succeeded
            try:
                result = fetch_real_diffusion_data_from_nist("http://primary-fake.com", fallback_urls=["http://secondary-fake.com"])
                
                # Verify the secondary URL was used
                assert mock_head.call_count == 2
                assert mock_get.call_count == 2
                
                # Verify save functions were called (indicating success)
                mock_save_meta.assert_called_once()
                mock_save_data.assert_called_once()
                
            except SystemExit:
                pytest.fail("fetch_real_diffusion_data_from_nist raised SystemExit even though a fallback URL succeeded")

    @patch('code.data.acquisition.requests.head')
    @patch('code.data.acquisition.requests.get')
    def test_404_all_fallbacks_fail_raises_systemexit(self, mock_get, mock_head):
        """
        Test that if the primary URL returns 404 AND all fallback URLs return 404,
        the pipeline raises SystemExit after exhausting all options.
        """
        # Setup: All URLs return 404
        mock_head.side_effect = [
            MagicMock(status_code=404), # Primary
            MagicMock(status_code=404), # Fallback 1
            MagicMock(status_code=404)  # Fallback 2
        ]
        
        # Mock GET to raise 404 for all attempts
        mock_404_response = MagicMock()
        mock_404_response.status_code = 404
        mock_404_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_404_response

        with pytest.raises(SystemExit) as exc_info:
            fetch_real_diffusion_data_from_nist("http://primary-fake.com", fallback_urls=["http://fallback1.com", "http://fallback2.com"])
        
        assert "Data Fetch Failed" in str(exc_info.value)
        assert "All verified URLs failed" in str(exc_info.value)