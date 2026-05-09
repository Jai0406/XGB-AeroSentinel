import spacy
import pytz
import pandas as pd
import pickle
import httpx
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
import urllib.parse
from components import NOISE_TOKENS, RISK_LABELS, get_verdict_text, get_advisory_bullets


# 1 LIFESPAN
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
    title="XGB-AeroSentinel API",
    description="Real-time weather and air quality risk analysis powered by XGBoost.",
    version="1.0.0",
    lifespan=lifespan,
)

# 2 PYDANTIC MODELS

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

class NewsItem(BaseModel):
    title:        str
    description:  str
    link:         str
    published_at: str

class AnalysisResponse(BaseModel):
    location:    LocationInfo
    times:       TimeSync
    weather:     WeatherMetrics
    air_quality: AirQuality
    assessment:  RiskAssessment
    advisory:    list[str]
    news:        list[NewsItem]
    
class LocationCandidate(BaseModel):
    name:      str
    admin1:    str
    country:   str
    latitude:  float
    longitude: float
    timezone:  str | None = None

class SearchResponse(BaseModel):
    candidates: list[LocationCandidate]
    auto_selected: bool  # True = sirf 1 result tha, seedha analyze karo


# 3. ML ENGINE

def predict_ml_risk(w: dict) -> int:
    if not ai_model:
        return 0
    heat_idx = w["temp_mean"] * (w["humidity"] / 100.0)
    features = pd.DataFrame([{
        "Temp_Mean_C":         w["temp_mean"],
        "Temp_Fluctuation":    abs(w["temp_max"] - w["temp_mean"]),
        "Humidity_Mean_pct":   w["humidity"],
        "Heat_Humidity_Index": heat_idx,
        "Wind_Speed_max_kmh":  w["wind_speed"],
        "Is_Raining":          1 if w["precipitation"] > 0 else 0,
        "Precipitation_mm":    w["precipitation"],
    }])
    return int(ai_model.predict(features)[0])


# 4 RISK & NARRATIVE ENGINE

def get_aqi_risk(aqi) -> int:
    try:
        val = float(aqi)
    except (TypeError, ValueError):
        return 0
    if val > 150:  return 2
    elif val > 50: return 1
    else:          return 0

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



# 5 ASYNC TELEMETRY ENGINE

