import unittest
import os
import json
from unittest.mock import patch
import requests
from code.data.acquisition import verify_url_reachability, fetch_real_diffusion_data_from_nist, save_source_metadata, save_fetched_data, acquire_and_save_diffusion_data

class TestAcquisition(unittest.TestCase):

    def test_verify_url_reachability(self):
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            self.assertTrue(verify_url_reachability("http://example.com"))

            mock_head.return_value.status_code = 404
            self.assertFalse(verify_url_reachability("http://example.com"))

        with patch('requests.head') as mock_head:
            mock_head.side_effect = requests.exceptions.RequestException
            self.assertFalse(verify_url_reachability("http://example.com"))

    def test_fetch_real_diffusion_data_from_nist(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.text = "test data"
            data = fetch_real_diffusion_data_from_nist("http://example.com/data.csv")
            self.assertEqual(data, "test data")

    def test_fetch_real_diffusion_data_from_nist_raises_error(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException
            with self.assertRaises(SystemExit):
                fetch_real_diffusion_data_from_nist("http://example.com/data.csv")

if __name__ == '__main__':
    unittest.main()