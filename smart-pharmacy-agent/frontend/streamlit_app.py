import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys, os

# Add root dir so "backend" can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.forecasting import compute_forecast
from backend.services.groq_agent import forecast_with_groq, explain_reorder, chat_with_groq
from backend.services.reorder import reorder_point, reorder_suggestion
from backend.services.redistribution import near_expiry_redistribution
from backend.services.routing import nearest_neighbor_route, build_stops_from_moves
from backend.services.voice import transcribe_audio_bytes, speak_text_to_audio_bytes, WHISPER_LANG

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'

st.set_page_config(page_title='Smart Pharmacy Inventory Agent', layout='wide')
st.title('💊 Smart Pharmacy Inventory Agent')

st.caption('Upload/inspect data → Forecast → Reorder alerts → Redistribution → Route planning')

# Load sample data
inv = pd.read_csv(DATA_DIR / 'sample_inventory.csv', parse_dates=['expiry_date'])
centers = pd.read_csv(DATA_DIR / 'centers.csv')
hist = pd.read_csv(DATA_DIR / 'demand_signals.csv')

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ['Inventory', 'Forecast & Reorder', 'Redistribution', 'Route Optimization', 'Chat & Voice']
)

# ------------------ TAB 1 ------------------
with tab1:
    st.subheader('Inventory Snapshot')
    st.dataframe(inv)

# ------------------ TAB 2 ------------------
with tab2:
    st.subheader('7-day Forecast & Reorder Suggestions')
    horizon = st.slider('Forecast horizon (days)', 3, 21, 7)
    use_groq = st.toggle('Use Groq LLM for forecasting', value=True)
    explain = st.toggle('Show AI Explanations', value=True)
    service = st.slider('Service level', 0.85, 0.99, 0.95, 0.01)
    rows = []
    for _, row in inv.iterrows():
        if use_groq:
            hist_series = list(hist[(hist.center_id==row.center_id)&(hist.drug==row.drug)].qty.tail(30))
            fc = np.array(forecast_with_groq(hist_series, horizon=horizon, drug=row.drug))
        else:
            fc = compute_forecast(hist, row.center_id, row.drug, horizon=horizon)
        rpoint = reorder_point(row.avg_daily_demand, int(row.lead_time_days), service_level=service, safety_stock=row.safety_stock)
        order_qty = reorder_suggestion(row.stock, rpoint)

        explanation = ""
        if explain:
            try:
                explanation = explain_reorder(row.center_id, row.drug, row.stock, rpoint)
            except Exception as e:
                explanation = f"(AI explanation failed: {e})"

        rows.append({
            'center_id': row.center_id,
            'drug': row.drug,
            'stock': row.stock,
            'avg_daily_demand': row.avg_daily_demand,
            'reorder_point': round(rpoint,2),
            'suggest_order_qty': int(order_qty),
            'forecast_sum': round(float(np.sum(fc)),2),
            'explanation': explanation
        })
    out = pd.DataFrame(rows).sort_values(['suggest_order_qty','forecast_sum'], ascending=False)
    st.dataframe(out)
    st.download_button('⬇️ Download suggestions (CSV)', data=out.to_csv(index=False), file_name='reorder_suggestions.csv')

# ------------------ TAB 3 ------------------
with tab3:
    st.subheader('Near-Expiry Redistribution (<=30 days)')
    demand = {}
    for _, row in inv.iterrows():
        fc = compute_forecast(hist, row.center_id, row.drug, horizon=7)
        demand[(row.center_id, row.drug)] = fc
    moves = near_expiry_redistribution(inv[['center_id','drug','stock','expiry_date']], demand, horizon=7, expiry_days=30)
    if moves.empty:
        st.success('No redistribution needed 👌')
    else:
        st.warning('Proposed Moves')
        st.dataframe(moves)
        st.download_button('⬇️ Download moves (CSV)', data=moves.to_csv(index=False), file_name='redistribution_moves.csv')

# ------------------ TAB 4 ------------------
with tab4:
    st.subheader('Urgent Route Optimization')
    if 'moves' not in locals() or moves.empty:
        st.info('Generate redistribution moves in previous tab to plan a route.')
    else:
        depot_id = st.selectbox('Select depot (source center)', sorted(inv.center_id.unique()))
        depot, stops = build_stops_from_moves(moves, centers, depot_id)
        order, dist = nearest_neighbor_route(depot, stops)
        st.write('Visit order:', ' → '.join(order))
        st.metric('Total distance (km)', f'{dist:.2f}')

# ------------------ TAB 5 ------------------
with tab5:
    st.subheader('💬 Chat with Pharmacy Assistant')

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Voice recorder integration
    st.caption("🎙️ Record your question (voice input)")
    try:
        from streamlit_mic_recorder import mic_recorder
        audio = mic_recorder(start_prompt="Start recording", stop_prompt="Stop", just_once=False, use_container_width=True)
    except Exception:
        audio = None
        st.info("Install `streamlit-mic-recorder` to use mic input.")

    if audio and isinstance(audio, dict) and audio.get("bytes"):
        st.audio(audio["bytes"], format="audio/wav")
        with st.spinner("Transcribing…"):
            try:
                text_from_voice = transcribe_audio_bytes(audio["bytes"], language=WHISPER_LANG)
                if text_from_voice:
                    st.success(f"Transcribed: {text_from_voice}")
                    st.session_state.messages.append({"role": "user", "content": text_from_voice})

                    # Get assistant reply immediately
                    with st.chat_message("assistant"):
                        low_stock_items = inv[inv['stock'] < (inv['avg_daily_demand'] * 7)]['drug'].tolist()
                        context_summary = f"Inventory highlights: Low stock (<1 week) for: {', '.join(low_stock_items) if low_stock_items else 'None'}\nAvailable centers: {', '.join(centers['name'].tolist())}\nUse this data to answer queries about stock, forecasts, etc."

                        try:
                            with st.spinner('Generating response...'):
                                response = chat_with_groq(text_from_voice, context_summary)
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})

                            # Auto speak response
                            audio_bytes = speak_text_to_audio_bytes(response, lang="en")
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3")

                        except Exception as e:
                            error_msg = f"Error generating response: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.error(f"Transcription error: {e}")

    # Typed chat fallback
    if prompt := st.chat_input("Ask about inventory, forecasts, reorders, redistribution, or routes."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            low_stock_items = inv[inv['stock'] < (inv['avg_daily_demand'] * 7)]['drug'].tolist()
            context_summary = f"Inventory highlights: Low stock (<1 week) for: {', '.join(low_stock_items) if low_stock_items else 'None'}\nAvailable centers: {', '.join(centers['name'].tolist())}\nUse this data to answer queries about stock, forecasts, etc."

            try:
                with st.spinner('Generating response...'):
                    response = chat_with_groq(prompt, context_summary)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
