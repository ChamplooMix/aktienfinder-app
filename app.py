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

# Header mit Skobeloff-Hintergrund
st.markdown(
    """
    <div style=\"background-color:#207373;padding:10px;border-radius:10px\">
        <h1 style=\"color:white;text-align:center;\">Aktienfinder-Clone</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Caching-Funktionen
@st.cache_data(ttl=3600)
def get_history(ticker_symbol: str, period: str) -> pd.DataFrame:
    """Lädt historische Kursdaten mit yf.download."""
    interval = "5m" if period == "1d" else "1d"
    try:
        df = yf.download(
            tickers=ticker_symbol,
            period=period,
            interval=interval,
            progress=False,
            threads=False
        )
    except HTTPError:
        raise
    except Exception:
        return pd.DataFrame()
    return df

@st.cache_data(ttl=3600)
def get_info(ticker_symbol: str) -> dict:
    """Lädt Fundamentaldaten über yf.Ticker.info."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        return ticker.info
    except (JSONDecodeError, HTTPError, KeyError, ValueError):
        return {}

# User Input
st.markdown("**Ticker eingeben (z.B. AAPL, MSFT)**")
ticker = st.text_input("Ticker", value="AAPL").upper()
period = st.selectbox(
    "Zeitraum",
    ["1d","5d","1mo","3mo","6mo","1y","5y","max"],
    index=2
)

if ticker:
    try:
        with st.spinner("Daten werden geladen…"):
            df = get_history(ticker, period)
            info = get_info(ticker)

        if df.empty:
            st.error(f"Keine Kursdaten für '{ticker}' gefunden.")
        else:
            # Chart
            df_reset = df.reset_index()
            chart = alt.Chart(df_reset).mark_line(point=True).encode(
                x="Datetime:T",
                y=alt.Y("Close:Q", title="Schlusskurs"),
                tooltip=["Datetime","Close"]
            ).properties(width=600, height=300)
            st.altair_chart(chart, use_container_width=True)

            # Kennzahlen
            cols = st.columns(2)
            with cols[0]:
                price = info.get('regularMarketPrice', 'n/a')
                curr = info.get('currency', '')
                st.metric("Aktueller Kurs", f"{price} {curr}")
                st.metric("Marktkapitalisierung", f"{info.get('marketCap','n/a'):,}")
            with cols[1]:
                st.metric("PE Ratio", info.get('trailingPE','n/a'))
                div = info.get('dividendYield', 0)
                st.metric("Dividendenrendite", f"{div*100:.2f}%" if div else "n/a")

            # Tabelle
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
