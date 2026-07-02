import streamlit as st
import os
import sys
import random
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# Local imports from project structure
from utils.helpers import (
    ensure_data_dirs,
    generate_user_id,
    hash_ip,
    format_timestamp,
    get_consent_log_path,
    log_consent_decision,
    validate_rating_count,
    truncate_user_agent,
    check_duplicate_ip,
    prepare_submission_row,
    append_to_submissions_csv,
    save_submission
)
from utils.config import get_consent_file_path, load_consent_text

# Constants
LATIN_SQUARE_SEQUENCES = [
    ["Professional", "Minimalist", "Low-Quality", "Neutral"],
    ["Minimalist", "Low-Quality", "Neutral", "Professional"],
    ["Low-Quality", "Neutral", "Professional", "Minimalist"],
    ["Neutral", "Professional", "Minimalist", "Low-Quality"]
]

EDUCATION_OPTIONS = [
    ("High School", 1),
    ("Bachelor's", 2),
    ("Master's", 3),
    ("PhD", 4)
]

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = generate_user_id()
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False
    if 'current_sequence' not in st.session_state:
        st.session_state.current_sequence = None
    if 'stimulus_index' not in st.session_state:
        st.session_state.stimulus_index = 0
    if 'ratings' not in st.session_state:
        st.session_state.ratings = {}
    if 'demographics' not in st.session_state:
        st.session_state.demographics = {}
    if 'raw_ip' not in st.session_state:
        st.session_state.raw_ip = None
    if 'hashed_ip' not in st.session_state:
        st.session_state.hashed_ip = None
    if 'submission_complete' not in st.session_state:
        st.session_state.submission_complete = False

def show_consent_form():
    """Display the IRB-approved consent form."""
    if st.session_state.consent_given:
        return True

    st.title("Informed Consent")
    consent_text = load_consent_text()
    st.markdown(consent_text)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree", key="agree_btn"):
            log_consent_decision(st.session_state.user_id, "Agreed")
            st.session_state.consent_given = True
            st.rerun()
    with col2:
        if st.button("I Do Not Agree", key="disagree_btn"):
            log_consent_decision(st.session_state.user_id, "Declined")
            st.warning("Thank you. You may withdraw from the study.")
            st.stop()
    return False