class AsyncGlobalWeatherEngine:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    AQI_URL  = "https://air-quality-api.open-meteo.com/v1/air-quality"
    GEO_URL  = "https://geocoding-api.open-meteo.com/v1/search"

    @staticmethod
    async def fetch_local_news(city: str) -> list[dict]:
        q_weather  = urllib.parse.quote(f"{city} weather")
        q_city     = urllib.parse.quote(city)
        url_main   = f"https://news.google.com/rss/search?q={q_weather}&hl=en-US&gl=US&ceid=US:en"
        url_backup = f"https://news.google.com/rss/search?q={q_city}&hl=en-US&gl=US&ceid=US:en"

        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                headers={"User-Agent": "Mozilla/5.0"},
                follow_redirects=True
            ) as client:
                res1  = await client.get(url_main)
                items = []

                if res1.status_code == 200:
                    soup1 = BeautifulSoup(res1.content.decode("utf-8", errors="replace"), "xml")
                    items = soup1.find_all("item")

                if len(items) < 5:
                    res2 = await client.get(url_backup)
                    if res2.status_code == 200:
                        soup2 = BeautifulSoup(res2.content.decode("utf-8", errors="replace"), "xml")
                        extra = soup2.find_all("item")
                        existing = {i.title.text for i in items if i.title}
                        for e in extra:
                            if e.title and e.title.text not in existing:
                                items.append(e)

                items = items[:10]

                news_list = []
                for item in items:
                    raw_title   = item.title.text if item.title else "Weather Update"
                    clean_title = raw_title.encode("utf-8").decode("utf-8").rsplit(" - ", 1)[0].strip()

                    desc = ""
                    if item.description:
                        desc_soup = BeautifulSoup(item.description.text, "html.parser")
                        desc = desc_soup.get_text(separator=" ", strip=True).rsplit(" - ", 1)[0].strip()
                        if len(desc) > 180:
                            desc = desc[:177] + "..."
                    if not desc:
                        desc = "Click to read the full article."

                    link = "#"
                    if item.link:
                        sib = item.link.next_sibling
                        if sib and isinstance(sib, str) and sib.strip().startswith("http"):
                            link = sib.strip()
                        else:
                            txt = item.link.get_text(strip=True)
                            if txt.startswith("http"):
                                link = txt

                    pub_raw = item.pubDate.text if item.pubDate else ""
                    try:
                        from email.utils import parsedate_to_datetime
                        dt  = parsedate_to_datetime(pub_raw)
                        pub = dt.strftime("%d %b %Y, %I:%M %p UTC")
                    except Exception:
                        pub = pub_raw if pub_raw else "Recently"

                    news_list.append({
                        "title":        clean_title,
                        "description":  desc,
                        "link":         link,
                        "published_at": pub,
                    })

                return news_list
        except Exception as e:
            print(f"News fetch error: {e}")

        return []

    @staticmethod
    async def fetch_metrics(lat: float, lon: float) -> tuple[dict, dict]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            w_res, a_res = await asyncio.gather(
                client.get(AsyncGlobalWeatherEngine.BASE_URL, params={
                    "latitude":      lat,
                    "longitude":     lon,
                    "current":       "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                    "daily":         "temperature_2m_max",
                    "timezone":      "auto",
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

# 6 NLP & TIME UTILITIES

def extract_city(text: str) -> str:
    if nlp:
        doc  = nlp(text)
        ents = [e.text for e in doc.ents if e.label_ in ("GPE", "LOC")]
        if ents:
            return ents[-1]
    clean_text = text.replace(",", " ")
    tokens     = clean_text.split()
    filtered   = [t for t in tokens if t.lower() not in NOISE_TOKENS]
    result     = " ".join(filtered).strip()
    if not result or len(result) < 2:
        return text.strip().title()
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


# 7 ENDPOINTS

@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze(
    query:     str   = Query(..., min_length=2, max_length=100),
    latitude:  float = Query(...),
    longitude: float = Query(...),
    timezone:  str   = Query(None),
    city:      str   = Query(None),
):
    query    = query.strip()
    lat      = latitude
    lon      = longitude
    full_loc = city or extract_city(query)
    tz       = timezone or "UTC"

    # Weather + news parallel fetch
    metrics_task = AsyncGlobalWeatherEngine.fetch_metrics(lat, lon)
    news_task    = AsyncGlobalWeatherEngine.fetch_local_news(city or extract_city(query))
    (w, a), news_data = await asyncio.gather(metrics_task, news_task)

    # Timezone override if   user selectss
    if tz and tz != "UTC":
        w["timezone"] = tz

    ml_risk    = predict_ml_risk(w)
    aqi_risk   = get_aqi_risk(a["aqi"])
    final_risk = max(ml_risk, aqi_risk)
    score, grade = composite_score(ml_risk, aqi_risk, w, a["aqi"])
    dominant    = get_dominant_pollutant(a)
    times       = get_global_times(w["timezone"])
    trend       = time_of_day_trend(times["local"])
    weather_exp = get_weather_explanation(w)
    verdict     = get_verdict_text(ml_risk, aqi_risk, final_risk)

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
        advisory=get_advisory_bullets(w, a, final_risk, dominant),
        news=news_data,
    )
    
    
@app.get("/search", status_code=status.HTTP_200_OK)
async def search_location(
    query: str = Query(..., min_length=2, max_length=100)
):
    query = query.strip()
    city_name = extract_city(query)

    country_hint = ""
    if nlp:
        doc  = nlp(query)
        ents = [e.text for e in doc.ents if e.label_ in ("GPE", "LOC")]
        if len(ents) >= 2:
            country_hint = ents[0]

    search_term = f"{city_name}, {country_hint}" if country_hint else city_name

    async with httpx.AsyncClient(timeout=60.0) as client:
        res  = await client.get(
            AsyncGlobalWeatherEngine.GEO_URL,
            params={"name": search_term, "count": 10, "format": "json"},
        )
        data = res.json()

    if "results" not in data or not data["results"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No locations found for '{city_name}'.",
        )

    candidates = []
    for r in data["results"]:
        candidates.append(LocationCandidate(
            name      = r["name"],
            admin1    = r.get("admin1", ""),
            country   = r.get("country", ""),
            latitude  = r["latitude"],
            longitude = r["longitude"],
            timezone  = r.get("timezone", "UTC"),
        ))

    return SearchResponse(
        candidates    = candidates,
        auto_selected = len(candidates) == 1,
    )