"""
API collector module for US1.
Collects study data from ClinicalTrials.gov and OSF.
"""

import json
import logging
import time
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests
from code.utils.logging import get_logger

logger = get_logger(__name__)

# API endpoints and rate limiting
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
OSF_API = "https://api.osf.io/v2/registrations/"
RATE_LIMIT_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3
BACKOFF_BASE = 2
BACKOFF_MAX = 30

RETRIEVAL_LOG_PATH = 'data/raw/retrieval_log.json'
MOCK_DATA_PATH = 'data/raw/mock_registry_response.json'


class APICollector:
    """Collects study data from clinical trial registries."""

    def __init__(self):
        self.retrieval_log = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'llmXive-Research/1.0'
        })

    def _log_retrieval(self, query: str, status_code: int, source: str):
        """Log a retrieval attempt."""
        entry = {
            'query': query,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status_code': status_code,
            'source': source
        }
        self.retrieval_log.append(entry)
        logger.info(f"Retrieved {source} query '{query}': {status_code}")

    def _save_retrieval_log(self):
        """Save retrieval log to file."""
        log_path = Path(RETRIEVAL_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(RETRIEVAL_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.retrieval_log, f, indent=2)

    def _fetch_with_backoff(self, url: str, params: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Fetch with exponential backoff."""
        for attempt in range(MAX_RETRIES):
            try:
                time.sleep(RATE_LIMIT_DELAY)
                response = self.session.get(url, params=params, timeout=30)
                self._log_retrieval(str(params), response.status_code, source)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = min(BACKOFF_BASE ** attempt, BACKOFF_MAX)
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to fetch {source}: {response.status_code}")
                    return None
            except requests.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = min(BACKOFF_BASE ** attempt, BACKOFF_MAX)
                    time.sleep(wait_time)
                    continue
                return None

        return None

    def fetch_clinicaltrials(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Fetch studies from ClinicalTrials.gov.

        Args:
            start_year: Start year for search
            end_year: End year for search

        Returns:
            List of study records
        """
        studies = []
        query_params = {
            'filter': f'hasResults:true,studyType:Randomized',
            'pageSize': 100,
            'pageToken': ''
        }

        # Search for ASD studies with social outcomes
        search_terms = f"autism spectrum disorder AND (social skills OR communication OR peer interaction)"
        query_params['filter'] += f",conditions:{search_terms}"

        page = 0
        while True:
            query_params['pageToken'] = f"page_{page}"
            result = self._fetch_with_backoff(CLINICALTRIALS_API, query_params, "ClinicalTrials.gov")

            if not result:
                break

            records = result.get('studies', [])
            if not records:
                break

            for record in records:
                # Extract relevant fields
                study = {
                    'id': record.get('protocolSection', {}).get('identificationModule', {}).get('nctId'),
                    'title': record.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle'),
                    'registry': 'ClinicalTrials.gov',
                    'age_range': self._extract_age_range(record),
                    'diagnosis': 'ASD',
                    'outcomes': self._extract_outcomes(record),
                    'description': record.get('protocolSection', {}).get('descriptionModule', {}).get('briefSummary'),
                    'abstract': record.get('protocolSection', {}).get('resultsModule', {}).get('abstractResult'),
                    'arms': record.get('protocolSection', {}).get('armsInterventionsModule', {}).get('armGroups'),
                    'start_year': self._extract_year(record),
                    'rater_type': 'unknown',
                    'blinded_assessment_flag': None
                }

                if study['id'] and study['start_year'] and start_year <= study['start_year'] <= end_year:
                    studies.append(study)

            if len(records) < 100:
                break
            page += 1

        return studies

    def _extract_age_range(self, record: Dict[str, Any]) -> Dict[str, int]:
        """Extract age range from record."""
        eligibility = record.get('protocolSection', {}).get('eligibilityModule', {})
        criteria = eligibility.get('eligibilityCriteria', '')

        # Try to parse age from criteria text
        import re
        age_match = re.search(r'(\d+)\s*-\s*(\d+)\s*years?', criteria)
        if age_match:
            return {'min': int(age_match.group(1)), 'max': int(age_match.group(2))}

        # Fallback to participant info
        participant_info = eligibility.get('healthyVolunteers')
        return {'min': 6, 'max': 12}  # Default for US1

    def _extract_outcomes(self, record: Dict[str, Any]) -> List[str]:
        """Extract outcome measures from record."""
        outcomes = []
        outcome_section = record.get('protocolSection', {}).get('outcomesModule', {})
        primary_outcomes = outcome_section.get('primaryOutcomes', [])

        for outcome in primary_outcomes:
            measure = outcome.get('measure', '')
            if measure:
                outcomes.append(measure)

        return outcomes if outcomes else ['Unknown']

    def _extract_year(self, record: Dict[str, Any]) -> Optional[int]:
        """Extract start year from record."""
        dates = record.get('protocolSection', {}).get('studyDatesModule', {})
        start_date = dates.get('startDate', {})
        if start_date:
            year = start_date.get('year')
            if year:
                return int(year)
        return None

    def fetch_osf(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Fetch studies from OSF.

        Args:
            start_year: Start year for search
            end_year: End year for search

        Returns:
            List of study records
        """
        studies = []
        params = {
            'filter[tags]': 'ASD,mindfulness,social-skills',
            'page[size]': 20
        }

        result = self._fetch_with_backoff(OSF_API, params, "OSF")
        if result:
            data = result.get('data', [])
            for item in data:
                attributes = item.get('attributes', {})
                study = {
                    'id': item.get('id'),
                    'title': attributes.get('title'),
                    'registry': 'OSF',
                    'age_range': {'min': 6, 'max': 12},
                    'diagnosis': 'ASD',
                    'outcomes': ['Unknown'],
                    'description': attributes.get('description'),
                    'abstract': None,
                    'arms': [],
                    'start_year': None,
                    'rater_type': 'unknown',
                    'blinded_assessment_flag': None
                }
                studies.append(study)

        return studies

    def collect(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Main collection method.

        Args:
            start_year: Start year for search
            end_year: End year for search

        Returns:
            Combined list of studies from all sources
        """
        # Check for mock data first (CI mode)
        if os.path.exists(MOCK_DATA_PATH):
            logger.info(f"Loading mock data from {MOCK_DATA_PATH}")
            with open(MOCK_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Live mode: fetch from APIs
        all_studies = []

        logger.info("Fetching from ClinicalTrials.gov...")
        ct_studies = self.fetch_clinicaltrials(start_year, end_year)
        all_studies.extend(ct_studies)

        logger.info("Fetching from OSF...")
        osf_studies = self.fetch_osf(start_year, end_year)
        all_studies.extend(osf_studies)

        # Save retrieval log
        self._save_retrieval_log()

        logger.info(f"Collected {len(all_studies)} studies total")
        return all_studies


def main():
    """Main entry point for collector module."""
    import argparse
    parser = argparse.ArgumentParser(description='Collect study data from registries')
    parser.add_argument('--start-year', type=int, default=2015, help='Start year')
    parser.add_argument('--end-year', type=int, default=2024, help='End year')
    args = parser.parse_args()

    collector = APICollector()
    studies = collector.collect(args.start_year, args.end_year)

    # Save raw data
    raw_path = Path('data/raw/collected_studies.json')
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(studies, f, indent=2)

    logger.info(f"Saved {len(studies)} studies to {raw_path}")


if __name__ == '__main__':
    main()