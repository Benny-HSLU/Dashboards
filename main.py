import streamlit as st

st.set_page_config(page_title="Gebäude Monitoring", layout="wide")

st.title("Willkommen beim Gebäude-Monitoring-System")
st.markdown("""
Wählen Sie links in der Sidebar das passende Dashboard aus:
- **Laien-Dashboard**: Schauen sie die Temperatur- und Feuchtigkeitswerte spezifischer Wohnungen nach. Und vergleichen sie sie.
- **Experten-Dashboard**: Technische Analyse der Heizkurve und Trendanalyse.
- **Debug-Dashboard**: Jede Datenquelle einzeln um Anomalien und Incosistenzen zu finden.
""")