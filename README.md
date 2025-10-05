# Smart Pharmacy Inventory Agent

An end-to-end **prototype** to predict demand, prevent stockouts, reduce expiry waste, and optimize urgent routes for medicine replenishment.

## Features
- 📊 **Simple forecasting**: Exponential Moving Average + seasonality factor (day-of-week).
- 🔔 **Reorder suggestions**: Safety stock, lead time, and service level (z-score) based.
- 🔁 **Redistribution**: Move near-expiry stock to centers with predicted shortfall.
- 🗺️ **Route optimization**: Greedy nearest-neighbor for urgent multi-stop delivery.
- 🖥️ **Streamlit UI**: Dashboard to upload data, run forecasts, see alerts, and simulate routes.
- ⚙️ **FastAPI backend** (optional): Same logic as reusable services (used by Streamlit directly).

- **Conversational interface**: Pharmacists can ask in plain English (or local language):
  - “Which medicines will expire next month?”
  - “Show me reorder alerts for antibiotics.”
  - **Voice + Text**: Voice input via Whisper, response via TTS for hands-free use.

> This is a lightweight, offline-friendly baseline (no heavy ML). Swap the forecasting module with ARIMA/Prophet later if needed.

## Quickstart (All-in-One using Streamlit)
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
streamlit run frontend/streamlit_app.py
```

## Data Schemas
- **data/sample_inventory.csv**: `center_id,drug,stock,avg_daily_demand,lead_time_days,safety_stock,expiry_date`
- **data/centers.csv**: `center_id,name,lat,lon`
- **data/demand_signals.csv**: `date,center_id,drug,qty` (historical sales/consumption)

> Replace with your real exports from pharmacy/HIS. Dates are ISO `YYYY-MM-DD`.

## Tests
```bash
pytest -q
```

### Testing Redistribution & Route Optimization
To test the end-to-end redistribution and route optimization features:

1. **Run the dedicated test script** (uses sample data, simple forecasts):
   ```bash
   cd smart-pharmacy-agent
   source .venv/bin/activate
   python backend/services/test_features.py
   ```
   Expected output: Suggested moves DataFrame, optimized route order, and total distance (e.g., ~1500 km with 5 centers).

2. **With Groq LLM forecasts** (uncomment the last line in test_features.py for advanced testing):
   - Ensure GROQ_API_KEY is set.
   - Rerun the script; it will use AI-generated forecasts for more dynamic results.

3. **In Streamlit UI**:
   - Run `streamlit run frontend/streamlit_app.py`.
   - Upload or use sample CSVs in the "Forecast & Reorder" tab.
   - Enable "Redistribution Simulation" to see moves and routes visualized.

This verifies expiry waste reduction and efficient delivery planning. Adjust expiry_days or horizon in test_features.py for custom scenarios.

## API (Optional)
Run FastAPI (if you prefer API mode):
```bash
uvicorn backend.main:app --reload
```


## 🔌 Groq Integration

This build can use **Groq LLM** for forecasting and explanations.

### Setup
1. Get an API key from Groq and set it in your environment (or a `.env` file in project root):
   ```bash
   export GROQ_API_KEY="your_key_here"
   export GROQ_MODEL="llama-3.1-8b-instant"  # optional
   ```
2. Install deps (already in requirements):
   ```bash
   pip install groq python-dotenv
   ```

### Use in Streamlit
- In the **Forecast & Reorder** tab, enable **"Use Groq LLM for forecasting"** (on by default).
<p align="center">
  <img src="smart-pharmacy-agent/docs/images/dashboard.png" width="700" alt="Streamlit Dashboard">
  <br>
  <em>Main Streamlit dashboard with tabs</em>
</p>

---

## UI Screenshots

<table>
  <tr>
    <td><img src="smart-pharmacy-agent/docs/images/dashboard.png" width="400" alt="Inventory"></td>
    <td><img src="smart-pharmacy-agent/docs/images/forecast.png" width="400" alt="Forecast"></td>
  </tr>
  <tr>
    <td align="center"><em>📦 Inventory Snapshot</em></td>
    <td align="center"><em>📊 Forecast & Reorder</em></td>
  </tr>
  <tr>
    <td><img src="smart-pharmacy-agent/docs/images/redistribution.png" width="400" alt="Redistribution"></td>
    <td><img src="smart-pharmacy-agent/docs/images/routes.png" width="400" alt="Routes"></td>
  </tr>
  <tr>
    <td align="center"><em>♻️ Redistribution Moves</em></td>
    <td align="center"><em>🗺️ Route Optimization</em></td>
  </tr>
</table>

---

## Voice & AI Features

<p align="center">
  <img src="smart-pharmacy-agent/docs/images/chat_interface.png" width="500" alt="Voice Demo">
  <br>
  <em>🎙️ Voice input and 🔊 TTS response</em>
</p>

<p align="center">
  <img src="smart-pharmacy-agent/docs/images/chat_interface_2.png" width="600" alt="Groq Forecast">
  <br>
  <em>🤖 Groq LLM-powered forecast explanations</em>
</p>

### API Endpoint
```
GET /forecast_groq?center_id=C01&drug=Insulin&horizon=7
```

## 🚀 Next-Level Enhancements

### 1. **Supply Chain Integration**

- **Vendor API integration**: Connect directly with supplier APIs (Sun Pharma, Cipla, etc.) to auto-place orders once reorder threshold is hit.
- **Lead-time modeling**: Adjust forecasts based on supplier delays or seasonal spikes.
- **Dynamic pricing**: Pull real-time supplier pricing and suggest best vendor.

### 2. **LLM-powered Chatbot for Pharmacists (Enhancements)**

- **Actionable commands**: “Place order for Paracetamol 500mg” → auto-triggers supplier API.

### 3. **Predictive Analytics Enhancements**

- **Multi-level forecasting**: Demand prediction not just per drug but grouped by:
    - **Category** (antibiotics, painkillers, etc.)
    - **Branch** (multi-center pharmacy chain)
- **External signals**: Factor in weather (flu season), public holidays, or epidemics (COVID-like events).
- **Anomaly detection**: Auto-flag sudden abnormal sales patterns (possible fraud or panic buying).

### 4. **Smart Redistribution**

- **AI matching engine**: Match centers with surplus stock to those with shortages.
- **Truckload optimization**: Use linear programming to minimize logistics cost.
- **Expiry risk dashboard**: Prioritize redistribution based on expiry dates.

### 5. **Scalability & Productionization**

- **Event-driven pipeline**: Use Kafka or AWS Kinesis for real-time inventory updates.
- **Cloud-native**: Deploy on AWS (Glue, Athena, S3) or GCP (BigQuery, Vertex AI).
- **Database backend**: Switch from CSV → PostgreSQL / DuckDB for persistence.

### 6. **User-facing Features**

- **Mobile App**: Flutter-based pharmacist dashboard for on-the-go monitoring.
- **Push Notifications**: Alerts for low-stock, near-expiry, and completed redistributions.
- **Reports Export**: CSV/PDF with reorder insights, expiry risk, and monthly demand trends.