"""
Streamlit Survey Application for Visual Aesthetics Study.

This module implements the full survey flow: Consent -> Demographics -> Stimuli -> Ratings -> Submission.
It strictly uses in-memory `st.session_state` for client-side state management.
"""
import streamlit as st
import os
import sys
import time
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.helpers import (
    hash_ip,
    generate_user_id,
    get_submissions_csv_path,
    ensure_data_dirs,
    format_timestamp,
    truncate_user_agent
)
from code.utils.config import get_consent_file_path, get_irb_protocol_id
from code.survey.constants import LATIN_SQUARE_MATRIX

# Constants
SESSION_TIMEOUT_SECONDS = 300  # 5 minutes
REQUIRED_RATINGS_COUNT = 4

def get_project_root():
    return PROJECT_ROOT

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'consent'
    
    if 'stimuli_order' not in st.session_state:
        # Default to a random order if not set, but will be overwritten by selection logic
        st.session_state.stimuli_order = []
    
    if 'ratings' not in st.session_state:
        st.session_state.ratings = {}  # {stimulus_name: {'credibility': val, 'professionalism': val}}
    
    if 'demographics' not in st.session_state:
        st.session_state.demographics = {'age': None, 'education': None}
    
    if 'last_active' not in st.session_state:
        st.session_state.last_active = time.time()
    
    if 'session_status' not in st.session_state:
        st.session_state.session_status = 'active'
    
    if 'submission_status' not in st.session_state:
        st.session_state.submission_status = 'pending'

def update_last_active():
    """Update the last active timestamp."""
    st.session_state.last_active = time.time()

def check_session_timeout():
    """Check if the session has timed out."""
    if 'last_active' in st.session_state:
        if time.time() - st.session_state.last_active > SESSION_TIMEOUT_SECONDS:
            st.session_state.session_status = 'timeout'
            st.session_state.submission_status = 'incomplete'
            return True
    return False

def extract_and_validate_ip():
    """Extract IP from headers, hash it, and validate existence."""
    ip_header = st.context.headers.get('X-Forwarded-For')
    if not ip_header:
        # Fallback for local testing if header is missing (only in dev)
        if os.getenv('MODE') == 'development':
            ip_header = "127.0.0.1"
        else:
            st.error("Session Rejected: Unable to verify identity.")
            st.stop()
    
    hashed_ip = hash_ip(ip_header)
    return hashed_ip

def show_consent_form():
    """Display the IRB-approved consent form."""
    st.header("Informed Consent")
    consent_path = get_consent_file_path()
    
    if not os.path.exists(consent_path):
        st.error(f"Consent form not found at {consent_path}")
        st.stop()
    
    with open(consent_path, 'r', encoding='utf-8') as f:
        consent_text = f.read()
    
    st.markdown(consent_text)
    
    protocol_id = get_irb_protocol_id()
    st.info(f"Protocol ID: {protocol_id}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree", key="consent_agree"):
            st.session_state.current_step = 'demographics'
            st.rerun()
    
    with col2:
        if st.button("I Do Not Agree", key="consent_disagree"):
            st.session_state.session_status = 'withdrawn'
            st.session_state.submission_status = 'withdrawn'
            st.rerun()

def show_demographics():
    """Render and handle demographic input form."""
    st.header("Participant Information")
    
    with st.form(key="demographics_form"):
        age = st.number_input("Age (years)", min_value=18, max_value=100, step=1)
        education = st.selectbox(
            "Education Level",
            ["High School", "Bachelor's", "Master's", "PhD"],
            index=None,
            placeholder="Select your education level"
        )
        
        submitted = st.form_submit_button("Continue")
        
        if submitted:
            if age and education:
                st.session_state.demographics['age'] = age
                st.session_state.demographics['education'] = education
                st.session_state.current_step = 'stimuli'
                st.rerun()
            else:
                st.error("Please fill in all fields.")

def render_stimulus(stimulus_name, stimulus_path):
    """Render a single stimulus HTML file."""
    st.markdown(f"### Stimulus: {stimulus_name}")
    
    if os.path.exists(stimulus_path):
        with open(stimulus_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=600, scrolling=True)
    else:
        st.error(f"Stimulus file not found: {stimulus_path}")

