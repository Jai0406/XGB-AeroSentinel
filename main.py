import spacy
import re
import pytz
import pandas as pd
import pickle
import httpx
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

# ==============================================================================
# 1. LIFESPAN
# ==============================================================================
nlp      = None
ai_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global nlp, ai_model
    nlp = spacy.load("en_core_web_sm")
    try:
        with open("weather_master_v1.pkl", "rb") as f:
            ai_model = pickle.load(f)
    except FileNotFoundError:
        print("WARNING: weather_master_v1.pkl not found. ML inference will fall back to 0.")
    yield

app = FastAPI(
    title="Predictive Meteorological Intelligence API",
    description="Real-time weather and air quality risk analysis powered by XGBoost.",
    version="1.0.0",
    lifespan=lifespan,
)

# ==============================================================================
# 2. PYDANTIC MODELS
# ==============================================================================
class CityRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="City name or natural language query like 'weather in Delhi'",
        examples=["Delhi", "whats the aqi of Mumbai"],
    )

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        v = v.strip()
        if v.isdigit():
            raise ValueError("Query must be a valid location string, not purely numeric.")
        return v


class LocationInfo(BaseModel):
    city:      str
    latitude:  float
    longitude: float
    timezone:  str


class WeatherMetrics(BaseModel):
    temperature_c:    float
    temp_max_c:       float
    humidity_pct:     int
    wind_speed_kmh:   float
    precipitation_mm: float
    observed_at:      str


class AirQuality(BaseModel):
    us_aqi:             int | None
    aqi_label:          str
    dominant_pollutant: str
    trend:              str
    pm25_ugm3:          float | None
    pm10_ugm3:          float | None
    no2_ugm3:           float | None
    so2_ugm3:           float | None
    o3_ugm3:            float | None
    co_mgm3:            float | None


class RiskAssessment(BaseModel):
    weather_risk:         str
    aqi_risk:             str
    final_risk:           str
    composite_score:      float
    composite_grade:      str
    meteorology_summary:  str
    air_toxicity_summary: str
    final_verdict:        str


class TimeSync(BaseModel):
    utc:   str
    ist:   str
    local: str


class AnalysisResponse(BaseModel):
    location:    LocationInfo
    times:       TimeSync
    weather:     WeatherMetrics
    air_quality: AirQuality
    assessment:  RiskAssessment
    advisory:    list[str]


# ==============================================================================
# 3. NLP NOISE TOKEN SET
# FIX: Expanded with temporal and descriptive words that appear in natural
#      language weather queries but are not part of the city name.
#      This replaces the old regex-strip approach for the fallback path.
# ==============================================================================
NOISE_TOKENS = {
    # question/command words
    "what", "whats", "how", "hows", "show", "tell", "check",
    "get", "give", "can", "you", "please", "is", "it",
    # weather domain words
    "weather", "aqi", "air", "quality", "temperature", "forecast",
    "sunny", "raining", "hot", "cold", "humid", "outside",
    # prepositions / articles
    "in", "of", "for", "about", "the", "a", "an", "at", "me",
    "city", "there", "like",
    # FIX: temporal words — were completely missing before
    "today", "tonight", "tomorrow", "now", "right", "currently",
    "this", "morning", "evening", "night", "afternoon", "atm",
    "moment", "time", "week",
}


# ==============================================================================
# 4. ML ENGINE
# ==============================================================================
RISK_LABELS = {0: "SAFE", 1: "MODERATE", 2: "HIGH RISK"}

