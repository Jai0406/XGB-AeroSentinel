import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="XGB-AeroSentinel",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "loc_query" not in st.session_state:
    st.session_state.loc_query = ""

def clear_search():
    st.session_state.loc_query = ""

# CSS

st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0B2B40 0%, #136A8A 100%) !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 2rem !important; max-width: 1200px; }

    [data-testid="stSidebar"] {
        background: rgba(11, 43, 64, 0.6) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="collapsedControl"] button {
        background: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        transition: background 0.25s ease, box-shadow 0.25s ease !important;
    }
    [data-testid="stSidebarCollapseButton"] button svg,
    [data-testid="collapsedControl"] button svg,
    [data-testid="stSidebarCollapseButton"] button svg *,
    [data-testid="collapsedControl"] button svg * {
        stroke: #FFFFFF !important;
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="collapsedControl"] button:hover {
        background: rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.35), 0 0 20px rgba(255, 255, 255, 0.15) !important;
    }

    h1, h2, h3 { color: #FFFFFF !important; font-weight: 400; letter-spacing: 0.5px; }
    p, span, div, li { color: #E0F2FE; }

    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        -webkit-text-fill-color: #000000 !important;
    }
    div[data-baseweb="input"] input::placeholder {
        color: rgba(0, 0, 0, 0.5) !important;
        -webkit-text-fill-color: rgba(0, 0, 0, 0.5) !important;
    }

    [data-testid="stFormSubmitButton"] button[kind="primary"] {
        width: 100%;
        border-radius: 8px !important;
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
        letter-spacing: 1px;
        font-weight: 500;
        transition: background 0.3s, box-shadow 0.3s;
    }
    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }

    button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px !important;
        padding: 0.3rem 1rem !important;
        min-height: 35px !important;
        transition: background 0.3s;
        box-shadow: none !important;
    }
    button[kind="secondary"] * {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    button[kind="secondary"]:hover {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }
    button[kind="secondary"]:focus,
    button[kind="secondary"]:active { box-shadow: none !important; }

    .glass-card {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: background 0.3s, border-color 0.3s;
    }
    .glass-card:hover {
        background-color: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.3);
    }

    .arch-card {
        background-color: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        transition: background 0.3s, border-color 0.3s;
    }
    .arch-card:hover {
        background-color: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .data-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .data-row:last-child { border-bottom: none; }
    .data-label  { font-size: 0.95rem; color: #B9D6E8; }
    .data-value  { font-size: 1.05rem; font-weight: 500; color: #FFFFFF; text-align: right; }

    .card-footer {
        margin-top: auto;
        padding-top: 15px;
        border-top: 1px dashed rgba(255, 255, 255, 0.15);
        font-size: 0.85rem;
        color: #B9D6E8;
        line-height: 1.4;
    }

    code {
        color: #A7F3D0 !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)


# UTILS & HELPERS

def render_telemetry_row(name: str, status: str):
    color = "#E6F0F9" if status == "OK" else "#FFB3B3"
    st.sidebar.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:6px 0;font-family:'Inter',sans-serif;font-size:13px;
                    border-bottom:1px solid rgba(255,255,255,0.1);">
            <span style="color:#B9D6E8;">{name}</span>
            <span style="color:{color};font-weight:600;">{status}</span>
        </div>
    """, unsafe_allow_html=True)

def get_risk_theme(risk_label: str):
    if "SAFE"     in risk_label: return {"color": "#10B981", "bg": "rgba(16,185,129,0.15)",  "border": "#10B981"}
    if "MODERATE" in risk_label: return {"color": "#F59E0B", "bg": "rgba(245,158,11,0.15)",  "border": "#F59E0B"}
    return                               {"color": "#EF4444", "bg": "rgba(239,68,68,0.20)",   "border": "#EF4444"}



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
            placeholder="Search a city... (e.g., 'Oslo','Bengaluru')",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Search Location", type="primary")

    # result_area wraps ALL output — old content saaf ho jaata hai har naye submit pe
    result_area = st.container()

    if submitted:
        with result_area:
            if not st.session_state.loc_query.strip():
                st.warning("Query cannot be empty.")
            else:
                with st.spinner("Analyzing atmospheric conditions..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/analyze",
                            params={"query": st.session_state.loc_query},
                            timeout=65
                        )
                        if res.status_code == 200:
                            data   = res.json()
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

                            _, col_center, _ = st.columns([4, 2, 4])
                            with col_center:
                                st.button("Clear Search", type="secondary",
                                          on_click=clear_search, use_container_width=True)
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

# VIEW 2: ENGINE ARCHITECTURE

elif nav_choice == "Engine Architecture":
    st.title("System Engineering & Architecture")
    st.markdown("### Weather Health Assessment Pipeline")
    st.markdown(
        "<p style='font-size:1.1rem;color:#B9D6E8;margin-bottom:25px;'>"
        "A highly optimized meteorological risk assessment API leveraging state-of-the-art NLP entity "
        "extraction, real-time data syncs, and an Extreme Gradient Boosting (XGBoost) inference engine.</p>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="arch-card">
        <h4 style="margin-top:0;color:#FFFFFF;">1. Predictive Risk Engine (XGBoost Sentinel)</h4>
        <p style="margin-bottom:15px;color:#E0F2FE;">The core brain of the application is a deeply tuned Machine Learning classifier designed to evaluate non-linear environmental stressors on human physiology.</p>
        <ul style="color:#B9D6E8;line-height:1.6;margin-left:20px;">
            <li><strong style="color:#FFFFFF;">Dataset & Scale:</strong> Trained on <strong>43,812 rows</strong> of historical meteorological data.</li>
            <li><strong style="color:#FFFFFF;">Feature Engineering:</strong> Includes <code>Temp_Fluctuation</code>, <code>Heat_Humidity_Index</code> proxy, and binary <code>Is_Raining</code> state.</li>
            <li><strong style="color:#FFFFFF;">Model Configuration:</strong> <code>XGBClassifier</code> with multi-class softmax objective.</li>
            <li><strong style="color:#FFFFFF;">Hyperparameter Tuning:</strong> <code>max_depth=4</code>, <code>learning_rate=0.03</code>, <code>reg_lambda=2.0</code>, 200 estimators.</li>
            <li><strong style="color:#FFFFFF;">Generalization:</strong> Gaussian noise injected into temperature and humidity training vectors for sensor-fault robustness.</li>
            <li><strong style="color:#FFFFFF;">Validation Performance:</strong> <strong>97% overall accuracy</strong> across Safe, Moderate, and High Risk classifications.</li>
        </ul>
    </div>

    <div class="arch-card">
        <h4 style="margin-top:0;color:#FFFFFF;">2. Intelligent Query Parsing Pipeline (NLP)</h4>
        <p style="margin-bottom:15px;color:#E0F2FE;">A robust NLP layer allows conversational queries instead of rigid exact-match inputs.</p>
        <ul style="color:#B9D6E8;line-height:1.6;margin-left:20px;">
            <li><strong style="color:#FFFFFF;">Engine:</strong> <code>spaCy</code> (en_core_web_sm).</li>
            <li><strong style="color:#FFFFFF;">Mechanism:</strong> Named Entity Recognition (NER) isolates geographical tokens (<code>GPE</code> / <code>LOC</code>), bypassing prepositions and temporal noise.</li>
            <li><strong style="color:#FFFFFF;">Fallback Guard:</strong> Custom semantic noise-filter strips weather-related query words if spaCy fails to resolve a city.</li>
        </ul>
    </div>

    <div class="arch-card">
        <h4 style="margin-top:0;color:#FFFFFF;">3. Asynchronous Real-Time Telemetry</h4>
        <ul style="color:#B9D6E8;line-height:1.6;margin-left:20px;">
            <li><strong style="color:#FFFFFF;">Data Broker:</strong> <code>Open-Meteo API</code>.</li>
            <li><strong style="color:#FFFFFF;">Async Processing:</strong> <code>httpx</code> + <code>asyncio</code> in FastAPI — simultaneous non-blocking requests to Weather and Air Quality endpoints.</li>
            <li><strong style="color:#FFFFFF;">Target Variables:</strong> Temperature, Humidity, Wind Speed, Precipitation, PM2.5, PM10, Ozone, NO2, SO2, CO.</li>
        </ul>
    </div>

    <div class="arch-card">
        <h4 style="margin-top:0;color:#FFFFFF;">4. Guardrail Rule-Engine (Deterministic Fallback)</h4>
        <ul style="color:#B9D6E8;line-height:1.6;margin-left:20px;">
            <li><strong style="color:#FFFFFF;">Safety Net:</strong> Independent AQI Risk Score computed via strict thresholding.</li>
            <li><strong style="color:#FFFFFF;">Risk Override:</strong> Final risk = <code>max(ml_risk, aqi_risk)</code>. Severe air toxicity instantly overrides any ML "Safe" or "Moderate" prediction with a mandatory <strong>HIGH RISK</strong> advisory.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)