import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import time
from requests.exceptions import HTTPError
from json.decoder import JSONDecodeError

# Seitenkonfiguration
st.set_page_config(
    page_title="Aktienfinder-Clone",
    page_icon="📈",
    layout="centered"
)

# Header
st.markdown(
    """
    <div style=\"background-color:#207373;padding:10px;border-radius:10px\">
        <h1 style=\"color:white;text-align:center;\">Aktienfinder-Clone</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Retry-Helper mit Backoff (Argument _func nicht gehashed)
@st.cache_data(ttl=3600)
def retry_api_call(_func, *args, **kwargs):
    max_retries = 3
    delay = 1
    for attempt in range(max_retries):
        try:
            return _func(*args, **kwargs)
        except HTTPError as http_err:
            if http_err.response.status_code == 429 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            else:
                raise

# Caching der API-Aufrufe
@st.cache_data(ttl=3600)
def get_history(ticker_symbol: str, period: str) -> pd.DataFrame:
    ticker_obj = yf.Ticker(ticker_symbol)
    # Für Intraday-Daten bei tagesaktuellen Abfragen
    if period == "1d":
        return retry_api_call(ticker_obj.history, period=period, interval="5m")
    return retry_api_call(ticker_obj.history, period=period)

@st.cache_data(ttl=3600)
def get_info(ticker_symbol: str) -> dict:
    ticker_obj = yf.Ticker(ticker_symbol)
    return retry_api_call(ticker_obj.info)

# User Input
st.markdown("**Ticker eingeben (z.B. AAPL, MSFT)**")
ticker = st.text_input("Ticker", value="AAPL").upper()
period = st.selectbox("Zeitraum", ["1d","5d","1mo","3mo","6mo","1y","5y","max"], index=2)

if ticker:
    try:
        with st.spinner("Daten werden geladen..."):
            df = get_history(ticker, period)
            info = get_info(ticker)

        if df.empty:
            st.error(f"Keine Kursdaten für '{ticker}' gefunden.")
        else:
            df_reset = df.reset_index()
            chart = alt.Chart(df_reset).mark_line(point=True).encode(
                x="Date:T", y=alt.Y("Close:Q", title="Schlusskurs"), tooltip=["Date","Close"]
            ).properties(width=600, height=300)
            st.altair_chart(chart, use_container_width=True)

            cols = st.columns(2)
            with cols[0]:
                st.metric("Aktueller Kurs", f"{info.get('regularMarketPrice','n/a')} {info.get('currency','')}" )
                st.metric("Marktkapitalisierung", f"{info.get('marketCap','n/a'):,}")
            with cols[1]:
                st.metric("PE Ratio", info.get('trailingPE','n/a'))
                div = info.get('dividendYield',0)
                st.metric("Dividendenrendite", f"{div*100:.2f}%" if div else "n/a")

            st.subheader("Historische Daten")
            st.dataframe(df)

    except HTTPError as http_err:
        if http_err.response.status_code == 429:
            st.error("429: Zu viele Anfragen. Bitte später erneut versuchen.")
        else:
            st.error(f"HTTP-Fehler: {http_err}")
    except JSONDecodeError:
        st.error("Antwort-Parsing-Fehler. Bitte später erneut versuchen.")
    except Exception as e:
        st.error(f"Unerwarteter Fehler: {e}")
