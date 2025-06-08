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
    layout="wide"
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

# Sidebar für Navigation
view = st.sidebar.selectbox("Ansicht wählen", ["Übersicht", "Detailansicht"])

# Utility-Funktionen
@st.cache_data(ttl=3600)
def get_history_last_90_days(ticker_symbol: str) -> pd.DataFrame:
    """Lädt die letzten 90 Tage an täglichen Schlusskursen mit prozentualer Veränderung."""
    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(period="90d", interval="1d", actions=False, auto_adjust=True)
    except HTTPError:
        return pd.DataFrame()
    df['Change'] = df['Close'].pct_change() * 100
    return df

@st.cache_data(ttl=3600)
def get_info(ticker_symbol: str) -> dict:
    """Lädt Fundamentaldaten über yf.Ticker.info."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        return ticker.info
    except Exception:
        return {}

if view == "Übersicht":
    st.subheader("Top 20 nach Marktkapitalisierung (weltweit)")
    # Definiere hier eine Liste globaler Top-Ticker (kann erweitert werden)
    top_tickers = [
        "AAPL","MSFT","GOOGL","AMZN","TSLA",
        "NVDA","META","BABA","TSM","V",
        "JNJ","WMT","JPM","UNH","LVMUY",
        "ROIC.F","SAP.DE","TM","OR.PA","NESN.SW"
    ]
    # Infos abrufen
    rows = []
    for t in top_tickers:
        info = get_info(t)
        cap = info.get('marketCap', 0)
        price = info.get('regularMarketPrice', 'n/a')
        rows.append({'Ticker': t, 'MarketCap': cap, 'Price': price})
    df_overview = pd.DataFrame(rows)
    df_overview = df_overview.sort_values('MarketCap', ascending=False)

    # Pagination
    page = st.sidebar.number_input("Seite", min_value=1, max_value=2, value=1)
    per_page = 10
    start = (page-1)*per_page
    end = page*per_page
    df_page = df_overview.iloc[start:end].copy()
    df_page['MarketCap'] = df_page['MarketCap'].map(lambda x: f"{x:,}")

    st.table(df_page)

else:
    st.subheader("Detailansicht")
    ticker = st.text_input("Ticker eingeben (z.B. AAPL, MSFT)", value="AAPL").upper()
    if ticker:
        df = get_history_last_90_days(ticker)
        info = get_info(ticker)
        if df.empty:
            st.error(f"Keine Daten für '{ticker}' gefunden.")
        else:
            # Chart
            df_reset = df.reset_index()
            chart = alt.Chart(df_reset).mark_line(point=True).encode(
                x="Date:T", y=alt.Y("Close:Q", title="Schlusskurs"), tooltip=["Date","Close","Change"]
            ).properties(width=700, height=300)
            st.altair_chart(chart, use_container_width=True)

            # Unternehmensinformationen
            st.markdown("**Unternehmensinformationen**")
            cols = st.columns(2)
            with cols[0]:
                st.write(f"**Branche:** {info.get('sector','n/a')}")
                st.write(f"**Unterbranche:** {info.get('industry','n/a')}")
                st.metric("P/E Ratio", info.get('trailingPE','n/a'))
                # Dividendenrendite
                dr = info.get('dividendRate',0)
                pr = info.get('regularMarketPrice',0)
                if dr and pr:
                    st.metric("Dividendenrendite", f"{dr/pr*100:.2f}%")
                else:
                    st.metric("Dividendenrendite", "n/a")
            with cols[1]:
                st.metric("P/E der Branche", info.get('industryPE','n/a'))
                st.metric("Letztes EPS", info.get('trailingEps','n/a'))
                st.metric("Forward EPS", info.get('forwardEps','n/a'))
                eg = info.get('earningsQuarterlyGrowth',0)
                st.metric("Q/Q Wachstum", f"{eg*100:.2f}%" if eg else 'n/a')

            # Tabelle mit Schlusskursen und Veränderung
            st.subheader("Letzte 90 Tage: Schlusskurse & Veränderung")
            st.dataframe(df[['Close','Change']])
