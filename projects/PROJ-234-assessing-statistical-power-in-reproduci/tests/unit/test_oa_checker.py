import pytest
from unittest.mock import patch, MagicMock
from code.utils.oa_checker import is_open_access

def test_known_oa_domains():
    # Mock requests.head to return 200 and a valid PDF content type
    with patch('requests.head') as mock_head:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/pdf"}
        mock_head.return_value = mock_resp
        
        # Arxiv
        assert is_open_access("https://arxiv.org/pdf/1234.5678.pdf") is True
        # PubMed Central
        assert is_open_access("https://pubmedcentral.nih.gov/article/123/") is True
        # DOI (Must match doi.org/10. as per spec)
        assert is_open_access("https://doi.org/10.1000/xyz123") is True
        # Non-OA domain
        assert is_open_access("https://paywalled-journal.com/article/1") is False

def test_content_type_validation():
    with patch('requests.head') as mock_head:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Invalid content type (e.g. image)
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_head.return_value = mock_resp
        
        assert is_open_access("https://arxiv.org/pdf/1234.5678.pdf") is False

def test_request_failure():
    with patch('requests.head') as mock_head:
        mock_head.side_effect = Exception("Network error")
        assert is_open_access("https://arxiv.org/pdf/1234.5678.pdf") is False
