import streamlit as st
from yahoo_fin import stock_info as si
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

# Caching der API-Aufrufe
@st.cache_data(ttl=3600)
def get_info(ticker_symbol: str) -> dict:
    """Lädt Kennzahlen, fängt Parsing- und HTTP-Fehler ab und liefert leeres Dict bei Problemen."""
    try:
        data = si.get_quote_data(ticker_symbol)
        live = si.get_live_price(ticker_symbol)
    except (JSONDecodeError, HTTPError):
        return {}
    return {
        "regularMarketPrice": live,
        "currency": data.get("currency"),
        "marketCap": data.get("marketCap"),
        "trailingPE": data.get("trailingPE"),
        "dividendYield": data.get("dividendYield")
    }
        "regularMarketPrice": live,
        "currency": data.get("currency"),
        "marketCap": data.get("marketCap"),
        "trailingPE": data.get("trailingPE"),
        "dividendYield": data.get("dividendYield")
    }

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
        with st.spinner("Daten werden geladen..."):
            df = get_history(ticker, period)
            info = get_info(ticker)

        if df.empty:
            st.error(f"Keine Kursdaten für '{ticker}' gefunden.")
        else:
            df_reset = df.reset_index()
            chart = alt.Chart(df_reset).mark_line(point=True).encode(
                x="date:T", y=alt.Y("close:Q", title="Schlusskurs"), tooltip=["date","close"]
            ).properties(width=600, height=300)
            st.altair_chart(chart, use_container_width=True)

            cols = st.columns(2)
            with cols[0]:
                st.metric("Aktueller Kurs", f"{info['regularMarketPrice']:.2f} {info['currency']}" )
                st.metric("Marktkapitalisierung", f"{info['marketCap']:,}")
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
