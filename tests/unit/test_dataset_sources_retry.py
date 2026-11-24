"""The dataset-source fetch retries a flaky source within a bound and never invents data.

Real HTTP against a local server (tests/helpers/replay_server.py); no client mocks."""

from __future__ import annotations

import logging

import pytest

from llmxive.librarian import dataset_sources as ds
from tests.helpers.replay_server import DROP, ReplayServer

OK = {"data": {"dataset": [{"file_id": 61, "name": "iris"}]}}
ROUTE = ("GET", "/list")


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch):
    monkeypatch.setattr(ds, "_RETRY_BACKOFF_SECONDS", 0.0)


@pytest.mark.parametrize("first", [(503, {}), (429, {}), DROP], ids=["503", "429", "dropped-connection"])
def test_one_transient_failure_is_retried_and_the_result_returned(first):
    with ReplayServer({ROUTE: [first, (200, OK)]}) as srv:
        assert ds._get_json(srv.base_url + "/list") == OK
        assert len(srv.requests) == 2


def test_a_source_that_stays_down_is_tried_a_bounded_number_of_times_then_none(caplog):
    with ReplayServer({ROUTE: [(503, {})]}) as srv, caplog.at_level(logging.WARNING, logger=ds.__name__):
        assert ds._get_json(srv.base_url + "/list") is None
        assert len(srv.requests) == ds._MAX_ATTEMPTS == 3
    assert "gave no result: HTTP 503" in caplog.text and "127.0.0.1" in caplog.text


def test_a_client_error_is_not_retried(caplog):
    with ReplayServer({ROUTE: [(404, {})]}) as srv, caplog.at_level(logging.WARNING, logger=ds.__name__):
        assert ds._get_json(srv.base_url + "/list") is None
        assert len(srv.requests) == 1
    assert "HTTP 404" in caplog.text


def test_a_non_json_200_is_not_retried_and_yields_nothing():
    with ReplayServer({ROUTE: [(200, b"<html>busy</html>")]}) as srv:
        assert ds._get_json(srv.base_url + "/list") is None
        assert len(srv.requests) == 1

