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

# Funktion zum Laden der letzten 90 Tage mit täglichen Schlusskursen und Veränderung
@st.cache_data(ttl=3600)
def get_history_last_90_days(ticker_symbol: str) -> pd.DataFrame:
    """Lädt die letzten 90 Tage an täglichen Schlusskursen mit Veränderung."""
    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(period="90d", interval="1d", actions=False, auto_adjust=True)
    except HTTPError:
        raise
    except Exception:
        return pd.DataFrame()
    # Veränderung zum Vortag in %
    df['Change'] = df['Close'].pct_change() * 100
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
                tooltip=["Date","Close","Change"]
            ).properties(width=600, height=300)
            st.altair_chart(chart, use_container_width=True)

            # Unternehmenskennzahlen
            st.subheader("Unternehmensinformationen")
            cols = st.columns(2)
            with cols[0]:
                st.write(f"**Branche:** {info.get('sector', 'n/a')}")
                st.write(f"**Unterbranche:** {info.get('industry', 'n/a')}")
            with cols[1]:
                st.metric("P/E Ratio", info.get('trailingPE', 'n/a'))
                # Dividendenrendite manuell
                div_rate = info.get('dividendRate', 0)
                price_price = info.get('regularMarketPrice', 0)
                if div_rate and price_price:
                    div_yield = div_rate / price_price
                    st.metric("Dividendenrendite", f"{div_yield*100:.2f}%")
                else:
                    st.metric("Dividendenrendite", "n/a")

            # P/E der Branche (falls verfügbar)
            industry_pe = info.get('industryPE', None)
            if industry_pe:
                st.metric("P/E der Branche", industry_pe)
            else:
                st.write("P/E der Branche: n/a")

            # Earnings Übersicht
            st.subheader("Earnings Übersicht")
            cols_e = st.columns(3)
            with cols_e[0]:
                st.metric("Letztes EPS", info.get('trailingEps', 'n/a'))
            with cols_e[1]:
                st.metric("Erwartetes EPS (Forward)", info.get('forwardEps', 'n/a'))
            with cols_e[2]:
                eg = info.get('earningsQuarterlyGrowth', None)
                st.metric("Q/Q Wachstum", f"{eg*100:.2f}%" if eg else 'n/a')

            # Tabelle
            st.subheader("Letzte 90 Tage: Schlusskurse und Veränderung")
            st.dataframe(df[['Close', 'Change']])

    except HTTPError as http_err:
        if http_err.response.status_code == 429:
            st.error("429: Zu viele Anfragen. Bitte später erneut versuchen.")
        else:
            st.error(f"HTTP-Fehler: {http_err}")
    except JSONDecodeError:
        st.error("Antwort-Parsing-Fehler. Bitte später erneut versuchen.")
    except Exception as e:
        st.error(f"Unerwarteter Fehler: {e}")
