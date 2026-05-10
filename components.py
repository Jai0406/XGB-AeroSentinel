import streamlit as st

# 1. UI COMPONENTS (For app.py)

def load_custom_css():
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
            background-color: rgba(255, 255, 255, 0.08) !important; /* Premium glassy dark look */
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 0.3rem 1rem !important;
            min-height: 35px !important;
            transition: background 0.3s, border-color 0.3s;
            box-shadow: none !important;
        }
        button[kind="secondary"] * {
            color: #FFFFFF !important; /* Text color changed to white */
            font-weight: 500 !important;
            font-size: 1rem !important;
        }
        button[kind="secondary"]:hover {
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
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

def render_architecture_view():
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


# 2. HARDCODED CONSTANTS (For main.py)

NOISE_TOKENS = {
    "what", "whats", "how", "hows", "show", "tell", "check",
    "get", "give", "can", "you", "please", "is", "it",
    "weather", "aqi", "air", "quality", "temperature", "forecast",
    "sunny", "raining", "hot", "cold", "humid", "outside",
    "in", "of", "for", "about", "the", "a", "an", "at", "me",
    "city", "there", "like",
    "today", "tonight", "tomorrow", "now", "right", "currently",
    "this", "morning", "evening", "night", "afternoon", "atm",
    "moment", "time", "week",
}

RISK_LABELS = {0: "SAFE", 1: "MODERATE", 2: "HIGH RISK"}

def get_verdict_text(ml_risk: int, aqi_risk: int, final_risk: int) -> str:
    combos = {
        (0, 0): "All meteorological parameters and air quality metrics are within normal limits. The overall environmental profile is SAFE.",
        (1, 0): "Air quality is excellent, but mild weather disturbances require a MODERATE level of caution for outdoor activities.",
        (0, 1): "Weather conditions remain stable, but elevated air pollution levels necessitate a MODERATE health advisory for sensitive groups.",
        (1, 1): "A combination of mild weather instability and degraded air quality results in an overall MODERATE environmental risk.",
        (2, 0): "Despite clean atmospheric conditions, severe meteorological anomalies pose a significant hazard, triggering a HIGH RISK alert.",
        (0, 2): "Weather conditions are relatively benign, but severe air toxicity poses a critical health threat, mandating a HIGH RISK classification.",
        (2, 1): "Severe weather threats compounded by moderately degraded air quality elevate the environmental status to HIGH RISK.",
        (1, 2): "Hazardous air pollution drastically overshadows mild weather instability, warranting a strict HIGH RISK health advisory.",
        (2, 2): "CRITICAL ALERT: A dangerous convergence of extreme weather and severe air toxicity. Maximum HIGH RISK protocols must be activated immediately.",
    }
    return combos.get(
        (ml_risk, aqi_risk),
        f"System finalized an environmental status of {RISK_LABELS.get(final_risk, 'UNKNOWN')}.")

def get_advisory_bullets(w: dict, a: dict, final_risk: int, dominant: str) -> list[str]:
    temp    = w["temp_mean"]
    aqi_val = a["aqi"] if a["aqi"] is not None else 0.0
    bullets: list[str] = []

    if final_risk == 0:
        bullets.extend([
            "Optimal conditions for all forms of outdoor exercise and extended physical activity.",
            "No respiratory, thermal, or environmental restrictions are currently indicated.",
            "Safe for vulnerable demographic groups (infants, elderly, immunocompromised) to be outdoors.",
            "Natural ventilation is recommended — open windows to refresh indoor air.",
            "Environmental stress levels are negligible; proceed with standard daily routines.",
        ])
    elif final_risk == 1:
        bullets.extend([
            "Moderate risk: General population can continue normal activities but should monitor for unusual fatigue.",
            "Sensitive individuals with asthma or cardiac conditions must carry rescue medications.",
            "Consider moving intense cardiovascular workouts to off-peak hours (early morning or late evening).",
            "Elderly and children should avoid prolonged, stationary outdoor exposure.",
            "Stay hydrated and monitor local updates in case conditions degrade further.",
        ])
    else:
        bullets.extend([
            "HIGH RISK ALERT: Immediate suspension of all non-essential outdoor physical activities is strongly advised.",
            "Significant risk of adverse health events for both healthy individuals and sensitive groups.",
            "Secure environments by sealing windows and utilizing active HEPA air purification.",
            "If outdoor transit is unavoidable, strict protective gear (N95 masks or thermal layers) is required.",
            "Keep emergency contacts readily available and monitor individuals prone to environmental stress.",
        ])

    if temp > 40:
        bullets.extend([
            f"Severe extreme heat ({temp}C): Restrict all outdoor exposure to strictly before 9 AM.",
            "Hydration protocol: Consume 3-4 liters of electrolyte-infused fluids to prevent severe dehydration.",
            "Wear loose, UV-reflective, light-colored, and highly breathable fabrics.",
            "High probability of heatstroke — seek immediate medical attention if sweating stops or severe dizziness occurs.",
            "Zero tolerance for leaving pets, children, or elderly in stationary or parked vehicles.",
        ])
    elif temp > 35:
        bullets.extend([
            f"Heat stress warning ({temp}C): Mandatory shade breaks for any outdoor labor.",
            "Increase baseline water consumption by at least 50% above normal daily levels.",
            "Apply broad-spectrum SPF 50+ sunscreen and wear wide-brimmed hats.",
            "Retreat to climate-controlled environments between 11 AM and 4 PM.",
            "Avoid heavy lifting or high-intensity training in direct sunlight.",
        ])
    elif temp < 5:
        bullets.extend([
            f"Severe cold ({temp}C): Critical hypothermia and frostbite risk for exposed extremities.",
            "Use a 3-layer system: moisture-wicking base, insulating mid-layer, windproof outer shell.",
            "Insulated gloves, thick thermal socks, and full head or ear coverings are mandatory.",
            "Asthmatics must wear a scarf or thermal mask over the mouth — cold air triggers bronchospasms.",
            "Prevent indoor pipe freezing and ensure safe, ventilated operation of indoor heating appliances.",
        ])
    elif temp < 10:
        bullets.extend([
            f"Cool weather ({temp}C): Slight risk of rapid core temperature drop during inactive periods.",
            "A wind-resistant light jacket or thermal sweater is required for prolonged outdoor time.",
            "Extended physical warm-ups are necessary before athletic activities to prevent muscle strains.",
            "Maintain steady water intake — winter air causes invisible fluid loss through respiration.",
            "Infants and elderly require at least one extra insulating layer compared to healthy adults.",
        ])

    if aqi_val > 300:
        bullets.extend([
            "HAZARDOUS AIR: Toxicity levels are catastrophic. Complete indoor lockdown required for all demographics.",
            "Seal all window and door gaps with damp towels if active HEPA purification is unavailable.",
            "N95, KN95, or P100 respirator masks are mandatory for any emergency outdoor evacuation.",
            "Cease frying food, burning candles, or vacuuming — these multiply indoor particle counts significantly.",
            "Extremely high risk of stroke, heart attack, and acute respiratory failure in vulnerable groups.",
        ])
    elif aqi_val > 200:
        bullets.extend([
            "Very poor AQI: Airborne particulate density is dangerously high. Cease all outdoor physical labor.",
            "Well-fitted N95 masks must be worn continuously outside — surgical or cloth masks are ineffective.",
            "Run HVAC systems exclusively on recirculate mode to block outside air from entering.",
            "Even healthy individuals will likely experience throat irritation, coughing, and chest tightness.",
            "Asthmatics should consult doctors about increasing preventative inhaler usage.",
        ])
    elif aqi_val > 150:
        bullets.extend([
            "Unhealthy air: Prolonged exposure will deposit harmful micro-particulates deep into lung tissues.",
            "Swap all outdoor cardiovascular routines for indoor gym sessions or home workouts.",
            "N95 masks are strongly recommended for anyone spending more than 30 consecutive minutes outside.",
            "Elderly and children must remain indoors to prevent long-term lung capacity degradation.",
            "Run standalone HEPA air purifiers at maximum capacity in primary living or sleeping spaces.",
        ])
    elif aqi_val > 100:
        bullets.extend([
            "Sensitive group warning: Air chemistry is degraded enough to trigger acute asthmatic reactions.",
            "Reduce the intensity and duration of heavy outdoor workouts — switch from running to walking.",
            "Watch for unusual coughing, shortness of breath, or excessive eye watering.",
            "Limit time spent near heavy traffic intersections, highways, or active construction sites.",
            "Individuals with severe seasonal allergies should consider taking antihistamines pre-emptively.",
        ])

    if aqi_val > 50:
        if "PM2.5" in dominant or "PM10" in dominant:
            bullets.extend([
                "Particulate threat: The dominant pollutant consists of microscopic solid particles that can cross into the bloodstream.",
                "Stay entirely clear of dust-heavy zones, industrial areas, and heavy diesel traffic corridors.",
                "Only properly sealed N95/KN95 respirators can filter PM2.5 effectively — scarves are not effective.",
                "Wear wrap-around sunglasses or clear protective eyewear to prevent ocular irritation.",
            ])
        elif "Ozone" in dominant:
            bullets.extend([
                "Ozone chemical threat: Ground-level ozone is corrosive to lung linings, acting like an internal chemical burn.",
                "Ozone concentration peaks with sunlight and heat — shift all outdoor tasks to early morning or after sunset.",
                "Expect increased wheezing and a temporary reduction in lung capacity even in healthy athletes.",
                "Standard N95 masks do not filter ozone gas — retreating indoors is the only effective defense.",
            ])
        elif "NO2" in dominant or "SO2" in dominant:
            bullets.extend([
                "Chemical gas threat: Elevated NO2 or SO2 levels indicate high localized combustion or industrial exhaust.",
                "Strictly avoid commuting along major highways, truck routes, or proximity to thermal power plants.",
                "If a sharp or acrid smell is detected outdoors, evacuate the immediate area at once.",
                "Asthmatics and COPD patients are extremely susceptible to severe airway constriction from these gases.",
            ])

    if w["precipitation"] > 0:
        bullets.extend([
            f"Active rainfall ({w['precipitation']}mm): Surface traction is compromised — high risk of hydroplaning for vehicles.",
            "Atmospheric water density will reduce driving and pedestrian visibility — use headlights.",
            "Waterproof outer shells, high-traction footwear, and reflective materials are advised.",
            "Rain may temporarily scrub PM2.5 from the air, but early rain can create hazardous acidic runoff.",
            "Seek grounded indoor shelter immediately if precipitation is accompanied by thunder or lightning.",
        ])

    return bullets