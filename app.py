import streamlit as st
import requests
from components import load_custom_css, render_telemetry_row, get_risk_theme, render_architecture_view

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="XGB-AeroSentinel",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded")

# Session state init
if "loc_query"         not in st.session_state: st.session_state.loc_query         = ""
if "candidates"        not in st.session_state: st.session_state.candidates        = []
if "selected_location" not in st.session_state: st.session_state.selected_location = None
if "analysis_data"     not in st.session_state: st.session_state.analysis_data     = None
if "search_results_cache" not in st.session_state: st.session_state.search_results_cache = []

def clear_search():
    st.session_state.loc_query         = ""
    st.session_state.candidates        = []
    st.session_state.selected_location = None
    st.session_state.analysis_data     = None
    st.session_state.search_results_cache = []
    
def back_to_results():
    st.session_state.candidates = st.session_state.search_results_cache
    st.session_state.selected_location = None
    st.session_state.analysis_data = None

load_custom_css()

# SIDEBAR
st.sidebar.title("☁️ XGB-AeroSentinel")
st.sidebar.caption("Meteorological Command Center")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

nav_choice = st.sidebar.radio("Navigation", ["Atmosphere Pulse", "Engine Architecture"])

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown("### System Telemetry")

api_status = ml_status = nlp_status = sync_status = "ERR"
try:
    res = requests.get(f"{API_URL}/health", timeout=5)
    if res.status_code == 200:
        api_status = ml_status = nlp_status = sync_status = "OK"
except Exception:
    pass

render_telemetry_row("API Gateway",            api_status)
render_telemetry_row("Risk Prediction Engine", ml_status)
render_telemetry_row("Entity Extraction",      nlp_status)
render_telemetry_row("Meteorological Stream",  sync_status)


