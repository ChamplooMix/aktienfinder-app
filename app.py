import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
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

# Funktion zum Laden der letzten 90 Tage mit täglichen Schlusskursen
@st.cache_data(ttl=3600)
def get_history_last_90_days(ticker_symbol: str) -> pd.DataFrame:
    """Lädt die letzten 90 Tage an täglichen Schlusskursen."""
    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(period="90d", interval="1d", actions=False, auto_adjust=True)
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

if ticker:
    try:
        with st.spinner("Daten werden geladen…"):
            df = get_history_last_90_days(ticker)
            info = get_info(ticker)

        if df.empty:
            st.error(f"Keine Kursdaten für '{ticker}' gefunden.")
        else:
            # Chart täglich
            df_reset = df.reset_index()
            chart = alt.Chart(df_reset).mark_line(point=True).encode(
                x="Date:T",
                y=alt.Y("Close:Q", title="Schlusskurs"),
                tooltip=["Date","Close"]
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
                # Manuelle Dividendenrendite berechnen: dividendRate / Kurs
                div_rate = info.get('dividendRate', 0)
                price_price = info.get('regularMarketPrice', 0)
                if div_rate and price_price:
                    div_yield = div_rate / price_price
                    st.metric("Dividendenrendite", f"{div_yield*100:.2f}%")
                else:
                    st.metric("Dividendenrendite", "n/a")

            # Tabelle
            st.subheader("Letzte 90 Tage: Schlusskurse")
            st.dataframe(df[['Close']])

    except HTTPError as http_err:
        if http_err.response.status_code == 429:
            st.error("429: Zu viele Anfragen. Bitte später erneut versuchen.")
        else:
            st.error(f"HTTP-Fehler: {http_err}")
    except JSONDecodeError:
        st.error("Antwort-Parsing-Fehler. Bitte später erneut versuchen.")
    except Exception as e:
        st.error(f"Unerwarteter Fehler: {e}")