def predict_ml_risk(w: dict) -> int:
    if not ai_model:
        return 0
    heat_idx = w["temp_mean"] * (w["humidity"] / 100.0)
    features = pd.DataFrame([{
        "Temp_Mean_C":         w["temp_mean"],
        # FIX: temp_max (daily max) - temp_mean (current obs) is conceptually
        # inconsistent. Using temp_mean as the reference for fluctuation since
        # both should ideally be from the same observation window.
        # If your training data used daily_max - current_obs, revert this.
        "Temp_Fluctuation":    abs(w["temp_max"] - w["temp_mean"]),
        "Humidity_Mean_pct":   w["humidity"],
        "Heat_Humidity_Index": heat_idx,
        "Wind_Speed_max_kmh":  w["wind_speed"],
        "Is_Raining":          1 if w["precipitation"] > 0 else 0,
        "Precipitation_mm":    w["precipitation"],
    }])
    return int(ai_model.predict(features)[0])


# ==============================================================================
# 5. RISK & NARRATIVE ENGINE
# ==============================================================================
def get_aqi_risk(aqi) -> tuple[int, str]:
    try:
        val = float(aqi)
    except (TypeError, ValueError):
        return 0, "N/A"
    if val > 150:   return 2, f"{val:.0f} - Unhealthy"
    elif val > 100: return 1, f"{val:.0f} - Sensitive Groups"
    elif val > 50:  return 1, f"{val:.0f} - Moderate"
    else:           return 0, f"{val:.0f} - Good"


def get_aqi_label(val: float) -> str:
    if val > 500:   return "OFF CHARTS"
    elif val > 300: return "HAZARDOUS"
    elif val > 200: return "VERY POOR"
    elif val > 150: return "UNHEALTHY"
    elif val > 100: return "SENSITIVE"
    elif val > 50:  return "MODERATE"
    else:           return "GOOD"


def composite_score(ml_risk: int, aqi_risk: int, w: dict, aqi_val) -> tuple[float, str]:
    try:
        aqi_float = float(aqi_val)
    except (TypeError, ValueError):
        aqi_float = 0.0

    ml_score   = (ml_risk / 2) * 40
    aqi_score  = min(aqi_float / 500, 1.0) * 40
    heat_idx   = w["temp_mean"] * (w["humidity"] / 100.0)
    heat_bonus = min((heat_idx - 20) / 30, 1.0) * 20 if heat_idx > 20 else 0.0
    score      = round(min(ml_score + aqi_score + heat_bonus, 100), 1)

    if score >= 70:   grade = "CRITICAL"
    elif score >= 50: grade = "HIGH"
    elif score >= 30: grade = "MODERATE"
    else:             grade = "LOW"

    return score, grade


def get_dominant_pollutant(a: dict) -> str:
    def pm25_to_aqi(c):
        bp = [(0,12,0,50),(12.1,35.4,51,100),(35.5,55.4,101,150),
              (55.5,150.4,151,200),(150.5,250.4,201,300),(250.5,500.4,301,500)]
        for lo, hi, alo, ahi in bp:
            if lo <= c <= hi:
                return ((ahi - alo) / (hi - lo)) * (c - lo) + alo
        return 500

    def pm10_to_aqi(c):
        bp = [(0,54,0,50),(55,154,51,100),(155,254,101,150),
              (255,354,151,200),(355,424,201,300),(425,604,301,500)]
        for lo, hi, alo, ahi in bp:
            if lo <= c <= hi:
                return ((ahi - alo) / (hi - lo)) * (c - lo) + alo
        return 500

    def o3_to_aqi(c):
        c_ppb = c / 2
        bp = [(0,54,0,50),(55,70,51,100),(71,85,101,150),
              (86,105,151,200),(106,200,201,300)]
        for lo, hi, alo, ahi in bp:
            if lo <= c_ppb <= hi:
                return ((ahi - alo) / (hi - lo)) * (c_ppb - lo) + alo
        return 300

    sub: dict[str, float] = {}
    try:
        if a["pm25"] is not None: sub["PM2.5"] = pm25_to_aqi(a["pm25"])
        if a["pm10"] is not None: sub["PM10"]  = pm10_to_aqi(a["pm10"])
        if a["o3"]   is not None: sub["Ozone"] = o3_to_aqi(a["o3"])
        if a["no2"]  is not None:
            v = a["no2"]
            sub["NO2"] = 200 if v > 200 else (150 if v > 100 else (100 if v > 53 else 50))
        if a["so2"]  is not None:
            v = a["so2"]
            sub["SO2"] = 200 if v > 185 else (150 if v > 75 else (100 if v > 35 else 50))
        if a["co"]   is not None:
            v = a["co"]
            sub["CO"]  = 200 if v > 12.4 else (100 if v > 4.4 else 50)
    except Exception:
        pass

    if not sub:
        return "Unknown"

    dominant = max(sub, key=sub.get)
    score    = sub[dominant]
    others   = [p for p, s in sub.items() if p != dominant and s >= score * 0.80 and s > 100]
    return f"{dominant} (also elevated: {', '.join(others)})" if others else dominant


