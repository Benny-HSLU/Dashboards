import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Laien-Dashboard", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df['Zeitreihe'] = pd.to_datetime(df['Zeitreihe'])
    return df


df = load_data()

# --- FIXE FARBSKALA DEFINIEREN ---
wohnungen_namen = [f"Wohnung {i}" for i in range(1, 11)]
farb_palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]
feste_farbskala = alt.Scale(domain=wohnungen_namen, range=farb_palette)

# --- SIDEBAR OBEN ---
st.sidebar.header("Wohnungen auswählen")
wohnung_options = list(range(1, 11))
selected_wohnungen = []

for i in wohnung_options:
    if st.sidebar.checkbox(f"Wohnung {i}", value=True, key=f"layen_w_{i}"):
        selected_wohnungen.append(i)

st.sidebar.write("---")

# --- SIDEBAR UNTEN ---
st.sidebar.subheader("Zeitraum")
date_range = st.sidebar.date_input(
    "Zeitraum auswählen",
    [df['Zeitreihe'].min(), df['Zeitreihe'].max()]
)

# --- HAUPTBEREICH ---
st.title("🏠 Wohnkomfort Übersicht")

if len(date_range) == 2 and len(selected_wohnungen) > 0:
    start_date, end_date = date_range
    mask = (df['Zeitreihe'].dt.date >= start_date) & (df['Zeitreihe'].dt.date <= end_date)
    f_df = df.loc[mask].copy()

    selected_temp_cols = [f'Temp_Sensor_{i}' for i in selected_wohnungen]
    selected_hum_cols = [f'Feuchte_Sensor_{i}' for i in selected_wohnungen]

    col1, col2 = st.columns(2)
    col1.metric("Ø Temperatur", f"{f_df[selected_temp_cols].mean().mean():.1f} °C")
    col2.metric("Ø Feuchtigkeit", f"{f_df[selected_hum_cols].mean().mean():.1f} %")

    # --- 1. Zeitverlauf: Temperatur ---
    st.subheader("Temperaturverlauf pro Wohnung")
    temp_long = f_df.melt(id_vars=['Zeitreihe'], value_vars=selected_temp_cols, var_name='Wohnung', value_name='Temp')
    temp_long['Wohnung'] = temp_long['Wohnung'].str.replace('Temp_Sensor_', 'Wohnung ')

    chart_t = alt.Chart(temp_long).mark_line().encode(
        x='Zeitreihe:T',
        y=alt.Y('Temp:Q', scale=alt.Scale(zero=False), title="Temperatur (°C)"),
        color=alt.Color('Wohnung:N', scale=feste_farbskala)
    ).properties(height=300).interactive()

    st.altair_chart(chart_t, use_container_width=True)

    # --- 2. Zeitverlauf: Feuchtigkeit ---
    st.subheader("Luftfeuchtigkeit pro Wohnung")
    hum_long = f_df.melt(id_vars=['Zeitreihe'], value_vars=selected_hum_cols, var_name='Wohnung', value_name='Hum')
    hum_long['Wohnung'] = hum_long['Wohnung'].str.replace('Feuchte_Sensor_', 'Wohnung ')

    chart_h = alt.Chart(hum_long).mark_line().encode(
        x='Zeitreihe:T',
        y=alt.Y('Hum:Q', title="Feuchtigkeit (%)"),
        color=alt.Color('Wohnung:N', scale=feste_farbskala)
    ).properties(height=300).interactive()

    st.altair_chart(chart_h, use_container_width=True)

    # --- 3. Density Plots ---
    st.divider()
    st.subheader("📊 Häufigkeitsverteilung (Wo lagen die Werte meistens?)")

    density_col1, density_col2 = st.columns(2)

    with density_col1:
        st.markdown("**Verteilung der Temperatur**")
        density_chart_t = alt.Chart(temp_long).transform_density(
            'Temp', as_=['Temp', 'density'], groupby=['Wohnung']
        ).mark_area(opacity=0.3, line=True).encode(
            x=alt.X('Temp:Q', title="Temperatur (°C)"),
            y=alt.Y('density:Q', title="Dichte / Häufigkeit", axis=None),
            color=alt.Color('Wohnung:N', scale=feste_farbskala)
        ).properties(height=250)
        st.altair_chart(density_chart_t, use_container_width=True)

    with density_col2:
        st.markdown("**Verteilung der Luftfeuchtigkeit**")
        density_chart_h = alt.Chart(hum_long).transform_density(
            'Hum', as_=['Hum', 'density'], groupby=['Wohnung']
        ).mark_area(opacity=0.3, line=True).encode(
            x=alt.X('Hum:Q', title="Feuchtigkeit (%)"),
            y=alt.Y('density:Q', title="Dichte / Häufigkeit", axis=None),
            color=alt.Color('Wohnung:N', scale=feste_farbskala)
        ).properties(height=250)
        st.altair_chart(density_chart_h, use_container_width=True)

elif len(selected_wohnungen) == 0:
    st.warning("Bitte wählen Sie mindestens eine Wohnung in der Sidebar aus.")
else:
    st.info("Bitte wählen Sie einen gültigen Zeitraum aus.")