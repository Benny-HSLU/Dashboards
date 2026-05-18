import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Debug Dashboard", layout="wide")


@st.cache_data
def load_data():
    # Wir laden das CSV und konvertieren die Zeitreihe
    df = pd.read_csv("data.csv")
    df['Zeitreihe'] = pd.to_datetime(df['Zeitreihe'])
    return df


try:
    df = load_data()

    st.title("🔍 Daten-Integrität & Debugging")
    st.info(
        "Hier werden alle Spalten des CSV-Files einzeln visualisiert, um Unregelmäßigkeiten in den Rohdaten zu finden.")

    # --- Sidebar Konfiguration ---
    # Wir schieben die Steuerung wieder nach unten, wie gewünscht
    for _ in range(10):
        st.sidebar.write("\n")

    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Debug-Filter")

    # Zeitraum-Auswahl
    date_range = st.sidebar.date_input(
        "Analyse-Zeitraum",
        [df['Zeitreihe'].min(), df['Zeitreihe'].max()]
    )

    # Spalten-Auswahl (falls man nur bestimmte Spalten prüfen will)
    all_columns = [col for col in df.columns if col != 'Zeitreihe']
    selected_cols = st.sidebar.multiselect(
        "Spalten filtern",
        options=all_columns,
        default=all_columns
    )

    if len(date_range) == 2:
        mask = (df['Zeitreihe'].dt.date >= date_range[0]) & (df['Zeitreihe'].dt.date <= date_range[1])
        f_df = df.loc[mask].copy()

        if not selected_cols:
            st.warning("Bitte wählen Sie mindestens eine Spalte in der Sidebar aus.")
        else:
            # --- Dynamische Grafiken ---
            for col in selected_cols:
                with st.expander(f"Spalte: {col}", expanded=True):
                    # Erstellung einer individuellen Grafik pro Spalte
                    chart = alt.Chart(f_df).mark_line(
                        color='#555555',
                        strokeWidth=1.5
                    ).encode(
                        x=alt.X('Zeitreihe:T', title='Zeit'),
                        y=alt.Y(f'{col}:Q', title='Wert', scale=alt.Scale(zero=False)),
                        tooltip=['Zeitreihe', col]
                    ).properties(
                        width='container',
                        height=200
                    ).interactive()

                    st.altair_chart(chart, use_container_width=True)

                    # Kleine Statistik-Zeile unter jeder Grafik
                    col_min = f_df[col].min()
                    col_max = f_df[col].max()
                    col_avg = f_df[col].mean()
                    st.caption(f"Min: {col_min:.2f} | Max: {col_max:.2f} | Durchschnitt: {col_avg:.2f}")

except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")