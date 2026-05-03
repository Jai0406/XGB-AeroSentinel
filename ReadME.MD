# XGB-AeroSentinel 🌦️
### AI-Powered Predictive Meteorological Intelligence & Risk Advisory Engine

XGB-AeroSentinel is a privacy-first, hybrid intelligence engine that combines XGBoost-driven meteorological forecasting with a rule-based air toxicity expert system. It doesn't just show the weather — it analyzes environmental hazards and generates tiered health advisories using a fully asynchronous stack.

---

## 🚀 Key Features

- **XGBoost Master Brain** — Trained on 43,812 global data points spanning 10 years of weather records from extreme climatic regions worldwide, achieving **97% overall accuracy** in environmental risk classification.
- **NLP Query Resolution** — Uses spaCy (`en_core_web_sm`) for Named Entity Recognition (NER) to intelligently extract city names from natural language queries like *"What's the air quality in Delhi?"*
- **Async Telemetry Pipeline** — Built on `httpx` and `asyncio` to fetch real-time weather and AQI data concurrently, minimizing API latency.
- **Composite Risk Scoring** — Merges ML weather predictions with EPA-standard air quality sub-indices to generate a single 0–100 Environmental Risk Score (Low → Critical).
- **5-Tier Advisory Engine** — Generates specific, actionable safety advisories across Temperature, AQI level, individual Pollutants (PM2.5, PM10, O₃, NO₂, SO₂), and Precipitation.

---

## 🧠 The Training Data — Why It's Different

Most weather models are trained on regional, short-term datasets. Weather Master V1 was built differently.

The `global_weather_master.csv` dataset contains **43,812 rows** of curated meteorological records aggregated across **10 years** of observations. The data was intentionally sourced from **climatically extreme and diverse regions** — Arctic cold, Saharan heat, tropical monsoons, and high-altitude storms — so the model learns robust, generalizable patterns rather than fitting to a single geography or season.

To handle the real-world class imbalance between rare extreme events and common moderate days, training used **stratified splits** and **balanced sample weights** (`compute_sample_weight`), ensuring the model is equally sensitive across all three risk classes.

**7 engineered features** were used for training, including two custom composite metrics:

| Feature | Description |
|---|---|
| `Temp_Mean_C` | Current ambient temperature |
| `Temp_Fluctuation` | Difference between daily max and current temp |
| `Humidity_Mean_pct` | Relative humidity percentage |
| `Heat_Humidity_Index` | Custom metric: `Temp × (Humidity / 100)` |
| `Wind_Speed_max_kmh` | Maximum wind speed |
| `Is_Raining` | Binary flag for active precipitation |
| `Precipitation_mm` | Precipitation intensity in millimeters |

---

## ⚡ Model Performance

Evaluated on a held-out test set of **8,763 samples** (20% stratified split):

| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| Safe | 0.83 | **0.99** | 0.90 | 1,153 |
| Moderate | **1.00** | 0.96 | **0.98** | 6,595 |
| High Risk | 0.97 | **0.99** | **0.98** | 1,015 |
| **Overall Accuracy** | | | **0.97** | **8,763** |

**Key observations:**
- High Risk recall of **0.99** — the model almost never misses a genuinely dangerous condition, which is the most safety-critical metric.
- Moderate precision of **1.00** — when the model says Moderate, it is always correct.
- Safe recall of **0.99** — nearly all safe days are correctly identified, minimizing unnecessary alerts.

**XGBoost Configuration:**

```python
XGBClassifier(
    objective    = 'multi:softmax',
    num_class    = 3,
    max_depth    = 4,          # Prevents overfitting on 43k rows
    learning_rate= 0.03,       # Conservative rate for stable convergence
    reg_lambda   = 2.0,        # L2 regularization for generalization
    n_estimators = 200,        # 200 trees for sufficient ensemble depth
    random_state = 42
)
```

**Real-world scenario inference tests:**

| Scenario | Prediction |
|---|---|
| Perfect Spring Day (22°C, 40% humidity) | Safe |
| Normal Monsoon Day (28°C, 85% humidity, rain) | Moderate |
| Extreme Delhi Heatwave (41°C, 55% humidity) | Moderate |
| Amazon Tropical Storm (33°C, 95% humidity, 25mm rain) | Moderate |
| Siberian Winter (−15°C, 35 km/h wind) | High Risk |
| Super Cyclone (heavy rain + extreme wind) | High Risk |

---

## ⚙️ How It Works — The Intelligence Pipeline

```
POST /analyze
      │
      ▼
[Layer 1]  spaCy NLP          →  Extracts GPE/LOC entities from natural language
      │
      ▼
[Layer 2]  Async Telemetry    →  Concurrent fetch of Weather + AQI (Open-Meteo)
      │
      ▼
[Layer 3]  XGBoost Inference  →  Predicts health risk from 7 meteorological features
      │
      ▼
[Layer 4]  EPA Expert System  →  AQI sub-index conversion, dominant pollutant detection
      │
      ▼
[Layer 5]  Narrative Engine   →  Composite score, final verdict, tiered advisory
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn (Async) |
| ML Inference | XGBoost (XGBClassifier) |
| NLP Engine | spaCy `en_core_web_sm` |
| Data Processing | Pandas, NumPy |
| HTTP Client | httpx (async) |
| Telemetry | Open-Meteo Weather & AQI APIs |
| Validation | Pydantic V2 |

---

## 💻 Installation & Setup

**Prerequisites:** Python 3.10+

**1. Clone the repository**
```bash
git clone https://github.com/Jai0406/XGB-AeroSentinel
cd XGB-AeroSentinel
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Download the NLP model**
```bash
python -m spacy download en_core_web_sm
```

**4. Launch the API**
```bash
uvicorn app:app --reload
```

The interactive API docs will be available at `http://127.0.0.1:8000/docs`.

---

## 📂 Project Structure

```
XGB-AeroSentinel/
│
├── app.py                          # FastAPI app — NLP, telemetry, risk logic
├── weather_prediction_model.ipynb  # Training pipeline, feature engineering & evaluation
├── weather_master_v1.pkl           # Serialized XGBoost master brain
├── requirements.txt                # Project dependencies
└── global_weather_master.csv       # 43,812-row global dataset used for training
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Returns API status and version |
| POST | `/analyze` | Main endpoint — accepts city query, returns full intelligence report |

**Sample Request:**
```
POST /analyze?query=Whats's weather in Mumbai?
```

---

## 👤 Author

Developed by [@Jai0406](https://github.com/Jai0406)