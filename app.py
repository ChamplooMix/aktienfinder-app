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
def history_90(ticker: str) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(
        period="90d", interval="1d", actions=False, auto_adjust=True
    )
    df["Change"] = df["Close"].pct_change() * 100
    return df

@st.cache_data(ttl=3600)
def cached_history(ticker: str) -> pd.DataFrame:
    return history_90(ticker)

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
        dy = inf.get("dividendYield", None)
        dy_str = f"{dy*100:.2f}%" if dy else "n/a"
        peg = inf.get("pegRatio", "n/a")
        pb = inf.get("priceToBook", "n/a")
        ps = inf.get("priceToSalesTrailing12Months", "n/a")
        h52 = inf.get("fiftyTwoWeekHigh", "n/a")
        l52 = inf.get("fiftyTwoWeekLow", "n/a")

        with st.expander(f"{t} — {mc:,} USD MarketCap", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Kurs:** {pr:.2f} {inf.get('currency','')}")
            c2.write(f"**Δ heute:** {ch:.2f}%")
            c3.write(f"**52w H/L:** {h52} / {l52}")

            c4, c5, c6 = st.columns(3)
            c4.write(f"**P/E:** {pe}")
            c5.write(f"**Div.-Rendite:** {dy_str}")
            c6.write(f"**PEG Ratio:** {peg}")

            c7, c8, c9 = st.columns(3)
            c7.write(f"**P/B:** {pb}")
            c8.write(f"**P/S:** {ps}")
            if c9.button("🔍 Details", key=f"btn_{t}"):
                st.session_state.selected = t
                st.session_state.view = "Detail"
                st.experimental_rerun()

# Detail-View
else:
    t = st.session_state.selected
    header, close_col = st.columns([8,1])
    header.subheader(f"Details zu {t}")
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
            "Dividendenrendite",
            f"{(inf.get('dividendYield',0)*100):.2f}%" if inf.get("dividendYield") else "n/a"
        ),
        ("P/B", inf.get("priceToBook","n/a")),
        ("P/S", inf.get("priceToSalesTrailing12Months","n/a")),
        ("PEG", inf.get("pegRatio","n/a"))
    ]
    for i in range(0, len(metrics), 2):
        c1, c2 = st.columns(2)
        c1.metric(metrics[i][0], metrics[i][1])
        if i+1 < len(metrics):
            c2.metric(metrics[i+1][0], metrics[i+1][1])

    # Earnings Historie
    st.subheader("Earnings Historie")
    try:
        earn = yf.Ticker(t).earnings
        st.table(earn)
    except Exception:
        st.write("Keine Earnings-Daten verfügbar.")

    # Ausblick & Fair Value
    st.subheader("Ausblick & Fair Value")
    f_eps = inf.get('forwardEps', None)
    growth = inf.get('earningsQuarterlyGrowth', 0) or 0
    industry_pe = inf.get('industryPE', None)
    if f_eps and industry_pe:
        fv_curr = f_eps * industry_pe
        fv_next = f_eps * (1 + growth) * industry_pe
        st.metric("Fair Value Ende laufendes Jahr", f"{fv_curr:.2f} {inf.get('currency','')}")
        st.metric("Fair Value Ende nächstes Jahr", f"{fv_next:.2f} {inf.get('currency','')}")
    else:
        st.write("Nicht genügend Daten, um Fair Value zu berechnen.")
