import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# Initialisierung
if 'view' not in st.session_state:
    st.session_state.view = 'Übersicht'
if 'selected' not in st.session_state:
    st.session_state.selected = None

st.set_page_config(layout="wide")
st.markdown(
    """<div style="background-color:#207373;padding:10px;border-radius:10px">
        <h1 style="color:white;text-align:center;">Aktienfinder-Clone</h1>
    </div>""",
    unsafe_allow_html=True
)

# Helfer
@st.cache_data(ttl=3600)
def history_90(ticker):
    df = yf.Ticker(ticker).history(period="90d", interval="1d", actions=False, auto_adjust=True)
    df['Change'] = df['Close'].pct_change()*100
    return df

@st.cache_data(ttl=3600)
def info(ticker):
    return yf.Ticker(ticker).info

# Übersicht
if st.session_state.view == 'Übersicht':
    st.subheader("Top 20 nach Marktkapitalisierung")
    tickers = ["AAPL","MSFT","GOOGL","AMZN","TSLA","NVDA","META","BABA","TSM","V",
               "JNJ","WMT","JPM","UNH","LVMUY","ROIC.F","SAP.DE","TM","OR.PA","NESN.SW"]
    for t in tickers:
        inf = info(t)
        df = history_90(t)
        mc = inf.get("marketCap", 0)
        pr = inf.get("regularMarketPrice", 0)
        ch = df['Change'].iloc[-1] if not df.empty else 0
        pe = inf.get("trailingPE", None)
        h52 = inf.get("fiftyTwoWeekHigh", None)
        l52 = inf.get("fiftyTwoWeekLow", None)

        # Ein Eintrag pro Ticker
        with st.expander(f"{t} – {mc:,} USD MktCap", expanded=False):
            cols = st.columns(2)
            cols[0].write(f"**Kurs:** {pr:.2f} {inf.get('currency','')}")
            cols[1].write(f"**∆ heute:** {ch:.2f}%")
            cols = st.columns(2)
            cols[0].write(f"**P/E:** {pe or 'n/a'}")
            cols[1].write(f"**52wH/L:** {h52 or 'n/a'} / {l52 or 'n/a'}")
            if st.button("🔍 Details", key=f"btn_{t}"):
                st.session_state.selected = t
                st.session_state.view = 'Detail'
                st.experimental_rerun()

# Detail
else:
    t = st.session_state.selected
    header, close = st.columns([9,1])
    header.subheader(f"Details: {t}")
    if close.button("❌"):
        st.session_state.view = 'Übersicht'
        st.experimental_rerun()

    df = history_90(t)
    inf = info(t)
    # Chart
    st.altair_chart(
        alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x="Date:T", y="Close:Q", tooltip=["Date","Close","Change"]
        ).properties(width="100%",height=300),
        use_container_width=True
    )
    # Kennzahlen mobil-optimiert
    metrics = [
        ("Branche", inf.get("sector","n/a")),
        ("Unterbranche", inf.get("industry","n/a")),
        ("P/E", inf.get("trailingPE","n/a")),
        ("Div.-Rendite", f"{(inf.get('dividendRate',0)/inf.get('regularMarketPrice',1)*100):.2f}%" if inf.get('dividendRate') else "n/a"),
        ("Letztes EPS", inf.get("trailingEps","n/a")),
        ("Forward EPS", inf.get("forwardEps","n/a")),
        ("Q/Q Wachstum", f"{(inf.get('earningsQuarterlyGrowth',0)*100):.2f}%" if inf.get('earningsQuarterlyGrowth') else "n/a")
    ]
    for i in range(0,len(metrics),2):
        c1, c2 = st.columns(2)
        c1.metric(*metrics[i])
        if i+1 < len(metrics):
            c2.metric(*metrics[i+1])

    # Tabelle
    st.subheader("Letzte 90 Tage: Schlusskurse & Veränderung")
    st.dataframe(df[['Close','Change']], use_container_width=True)