def render_stimulus():
    """Render the current stimulus HTML file."""
    if st.session_state.current_sequence is None:
        # Select a random sequence
        st.session_state.current_sequence = random.choice(LATIN_SQUARE_SEQUENCES)
    
    stimulus_name = st.session_state.current_sequence[st.session_state.stimulus_index]
    stimulus_path = f"code/stimuli/{stimulus_name.lower().replace('-', '_')}.html"
    
    if not os.path.exists(stimulus_path):
        st.error(f"Stimulus file not found: {stimulus_path}")
        return

    with open(stimulus_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    st.components.v1.html(html_content, height=600, scrolling=True)
    st.markdown(f"**Condition:** {stimulus_name}")

def collect_ratings():
    """Collect credibility and professionalism ratings for the current stimulus."""
    stimulus_name = st.session_state.current_sequence[st.session_state.stimulus_index]
    key_prefix = f"stim_{st.session_state.stimulus_index}_{stimulus_name.replace(' ', '_')}"
    
    st.markdown(f"Please rate the following for the {stimulus_name} page:")
    
    col1, col2 = st.columns(2)
    with col1:
        credibility = st.slider(
            "Credibility",
            min_value=1,
            max_value=7,
            value=4,
            key=f"{key_prefix}_cred"
        )
    with col2:
        professionalism = st.slider(
            "Professionalism",
            min_value=1,
            max_value=7,
            value=4,
            key=f"{key_prefix}_prof"
        )
    
    if st.button("Next Stimulus", key="next_stim_btn"):
        st.session_state.ratings[stimulus_name] = {
            "credibility": credibility,
            "professionalism": professionalism
        }
        st.session_state.stimulus_index += 1
        st.rerun()

def show_demographics():
    """Render demographic input form: Age and Education."""
    st.markdown("### Demographics")
    st.markdown("Please provide the following information to complete the survey.")

    # Education Dropdown
    edu_label = st.selectbox(
        "Highest Level of Education",
        options=[opt[0] for opt in EDUCATION_OPTIONS],
        index=1,
        key="demo_edu"
    )
    
    # Map selected label to integer code
    selected_edu_code = next(opt[1] for opt in EDUCATION_OPTIONS if opt[0] == edu_label)
    st.session_state.demographics['education_code'] = selected_edu_code

    # Age Number Input
    age = st.number_input(
        "Age (years)",
        min_value=18,
        max_value=120,
        value=25,
        step=1,
        key="demo_age"
    )
    st.session_state.demographics['age'] = int(age)

    if st.button("Submit Survey", key="submit_survey_btn"):
        st.session_state.demographics['submitted'] = True
        st.rerun()

def save_submission_logic():
    """Handle the final submission, writing demographics and ratings to CSV."""
    if not st.session_state.get('demographics', {}).get('submitted', False):
        return

    # Validate ratings count
    if len(st.session_state.ratings) != 4:
        st.error("Error: Missing ratings. Please ensure all 4 stimuli were rated.")
        st.stop()

    # Prepare submission data
    user_id = st.session_state.user_id
    timestamp = format_timestamp()
    device_info = st.session_state.get('raw_ip', 'unknown') # Placeholder for actual device info logic if needed
    
    # Ensure data directories exist
    ensure_data_dirs()

    # Construct row data
    row_data = {
        "user_id": user_id,
        "timestamp": timestamp,
        "sequence": ",".join(st.session_state.current_sequence),
        "submission_status": "complete",
        "session_timeout": "false",
        "rating_count": len(st.session_state.ratings)
    }

    # Add ratings
    for stim_name, ratings in st.session_state.ratings.items():
        row_data[f"{stim_name}_credibility"] = ratings['credibility']
        row_data[f"{stim_name}_professionalism"] = ratings['professionalism']

    # Add Demographics (Age and Education Code)
    # T023d: Write Age (integer) and Education (integer code 1-4)
    if 'age' in st.session_state.demographics:
        row_data["age"] = st.session_state.demographics['age']
    else:
        row_data["age"] = None # Should not happen if validation passed

    if 'education_code' in st.session_state.demographics:
        row_data["education"] = st.session_state.demographics['education_code']
    else:
        row_data["education"] = None # Should not happen if validation passed

    # Handle IP hashing and duplicate flagging
    hashed_ip = st.session_state.get('hashed_ip', None)
    if hashed_ip:
        row_data["hashed_ip"] = hashed_ip
        is_duplicate = check_duplicate_ip(hashed_ip)
        row_data["duplicate_flag"] = "true" if is_duplicate else "false"
    else:
        row_data["hashed_ip"] = "N/A"
        row_data["duplicate_flag"] = "false"

    # Append to CSV
    append_to_submissions_csv(row_data)

    # Clear session state
    st.session_state.clear()
    st.session_state.submission_complete = True
    st.success("Thank you for your participation! Your data has been recorded.")
    st.info("You may now close this window.")

def main():
    """Main application entry point."""
    st.set_page_config(page_title="Visual Aesthetics Study", layout="centered")
    init_session_state()

    # Capture IP (T023a) - In a real deployment, this would come from request headers
    # For Streamlit, we simulate or capture from st.context if available in future versions
    # Currently, we rely on the helper to handle the logic if raw_ip is set
    if st.session_state.raw_ip is None:
        # Simulate capture for local testing or use a placeholder
        # In production, this should be injected by the hosting environment
        st.session_state.raw_ip = os.getenv("USER_IP", "192.168.1.100") 
        # T023b: Immediate hashing
        st.session_state.hashed_ip = hash_ip(st.session_state.raw_ip)

    if not show_consent_form():
        return

    if st.session_state.submission_complete:
        return

    # Phase 1: Stimuli Presentation
    if st.session_state.stimulus_index < 4:
        st.title("Visual Aesthetics Survey")
        st.write(f"Stimulus {st.session_state.stimulus_index + 1} of 4")
        render_stimulus()
        collect_ratings()
    else:
        # Phase 2: Demographics (T023d_ui / T023d)
        st.title("Demographics")
        if not st.session_state.demographics.get('submitted', False):
            show_demographics()
        else:
            save_submission_logic()

if __name__ == "__main__":
    main()
