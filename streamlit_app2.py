import streamlit as st
import requests
from datetime import datetime, date
import json
import re

# Page configuration
st.set_page_config(
    page_title="TRIPPY - AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .trip-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .itinerary-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #1E88E5;
    }
    .day-header {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border-left: 3px solid #1976d2;
    }
</style>
""", unsafe_allow_html=True)

# Function to clean and format the itinerary text
def format_itinerary(text):
    if not text:
        return "No itinerary data available."
    text = str(text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text).strip()
    if any(marker in text for marker in ['#', '**', '*', '-', '1.', '2.']):
        return text
    lines = text.split('\n')
    formatted_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if (line.isupper() and len(line) < 50) or line.startswith(('Day ', 'DAY ')):
            formatted_lines.append(f"## {line}")
        elif any(line.startswith(prefix) for prefix in ['Morning:', 'Afternoon:', 'Evening:', 'Night:']):
            formatted_lines.append(f"### {line}")
        elif line.startswith(('- ', '• ', '* ')) or re.match(r'^\d+\.', line):
            formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    return '\n\n'.join(formatted_lines)

# Function to display itinerary in sections
def display_formatted_itinerary(itinerary_text):
    sections = re.split(r'\n(?=#{1,3}\s)', itinerary_text)
    for section in sections:
        if not section.strip():
            continue
        if re.match(r'^#{1,3}\s*(Day\s*\d+|DAY\s*\d+)', section, re.IGNORECASE):
            with st.container():
                st.markdown('<div class="day-header">', unsafe_allow_html=True)
                st.markdown(section)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown('<div class="itinerary-section">', unsafe_allow_html=True)
                st.markdown(section)
                st.markdown('</div>', unsafe_allow_html=True)

# Initialize session state
if 'api_response' not in st.session_state:
    st.session_state.api_response = None
if 'loading' not in st.session_state:
    st.session_state.loading = False
if 'trip_data' not in st.session_state:
    st.session_state.trip_data = None

# Main header
st.markdown('<h1 class="main-header">✈️ TRIPPY</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your AI-Powered Travel Planning Assistant</p>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_base_url = st.text_input(
        "API Base URL",
        value="https://abc-lpk5.onrender.com",
        help="The base URL of your TRIPPY API"
    )

    if st.button("🔍 Check API Health"):
        try:
            health_response = requests.get(f"{api_base_url}/api/v1/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.success(f"✅ API is healthy!\nStatus: {health_data.get('status', 'N/A')}")
            else:
                st.error(f"❌ API health check failed: {health_response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to API: {str(e)}")

    st.divider()
    st.header("🎨 Display Options")
    display_mode = st.radio(
        "Choose display format:",
        ["Enhanced Formatting", "Raw Markdown", "Plain Text"]
    )

    st.divider()
    st.header("ℹ️ About")
    st.markdown("""
    **TRIPPY** uses advanced AI to create personalized travel itineraries.
    - 🌍 Destination preferences  
    - 📅 Travel dates  
    - 🎯 Interests  
    - 💰 Budget  
    """)

col1, col2 = st.columns([2, 1])

with col1:
    st.header("🗺️ Plan Your Trip")
    with st.form("trip_form"):
        col_orig, col_dest = st.columns(2)
        with col_orig:
            origin = st.text_input("From (Origin)", placeholder="e.g., Bangalore, India")
        with col_dest:
            destination = st.text_input("To (Destination)", placeholder="e.g., Krabi, Thailand")
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date", value=date.today(), min_value=date.today())
        with col_end:
            end_date = st.date_input("End Date", value=date.today(), min_value=date.today())
        interests = st.text_area(
            "Travel Interests & Preferences",
            placeholder="e.g., 2 adults who love swimming, hiking, local food, and water sports.",
            height=100
        )
        submitted = st.form_submit_button("🚀 Generate Trip Plan", use_container_width=True)
        if submitted:
            if not all([origin, destination, interests]):
                st.error("❌ Please fill in all required fields.")
            elif end_date <= start_date:
                st.error("❌ End date must be after start date.")
            else:
                st.session_state.trip_data = {
                    "origin": origin,
                    "destination": destination,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "interests": interests
                }
                st.session_state.loading = True
                st.session_state.api_response = None

with col2:
    st.header("📋 Trip Summary")
    if 'origin' in locals() and any([origin, destination, interests]):
        st.markdown('<div class="trip-card">', unsafe_allow_html=True)
        if origin:
            st.markdown(f"**From:** {origin}")
        if destination:
            st.markdown(f"**To:** {destination}")
        if start_date and end_date and end_date > start_date:
            duration = (end_date - start_date).days
            st.markdown(f"**Duration:** {duration} days")
            st.markdown(f"**Dates:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        if interests:
            st.markdown(f"**Interests:** {interests[:100]}{'...' if len(interests) > 100 else ''}")
        st.markdown('</div>', unsafe_allow_html=True)

# Handle API call
if st.session_state.loading and st.session_state.trip_data:
    with st.spinner("🤖 AI is crafting your perfect trip..."):
        try:
            response = requests.post(
                f"{api_base_url}/api/v1/plan-trip",
                json=st.session_state.trip_data,
                timeout=300
            )
            if response.status_code == 200:
                st.session_state.api_response = response.json()
                st.session_state.loading = False
                st.rerun()
            else:
                st.session_state.loading = False
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                st.error(f"❌ API Error ({response.status_code}): {error_detail}")
        except requests.exceptions.Timeout:
            st.session_state.loading = False
            st.error("⏰ Request timed out.")
        except requests.exceptions.RequestException as e:
            st.session_state.loading = False
            st.error(f"❌ Connection Error: {str(e)}")
        except Exception as e:
            st.session_state.loading = False
            st.error(f"❌ Unexpected Error: {str(e)}")

# Display API response
if st.session_state.api_response:
    response_data = st.session_state.api_response
    if response_data.get('status') == 'success':
        st.markdown('<div class="success-message">✅ Trip plan generated successfully!</div>', unsafe_allow_html=True)
        st.header("🗓️ Your Personalized Trip Itinerary")
        itinerary = response_data.get('itinerary', '')
        if itinerary:
            tab1, tab2, tab3 = st.tabs(["📖 Full Itinerary", "🔍 Debug View", "💾 Export Options"])
            with tab1:
                if display_mode == "Enhanced Formatting":
                    formatted_itinerary = format_itinerary(itinerary)
                    display_formatted_itinerary(formatted_itinerary)
                elif display_mode == "Raw Markdown":
                    st.markdown(itinerary)
                else:
                    st.text(itinerary)
            with tab2:
                st.subheader("🔍 Raw API Response")
                st.write("**Response Type:**", type(itinerary).__name__)
                st.write("**Response Length:**", len(str(itinerary)))
                st.write("**First 500 characters:**")
                st.code(str(itinerary)[:500] + "..." if len(str(itinerary)) > 500 else str(itinerary))
                with st.expander("View Full Raw Response"):
                    st.code(str(itinerary))
            with tab3:
                col_download1, col_download2 = st.columns(2)
                with col_download1:
                    download_text = format_itinerary(itinerary) if display_mode == "Enhanced Formatting" else str(itinerary)
                    st.download_button(
                        label="📄 Download as Text",
                        data=download_text,
                        file_name=f"trip_itinerary_{destination.replace(' ', '_') if destination else 'unknown'}_{start_date if 'start_date' in locals() else 'unknown'}.txt",
                        mime="text/plain"
                    )
                with col_download2:
                    json_data = json.dumps(response_data, indent=2)
                    st.download_button(
                        label="📊 Download as JSON",
                        data=json_data,
                        file_name=f"trip_data_{destination.replace(' ', '_') if destination else 'unknown'}_{start_date if 'start_date' in locals() else 'unknown'}.json",
                        mime="application/json"
                    )
        if st.button("🗑️ Clear Results"):
            st.session_state.api_response = None
            st.rerun()
    else:
        error_msg = response_data.get('error', response_data.get('message', 'Unknown error'))
        st.markdown(f'<div class="error-message">❌ Error: {error_msg}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Powered by TRIPPY API | Built with ❤️ using Streamlit</p>
        <p>🤖 AI-generated itineraries are suggestions. Please verify details before booking.</p>
    </div>
    """,
    unsafe_allow_html=True
)
