import os
import streamlit as st
from google.genai import Client, types
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
import re
from io import BytesIO

# Load environment variables
load_dotenv()

# Initialize session state for managing multiple travel plans
if 'travel_sessions' not in st.session_state:
    st.session_state.travel_sessions = []
if 'active_session' not in st.session_state:
    st.session_state.active_session = None
if 'session_counter' not in st.session_state:
    st.session_state.session_counter = 0
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}

# Page configuration
st.set_page_config(
    page_title="FreeWen - Travel AI Companion",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize map visibility state
if 'map_visible' not in st.session_state:
    st.session_state.map_visible = True

# Custom CSS for fixed right panel with collapsible functionality
st.markdown("""
<style>
    /* Fixed right panel for map */
    .map-panel {
        position: fixed;
        right: 0;
        top: 80px;
        width: 380px;
        height: calc(100vh - 100px);
        overflow-y: auto;
        background: white;
        padding: 20px;
        border-radius: 10px 0 0 10px;
        box-shadow: -2px 0 12px rgba(0,0,0,0.1);
        z-index: 999;
        transition: transform 0.3s ease;
    }
    
    .map-panel.hidden {
        transform: translateX(100%);
    }
    
    /* Floating toggle button */
    .floating-map-toggle {
        position: fixed;
        right: 390px;
        top: 100px;
        background: #4CAF50;
        color: white;
        border: 2px solid #45a049;
        border-radius: 8px 0 0 8px;
        padding: 12px 10px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: -3px 3px 10px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        font-size: 20px;
        line-height: 1;
        writing-mode: vertical-rl;
        text-orientation: mixed;
    }
    
    .floating-map-toggle:hover {
        background: #45a049;
        box-shadow: -3px 3px 15px rgba(0,0,0,0.4);
        transform: translateX(-2px);
    }
    
    .floating-map-toggle.collapsed {
        right: 0;
        border-radius: 8px 0 0 8px;
    }
    
    /* Main content with margin for map panel */
    .main-content {
        margin-right: 400px;
        transition: margin-right 0.3s ease;
    }
    
    .main-content.expanded {
        margin-right: 20px;
    }
    
    /* Make sure main content doesn't overlap */
    section.main > div {
        padding-right: 420px;
        transition: padding-right 0.3s ease;
    }
    
    section.main > div.expanded {
        padding-right: 20px;
    }
    
    @media (max-width: 1200px) {
        .map-panel {
            display: none;
        }
        .floating-map-toggle {
            display: none;
        }
        section.main > div {
            padding-right: 20px !important;
        }
    }
    
    /* Fix iframe container */
    .map-panel iframe {
        display: block;
        margin-bottom: 15px;
    }
    
    /* Fix content overflow */
    .map-panel h3, .map-panel h4, .map-panel p, .map-panel a {
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for tables
st.markdown("""
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    table thead tr {
        background-color: #4CAF50;
        color: white;
        text-align: left;
        font-weight: bold;
    }
    
    table th,
    table td {
        padding: 12px 15px;
        border: 1px solid #ddd;
    }
    
    table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    
    table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    
    table tbody tr:hover {
        background-color: #e8f5e9;
        cursor: pointer;
    }
    
    table a {
        color: #1976D2;
        text-decoration: none;
        font-weight: 500;
    }
    
    table a:hover {
        text-decoration: underline;
        color: #0D47A1;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Gemini client
@st.cache_resource
def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return genai.Client(api_key=api_key)

def generate_travel_plan(origin, destination, start_date, end_date, budget, currency, preferences, num_travelers=1):
    """Generate travel plan using Gemini with Google Search grounding"""
    client = get_gemini_client()
    
    # Configure grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    
    # Format dates for URLs
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    trip_duration = (end_date - start_date).days
    
    # Build preferences text
    pref_text = f"""
    **Travel Preferences:**
    - Number of Travelers: {num_travelers} {"person" if num_travelers == 1 else "people"}
    - Pace: {preferences['pace']}
    - Style: {preferences['style']}
    - Activities: {preferences['activities']}
    - Accommodation Type: {preferences['accommodation']}
    - Food Preference: {preferences['food']}
    """
    
    # Create detailed prompt with STRICT table formatting
    prompt = f"""
    I need help planning a trip with the following details:
    - Origin: {origin}
    - Destination: {destination}
    - Travel dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({trip_duration} days)
    - Number of Travelers: {num_travelers} {"person" if num_travelers == 1 else "people"}
    - Total Budget: {budget:,.2f} {currency} (for all {num_travelers} {"traveler" if num_travelers == 1 else "travelers"})
    
    {pref_text}
    
    **CRITICAL: You MUST format your response using MARKDOWN TABLES ONLY (pipe-separated format).**
    
    ## FLIGHTS
    
    | Airline | Departure | Arrival | Duration | Price ({currency}) | Booking Link |
    |---------|-----------|---------|----------|-------------------|--------------|
    
    Provide 3-5 flight options. Each row must have ALL columns filled with real data from Google Search.
    Use this booking link format: https://www.google.com/travel/flights?q=Flights%20from%20{origin.replace(' ', '%20')}%20to%20{destination.replace(' ', '%20')}%20on%20{start_date_str}
    
    ## HOTELS
    
    | Hotel Name | Rating | Price per Night ({currency}) | Total Cost ({currency}) | Location | Booking Link | Map Link |
    |------------|--------|------------------------------|------------------------|----------|--------------|----------|
    
    Provide 4-6 hotel options matching "{preferences['accommodation']}" preference. 
    **IMPORTANT: Prices should be for accommodation suitable for {num_travelers} {"person" if num_travelers == 1 else "people"} (consider room capacity and number of rooms needed).**
    Each row must have ALL columns filled.
    Booking link format: https://www.booking.com/searchresults.html?ss={destination.replace(' ', '+')}&checkin={start_date_str}&checkout={end_date_str}&group_adults={num_travelers}
    Map link format: https://www.google.com/maps/search/[Hotel+Name+{destination.replace(' ', '+')}]
    
    ## ITINERARY
    
    **IMPORTANT: Create a DETAILED HOUR-BY-HOUR schedule for each day with specific times, transportation, and food stops.**
    **NOTE: All costs should account for {num_travelers} {"person" if num_travelers == 1 else "people"} unless otherwise specified.**
    
    | Day | Date | Time | Activity Type | Activity/Location | Duration | Cost ({currency}) | Transportation | Notes | Map Link |
    |-----|------|------|---------------|-------------------|----------|-------------------|----------------|-------|----------|
    
    For EACH of the {trip_duration} days, create a detailed hour-by-hour itinerary following this structure:
    
    **Day 1 Example Format:**
    | 1 | {start_date.strftime('%B %d, %Y')} | 8:00 AM | Breakfast | [Restaurant Name] | 1 hour | [Amount] | Walk/Hotel | [Cuisine type] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 9:30 AM | Transportation | [From Hotel to Attraction] | 30 min | [Amount] | Taxi/Metro/Bus | [Route details] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 10:00 AM | Sightseeing | [Attraction Name] | 2 hours | [Amount] | - | [Brief description] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 12:00 PM | Transportation | [From Attraction to Restaurant] | 15 min | [Amount] | Walk/Metro | [Route] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 12:30 PM | Lunch | [Restaurant Name] | 1.5 hours | [Amount] | - | [Cuisine, specialties] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 2:00 PM | Transportation | [To next location] | 20 min | [Amount] | Bus/Metro | [Route] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 2:30 PM | Activity | [Activity Name] | 2 hours | [Amount] | - | [Details] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 4:30 PM | Coffee/Snack | [Cafe Name] | 45 min | [Amount] | Walk | [Type of place] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 5:30 PM | Transportation | [To dinner area] | 25 min | [Amount] | Metro/Taxi | [Route] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 6:00 PM | Shopping/Activity | [Location] | 1.5 hours | [Amount] | - | [Details] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 7:30 PM | Dinner | [Restaurant Name] | 2 hours | [Amount] | Walk | [Cuisine, must-try dishes] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 9:30 PM | Transportation | [Back to Hotel] | 30 min | [Amount] | Taxi/Metro | [Route] | [Map Link] |
    | 1 | {start_date.strftime('%B %d, %Y')} | 10:00 PM | Rest | Return to Hotel | - | - | - | End of day | - |
    
    **CRITICAL REQUIREMENTS for Itinerary:**
    1. Include specific times (e.g., 8:00 AM, not just "Morning")
    2. ALWAYS include transportation between locations with:
       - Mode of transport (Walk, Metro, Bus, Taxi, Train, etc.)
       - Estimated duration
       - Estimated cost
       - Route details in Notes
    3. Include ALL meal stops (Breakfast, Lunch, Dinner, Snacks/Coffee)
    4. For food stops, specify:
       - Restaurant/Cafe name
       - Type of cuisine
       - Recommended dishes in Notes
       - Estimated meal cost
    5. Activity Type must be one of: Breakfast, Lunch, Dinner, Coffee/Snack, Transportation, Sightseeing, Activity, Shopping, Rest
    6. Every location must have a Map Link
    7. Tailor to "{preferences['pace']}" pace:
       - Relaxed: More breaks, leisurely meals, 2-3 main activities per day
       - Moderate: 3-4 activities with reasonable breaks
       - Packed: 5+ activities, quick meals, maximize experiences
    8. Match "{preferences['style']}" style and "{preferences['activities']}" activities
    9. Consider "{preferences['food']}" food preference for restaurant selections
    
    After the itinerary table, provide daily summaries:
    **Day 1 Total: [Transportation: X {currency}] [Food: X {currency}] [Activities: X {currency}] [Daily Total: X {currency}]**
    **Day 2 Total: [Transportation: X {currency}] [Food: X {currency}] [Activities: X {currency}] [Daily Total: X {currency}]**
    (continue for all {trip_duration} days)
    
    ## BUDGET
    
    | Item | Amount ({currency}) |
    |------|---------------------|
    | Round-trip Flights | [Amount] |
    | Accommodation ({trip_duration} nights) | [Amount] |
    | Transportation (total all days) | [Amount] |
    | Food & Dining (total all days) | [Amount] |
    | Activities & Entrance Fees (total) | [Amount] |
    | Miscellaneous (10% buffer) | [Amount] |
    | **TOTAL ESTIMATED COST** | **[Amount]** |
    | **YOUR BUDGET** | **{budget:,.2f}** |
    | **DIFFERENCE** | **[Over/Under by amount]** |
    
    **CRITICAL RULES:**
    1. Use ONLY pipe-separated markdown tables (| column | column |)
    2. Include table headers with separator row (|-------|-------|)
    3. NO bullet points, NO numbered lists, NO other formats
    4. Every table cell must be filled
    5. All URLs must be complete https:// links
    6. All prices in {currency}
    7. Use Google Search for current, realistic prices
    8. Tailor ALL content to the travel preferences
    9. Create hour-by-hour detailed schedule with specific times
    10. Include transportation between every location change
    11. Include all meals (breakfast, lunch, dinner, snacks)
    """
    
    # Generate content with grounding
    response = client.models.generate_content(
        # model="gemini-2.0-flash-exp",
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    
    return response.text

def mask_url(text, link_text="🔗 Link"):
    """Convert raw URLs to masked markdown links"""
    # Pattern to match URLs
    url_pattern = r'(https?://[^\s\)]+)'
    
    # Replace URLs with masked links
    def replace_url(match):
        url = match.group(1)
        # Try to determine appropriate link text based on URL content
        if 'google.com/travel/flights' in url or 'flight' in url.lower():
            return f"[✈️ Book Flight]({url})"
        elif 'booking.com' in url or 'hotel' in url.lower() or 'agoda' in url:
            return f"[🏨 Book Hotel]({url})"
        elif 'google.com/maps' in url or 'maps' in url.lower():
            return f"[📍 View Map]({url})"
        else:
            return f"[{link_text}]({url})"
    
    # Only mask URLs that aren't already in markdown format
    # Don't mask if already in format [text](url)
    masked_text = re.sub(r'(?<!\]\()' + url_pattern, replace_url, text)
    return masked_text

def parse_markdown_table(table_text):
    """Parse a markdown table into a pandas DataFrame"""
    lines = [line.strip() for line in table_text.strip().split('\n') if line.strip()]
    
    if len(lines) < 3:  # Need at least header, separator, and one data row
        return None
    
    # Extract headers
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    
    # Extract data rows (skip separator line at index 1)
    data = []
    for line in lines[2:]:  # Skip header and separator
        if '|' in line:
            row = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(row) == len(headers):  # Only add rows with correct column count
                data.append(row)
    
    if data:
        df = pd.DataFrame(data, columns=headers)
        
        # Convert markdown links to HTML in all columns
        for col in df.columns:
            df[col] = df[col].apply(convert_markdown_links_to_html)
        
        return df
    return None

def convert_markdown_links_to_html(text):
    """Convert markdown links [text](url) to HTML clickable links"""
    if pd.isna(text):
        return text
    
    # Pattern to match markdown links: [text](url)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}" target="_blank">{link_text}</a>'
    
    return re.sub(pattern, replace_link, str(text))

def parse_and_display_travel_plan(travel_plan, currency, trip_duration, start_date):
    """Parse and beautifully display the travel plan with tables and organized sections"""
    
    # Store all dataframes for Excel export
    all_dataframes = {}
    
    # Mask all URLs in the travel plan
    travel_plan = mask_url(travel_plan)
    
    # Display with better formatting
    sections = travel_plan.split('##')
    
    for section in sections:
        if not section.strip():
            continue
        
        # Get the section title (first line)
        section_lines = section.strip().split('\n')
        section_title = section_lines[0].strip().upper() if section_lines else ""
        
        # Check section type based on title only
        if 'FLIGHT' in section_title:
            st.header("✈️ Flight Options")
            
            # Try to extract markdown table
            table_match = re.search(r'\|.*\|.*\n\|[-\s|]+\n(\|.*\n)+', section, re.MULTILINE)
            if table_match:
                df_flights = parse_markdown_table(table_match.group(0))
                if df_flights is not None and not df_flights.empty:
                    # Display as HTML table for clickable links (single display)
                    st.markdown(df_flights.to_html(escape=False, index=False), unsafe_allow_html=True)
                    all_dataframes['Flights'] = df_flights
                else:
                    st.markdown(section)
            else:
                st.markdown(section)
            
        elif 'HOTEL' in section_title:
            st.header("🏨 Hotel Recommendations")
            
            # Try to extract markdown table
            table_match = re.search(r'\|.*\|.*\n\|[-\s|]+\n(\|.*\n)+', section, re.MULTILINE)
            if table_match:
                df_hotels = parse_markdown_table(table_match.group(0))
                if df_hotels is not None and not df_hotels.empty:
                    st.markdown(df_hotels.to_html(escape=False, index=False), unsafe_allow_html=True)
                    all_dataframes['Hotels'] = df_hotels
                else:
                    st.markdown(section)
            else:
                st.markdown(section)
            
        elif 'ITINERARY' in section_title:
            st.header("📅 Detailed Daily Itinerary")
            
            # Add custom CSS for better itinerary display (apply once)
            st.markdown("""
            <style>
                .itinerary-table {
                    font-size: 13px;
                }
                .itinerary-table td {
                    padding: 10px 12px;
                    vertical-align: top;
                }
                .time-col {
                    font-weight: bold;
                    color: #1976D2;
                    white-space: nowrap;
                }
                .transport-row {
                    background-color: #E3F2FD !important;
                }
                .food-row {
                    background-color: #FFF3E0 !important;
                }
                .activity-row {
                    background-color: #F1F8E9 !important;
                }
                .day-header {
                    background-color: #4CAF50;
                    color: white;
                    padding: 15px;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                    font-size: 18px;
                    font-weight: bold;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Try to extract markdown table
            table_match = re.search(r'\|.*\|.*\n\|[-\s|]+\n(\|.*\n)+', section, re.MULTILINE)
            if table_match:
                df_itinerary = parse_markdown_table(table_match.group(0))
                if df_itinerary is not None and not df_itinerary.empty:
                    # Group by day for display
                    if 'Day' in df_itinerary.columns:
                        unique_days = df_itinerary['Day'].unique()
                        for day in unique_days:
                            day_data = df_itinerary[df_itinerary['Day'] == day].copy()
                            date_val = day_data['Date'].iloc[0] if 'Date' in day_data.columns else ""
                            
                            # Display day header
                            st.markdown(f'<div class="day-header">📆 Day {day} - {date_val}</div>', unsafe_allow_html=True)
                            
                            # Create table for this day
                            display_html = '<div class="itinerary-table">'
                            display_html += '<table style="width:100%; border-collapse: collapse; margin-bottom: 20px;">'
                            
                            # Custom headers (exclude Day and Date columns)
                            display_html += '<thead><tr style="background-color: #4CAF50; color: white;">'
                            for col in day_data.columns:
                                if col not in ['Day', 'Date']:
                                    display_html += f'<th style="padding: 12px; border: 1px solid #ddd;">{col}</th>'
                            display_html += '</tr></thead><tbody>'
                            
                            # Add rows with color coding
                            for idx, row in day_data.iterrows():
                                activity_type = str(row.get('Activity Type', '')).lower()
                                
                                # Determine row color based on activity type
                                row_class = ''
                                if 'transport' in activity_type:
                                    row_class = 'transport-row'
                                elif any(meal in activity_type for meal in ['breakfast', 'lunch', 'dinner', 'coffee', 'snack']):
                                    row_class = 'food-row'
                                else:
                                    row_class = 'activity-row'
                                
                                display_html += f'<tr class="{row_class}">'
                                for col in day_data.columns:
                                    if col not in ['Day', 'Date']:
                                        cell_value = str(row[col]) if pd.notna(row[col]) else '-'
                                        # Add special styling for time column
                                        if col == 'Time':
                                            display_html += f'<td class="time-col" style="border: 1px solid #ddd;">{cell_value}</td>'
                                        else:
                                            display_html += f'<td style="border: 1px solid #ddd;">{cell_value}</td>'
                                display_html += '</tr>'
                            
                            display_html += '</tbody></table></div>'
                            st.markdown(display_html, unsafe_allow_html=True)
                            
                            # Look for daily total in text after table
                            day_total_pattern = rf'\*\*Day {day} Total:?\s*([^\*\n]+)'
                            total_match = re.search(day_total_pattern, section, re.IGNORECASE)
                            if total_match:
                                total_text = total_match.group(1).strip()
                                st.info(f"💵 {total_text}")
                            
                            # Add a divider between days
                            st.markdown("---")
                        
                        all_dataframes['Itinerary'] = df_itinerary
                    else:
                        st.markdown(df_itinerary.to_html(escape=False, index=False), unsafe_allow_html=True)
                        all_dataframes['Itinerary'] = df_itinerary
                else:
                    st.markdown(section)
            else:
                st.markdown(section)
                    
        elif 'BUDGET' in section_title:
            st.header("💰 Budget Breakdown")
            
            # Try to extract markdown table
            table_match = re.search(r'\|.*\|.*\n\|[-\s|]+\n(\|.*\n)+', section, re.MULTILINE)
            if table_match:
                df_budget = parse_markdown_table(table_match.group(0))
                if df_budget is not None and not df_budget.empty:
                    st.markdown(df_budget.to_html(escape=False, index=False), unsafe_allow_html=True)
                    all_dataframes['Budget'] = df_budget
                else:
                    st.markdown(section)
            else:
                st.markdown(section)
                
        elif 'DESTINATION MAP' in section_title or 'MAP' in section_title:
            st.header("🗺️ Destination Map")
            st.markdown(section)
            
        else:
            # Display other sections normally
            if section.strip():
                st.markdown(section)
    
    return all_dataframes

def create_excel_export(dataframes, destination):
    """Create an Excel file with multiple sheets from dataframes"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output

# App Header
st.title("✈️ FreeWen - Your Travel AI Companion")
st.markdown("Plan your perfect trip with AI-powered insights and real-time search")

# Sidebar for session management
with st.sidebar:
    # Display logo
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
        st.markdown("---")
    
    st.header("📋 Travel Sessions")
    
    # New session button
    if st.button("➕ New Travel Plan", use_container_width=True, type="primary"):
        st.session_state.session_counter += 1
        new_session = {
            'id': st.session_state.session_counter,
            'name': f"Trip {st.session_state.session_counter}",
            'origin': '',
            'destination': '',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'currency': 'PHP',
            'budget': 100000.0,
            'num_travelers': 1,
            'pace': 'Moderate',
            'style': 'Balanced Mix',
            'activities': ['Cultural & Historical Sites', 'Food & Dining'],
            'custom_activities': [],  # Store user-added custom activities
            'accommodation': 'Mid-range Hotels',
            'food': 'Mix of Local & International',
            'travel_plan': None,
            'dataframes': None,
            'bookings': []  # Store uploaded bookings and tickets
        }
        st.session_state.travel_sessions.append(new_session)
        st.session_state.active_session = new_session['id']
        st.rerun()
    
    st.markdown("---")
    
    # Display existing sessions
    if st.session_state.travel_sessions:
        st.subheader("Your Travel Plans")
        
        for session in st.session_state.travel_sessions:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Session name (editable)
                session_label = f"{session['name']}"
                if session['destination']:
                    session_label += f" - {session['destination']}"
                
                if st.button(
                    session_label,
                    key=f"session_{session['id']}",
                    use_container_width=True,
                    type="primary" if st.session_state.active_session == session['id'] else "secondary"
                ):
                    st.session_state.active_session = session['id']
                    st.rerun()
            
            with col2:
                # Delete session button
                if st.button("🗑️", key=f"delete_{session['id']}", help="Delete this travel plan"):
                    st.session_state.travel_sessions = [s for s in st.session_state.travel_sessions if s['id'] != session['id']]
                    if st.session_state.active_session == session['id']:
                        st.session_state.active_session = st.session_state.travel_sessions[0]['id'] if st.session_state.travel_sessions else None
                    st.rerun()
    else:
        st.info("👆 Click 'New Travel Plan' to start planning your trip!")
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Create multiple travel plans
    - Compare different destinations
    - Switch between sessions easily
    - Export each plan to Excel
    """)

# Main content area
if st.session_state.active_session:
    # Get active session data
    active_session = next((s for s in st.session_state.travel_sessions if s['id'] == st.session_state.active_session), None)
    
    if active_session:
        # Create fixed map panel HTML with Streamlit toggle button
        if active_session['destination']:
            destination_encoded = active_session['destination'].replace(' ', '+')
            origin_encoded = active_session['origin'].replace(' ', '+') if active_session['origin'] else ''
            
            # Initialize map location
            if 'map_location' not in active_session:
                active_session['map_location'] = active_session['destination']
            
            current_map_location = active_session.get('map_location', active_session['destination'])
            current_map_encoded = current_map_location.replace(' ', '+')
            
            # Panel visibility class
            panel_class = "" if st.session_state.map_visible else "hidden"
            
            # Create the simplified map panel (just the map)
            map_html = f"""
            <style>
                /* Apply content width adjustment */
                section.main > div {{
                    padding-right: {'20px' if not st.session_state.map_visible else '420px'} !important;
                }}
            </style>
            
            <div class="map-panel {panel_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0;">🗺️ Travel Map</h3>
                </div>
                <iframe
                    width="100%"
                    height="500"
                    frameborder="0"
                    style="border:0; border-radius: 8px; display: block;"
                    src="https://maps.google.com/maps?q={current_map_encoded}&t=&z=13&ie=UTF8&iwloc=&output=embed"
                    allowfullscreen>
                </iframe>
                <p style="font-size: 12px; color: #666; margin: 10px 0; text-align: center;">� {current_map_location}</p>
            </div>
            """
            st.markdown(map_html, unsafe_allow_html=True)
            
            # Add close/open button inside the map panel or as a floating button
            if st.session_state.map_visible:
                # Close button inside map panel
                st.markdown("""
                <style>
                    div[data-testid="column"]:has(button[key*="close_map"]) {
                        position: fixed !important;
                        right: 20px !important;
                        top: 90px !important;
                        z-index: 1000 !important;
                        width: auto !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                

                if st.button("✖️", key=f"close_map_{active_session['id']}", help="Close map panel", type="secondary"):
                    st.session_state.map_visible = False
                    st.rerun()
            else:
                # Show open button when map is hidden
                st.markdown("""
                <style>
                    div[data-testid="column"]:has(button[key*="open_map"]) {
                        position: fixed !important;
                        right: 20px !important;
                        top: 90px !important;
                        z-index: 1000 !important;
                        width: auto !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                col_spacer, col_open = st.columns([20, 1])
                with col_open:
                    if st.button("🗺️", key=f"open_map_{active_session['id']}", help="Open map panel", type="primary"):
                        st.session_state.map_visible = True
                        st.rerun()
        
        st.subheader(f"📝 {active_session['name']}")
        
        # Rename session option
        col1, col2 = st.columns([3, 1])
        with col1:
            new_name = st.text_input("Rename this travel plan:", value=active_session['name'], key=f"rename_{active_session['id']}")
            if new_name != active_session['name']:
                active_session['name'] = new_name
        
        st.markdown("---")
        
        # Create tabs for different sections
        tab1, tab2 = st.tabs(["� Trip Planning", "🎫 Bookings & Tickets"])
        
        with tab1:
            # Trip Details Section
            st.header("🗺️ Trip Details")
            
            col1, col2 = st.columns(2)
            with col1:
                origin = st.text_input(
                    "Origin City",
                    value=active_session['origin'],
                    placeholder="e.g., Manila, Philippines",
                    help="Where are you traveling from?",
                    key=f"origin_{active_session['id']}"
                )
                active_session['origin'] = origin
                    
            with col2:
                destination = st.text_input(
                    "Destination City",
                    value=active_session['destination'],
                    placeholder="e.g., Tokyo, Japan",
                    help="Where do you want to go?",
                    key=f"destination_{active_session['id']}"
                )
                active_session['destination'] = destination
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=active_session['start_date'],
                    help="When do you want to leave?",
                    key=f"start_{active_session['id']}"
                )
                active_session['start_date'] = start_date
                
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=active_session['end_date'],
                    help="When do you want to return?",
                    key=f"end_{active_session['id']}"
                )
                active_session['end_date'] = end_date
            
            with col3:
                # Initialize num_travelers if not exists
                if 'num_travelers' not in active_session:
                    active_session['num_travelers'] = 1
                
                num_travelers = st.number_input(
                    "Number of Travelers",
                    min_value=1,
                    max_value=20,
                    value=active_session['num_travelers'],
                    step=1,
                    help="How many people are traveling?",
                    key=f"num_travelers_{active_session['id']}"
                )
                active_session['num_travelers'] = num_travelers
            
            with col4:
                currency = st.selectbox(
                    "Currency",
                    options=["PHP", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "SGD", "HKD", "CNY"],
                    index=["PHP", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "SGD", "HKD", "CNY"].index(active_session['currency']),
                    help="Choose your preferred currency",
                    key=f"currency_{active_session['id']}"
                )
                active_session['currency'] = currency
            
            with col5:
                budget = st.number_input(
                    f"Budget ({currency})",
                    min_value=0.0,
                    value=float(active_session['budget']) if currency == active_session['currency'] else (100000.0 if currency == "PHP" else 2000.0),
                    step=1000.0 if currency == "PHP" else 100.0,
                    help="Total budget for your trip",
                    key=f"budget_{active_session['id']}"
                )
                active_session['budget'] = budget
            
            st.markdown("---")
            
            # Travel Preferences Section
            st.header("⚙️ Travel Preferences")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pace = st.select_slider(
                    "Travel Pace",
                    options=["Relaxed/Chill", "Moderate", "Packed/Adventure"],
                    value=active_session['pace'],
                    help="How do you want to spend your time?",
                    key=f"pace_{active_session['id']}"
                )
                active_session['pace'] = pace
                
                style = st.radio(
                    "Travel Style",
                    options=["Nature & Outdoors", "City & Culture", "Balanced Mix"],
                    index=["Nature & Outdoors", "City & Culture", "Balanced Mix"].index(active_session['style']),
                    help="What type of experiences do you prefer?",
                    key=f"style_{active_session['id']}"
                )
                active_session['style'] = style
            
            with col2:
                # Initialize custom activities if not exists
                if 'custom_activities' not in active_session:
                    active_session['custom_activities'] = []
                
                # Combine default and custom activities for options
                default_activities = [
                    "Adventure Sports",
                    "Cultural & Historical Sites",
                    "Food & Dining",
                    "Shopping",
                    "Photography",
                    "Nightlife",
                    "Wellness & Spa",
                    "Beach & Water Activities",
                    "Art & Museums",
                    "Local Experiences"
                ]
                
                all_activities = default_activities + active_session['custom_activities']
                
                activities = st.multiselect(
                    "Preferred Activities",
                    options=all_activities,
                    default=active_session['activities'],
                    help="Select all that interest you",
                    key=f"activities_{active_session['id']}"
                )
                active_session['activities'] = activities
                
                # Add custom activity input
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    custom_activity = st.text_input(
                        "Add custom activity",
                        placeholder="e.g., Wine Tasting, Scuba Diving...",
                        key=f"custom_activity_{active_session['id']}",
                        label_visibility="collapsed"
                    )
                with col_b:
                    if st.button("➕ Add", key=f"add_activity_{active_session['id']}", use_container_width=True):
                        if custom_activity and custom_activity.strip():
                            if custom_activity.strip() not in all_activities:
                                active_session['custom_activities'].append(custom_activity.strip())
                                active_session['activities'].append(custom_activity.strip())
                                st.rerun()
                            else:
                                st.warning("Activity already exists!")
            
            with col3:
                accommodation = st.selectbox(
                    "Accommodation Type",
                    options=["Budget Hostels", "Mid-range Hotels", "Luxury Hotels", "Boutique Hotels", "Vacation Rentals/Airbnb"],
                    index=["Budget Hostels", "Mid-range Hotels", "Luxury Hotels", "Boutique Hotels", "Vacation Rentals/Airbnb"].index(active_session['accommodation']),
                    help="What type of accommodation do you prefer?",
                    key=f"accommodation_{active_session['id']}"
                )
                active_session['accommodation'] = accommodation
            
            food = st.selectbox(
                "Food Preference",
                options=["Street Food & Local Eats", "Mix of Local & International", "Fine Dining", "Vegetarian/Vegan", "No Preference"],
                index=["Street Food & Local Eats", "Mix of Local & International", "Fine Dining", "Vegetarian/Vegan", "No Preference"].index(active_session['food']),
                help="What's your dining style?",
                key=f"food_{active_session['id']}"
            )
            active_session['food'] = food
            
            st.markdown("---")
            
            # Generate button
            generate_btn = st.button("🔍 Generate Travel Plan", type="primary", use_container_width=False, key=f"generate_{active_session['id']}")
            
            # Main content area for results
            if generate_btn:
                # Validation
                if not origin or not destination:
                    st.error("⚠️ Please enter both origin and destination cities.")
                elif start_date >= end_date:
                    st.error("⚠️ End date must be after start date.")
                elif budget <= 0:
                    st.error("⚠️ Please enter a valid budget.")
                else:
                    # Calculate trip duration
                    trip_duration = (end_date - start_date).days
                    
                    # Prepare preferences
                    preferences = {
                        'pace': pace,
                        'style': style,
                        'activities': ', '.join(activities) if activities else 'General sightseeing',
                        'accommodation': accommodation,
                        'food': food
                    }
                    
                    # Display trip summary
                    st.info(f"**Trip Summary**: {origin} → {destination} | {trip_duration} days | Budget: {budget:,.2f} {currency}")
                    
                    # Display preferences summary
                    with st.expander("✨ Your Travel Preferences", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Pace:** {pace}")
                            st.write(f"**Style:** {style}")
                            st.write(f"**Accommodation:** {accommodation}")
                        with col2:
                            st.write(f"**Food:** {food}")
                            st.write(f"**Activities:** {preferences['activities']}")
                    
                    # Add Google Maps link for destination
                    maps_url = f"https://www.google.com/maps/search/{destination.replace(' ', '+')}"
                    st.markdown(f"🗺️ [View {destination} on Google Maps]({maps_url})")
                    
                    # Generate travel plan
                    with st.spinner("🤖 AI is searching and planning your perfect trip..."):
                        try:
                            travel_plan = generate_travel_plan(origin, destination, start_date, end_date, budget, currency, preferences, active_session['num_travelers'])
                            
                            st.success("✅ Your travel plan is ready!")
                            st.markdown("---")
                            
                            # Parse and display the travel plan beautifully
                            all_dataframes = parse_and_display_travel_plan(travel_plan, currency, trip_duration, start_date)
                            
                            # Store in session
                            active_session['travel_plan'] = travel_plan
                            active_session['dataframes'] = all_dataframes
                            
                            st.markdown("---")
                            
                            # Display Trip Summary at the end
                            if active_session['destination']:
                                trip_col1, trip_col2 = st.columns([2, 1])
                                
                                with trip_col1:
                                    st.markdown("### 📋 Trip Summary")
                                    summary_col1, summary_col2 = st.columns(2)
                                    with summary_col1:
                                        st.markdown(f"**🌍 Destination:** {active_session['destination']}")
                                        st.markdown(f"**📅 Duration:** {(active_session['end_date'] - active_session['start_date']).days} days")
                                        st.markdown(f"**👥 Travelers:** {active_session.get('num_travelers', 1)} {'person' if active_session.get('num_travelers', 1) == 1 else 'people'}")
                                    with summary_col2:
                                        st.markdown(f"**💰 Budget:** {active_session['budget']:,.0f} {active_session['currency']}")
                                        st.markdown(f"**✈️ Dates:** {active_session['start_date'].strftime('%b %d, %Y')} - {active_session['end_date'].strftime('%b %d, %Y')}")
                                
                                with trip_col2:
                                    st.markdown("### 🔗 Quick Links")
                                    destination_encoded = active_session['destination'].replace(' ', '+')
                                    origin_encoded = active_session['origin'].replace(' ', '+') if active_session['origin'] else ''
                                    
                                    st.markdown(f"[📍 View {active_session['destination']} on Maps](https://www.google.com/maps/search/{destination_encoded})")
                                    if origin_encoded:
                                        st.markdown(f"[🧭 Get Directions from {active_session['origin']}](https://www.google.com/maps/dir/{origin_encoded}/{destination_encoded})")
                            
                            st.markdown("---")
                            
                            # Excel download option
                            if all_dataframes:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col3:
                                    excel_data = create_excel_export(all_dataframes, destination)
                                    st.download_button(
                                        label="📊 Export to Excel",
                                        data=excel_data,
                                        file_name=f"FreeWen_{destination.replace(' ', '_')}_{start_date.strftime('%Y%m%d')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True,
                                        type="primary"
                                    )
                            else:
                                st.warning("⚠️ No tabular data available for export. The AI response may not have followed the table format.")
                            
                        except Exception as e:
                            st.error(f"❌ An error occurred: {str(e)}")
                            st.info("Please check your GEMINI_API_KEY in the .env file and try again.")
            
            # Display previously generated plan if exists
            elif active_session['travel_plan']:
                st.info("📄 Previously generated travel plan")
                
                trip_duration = (active_session['end_date'] - active_session['start_date']).days
                
                # Display preferences summary
                with st.expander("✨ Travel Preferences Used", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Pace:** {active_session['pace']}")
                        st.write(f"**Style:** {active_session['style']}")
                        st.write(f"**Accommodation:** {active_session['accommodation']}")
                    with col2:
                        st.write(f"**Food:** {active_session['food']}")
                        st.write(f"**Activities:** {', '.join(active_session['activities']) if active_session['activities'] else 'General sightseeing'}")
                
                st.markdown("---")
                
                # Display the saved plan
                all_dataframes = parse_and_display_travel_plan(
                    active_session['travel_plan'], 
                    active_session['currency'], 
                    trip_duration, 
                    active_session['start_date']
                )
                
                st.markdown("---")
                
                # Display Trip Summary at the end
                if active_session['destination']:
                    trip_col1, trip_col2 = st.columns([2, 1])
                    
                    with trip_col1:
                        st.markdown("### 📋 Trip Summary")
                        summary_col1, summary_col2 = st.columns(2)
                        with summary_col1:
                            st.markdown(f"**🌍 Destination:** {active_session['destination']}")
                            st.markdown(f"**📅 Duration:** {(active_session['end_date'] - active_session['start_date']).days} days")
                            st.markdown(f"**👥 Travelers:** {active_session.get('num_travelers', 1)} {'person' if active_session.get('num_travelers', 1) == 1 else 'people'}")
                        with summary_col2:
                            st.markdown(f"**💰 Budget:** {active_session['budget']:,.0f} {active_session['currency']}")
                            st.markdown(f"**✈️ Dates:** {active_session['start_date'].strftime('%b %d, %Y')} - {active_session['end_date'].strftime('%b %d, %Y')}")
                    
                    with trip_col2:
                        st.markdown("### 🔗 Quick Links")
                        destination_encoded = active_session['destination'].replace(' ', '+')
                        origin_encoded = active_session['origin'].replace(' ', '+') if active_session['origin'] else ''
                        
                        st.markdown(f"[📍 View {active_session['destination']} on Maps](https://www.google.com/maps/search/{destination_encoded})")
                        if origin_encoded:
                            st.markdown(f"[🧭 Get Directions from {active_session['origin']}](https://www.google.com/maps/dir/{origin_encoded}/{destination_encoded})")
                
                st.markdown("---")
                
                # Excel download option
                if all_dataframes:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col3:
                        excel_data = create_excel_export(all_dataframes, active_session['destination'])
                        st.download_button(
                            label="📊 Export to Excel",
                            data=excel_data,
                            file_name=f"FreeWen_{active_session['destination'].replace(' ', '_')}_{active_session['start_date'].strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary",
                            key=f"download_{active_session['id']}"
                        )
        
        with tab2:
            # Bookings & Tickets Section
            st.header("🎫 Bookings & Tickets")
            st.markdown("Upload and manage your flight bookings, hotel confirmations, activity tickets, and other travel documents here.")
            
            # Initialize bookings list if not exists
            if 'bookings' not in active_session:
                active_session['bookings'] = []
            
            # Upload section
            st.subheader("📤 Upload Documents")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                uploaded_files = st.file_uploader(
                    "Choose files to upload",
                    type=['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt'],
                    accept_multiple_files=True,
                    key=f"uploader_{active_session['id']}",
                    help="Upload your booking confirmations, tickets, vouchers, etc."
                )
            
            with col2:
                document_type = st.selectbox(
                    "Document Type",
                    options=["✈️ Flight Booking", "🏨 Hotel Confirmation", "🎟️ Activity Ticket", "🚗 Car Rental", "🚂 Train/Bus Ticket", "📄 Other"],
                    key=f"doc_type_{active_session['id']}"
                )
            
            document_notes = st.text_area(
                "Notes (optional)",
                placeholder="Add any notes about this booking...",
                key=f"notes_{active_session['id']}",
                height=100
            )
            
            if uploaded_files:
                if st.button("💾 Save Documents", type="primary", key=f"save_docs_{active_session['id']}"):
                    for uploaded_file in uploaded_files:
                        # Read file bytes
                        file_bytes = uploaded_file.read()
                        
                        # Create booking entry
                        booking = {
                            'id': len(active_session['bookings']) + 1,
                            'name': uploaded_file.name,
                            'type': document_type,
                            'size': len(file_bytes),
                            'file_type': uploaded_file.type,
                            'bytes': file_bytes,
                            'notes': document_notes,
                            'uploaded_date': datetime.now().strftime('%Y-%m-%d %H:%M')
                        }
                        
                        active_session['bookings'].append(booking)
                    
                    st.success(f"✅ {len(uploaded_files)} document(s) saved successfully!")
                    st.rerun()
            
            st.markdown("---")
            
            # Display saved bookings
            st.subheader("📚 Saved Documents")
            
            if active_session['bookings']:
                # Group by document type
                booking_types = {}
                for booking in active_session['bookings']:
                    doc_type = booking['type']
                    if doc_type not in booking_types:
                        booking_types[doc_type] = []
                    booking_types[doc_type].append(booking)
                
                # Display by category
                for doc_type, bookings_list in booking_types.items():
                    with st.expander(f"{doc_type} ({len(bookings_list)})", expanded=True):
                        for booking in bookings_list:
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            
                            with col1:
                                st.markdown(f"**📎 {booking['name']}**")
                                if booking['notes']:
                                    st.caption(booking['notes'])
                            
                            with col2:
                                st.caption(f"📅 {booking['uploaded_date']}")
                                st.caption(f"📦 {booking['size'] / 1024:.1f} KB")
                            
                            with col3:
                                # Download button
                                st.download_button(
                                    label="⬇️ Download",
                                    data=booking['bytes'],
                                    file_name=booking['name'],
                                    mime=booking['file_type'],
                                    key=f"download_booking_{active_session['id']}_{booking['id']}",
                                    use_container_width=True
                                )
                            
                            with col4:
                                # Delete button
                                if st.button("🗑️", key=f"delete_booking_{active_session['id']}_{booking['id']}", help="Delete this document"):
                                    active_session['bookings'] = [b for b in active_session['bookings'] if b['id'] != booking['id']]
                                    st.rerun()
                            
                            st.markdown("---")
                
                # Summary stats
                st.info(f"📊 Total documents: {len(active_session['bookings'])} | Total size: {sum(b['size'] for b in active_session['bookings']) / 1024:.1f} KB")
                
                # Bulk actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Clear All Documents", key=f"clear_all_{active_session['id']}", help="Delete all uploaded documents"):
                        active_session['bookings'] = []
                        st.rerun()
                
            else:
                st.info("📭 No documents uploaded yet. Use the upload section above to add your bookings and tickets.")

else:
    # Welcome message when no session is active
    st.markdown("""
    ### Welcome to FreeWen! 👋
    
    Your AI-powered travel companion that helps you plan the perfect trip.
    
    **How it works:**
    1. Click "➕ New Travel Plan" in the sidebar to start
    2. Enter your trip details and preferences
    3. Click "Generate Travel Plan"
    4. Get AI-generated recommendations for:
       - ✈️ Flight options
       - 🏨 Hotel recommendations
       - 📍 Daily itinerary
       - 💰 Budget breakdown
    
    **Features:**
    - 📋 Create multiple travel plans
    - 💾 Save and compare different trips
    - 📊 Export to Excel
    - 🔗 Clickable booking links
    
    **Powered by:**
    - 🤖 Google Gemini AI
    - 🔍 Real-time Google Search grounding
    
    Start planning your adventure now! 🌍
    """)
    
    # Display example trips
    st.markdown("### 💡 Popular Destinations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image("https://images.unsplash.com/photo-1502602898657-3e91760cbb34", use_container_width=True)
        st.caption("Paris, France")
    
    with col2:
        st.image("https://images.unsplash.com/photo-1513407030348-c983a97b98d8", use_container_width=True)
        st.caption("Tokyo, Japan")
    
    with col3:
        st.image("https://images.unsplash.com/photo-1523906834658-6e24ef2386f9", use_container_width=True)
        st.caption("Santorini, Greece")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ by FreeWen | Powered by Google Gemini AI</div>",
    unsafe_allow_html=True
)
