import streamlit as st

st.set_page_config(page_title="Gebäude Monitoring", layout="wide")

st.title("Willkommen beim Gebäude-Monitoring-System")
st.markdown("""
Wählen Sie links in der Sidebar das passende Dashboard aus:
- **Laien-Dashboard**: Fokus auf Wohnkomfort (Temperatur & Feuchtigkeit).
- **Experten-Dashboard**: Technische Analyse der Heizkurve und Gebäudeperformance.
""")