def get_weather_explanation(w: dict) -> str:
    reasons       = []
    heat_idx      = w["temp_mean"] * (w["humidity"] / 100.0)
    combo_matched = False

    if w["temp_mean"] > 35 and w["humidity"] < 25:
        reasons.append(f"extreme dry heat ({w['temp_mean']}C, {w['humidity']}%) - high dehydration and dust risk")
        combo_matched = True
    elif w["temp_mean"] > 32 and w["humidity"] > 70:
        reasons.append(f"oppressive humid heat (Heat Index: {heat_idx:.1f}) - severe heat exhaustion risk")
        combo_matched = True
    elif w["temp_mean"] < 5 and w["wind_speed"] > 30:
        reasons.append(f"severe wind chill ({w['temp_mean']}C, {w['wind_speed']} km/h) - frostbite risk")
        combo_matched = True
    elif w["precipitation"] > 10 and w["wind_speed"] > 40:
        reasons.append(f"storm conditions (rain: {w['precipitation']}mm, wind: {w['wind_speed']} km/h) - low visibility")
        combo_matched = True

    if not combo_matched:
        if w["temp_mean"] > 35:   reasons.append(f"extreme heat ({w['temp_mean']}C)")
        elif w["temp_mean"] < 10: reasons.append(f"cold temperature ({w['temp_mean']}C)")
        else:                     reasons.append(f"normal temperature ({w['temp_mean']}C)")
        if w["humidity"] > 80:    reasons.append(f"high humidity ({w['humidity']}%)")
        elif w["humidity"] < 20:  reasons.append(f"very dry air ({w['humidity']}%)")

    if not (w["precipitation"] > 10 and w["wind_speed"] > 40):
        if w["wind_speed"] > 40:   reasons.append(f"strong winds ({w['wind_speed']} km/h)")
        if w["precipitation"] > 0: reasons.append(f"active precipitation ({w['precipitation']} mm)")

    return ", ".join(reasons) if reasons else "conditions within normal parameters"


def build_final_verdict(ml_risk: int, aqi_risk: int, final_risk: int) -> str:
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
        f"System finalized an environmental status of {RISK_LABELS.get(final_risk, 'UNKNOWN')}."
    )


def build_advisory(w: dict, a: dict, final_risk: int) -> list[str]:
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
        dominant = get_dominant_pollutant(a)
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


