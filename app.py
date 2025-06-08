import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

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
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        # Chart mit Altair und Highlight-Farben
        df_reset = df.reset_index()
        chart = alt.Chart(df_reset).mark_line(point=True).encode(
            x="Date:T",
            y=alt.Y("Close:Q", title="Schlusskurs"),
            tooltip=["Date","Close"]
        ).properties(width=600, height=300)
        st.altair_chart(chart, use_container_width=True)

        # Kennzahlen
        info = stock.info
        cols = st.columns(2)
        with cols[0]:
            st.metric("Aktueller Kurs", f"{info['regularMarketPrice']:.2f} {info['currency']}")
            st.metric("Marktkapitalisierung", f"{info['marketCap']:,}")
        with cols[1]:
            st.metric("PE Ratio", info.get('trailingPE', 'n/a'))
            st.metric("Dividendenrendite", f"{info.get('dividendYield',0)*100:.2f}%")

        # Daten als Tabelle
        st.subheader("Historische Daten")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Daten: {e}")
