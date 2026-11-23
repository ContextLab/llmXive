"""
Withdrawal Page for PROJ-205.

Displayed when a participant chooses 'I Do Not Agree' to the informed consent.
This page provides a polite closing message and no data collection occurs.
"""
import streamlit as st

st.set_page_config(
    page_title="Withdrawal - Visual Aesthetics Study",
    page_icon="👋",
    layout="centered"
)

def main():
    """Render the withdrawal message."""
    # Hide the sidebar and other Streamlit elements for a clean, final look
    st.markdown("""
        <style>
        .stApp {
            max-width: 600px;
            margin: 0 auto;
            padding-top: 100px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Thank you for your time")

    st.markdown("""
        <br>
        <p style="font-size: 1.2rem; color: #555;">
            You have chosen not to participate in this study.
            <br><br>
            Your decision is respected, and no data has been collected from this session.
            <br><br>
            If you have any questions or concerns, please contact the research team.
        </p>
        <br>
    """, unsafe_allow_html=True)

    st.info("This session has ended.")

if __name__ == "__main__":
    main()
