import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# Session-State initialisieren
if "view" not in st.session_state:
    st.session_state.view = "Übersicht"
if "selected" not in st.session_state:
    st.session_state.selected = None

# Seiten-Konfiguration & Header
st.set_page_config(layout="wide")
st.markdown(
    """
    <div style="background-color:#207373;padding:10px;border-radius:10px">
        <h1 style="color:white;text-align:center;">Aktienfinder-Clone</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Helper-Funktionen
@st.cache_data(ttl=3600)
def history_90(ticker: str) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(
        period="90d", interval="1d", actions=False, auto_adjust=True
    )
    df["Change"] = df["Close"].pct_change() * 100
    return df

@st.cache_data(ttl=3600)
def info(ticker: str) -> dict:
    return yf.Ticker(ticker).info

# Übersicht-View
if st.session_state.view == "Übersicht":
    st.subheader("Top 20 nach Marktkapitalisierung (weltweit)")

    tickers = [
        "AAPL","MSFT","GOOGL","AMZN","TSLA",
        "NVDA","META","BABA","TSM","V",
        "JNJ","WMT","JPM","UNH","LVMUY",
        "ROIC.F","SAP.DE","TM","OR.PA","NESN.SW"
    ]

    for t in tickers:
        inf = info(t)
        df = history_90(t)
        mc = inf.get("marketCap", 0)
        pr = inf.get("regularMarketPrice", 0)
        ch = df["Change"].iloc[-1] if not df.empty else 0
        pe = inf.get("trailingPE", "n/a")
        h52 = inf.get("fiftyTwoWeekHigh", "n/a")
        l52 = inf.get("fiftyTwoWeekLow", "n/a")

        with st.expander(f"{t} — {mc:,} USD MarketCap", expanded=False):
            c1, c2 = st.columns(2)
            c1.write(f"**Kurs:** {pr:.2f} {inf.get('currency','')}")
            c2.write(f"**Δ heute:** {ch:.2f}%")

            c3, c4 = st.columns(2)
            c3.write(f"**P/E:** {pe}")
            c4.write(f"**52w H/L:** {h52} / {l52}")

            if st.button("🔍 Details", key=f"btn_{t}"):
                st.session_state.selected = t
                st.session_state.view = "Detail"
                st.experimental_rerun()

# Detail-View
else:
    t = st.session_state.selected
    header_col, close_col = st.columns([9,1])
    header_col.subheader(f"Details zu {t}")
    if close_col.button("❌"):
        st.session_state.view = "Übersicht"
        st.session_state.selected = None
        st.experimental_rerun()

    df = history_90(t)
    inf = info(t)

    # Chart
    chart = (
        alt.Chart(df.reset_index())
        .mark_line(point=True)
        .encode(
            x="Date:T",
            y="Close:Q",
            tooltip=["Date","Close","Change"]
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    # Mobile-optimierte Kennzahlen
    metrics = [
        ("Branche", inf.get("sector","n/a")),
        ("Unterbranche", inf.get("industry","n/a")),
        ("P/E", inf.get("trailingPE","n/a")),
        (
            "Div.-Rendite",
            f"{(inf.get('dividendRate',0) / inf.get('regularMarketPrice',1) * 100):.2f}%"
            if inf.get("dividendRate") else "n/a"
        ),
        ("Letztes EPS", inf.get("trailingEps","n/a")),
        ("Forward EPS", inf.get("forwardEps","n/a")),
        (
            "Q/Q Wachstum",
            f"{(inf.get('earningsQuarterlyGrowth',0) * 100):.2f}%"
            if inf.get("earningsQuarterlyGrowth") else "n/a"
        ),
    ]
    for i in range(0, len(metrics), 2):
        col1, col2 = st.columns(2)
        col1.metric(metrics[i][0], metrics[i][1])
        if i+1 < len(metrics):
            col2.metric(metrics[i+1][0], metrics[i+1][1])

    # Tabelle
    st.subheader("Letzte 90 Tage: Schlusskurse & Veränderung")
    st.dataframe(df[["Close","Change"]], use_container_width=True)