# VIEW 1: ATMOSPHERE PULSE
if nav_choice == "Atmosphere Pulse":
    st.title("Aero-Risk Intelligence Hub")

    with st.form("radar_form", clear_on_submit=False):
        st.text_input(
            "Location Query",
            key="loc_query",
            placeholder="Search a city... (e.g., 'Oslo', 'Bengaluru')",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Search Location", type="primary")

    # STEP 1: Search submit hone pe  search call karo
    if submitted:
        if not st.session_state.loc_query.strip():
            st.warning("Query cannot be empty.")
        else:
            # Pehle sab reset karo
            st.session_state.candidates        = []
            st.session_state.selected_location = None
            st.session_state.analysis_data     = None

            with st.spinner("Searching locations..."):
                try:
                    res = requests.get(
                        f"{API_URL}/search",
                        params={"query": st.session_state.loc_query},
                        timeout=15
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if data["auto_selected"]:
                            st.session_state.selected_location = data["candidates"][0]
                            st.session_state.search_results_cache = [] # Single result me cache nahi chahiye
                        else:
                            st.session_state.candidates = data["candidates"]
                            st.session_state.search_results_cache = data["candidates"] # Cache me data save karo
                    else:
                        try:
                            err = res.json().get("detail", res.text)
                        except Exception:
                            err = res.text
                        st.error(f"Engine Fault: {err}")
                except requests.exceptions.ConnectionError:
                    st.error("API Gateway Unreachable. Verify backend is running.")
                except Exception as e:
                    st.error(f"Critical Exception: {e}")

    # STEP 2: Multiple results hain to selection UI dikhao
    if st.session_state.candidates:
        st.markdown(f"""
            <div class="glass-card" style="height:auto;margin-bottom:20px;">
                <h3 style="margin-top:0;color:#FFFFFF;font-size:1.1rem;
                           border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:10px;">
                     {len(st.session_state.candidates)} locations found — select one:
                </h3>
            </div>""", unsafe_allow_html=True)

        for i, c in enumerate(st.session_state.candidates):
            label = f"📍  {c['name']}"
            if c.get("admin1"):   label += f",  {c['admin1']}"
            if c.get("country"):  label += f"  —  {c['country']}"
            if st.button(label, key=f"loc_{i}", use_container_width=True):
                st.session_state.selected_location = c
                st.session_state.candidates        = []
                st.rerun()

    # STEP 3: If Location select call analyze
    if st.session_state.selected_location and st.session_state.analysis_data is None:
        c = st.session_state.selected_location
        city_display = c["name"]
        if c.get("admin1"):  city_display += f", {c['admin1']}"
        if c.get("country"): city_display += f", {c['country']}"

        with st.spinner("Analyzing atmospheric conditions..."):
            try:
                res = requests.post(
                    f"{API_URL}/analyze",
                    params={
                        "query":     st.session_state.loc_query,
                        "latitude":  c["latitude"],
                        "longitude": c["longitude"],
                        "timezone":  c.get("timezone", "UTC"),
                        "city":      city_display,
                    },
                    timeout=65
                )
                if res.status_code == 200:
                    st.session_state.analysis_data = res.json()
                else:
                    try:
                        err = res.json().get("detail", res.text)
                    except Exception:
                        err = res.text
                    st.error(f"Engine Fault: {err}")
            except requests.exceptions.ConnectionError:
                st.error("API Gateway Unreachable. Verify backend is running.")
            except Exception as e:
                st.error(f"Critical Exception: {e}")

    # STEP 4: if we have Analysis data then  renderr
    if st.session_state.analysis_data:
        data   = st.session_state.analysis_data
        loc    = data["location"]
        w      = data["weather"]
        aq     = data["air_quality"]
        assess = data["assessment"]

        st.markdown(
            f"<p style='color:#FFFFFF;font-weight:500;margin-bottom:20px;"
            f"border-bottom:1px solid rgba(255,255,255,0.2);padding-bottom:10px;'>"
            f"📍 {loc['city']} (Local Time: {data['times']['local']})</p>",
            unsafe_allow_html=True
        )

        heat_index = round(w['temperature_c'] * (w['humidity_pct'] / 100.0), 1)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="glass-card">
                <h3 style="margin-top:0;border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:10px;">Meteorological Data</h3>
                <div class="data-row"><span class="data-label">Temperature</span>
                    <span class="data-value">{w['temperature_c']}°C <span style="font-size:0.8rem;color:#B9D6E8;">(Max: {w['temp_max_c']}°C)</span></span></div>
                <div class="data-row"><span class="data-label">Humidity</span>
                    <span class="data-value">{w['humidity_pct']}%</span></div>
                <div class="data-row"><span class="data-label">Heat Index Proxy</span>
                    <span class="data-value">{heat_index}</span></div>
                <div class="data-row"><span class="data-label">Wind Speed</span>
                    <span class="data-value">{w['wind_speed_kmh']} km/h</span></div>
                <div class="data-row"><span class="data-label">Precipitation</span>
                    <span class="data-value">{w['precipitation_mm']} mm</span></div>
                <div class="card-footer">{assess['meteorology_summary']}</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            extra_pollutants = ""
            if aq.get('pm25_ugm3'):
                extra_pollutants += f'<div class="data-row"><span class="data-label">PM2.5</span><span class="data-value">{aq["pm25_ugm3"]} µg/m³</span></div>'
            if aq.get('o3_ugm3'):
                extra_pollutants += f'<div class="data-row"><span class="data-label">Ozone</span><span class="data-value">{aq["o3_ugm3"]} µg/m³</span></div>'
            if not extra_pollutants:
                extra_pollutants = '<div class="data-row"><span class="data-label">-</span><span class="data-value">-</span></div>'

            st.markdown(f"""
            <div class="glass-card">
                <h3 style="margin-top:0;border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:10px;">Air Toxicity (AQI)</h3>
                <div class="data-row"><span class="data-label">AQI</span>
                    <span class="data-value">{aq['us_aqi']} ({aq['aqi_label']})</span></div>
                <div class="data-row"><span class="data-label">Dominant Pollutant</span>
                    <span class="data-value">{aq['dominant_pollutant']}</span></div>
                <div class="data-row"><span class="data-label">Trend</span>
                    <span class="data-value">{aq['trend']}</span></div>
                {extra_pollutants}
                <div class="card-footer">{assess['air_toxicity_summary']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        theme = get_risk_theme(assess["final_risk"])
        st.markdown(f"""
            <div style="background:{theme['bg']};backdrop-filter:blur(12px);
                        border:1px solid {theme['border']};border-radius:12px;
                        padding:25px;text-align:center;margin-bottom:20px;">
                <h1 style="color:{theme['color']} !important;margin:0;
                           text-transform:uppercase;letter-spacing:2px;">
                    OVERALL STATUS: {assess['final_risk']}
                </h1>
                <p style="margin:5px 0 0 0;color:#E0F2FE;font-size:1.1rem;">
                    Composite Score: <span style="color:#FFFFFF;font-weight:bold;">
                    {assess['composite_score']}/100</span> ({assess['composite_grade']})
                </p>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
            <div class="glass-card" style="height:auto;margin-bottom:20px;border-left:5px solid {theme['color']};">
                <h3 style="margin-top:0;color:#FFFFFF;font-size:1.2rem;">System Verdict</h3>
                <div style="font-size:1.05rem;color:#E0F2FE;font-weight:500;line-height:1.6;">
                    {assess['final_verdict']}
                </div>
            </div>""", unsafe_allow_html=True)

        advisory_html = "".join(
            [f"<li style='margin-bottom:8px;'>{item}</li>" for item in data["advisory"]]
        )
        st.markdown(f"""
            <div class="glass-card" style="height:auto;margin-bottom:30px;">
                <h3 style="margin-top:0;color:#FFFFFF;font-size:1.2rem;
                           border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:10px;">
                    Actionable Advisory</h3>
                <ul style="color:#B9D6E8;line-height:1.6;margin-left:20px;padding-top:10px;">
                    {advisory_html}
                </ul>
            </div>""", unsafe_allow_html=True)

        if data.get("news"):
            news_html = "".join([
                f"<li style='margin-bottom:18px;border-bottom:1px solid rgba(255,255,255,0.07);padding-bottom:14px;'>"
                f"<a href='{item['link']}' target='_blank' style='color:#A7F3D0;text-decoration:none;"
                f"font-weight:600;font-size:0.97rem;line-height:1.4;display:block;margin-bottom:4px;"
                f"transition:color 0.2s;' onmouseover=\"this.style.color='#FFFFFF'\" "
                f"onmouseout=\"this.style.color='#A7F3D0'\">{item['title']}</a>"
                f"<span style='font-size:0.83rem;color:#CBD5E1;line-height:1.5;display:block;margin-bottom:5px;'>"
                f"{item.get('description', 'Click to read the full article.')}</span>"
                f"<span style='font-size:0.78rem;color:#7DD3FC;'>🕒 {item['published_at']}</span>"
                f"</li>"
                for item in data["news"]
            ])
            st.markdown(f"""
                <div class="glass-card" style="height:auto;margin-bottom:30px;">
                    <h3 style="margin-top:0;color:#FFFFFF;font-size:1.2rem;
                               border-bottom:1px solid rgba(255,255,255,0.15);padding-bottom:10px;">
                        Local Weather Intel</h3>
                    <ul style="list-style-type:none;padding-left:0;margin-top:15px;">
                        {news_html}
                    </ul>
                </div>""", unsafe_allow_html=True)

        _, col_center, _ = st.columns([4, 2, 4])
        with col_center:
            # Agar cache me 1 se zyada results hain, tabhi "Back to Results" dikhao
            if len(st.session_state.get("search_results_cache", [])) > 1:
                st.button("Back to Results", type="secondary",
                          on_click=back_to_results, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True) # Thoda space dene ke liye
                
            st.button("Clear Search", type="secondary",
                      on_click=clear_search, use_container_width=True)

# VIEW 2: ENGINE ARCHITECTURE
elif nav_choice == "Engine Architecture":
    render_architecture_view()