# ==============================================================================
# 6. ASYNC TELEMETRY ENGINE
# ==============================================================================
class AsyncGlobalWeatherEngine:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    AQI_URL  = "https://air-quality-api.open-meteo.com/v1/air-quality"
    GEO_URL  = "https://geocoding-api.open-meteo.com/v1/search"

    @staticmethod
    async def get_coords(city: str) -> tuple | None:
        async with httpx.AsyncClient() as client:
            res  = await client.get(
                AsyncGlobalWeatherEngine.GEO_URL,
                params={"name": city, "count": 1, "format": "json"},
            )
            data = res.json()
        if "results" in data:
            r = data["results"][0]
            return r["latitude"], r["longitude"], f"{r['name']}, {r.get('country', '')}"
        return None

    @staticmethod
    async def fetch_metrics(lat: float, lon: float) -> tuple[dict, dict]:
        async with httpx.AsyncClient() as client:
            w_res, a_res = await asyncio.gather(
                client.get(AsyncGlobalWeatherEngine.BASE_URL, params={
                    "latitude":     lat,
                    "longitude":    lon,
                    "current":      "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                    "daily":        "temperature_2m_max",
                    "timezone":     "auto",
                    "forecast_days": 1,
                }),
                client.get(AsyncGlobalWeatherEngine.AQI_URL, params={
                    "latitude":  lat,
                    "longitude": lon,
                    "current":   "us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
                    "timezone":  "auto",
                }),
            )

        w_json = w_res.json()
        a_json = a_res.json()
        cw     = w_json["current"]
        ca     = a_json["current"]

        def num(val) -> float | None:
            try:    return float(val)
            except: return None

        co_raw = num(ca.get("carbon_monoxide"))

        weather = {
            "temp_mean":     cw["temperature_2m"],
            "temp_max":      w_json["daily"]["temperature_2m_max"][0],
            "humidity":      cw["relative_humidity_2m"],
            "wind_speed":    cw["wind_speed_10m"],
            "precipitation": cw["precipitation"],
            "time":          cw["time"],
            "timezone":      w_json.get("timezone", "UTC"),
        }

        aqi = {
            "aqi":  num(ca.get("us_aqi")),
            "pm25": num(ca.get("pm2_5")),
            "pm10": num(ca.get("pm10")),
            "no2":  num(ca.get("nitrogen_dioxide")),
            "so2":  num(ca.get("sulphur_dioxide")),
            "o3":   num(ca.get("ozone")),
            "co":   round(co_raw / 1000, 3) if co_raw is not None else None,
        }

        return weather, aqi


# ==============================================================================
# 7. NLP & TIME UTILITIES
# ==============================================================================
def extract_city(text: str) -> str:
    """
    FIX — Complete rewrite of city extraction logic.

    Old approach: strip tokens via regex first, then pass dirty text to spaCy.
    Problem: spaCy received garbage like "right now boston" instead of clean input,
    making GPE detection unreliable on the small model.

    New approach:
      1. Run spaCy on the RAW original text — highest accuracy, no corruption.
      2. If spaCy finds a GPE/LOC entity, return it immediately.
      3. Only if spaCy finds nothing, fall back to token-level noise removal
         using the NOISE_TOKENS set (which now includes temporal words).
      4. Guard against empty/junk fallback result before returning.

    This correctly handles queries like:
      - "is it sunny today in new delhi"   -> spaCy -> "New Delhi"
      - "right now weather boston"         -> spaCy -> "Boston"
      - "whats the aqi of new york today"  -> spaCy -> "New York"
      - "temperature right now in tokyo"   -> spaCy -> "Tokyo"
    """
    # Step 1: spaCy on raw text — do NOT pre-strip
    if nlp:
        doc  = nlp(text)
        ents = [e.text for e in doc.ents if e.label_ in ("GPE", "LOC")]
        if ents:
            return ents[-1]  # last entity is usually the city in natural queries

    # Step 2: Token-level fallback using domain noise set
    tokens   = text.lower().split()
    filtered = [t for t in tokens if t not in NOISE_TOKENS]

    result = " ".join(filtered).strip()

    # Step 3: Guard — if filtering ate everything or left junk, return original
    # and let the geocoder produce a clean 404 rather than sending garbage.
    if not result or len(result) < 2:
        return text.strip()

    return result.title()


def get_global_times(tz_str: str) -> dict:
    utc_now = datetime.now(pytz.utc)
    ist_now = utc_now.astimezone(pytz.timezone("Asia/Kolkata"))
    try:    local = utc_now.astimezone(pytz.timezone(tz_str))
    except: local = utc_now
    fmt = "%Y-%m-%d %H:%M %Z"
    return {
        "utc":   utc_now.strftime(fmt),
        "ist":   ist_now.strftime(fmt),
        "local": local.strftime(fmt),
    }


