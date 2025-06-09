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

# Header mit Skobeloff-Hintergrund
st.markdown(
    """
    <div style=\"background-color:#207373;padding:10px;border-radius:10px\">
        <h1 style=\"color:white;text-align:center;\">Aktienfinder-Clone</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Übersicht oder Detail basierend auf Session State
if st.session_state.view == 'Übersicht':
    st.subheader("Top 20 nach Marktkapitalisierung (weltweit)")
    top_tickers = [
        "AAPL","MSFT","GOOGL","AMZN","TSLA",
        "NVDA","META","BABA","TSM","V",
        "JNJ","WMT","JPM","UNH","LVMUY",
        "ROIC.F","SAP.DE","TM","OR.PA","NESN.SW"
    ]
    rows = []
    for t in top_tickers:
        info = get_info(t)
        cap = info.get('marketCap', 0)
        price = info.get('regularMarketPrice', 0)
        df_hist = get_history_last_90_days(t)
        change = df_hist['Change'].iloc[-1] if not df_hist.empty else None
        pe = info.get('trailingPE', None)
        high = info.get('fiftyTwoWeekHigh', None)
        low = info.get('fiftyTwoWeekLow', None)
        rows.append({
            'Ticker': t,
            'MarketCap': cap,
            'Price': price,
            'Change': change,
            'P/E': pe,
            '52wHigh': high,
            '52wLow': low
        })
    df_overview = pd.DataFrame(rows).sort_values('MarketCap', ascending=False)

    # Pagination
    page = st.sidebar.number_input("Seite", min_value=1, max_value=2, value=1)
    per_page = 10
    start = (page-1)*per_page
    end = page*per_page
    df_page = df_overview.iloc[start:end]

    st.write("**Klicke auf ein Ticker für Details**")
    for _, row in df_page.iterrows():
        cols = st.columns([1,2,1,1,1,1,1])
        if cols[0].button(row['Ticker'], key=f"btn_{row['Ticker']}"):
            st.session_state.view = 'Detailansicht'
            st.session_state.selected_ticker = row['Ticker']
            st.experimental_rerun()
        cols[1].write(f"{row['MarketCap']:,}")
        cols[2].write(f"{row['Price']}")
        cols[3].write(f"{row['Change']:.2f}%" if row['Change'] is not None else 'n/a')
        cols[4].write(f"{row['P/E']:.2f}" if row['P/E'] else 'n/a')
        cols[5].write(f"{row['52wHigh']:.2f}" if row['52wHigh'] else 'n/a')
        cols[6].write(f"{row['52wLow']:.2f}" if row['52wLow'] else 'n/a')

else:
    # Detailansicht: Titelleiste mit Close-Button
    ticker = st.session_state.selected_ticker
    header_cols = st.columns([9,1])
    header_cols[0].subheader(f"Details zu {ticker}")
    if header_cols[1].button("❌", key="close_detail"):
        st.session_state.view = 'Übersicht'
        st.session_state.selected_ticker = None
        st.experimental_rerun()

    # Daten laden
    df = get_history_last_90_days(ticker)
    info = get_info(ticker)
    if df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
    else:
        df_reset = df.reset_index()
        chart = alt.Chart(df_reset).mark_line(point=True).encode(
            x="Date:T", y=alt.Y("Close:Q", title="Schlusskurs"), tooltip=["Date","Close","Change"]
        ).properties(width=700, height=300)
        st.altair_chart(chart, use_container_width=True)

        st.markdown("**Unternehmensinformationen**")
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**Branche:** {info.get('sector','n/a')}")
            st.write(f"**Unterbranche:** {info.get('industry','n/a')}")
            st.metric("P/E Ratio", info.get('trailingPE','n/a'))
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

        st.subheader("Letzte 90 Tage: Schlusskurse & Veränderung")
        st.dataframe(df[['Close','Change']])
