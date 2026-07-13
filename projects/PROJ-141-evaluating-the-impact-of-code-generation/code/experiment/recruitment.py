"""
Participant Recruitment Flow for Code Generation Experiment.

This module implements the recruitment flow for participants, including:
- Experience filtering (≥1 year programming experience)
- Eligibility verification
- Recruitment data collection
- Participant status tracking
"""

import os
import sys
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Import from existing project modules
from config.settings import get_config, get_experiment_config
from logs.experiment import setup_experiment_logger, log_experiment_event
from data.models import Participant

# Configure logging
logger = setup_experiment_logger("recruitment")

class RecruitmentError(Exception):
    """Custom exception for recruitment-related errors."""
    pass

class EligibilityError(RecruitmentError):
    """Raised when a participant fails eligibility checks."""
    pass

def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex pattern.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_experience_years(years: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate that programming experience is ≥1 year.
    
    Args:
        years: Programming experience in years (can be int, float, or string)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if isinstance(years, str):
            years = float(years.strip())
        
        if not isinstance(years, (int, float)):
            return False, "Experience must be a numeric value"
        
        if years < 0:
            return False, "Experience cannot be negative"
        
        if years < 1:
            return False, "Minimum 1 year of programming experience required"
        
        return True, None
        
    except (ValueError, TypeError) as e:
        return False, f"Invalid experience value: {str(e)}"

def validate_age(age: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate age is within acceptable range (18-120).
    
    Args:
        age: Age in years
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if isinstance(age, str):
            age = int(age.strip())
        
        if not isinstance(age, int):
            return False, "Age must be an integer"
        
        if age < 18:
            return False, "Minimum age is 18 years"
        
        if age > 120:
            return False, "Age cannot exceed 120 years"
        
        return True, None
        
    except (ValueError, TypeError) as e:
        return False, f"Invalid age value: {str(e)}"

def validate_language_proficiency(language: str) -> Tuple[bool, Optional[str]]:
    """
    Validate primary programming language is supported.
    
    Args:
        language: Programming language name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_languages = {"python", "java", "javascript", "typescript", "c", "cpp", "go", "rust"}
    
    if not language:
        return False, "Programming language is required"
    
    if language.lower() not in supported_languages:
        return False, f"Language '{language}' not in supported list: {supported_languages}"
    
    return True, None

def validate_country(country: str) -> Tuple[bool, Optional[str]]:
    """
    Validate country code (ISO 3166-1 alpha-2).
    
    Args:
        country: Country code (e.g., "US", "CA", "GB")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Simple validation for 2-letter country codes
    if not country or len(country) != 2:
        return False, "Country must be a 2-letter ISO code"
    
    if not country.isalpha():
        return False, "Country code must contain only letters"
    
    return True, None

def collect_recruitment_data(
    email: str,
    age: int,
    country: str,
    primary_language: str,
    experience_years: float,
    has_university_degree: bool,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Collect and validate recruitment data from a potential participant.
    
    Args:
        email: Participant email address
        age: Participant age in years
        country: Participant country (ISO 3166-1 alpha-2)
        primary_language: Primary programming language
        experience_years: Years of programming experience
        has_university_degree: Whether participant has a university degree
        additional_info: Optional additional information
        
    Returns:
        Dictionary containing validated recruitment data
        
    Raises:
        EligibilityError: If any validation fails
    """
    # Validate email
    if not validate_email_format(email):
        raise EligibilityError(f"Invalid email format: {email}")
    
    # Validate age
    is_valid, error = validate_age(age)
    if not is_valid:
        raise EligibilityError(f"Age validation failed: {error}")
    
    # Validate country
    is_valid, error = validate_country(country)
    if not is_valid:
        raise EligibilityError(f"Country validation failed: {error}")
    
    # Validate language
    is_valid, error = validate_language_proficiency(primary_language)
    if not is_valid:
        raise EligibilityError(f"Language validation failed: {error}")
    
    # Validate experience (≥1 year requirement)
    is_valid, error = validate_experience_years(experience_years)
    if not is_valid:
        raise EligibilityError(f"Experience validation failed: {error}")
    
    # Build participant record
    participant_data = {
        "email": email,
        "age": age,
        "country": country.upper(),
        "primary_language": primary_language.lower(),
        "experience_years": float(experience_years),
        "has_university_degree": has_university_degree,
        "additional_info": additional_info or {},
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending_review",
        "eligibility": {
            "email_valid": True,
            "age_valid": True,
            "country_valid": True,
            "language_valid": True,
            "experience_valid": True,
            "overall_eligible": True
        }
    }
    
    logger.info(f"Collected recruitment data for email: {email}")
    return participant_data

def check_eligibility(participant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check overall eligibility of a participant based on collected data.
    
    Args:
        participant_data: Dictionary containing participant information
        
    Returns:
        Dictionary with eligibility status and reasons
    """
    eligibility = {
        "is_eligible": True,
        "reasons": [],
        "disqualifications": []
    }
    
    # Check experience requirement (≥1 year)
    experience = participant_data.get("experience_years", 0)
    if experience < 1:
        eligibility["is_eligible"] = False
        eligibility["disqualifications"].append(
            f"Insufficient experience: {experience} years (minimum 1 required)"
        )
        eligibility["eligibility"]["experience_valid"] = False
    else:
        eligibility["reasons"].append(
            f"Meets experience requirement: {experience} years"
        )
    
    # Check age requirement
    age = participant_data.get("age", 0)
    if age < 18:
        eligibility["is_eligible"] = False
        eligibility["disqualifications"].append(
            f"Age below minimum: {age} years (minimum 18 required)"
        )
        eligibility["eligibility"]["age_valid"] = False
    
    # Check email format
    if not validate_email_format(participant_data.get("email", "")):
        eligibility["is_eligible"] = False
        eligibility["disqualifications"].append("Invalid email format")
        eligibility["eligibility"]["email_valid"] = False
    
    # Check language support
    language = participant_data.get("primary_language", "")
    if not validate_language_proficiency(language)[0]:
        eligibility["is_eligible"] = False
        eligibility["disqualifications"].append(
            f"Unsupported programming language: {language}"
        )
        eligibility["eligibility"]["language_valid"] = False
    
    # Check country
    if not validate_country(participant_data.get("country", ""))[0]:
        eligibility["is_eligible"] = False
        eligibility["disqualifications"].append("Invalid country code")
        eligibility["eligibility"]["country_valid"] = False
    
    # Update overall eligibility flag
    eligibility["eligibility"]["overall_eligible"] = eligibility["is_eligible"]
    
    logger.info(
        f"Eligibility check completed: {eligibility['is_eligible']} "
        f"for email: {participant_data.get('email')}"
    )
    
    return eligibility

def save_recruitment_record(
    participant_data: Dict[str, Any],
    eligibility_result: Dict[str, Any]
) -> str:
    """
    Save recruitment record to the recruitment database file.
    
    Args:
        participant_data: Validated participant data
        eligibility_result: Eligibility check results
        
    Returns:
        Path to the saved recruitment record file
    """
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    recruitment_dir = data_dir / "recruitment"
    recruitment_dir.mkdir(parents=True, exist_ok=True)
    
    # Update status based on eligibility
    status = "eligible" if eligibility_result["is_eligible"] else "ineligible"
    participant_data["status"] = status
    participant_data["eligibility_result"] = eligibility_result
    participant_data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    
    # Generate filename based on email hash
    email_hash = hashlib.sha256(participant_data["email"].encode()).hexdigest()[:12]
    filename = f"recruitment_{email_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = recruitment_dir / filename
    
    # Write record
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(participant_data, f, indent=2, default=str)
    
    logger.info(f"Saved recruitment record to: {filepath}")
    return str(filepath)

def process_recruitment_application(
    email: str,
    age: int,
    country: str,
    primary_language: str,
    experience_years: float,
    has_university_degree: bool,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a complete recruitment application.
    
    Args:
        email: Participant email
        age: Participant age
        country: Participant country
        primary_language: Primary programming language
        experience_years: Years of programming experience
        has_university_degree: Whether participant has a degree
        additional_info: Additional information
        
    Returns:
        Dictionary containing application result with eligibility status
    """
    try:
        # Collect and validate data
        participant_data = collect_recruitment_data(
            email=email,
            age=age,
            country=country,
            primary_language=primary_language,
            experience_years=experience_years,
            has_university_degree=has_university_degree,
            additional_info=additional_info
        )
        
        # Check eligibility
        eligibility_result = check_eligibility(participant_data)
        
        # Save record
        record_path = save_recruitment_record(participant_data, eligibility_result)
        
        # Log event
        log_experiment_event(
            event_type="recruitment_application",
            data={
                "email_hash": hashlib.sha256(email.encode()).hexdigest()[:8],
                "eligible": eligibility_result["is_eligible"],
                "record_path": record_path
            }
        )
        
        return {
            "success": True,
            "eligible": eligibility_result["is_eligible"],
            "disqualifications": eligibility_result.get("disqualifications", []),
            "record_path": record_path,
            "message": "Application processed successfully" if eligibility_result["is_eligible"] 
                       else f"Application ineligible: {', '.join(eligibility_result['disqualifications'])}"
        }
        
    except EligibilityError as e:
        logger.error(f"Eligibility error: {str(e)}")
        return {
            "success": False,
            "eligible": False,
            "error": str(e),
            "message": f"Application rejected: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error processing application: {str(e)}")
        return {
            "success": False,
            "eligible": False,
            "error": str(e),
            "message": f"Application processing failed: {str(e)}"
        }

def get_recruitment_statistics() -> Dict[str, Any]:
    """
    Get statistics about recruitment applications.
    
    Returns:
        Dictionary containing recruitment statistics
    """
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    recruitment_dir = data_dir / "recruitment"
    
    if not recruitment_dir.exists():
        return {
            "total_applications": 0,
            "eligible": 0,
            "ineligible": 0,
            "pending": 0
        }
    
    total = 0
    eligible = 0
    ineligible = 0
    pending = 0
    
    for filepath in recruitment_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                total += 1
                status = data.get("status", "pending")
                if status == "eligible":
                    eligible += 1
                elif status == "ineligible":
                    ineligible += 1
                else:
                    pending += 1
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read recruitment file {filepath}: {e}")
    
    return {
        "total_applications": total,
        "eligible": eligible,
        "ineligible": ineligible,
        "pending": pending,
        "eligibility_rate": eligible / total if total > 0 else 0
    }

def main():
    """Main function for testing recruitment flow."""
    # Example usage
    print("Participant Recruitment Flow")
    print("=" * 50)
    
    # Test valid application
    print("\nTest 1: Valid application (≥1 year experience)")
    result = process_recruitment_application(
        email="test@example.com",
        age=25,
        country="US",
        primary_language="python",
        experience_years=3.5,
        has_university_degree=True
    )
    print(f"Result: {result}")
    
    # Test invalid application (insufficient experience)
    print("\nTest 2: Invalid application (<1 year experience)")
    result = process_recruitment_application(
        email="novice@example.com",
        age=22,
        country="CA",
        primary_language="java",
        experience_years=0.5,
        has_university_degree=False
    )
    print(f"Result: {result}")
    
    # Get statistics
    print("\nRecruitment Statistics:")
    stats = get_recruitment_statistics()
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()