def time_of_day_trend(local_time_str: str) -> str:
    try:
        hour = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M %Z").hour
    except Exception:
        return "Stable"
    if 6 <= hour < 10:    return "Rising - morning traffic rush"
    elif 10 <= hour < 15: return "Peaking - max solar and traffic overlap"
    elif 15 <= hour < 20: return "Easing - post-peak dispersal"
    else:                  return "Stable - overnight low activity"


# ==============================================================================
# 8. ENDPOINTS
# ==============================================================================
@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Environmental Risk Advisory",
    description=(
        "Fetches real-time weather and AQI data, processes it through the ML engine, "
        "and generates a detailed JSON advisory report."
    ),
)
async def analyze(
    query: str = Query(
        ...,
        min_length=2,
        max_length=100,
        title="Location Query",
        description="Enter a city name or natural language query.",
    )
):
    query = query.strip()
    if query.isdigit():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query must be a valid location string, not purely numeric.",
        )

    city_name = extract_city(query)
    coords    = await AsyncGlobalWeatherEngine.get_coords(city_name)

    if not coords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location entity '{city_name}' could not be resolved.",
        )

    lat, lon, full_loc = coords
    w, a = await AsyncGlobalWeatherEngine.fetch_metrics(lat, lon)

    ml_risk           = predict_ml_risk(w)
    aqi_risk, _       = get_aqi_risk(a["aqi"])
    final_risk        = max(ml_risk, aqi_risk)
    score, grade      = composite_score(ml_risk, aqi_risk, w, a["aqi"])
    dominant          = get_dominant_pollutant(a)
    times             = get_global_times(w["timezone"])
    trend             = time_of_day_trend(times["local"])
    weather_exp       = get_weather_explanation(w)
    verdict           = build_final_verdict(ml_risk, aqi_risk, final_risk)

    risk_phrasing = {
        0: "indicating a safe environmental profile",
        1: "showing a moderate risk level",
        2: "indicating a high risk threat level",
    }

    return AnalysisResponse(
        location=LocationInfo(
            city=full_loc,
            latitude=lat,
            longitude=lon,
            timezone=w["timezone"],
        ),
        times=TimeSync(**times),
        weather=WeatherMetrics(
            temperature_c=w["temp_mean"],
            temp_max_c=w["temp_max"],
            humidity_pct=int(w["humidity"]),
            wind_speed_kmh=w["wind_speed"],
            precipitation_mm=w["precipitation"],
            observed_at=w["time"],
        ),
        air_quality=AirQuality(
            us_aqi=int(a["aqi"]) if a["aqi"] is not None else None,
            aqi_label=get_aqi_label(a["aqi"]) if a["aqi"] is not None else "N/A",
            dominant_pollutant=dominant,
            trend=trend,
            pm25_ugm3=a["pm25"],
            pm10_ugm3=a["pm10"],
            no2_ugm3=a["no2"],
            so2_ugm3=a["so2"],
            o3_ugm3=a["o3"],
            co_mgm3=a["co"],
        ),
        assessment=RiskAssessment(
            weather_risk=RISK_LABELS[ml_risk],
            aqi_risk=RISK_LABELS[aqi_risk],
            final_risk=RISK_LABELS[final_risk],
            composite_score=score,
            composite_grade=grade,
            meteorology_summary=(
                f"Meteorological profile shows {weather_exp}, "
                f"{risk_phrasing[ml_risk]}."
            ),
            air_toxicity_summary=(
                f"Air toxicity levels (Composite Index: {a['aqi']}, "
                f"dominant: {dominant}) are {risk_phrasing[aqi_risk]}."
            ),
            final_verdict=verdict,
        ),
        advisory=build_advisory(w, a, final_risk),
    )