import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone
import json
import csv
import tempfile
from pathlib import Path

from src.cli.collect_data import (
    parse_args,
    fetch_top_packages,
    process_package,
    run_data_collection,
    export_to_csv,
    calculate_age_metrics,
    calculate_and_export_metrics,
    main
)
from src.models.data_models import Dependency, Package

def test_parse_args_default():
    args = parse_args([])
    assert args.top_packages == 100
    assert args.export is False
    assert args.metrics is False
    assert args.output_dir == "data/processed"
    assert args.log_level == "INFO"

def test_parse_args_custom():
    args = parse_args([
        "--top-packages", "50",
        "--export",
        "--metrics",
        "--output-dir", "custom/output",
        "--log-level", "DEBUG"
    ])
    assert args.top_packages == 50
    assert args.export is True
    assert args.metrics is True
    assert args.output_dir == "custom/output"
    assert args.log_level == "DEBUG"

@patch('src.cli.collect_data.NpmClient')
def test_fetch_top_packages(mock_client_cls):
    mock_client = MagicMock()
    mock_client.fetch_top_packages.return_value = [
        {"name": "pkg1"}, {"name": "pkg2"}
    ]
    mock_client_cls.return_value = mock_client
    
    from src.cli.collect_data import NpmClient
    client = NpmClient()
    result = fetch_top_packages(client, 10)
    
    assert len(result) == 2
    mock_client.fetch_top_packages.assert_called_once_with(10)

@patch('src.cli.collect_data.NpmClient')
@patch('src.cli.collect_data.GithubClient')
@patch('src.cli.collect_data.AuditClient')
@patch('src.cli.collect_data.DependencyResolver')
def test_process_package_handles_missing_dates(
    mock_resolver_cls, mock_audit_cls, mock_github_cls, mock_npm_cls
):
    # Setup mocks
    mock_npm = MagicMock()
    mock_npm.get_package_metadata.return_value = {"name": "test-pkg"}
    mock_npm_cls.return_value = mock_npm
    
    mock_github = MagicMock()
    mock_github.get_repository_info.return_value = None  # Simulate missing repo
    mock_github_cls.return_value = mock_github
    
    mock_audit = MagicMock()
    mock_audit.fetch_audit_data.return_value = {"vulnerabilities": {}}
    mock_audit_cls.return_value = mock_audit
    
    mock_resolver = MagicMock()
    mock_resolver.resolve_dependencies.return_value = [
        {"name": "dep1", "version": "1.0.0"},
        {"name": "dep2", "version": "2.0.0"}
    ]
    mock_resolver_cls.return_value = mock_resolver
    
    from src.cli.collect_data import NpmClient, GithubClient, AuditClient, DependencyResolver
    npm = NpmClient()
    gh = GithubClient()
    audit = AuditClient()
    resolver = DependencyResolver(npm, gh, audit)
    
    deps = process_package("test-pkg", npm, gh, audit, resolver)
    
    assert len(deps) == 2
    # Verify that records have None for dates when repo info is missing
    assert deps[0]["last_release_date"] is None
    assert deps[0]["age_in_days"] is None
    assert deps[0]["vulnerability_count"] == 0

@patch('builtins.open', new_callable=mock_open)
def test_export_to_csv_creates_file(mock_file):
    data = [
        {"name": "dep1", "version": "1.0.0", "parent_package": "pkg1",
         "last_commit_date": None, "last_release_date": None,
         "vulnerability_count": 0, "age_in_days": None, "has_release_metadata": False}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        export_to_csv(data, output_path)
        
        # Verify file was opened for writing
        mock_file.assert_called()
        # Verify CSV header and row
        handle = mock_file()
        calls = handle.write.call_args_list
        # Check that header was written
        header_written = any("name" in str(call) for call in calls)
        assert header_written

def test_calculate_metrics_includes_null_ratio():
    data = [
        {"name": "dep1", "last_release_date": "2023-01-01T00:00:00Z"},
        {"name": "dep2", "last_release_date": None},
        {"name": "dep3", "last_release_date": "2023-01-01T00:00:00Z"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        calculate_and_export_metrics(data, output_dir)
        
        metrics_path = output_dir / "metrics.json"
        assert metrics_path.exists()
        
        with open(metrics_path) as f:
            metrics = json.load(f)
        
        assert "total_dependencies" in metrics
        assert "missing_release_metadata_ratio" in metrics
        assert metrics["total_dependencies"] == 3
        assert metrics["missing_release_metadata_ratio"] == 1/3

def test_calculate_age_metrics_updates_data():
    now = datetime.now(timezone.utc)
    past_date = (now.replace(year=now.year - 1)).isoformat()
    
    data = [
        {"name": "dep1", "last_release_date": past_date},
        {"name": "dep2", "last_release_date": None},
        {"name": "dep3", "last_release_date": "invalid-date"}
    ]
    
    missing_ratio = calculate_age_metrics(data)
    
    # Check that valid date got an age
    assert data[0]["age_in_days"] is not None
    assert data[0]["age_in_days"] > 360  # Roughly a year
    
    # Check that null date stays null
    assert data[1]["age_in_days"] is None
    
    # Check that invalid date becomes null
    assert data[2]["age_in_days"] is None
    
    # Check missing ratio
    assert missing_ratio == 2/3  # 2 out of 3 are missing/invalid