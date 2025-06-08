import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from requests.exceptions import HTTPError

# Seitenkonfiguration
st.set_page_config(
    page_title="Aktienfinder-Clone",
    page_icon="📈",
    layout="centered"
)

# Header mit Hintergrundfarbe
st.markdown(
    f"""
    <div style="background-color:#207373;padding:10px;border-radius:10px">
        <h1 style="color:white;text-align:center;">Aktienfinder-Clone</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Caching-Funktionen für Yahoo Finance API-Aufrufe
@st.cache_data(ttl=3600)
def get_history(ticker_symbol: str, period: str) -> pd.DataFrame:
    ticker_obj = yf.Ticker(ticker_symbol)
    return ticker_obj.history(period=period)

@st.cache_data(ttl=3600)
def get_info(ticker_symbol: str) -> dict:
    ticker_obj = yf.Ticker(ticker_symbol)
    return ticker_obj.info

# Eingabebereich
st.markdown("**Gib ein Tickersymbol ein (z.B. AAPL, MSFT)**")
ticker = st.text_input("Ticker", value="AAPL").upper()

# Zeitraum-Auswahl
period = st.selectbox(
    "Zeitraum",
    options=["1d","5d","1mo","3mo","6mo","1y","5y","max"],
    index=2
)

if ticker:
    try:
        # Daten abrufen (aus Cache oder neu)
        df = get_history(ticker, period)
        info = get_info(ticker)

        # Chart mit Altair und Highlight-Farben
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
            st.metric("Aktueller Kurs", f"{info.get('regularMarketPrice', 'n/a')} {info.get('currency', '')}")
            st.metric("Marktkapitalisierung", f"{info.get('marketCap', 'n/a'):,}")
        with cols[1]:
            st.metric("PE Ratio", info.get('trailingPE', 'n/a'))
            dividend = info.get('dividendYield', 0)
            st.metric("Dividendenrendite", f"{dividend*100:.2f}%" if dividend else "n/a")

        # Daten als Tabelle
        st.subheader("Historische Daten")
        st.dataframe(df)

    except HTTPError as http_err:
        if http_err.response.status_code == 429:
            st.error("Fehler 429: Zu viele Anfragen an Yahoo Finance. Bitte warte einen Moment und versuche es erneut.")
        else:
            st.error(f"HTTP-Fehler beim Abrufen der Daten: {http_err}")
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Daten: {e}")
