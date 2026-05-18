import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Experten-Dashboard", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df['Zeitreihe'] = pd.to_datetime(df['Zeitreihe'])
    return df


df = load_data()

# --- FIXE FARBSKALA DEFINIEREN (für den Trend) ---
wohnungen_namen = [f"Wohnung {i}" for i in range(1, 11)]
farb_palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]
feste_farbskala = alt.Scale(domain=wohnungen_namen, range=farb_palette)

# --- SIDEBAR OBEN: WOHNUNGS-AUSWAHL ---
st.sidebar.header("Wohnungen auswählen")
wohnung_options = list(range(1, 11))
selected_wohnungen = []

for i in wohnung_options:
    if st.sidebar.checkbox(f"Wohnung {i}", value=True, key=f"expert_w_{i}"):
        selected_wohnungen.append(i)

st.sidebar.write("---")

# --- SIDEBAR UNTEN: ZEITRAUM ---
st.sidebar.subheader("📅 Analyse-Zeitraum")
date_range = st.sidebar.date_input(
    "Zeitraum wählen",
    [df['Zeitreihe'].min(), df['Zeitreihe'].max()]
)

# --- HAUPTBEREICH ---
st.title("⚙️ Technisches Monitoring (Verwaltung)")

if len(date_range) == 2 and len(selected_wohnungen) > 0:
    mask = (df['Zeitreihe'].dt.date >= date_range[0]) & (df['Zeitreihe'].dt.date <= date_range[1])
    f_df = df.loc[mask].copy()

    # Spaltennamen basierend auf der Sidebar-Auswahl generieren (für Heatmaps & Trend)
    selected_temp_cols = [f'Temp_Sensor_{i}' for i in selected_wohnungen]
    selected_hum_cols = [f'Feuchte_Sensor_{i}' for i in selected_wohnungen]

    # Dynamische Mittelwerte für die Heatmaps berechnen
    f_df['Mittelwert_Innentemperatur_Auswahl'] = f_df[selected_temp_cols].mean(axis=1)
    f_df['Mittelwert_Feuchtigkeit_Auswahl'] = f_df[selected_hum_cols].mean(axis=1)

    # Globaler Mittelwert-Spaltenname aus dem Datensatz fischen
    global_temp_col = [c for c in f_df.columns if 'Innentemperatur' in c and 'Mittelwert' in c][0]

    # =========================================================================
    # NEU: DROPDOWN FÜR HEIZKURVE & NEUE SCHWELLENWERTE
    # =========================================================================
    st.subheader("Heizkurve: Vorlauftemperatur vs. Aussentemperatur")

    # Optionen für das Dropdown-Menü bauen
    dropdown_options = ["Gesamtes Gebäude (Mittelwert)"] + [f"Wohnung {i}" for i in range(1, 11)]

    selected_curve_target = st.selectbox(
        "Datenbasis für die farbliche Status-Einfärbung der Heizkurve wählen:",
        options=dropdown_options,
        index=0
    )

    # Bestimmen, welche Spalte für die Farbberechnung herangezogen wird
    if selected_curve_target == "Gesamtes Gebäude (Mittelwert)":
        color_target_col = global_temp_col
        label_tooltip = "Ø Temp Gebäude"
    else:
        # Extrahiert die Nummer der Wohnung aus dem String, z.B. "Wohnung 5" -> 5
        whg_num = selected_curve_target.split(" ")[1]
        color_target_col = f'Temp_Sensor_{whg_num}'
        label_tooltip = f"Temp {selected_curve_target}"


    # Funktion für die neuen Schwellenwerte (> 23°C und < 20°C)
    def get_expert_color_updated(temp):
        if pd.isna(temp): return 'Keine Daten'
        if temp > 23: return 'Heiss (> 23°C)'
        if temp < 20: return 'Kalt (< 20°C)'
        return 'Normal (20-23°C)'


    # Temporäre Spalte für die Visualisierungsfarbe anlegen
    f_df['Heizkurve_Status_Farbe'] = f_df[color_target_col].apply(get_expert_color_updated)

    color_scale = alt.Scale(
        domain=['Heiss (> 23°C)', 'Normal (20-23°C)', 'Kalt (< 20°C)'],
        range=['red', 'green', 'blue']
    )

    y_min = f_df['Vorlauftemperatur_KWH04'].min() - 2
    y_max = f_df['Vorlauftemperatur_KWH04'].max() + 2

    base = alt.Chart(f_df).encode(
        x=alt.X('Aussentemperatur_Meteoswiss:Q', title='Aussentemperatur (°C)'),
        y=alt.Y('Vorlauftemperatur_KWH04:Q', title='Vorlauftemperatur (°C)', scale=alt.Scale(domain=[y_min, y_max]))
    )

    points = base.mark_point(filled=True, size=80).encode(
        color=alt.Color('Heizkurve_Status_Farbe:N', scale=color_scale, title=f"Status: {selected_curve_target}"),
        tooltip=[
            alt.Tooltip('Zeitreihe:T', title='Datum'),
            alt.Tooltip('Aussentemperatur_Meteoswiss:Q', title='Aussen-Temp', format='.1f'),
            alt.Tooltip('Vorlauftemperatur_KWH04:Q', title='Vorlauf-Temp', format='.1f'),
            alt.Tooltip(f'{color_target_col}:Q', title=label_tooltip, format='.1f')
        ]
    )

    trend = base.transform_regression('Aussentemperatur_Meteoswiss', 'Vorlauftemperatur_KWH04').mark_line(color='red',
                                                                                                          size=3)

    st.altair_chart(points + trend, use_container_width=True)
    # =========================================================================

    # --- 2. Calendar Heatmaps ---
    st.divider()
    st.subheader("📅 Zeitliche Heatmaps (Mittelwert der gewählten Wohnungen)")

    f_df['Woche'] = f_df['Zeitreihe'].dt.isocalendar().week
    f_df['Wochentag'] = f_df['Zeitreihe'].dt.strftime('%a')
    wochentage_ordnung = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    heat_col1, heat_col2 = st.columns(2)

    with heat_col1:
        st.markdown("**Ø Innentemperatur gewählte Wohnungen**")
        heatmap_t = alt.Chart(f_df).mark_rect().encode(
            x=alt.X('Woche:O', title='Kalenderwoche', scale=alt.Scale(paddingInner=0.05)),
            y=alt.Y('Wochentag:O', title='Wochentag', sort=wochentage_ordnung),
            color=alt.Color('Mittelwert_Innentemperatur_Auswahl:Q',
                            scale=alt.Scale(scheme='yelloworangered'),
                            title='Temp (°C)'),
            tooltip=[
                alt.Tooltip('Zeitreihe:T', title='Datum'),
                alt.Tooltip('Mittelwert_Innentemperatur_Auswahl:Q', title='Ø Temp (Auswahl)', format='.1f')
            ]
        ).properties(height=260)
        st.altair_chart(heatmap_t, use_container_width=True)

    with heat_col2:
        st.markdown("**Ø Luftfeuchtigkeit gewählte Wohnungen**")
        heatmap_h = alt.Chart(f_df).mark_rect().encode(
            x=alt.X('Woche:O', title='Kalenderwoche', scale=alt.Scale(paddingInner=0.05)),
            y=alt.Y('Wochentag:O', title='Wochentag', sort=wochentage_ordnung),
            color=alt.Color('Mittelwert_Feuchtigkeit_Auswahl:Q',
                            scale=alt.Scale(scheme='tealblues'),
                            title='Feuchte (%)'),
            tooltip=[
                alt.Tooltip('Zeitreihe:T', title='Datum'),
                alt.Tooltip('Mittelwert_Feuchtigkeit_Auswahl:Q', title='Ø Feuchte (Auswahl)', format='.1f')
            ]
        ).properties(height=260)
        st.altair_chart(heatmap_h, use_container_width=True)

    # --- 3. Wöchentlicher Trend ---
    st.divider()
    st.subheader("🗓️ Wöchentlicher Trend (Durchschnitt nach Wochentag pro Wohnung)")

    temp_long = f_df.melt(id_vars=['Zeitreihe', 'Wochentag'], value_vars=selected_temp_cols, var_name='Wohnung',
                          value_name='Temp')
    temp_long['Wohnung'] = temp_long['Wohnung'].str.replace('Temp_Sensor_', 'Wohnung ')

    hum_long = f_df.melt(id_vars=['Zeitreihe', 'Wochentag'], value_vars=selected_hum_cols, var_name='Wohnung',
                         value_name='Hum')
    hum_long['Wohnung'] = hum_long['Wohnung'].str.replace('Feuchte_Sensor_', 'Wohnung ')

    trend_col1, trend_col2 = st.columns(2)

    with trend_col1:
        st.markdown("**Wöchentlicher Temperatur-Trend**")
        weekly_trend_t = alt.Chart(temp_long).transform_aggregate(
            Mittelwert_Temp='mean(Temp)', groupby=['Wochentag', 'Wohnung']
        ).mark_line(point=True).encode(
            x=alt.X('Wochentag:O', title='Wochentag', sort=wochentage_ordnung),
            y=alt.Y('Mittelwert_Temp:Q', title='Ø Temperatur (°C)', scale=alt.Scale(zero=False)),
            color=alt.Color('Wohnung:N', scale=feste_farbskala),
            tooltip=['Wohnung', 'Wochentag', alt.Tooltip('Mittelwert_Temp:Q', title='Ø Temp', format='.1f')]
        ).properties(height=300)
        st.altair_chart(weekly_trend_t, use_container_width=True)

    with trend_col2:
        st.markdown("**Wöchentlicher Feuchtigkeits-Trend**")
        weekly_trend_h = alt.Chart(hum_long).transform_aggregate(
            Mittelwert_Hum='mean(Hum)', groupby=['Wochentag', 'Wohnung']
        ).mark_line(point=True).encode(
            x=alt.X('Wochentag:O', title='Wochentag', sort=wochentage_ordnung),
            y=alt.Y('Mittelwert_Hum:Q', title='Ø relative Feuchte (%)'),
            color=alt.Color('Wohnung:N', scale=feste_farbskala),
            tooltip=['Wohnung', 'Wochentag', alt.Tooltip('Mittelwert_Hum:Q', title='Ø Feuchte', format='.1f')]
        ).properties(height=300)
        st.altair_chart(weekly_trend_h, use_container_width=True)

    # Technische KPIs ganz unten
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric("Max. Vorlauf im Zeitraum", f"{f_df['Vorlauftemperatur_KWH04'].max():.1f} °C")
    m2.metric("Min. Aussen im Zeitraum", f"{f_df['Aussentemperatur_Meteoswiss'].min():.1f} °C")

elif len(selected_wohnungen) == 0:
    st.warning("Bitte wählen Sie mindestens eine Wohnung in der Sidebar aus, um die Analyse zu starten.")
else:
    st.info("Bitte wählen Sie einen Zeitraum in der Sidebar aus.")