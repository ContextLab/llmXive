"""
Unit tests for the `paginate_api` helper.

The test constructs a mock ``fetch_page`` function that returns two pages
of data, each with a ``data`` list and a ``pagination`` dictionary
indicating whether a subsequent page exists.  The helper should combine
the ``data`` elements from both pages into a single flat list.
"""

import unittest
import logging
from scripts.utils.pagination import paginate_api

class TestPagination(unittest.TestCase):
    def setUp(self):
        # Simple logger that discards output – we only need the interface.
        self.logger = logging.getLogger("test_pagination")
        self.logger.addHandler(logging.NullHandler())

    def mock_fetch_page(self, url, logger):
        """
        Mock ``fetch_page`` that returns predictable payloads.
        The URL is expected to contain the page number as the last
        character (e.g., ``...page=1``).  For page 1 we return two items
        and indicate ``has_next=True``.  For page 2 we return one item
        and ``has_next=False``.
        """
        if "page=1" in url:
            return {
                "data": [{"id": "run1"}, {"id": "run2"}],
                "pagination": {"has_next": True}
            }
        elif "page=2" in url:
            return {
                "data": [{"id": "run3"}],
                "pagination": {"has_next": False}
            }
        else:
            # No data for any other page – signals termination.
            return {"data": [], "pagination": {"has_next": False}}

    def test_paginate_collects_all_items(self):
        """
        Verify that ``paginate_api`` returns a flat list containing
        all items from the mocked pages.
        """
        # URL builder that simply encodes the page number.
        url_builder = lambda page: f"https://example.com/api?page={page}"
        result = paginate_api(self.mock_fetch_page, url_builder, self.logger, max_pages=10, sleep_seconds=0)

        expected = [
            {"id": "run1"},
            {"id": "run2"},
            {"id": "run3"}
        ]
        self.assertEqual(result, expected)

    def test_early_termination_on_empty_page(self):
        """
        If the first page returns no items, pagination should stop
        immediately and return an empty list.
        """
        def empty_fetch(url, logger):
            return {"data": [], "pagination": {"has_next": False}}

        url_builder = lambda page: f"https://example.com/api?page={page}"
        result = paginate_api(empty_fetch, url_builder, self.logger, max_pages=5, sleep_seconds=0)
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
