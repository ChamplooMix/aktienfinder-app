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

# Session State initialisieren
if 'view' not in st.session_state:
    st.session_state.view = 'Übersicht'
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# Hilfsfunktionen
@st.cache_data(ttl=3600)
def get_history_last_90_days(ticker_symbol: str) -> pd.DataFrame:
    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(period="90d", interval="1d", actions=False, auto_adjust=True)
    except Exception:
        return pd.DataFrame()
    df['Change'] = df['Close'].pct_change() * 100
    return df

@st.cache_data(ttl=3600)
def get_info(ticker_symbol: str) -> dict:
    try:
        return yf.Ticker(ticker_symbol).info
    except Exception:
        return {}

# Header
st.markdown(
    """
    <div style=\"background-color:#207373;padding:10px;border-radius:10px\">
      <h1 style=\"color:white;text-align:center;\">Aktienfinder-Clone</h1>
    </div>
    """,
    unsafe_allow_html=True
)

if st.session_state.view == 'Übersicht':
    st.subheader("Top 20 nach Marktkapitalisierung (weltweit)")
    tickers = ["AAPL","MSFT","GOOGL","AMZN","TSLA","NVDA","META","BABA","TSM","V",
               "JNJ","WMT","JPM","UNH","LVMUY","ROIC.F","SAP.DE","TM","OR.PA","NESN.SW"]
    data = []
    for t in tickers:
        info = get_info(t)
        hist = get_history_last_90_days(t)
        data.append({
            'Ticker': t,
            'MarketCap': info.get('marketCap', 0),
            'Price': info.get('regularMarketPrice', 0),
            'Change %': hist['Change'].iloc[-1] if not hist.empty else None,
            'P/E': info.get('trailingPE', None),
            '52wHigh': info.get('fiftyTwoWeekHigh', None),
            '52wLow': info.get('fiftyTwoWeekLow', None)
        })
    df_overview = pd.DataFrame(data).sort_values('MarketCap', ascending=False)

    # Pagination
    page = st.sidebar.number_input("Seite", 1, (len(df_overview)//10), 1)
    per_page = 10
    df_page = df_overview.iloc[(page-1)*per_page:page*per_page].copy()
    df_page['MarketCap'] = df_page['MarketCap'].map(lambda x: f"{x:,}")

    # Scrollbare Tabelle mit Buttons für Ticker
    st.markdown("<style>div.stDataFrame div.row_widget{display:flex;flex-wrap:nowrap;overflow-x:auto;}</style>", unsafe_allow_html=True)
    for row in df_page.itertuples(index=False):
        cols = st.columns([1,2,1,1,1,1,1], gap="small")
        if cols[0].button(row.Ticker, key=f"btn_{row.Ticker}"):
            st.session_state.view = 'Detailansicht'
            st.session_state.selected_ticker = row.Ticker
            st.experimental_rerun()
        cols[1].write(row.MarketCap)
        cols[2].write(row.Price)
        cols[3].write(f"{row._4:.2f}%" if row._4 is not None else 'n/a')
        cols[4].write(f"{row._5:.2f}" if row._5 else 'n/a')
        cols[5].write(f"{row._6:.2f}" if row._6 else 'n/a')
        cols[6].write(f"{row._7:.2f}" if row._7 else 'n/a')

elif st.session_state.view == 'Detailansicht':
    ticker = st.session_state.selected_ticker
    # Close-Button
    header = st.columns([9,1])
    header[0].subheader(f"Details zu {ticker}")
    if header[1].button("❌", key="close"):  
        st.session_state.view = 'Übersicht'
        st.session_state.selected_ticker = None
        st.experimental_rerun()

    # Detaildaten
    df = get_history_last_90_days(ticker)
    info = get_info(ticker)
    if df.empty:
        st.error(f"Keine Daten für {ticker} gefunden.")
    else:
        chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x="Date:T", y=alt.Y("Close:Q"), tooltip=["Date","Close","Change"]
        ).properties(width=700, height=300)
        st.altair_chart(chart, use_container_width=True)
        st.markdown("**Unternehmensinformationen**")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Branche:** {info.get('sector','n/a')}")
            st.write(f"**Unterbranche:** {info.get('industry','n/a')}")
            st.metric("P/E", info.get('trailingPE','n/a'))
            dr = info.get('dividendRate',0); pr = info.get('regularMarketPrice',0)
            st.metric("Dividendenrendite", f"{dr/pr*100:.2f}%" if dr and pr else 'n/a')
        with c2:
            st.metric("P/E der Branche", info.get('industryPE','n/a'))
            st.metric("Letztes EPS", info.get('trailingEps','n/a'))
            st.metric("Forward EPS", info.get('forwardEps','n/a'))
            eg = info.get('earningsQuarterlyGrowth',0)
            st.metric("Q/Q Wachstum", f"{eg*100:.2f}%" if eg else 'n/a')
        st.subheader("Letzte 90 Tage: Schlusskurse & Veränderung")
        st.dataframe(df[['Close','Change']])