def show_ratings(current_stimulus_index):
    """Display rating inputs for the current stimulus."""
    stimulus_name = st.session_state.stimuli_order[current_stimulus_index]
    st.header(f"Rate: {stimulus_name}")
    
    if stimulus_name not in st.session_state.ratings:
        st.session_state.ratings[stimulus_name] = {'credibility': None, 'professionalism': None}
    
    current_ratings = st.session_state.ratings[stimulus_name]
    
    credibility = st.slider(
        "Credibility (1-7)", 
        min_value=1, 
        max_value=7, 
        value=current_ratings['credibility'] if current_ratings['credibility'] else 4,
        key=f"cred_{stimulus_name}"
    )
    
    professionalism = st.slider(
        "Professionalism (1-7)", 
        min_value=1, 
        max_value=7, 
        value=current_ratings['professionalism'] if current_ratings['professionalism'] else 4,
        key=f"prof_{stimulus_name}"
    )
    
    # Update state
    st.session_state.ratings[stimulus_name]['credibility'] = credibility
    st.session_state.ratings[stimulus_name]['professionalism'] = professionalism

    col1, col2 = st.columns(2)
    with col1:
        if current_stimulus_index > 0:
            if st.button("Previous"):
                st.session_state.current_stimulus_index = current_stimulus_index - 1
                st.rerun()
    
    with col2:
        if current_stimulus_index < len(st.session_state.stimuli_order) - 1:
            if st.button("Next"):
                st.session_state.current_stimulus_index = current_stimulus_index + 1
                st.rerun()
        else:
            if st.button("Submit Survey"):
                if validate_all_rated():
                    st.session_state.current_step = 'submission'
                    st.rerun()
                else:
                    st.error("Please rate all stimuli before submitting.")

def validate_all_rated():
    """Check if all stimuli have been rated."""
    if 'stimuli_order' not in st.session_state:
        return False
    
    for stimulus in st.session_state.stimuli_order:
        if stimulus not in st.session_state.ratings:
            return False
        if st.session_state.ratings[stimulus]['credibility'] is None:
            return False
        if st.session_state.ratings[stimulus]['professionalism'] is None:
            return False
    
    return True

def submit_survey():
    """Handle final submission and data export."""
    st.session_state.submission_status = 'complete'
    st.session_state.session_status = 'completed'
    
    # Prepare data row
    participant_id = st.session_state.participant_id
    hashed_ip = extract_and_validate_ip()
    demographics = st.session_state.demographics
    timestamp = format_timestamp()
    user_agent = truncate_user_agent(st.context.headers.get('User-Agent', ''))
    
    rows = []
    for stimulus_name in st.session_state.stimuli_order:
        rating = st.session_state.ratings[stimulus_name]
        row = {
            'participant_id': participant_id,
            'stimulus_id': stimulus_name,
            'credibility': rating['credibility'],
            'professionalism': rating['professionalism'],
            'timestamp': timestamp,
            'hashed_ip': hashed_ip,
            'age': demographics['age'],
            'education': demographics['education'],
            'duplicate_flag': 'N/A', # Will be set by audit
            'session_status': st.session_state.session_status,
            'submission_status': st.session_state.submission_status,
            'user_agent': user_agent
        }
        rows.append(row)
    
    # Write to CSV
    ensure_data_dirs()
    csv_path = get_submissions_csv_path()
    file_exists = os.path.isfile(csv_path)
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    
    # Clear session state to prevent resubmission
    st.session_state.clear()
    st.success("Thank you for your participation! Your responses have been recorded.")
    st.stop()

def main():
    """Main entry point for the Streamlit app."""
    st.set_page_config(page_title="Visual Aesthetics Study", layout="wide")
    
    init_session_state()
    update_last_active()
    
    if check_session_timeout():
        st.error("Session timed out due to inactivity. Please restart.")
        st.stop()
    
    # Handle withdrawal
    if st.session_state.session_status == 'withdrawn':
        st.info("Thank you for your time. You have withdrawn from the study.")
        st.stop()
    
    # Determine current step
    step = st.session_state.current_step
    
    if step == 'consent':
        show_consent_form()
    elif step == 'demographics':
        show_demographics()
    elif step == 'stimuli':
        # Initialize stimuli order if not set
        if not st.session_state.stimuli_order:
            # Use hash of participant ID to select Latin Square row
            row_index = hash(st.session_state.participant_id) % 4
            st.session_state.stimuli_order = LATIN_SQUARE_MATRIX[row_index]
            st.session_state.current_stimulus_index = 0
        
        current_idx = st.session_state.get('current_stimulus_index', 0)
        stimulus_name = st.session_state.stimuli_order[current_idx]
        
        # Map stimulus name to file path
        stimulus_map = {
            'Professional': 'code/stimuli/professional.html',
            'Minimalist': 'code/stimuli/minimalist.html',
            'Low-Quality': 'code/stimuli/low_quality.html',
            'Neutral': 'code/stimuli/neutral.html'
        }
        
        stimulus_path = stimulus_map.get(stimulus_name)
        if not stimulus_path:
            st.error(f"Stimulus path not found for {stimulus_name}")
            st.stop()
        
        render_stimulus(stimulus_name, stimulus_path)
        show_ratings(current_idx)
    elif step == 'submission':
        submit_survey()
    else:
        st.error("Unknown state. Please refresh the page.")

if __name__ == "__main__":
    main()