import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from oauth2client.service_account import ServiceAccountCredentials
import gspread

lugares_dict = {
    "Libres": "Libres",
    "Otro": "Otro",
    "Pedregal": "Pedregal",
    "Patio": "Patio"
}


# Configurar credenciales para acceder a Google Sheets usando st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_creds"], scope)
gc = gspread.authorize(credentials)

# Abrir la hoja de cálculo
spreadsheet_id = st.secrets["google_creds"]["spreadsheet_id"]
worksheet = gc.open_by_key(spreadsheet_id).worksheet("Hoja 1")

# Obtener los datos desde Google Sheets
registros = worksheet.get_all_records()
data = pd.DataFrame(registros)

# Convertir la columna 'fecha' a tipo datetime
data["fecha"] = pd.to_datetime(data["fecha"])

# Título de la app
st.title("Gráficas por Grupo de Ejercicios")

# Selección del grupo
grupos_unicos = data["grupo"].unique()
location_seleccionado = st.selectbox("Lugar", options=list(lugares_dict.values()))
grupo_seleccionado = st.selectbox("Selecciona un grupo", grupos_unicos)
# Selección de fechas personalizadas o preestablecidas
st.sidebar.header("Filtrar por Fechas")

# Temporadas preestablecidas
temporadas = {
    "Todo": (data["fecha"].min(), data["fecha"].max())
}

# Seleccionar temporada o rango personalizado
temporada_seleccionada = st.sidebar.selectbox("Selecciona una temporada", list(temporadas.keys()))
fecha_inicio, fecha_fin = temporadas[temporada_seleccionada]

# Opción de personalizar fechas
personalizado = st.sidebar.checkbox("Seleccionar rango de fechas personalizado")
if personalizado:
    fecha_inicio = st.sidebar.date_input("Fecha inicio", pd.to_datetime(fecha_inicio))
    fecha_fin = st.sidebar.date_input("Fecha fin", pd.to_datetime(fecha_fin))

# Asegurarse de que las fechas sean del tipo datetime
fecha_inicio = pd.to_datetime(fecha_inicio)
fecha_fin = pd.to_datetime(fecha_fin)

# Obtener solo los ejercicios del grupo seleccionado que tienen datos en la ubicación y fechas elegidas
ejercicios_posibles = data[data["grupo"] == grupo_seleccionado]["ejercicio"].unique()

# Filtrar datos por ubicación y fechas
data_filtrado = data[
    (data["fecha"] >= fecha_inicio) & 
    (data["fecha"] <= fecha_fin) & 
    (data["location"] == location_seleccionado)
]

# Cruzar: ejercicios del grupo que existen en los datos filtrados
ejercicios_unicos = [e for e in ejercicios_posibles if e in data_filtrado["ejercicio"].unique()]

# Determinar el tamaño del mosaico
num_ejercicios = len(ejercicios_unicos)
cols = 2
rows = (num_ejercicios + cols - 1) // cols  # Redondear hacia arriba para filas

# Crear el mosaico de subplots
fig, axes = plt.subplots(rows, cols, figsize=(20, 7 * rows), dpi=500, constrained_layout=True)
fig.patch.set_facecolor('#0F1116')
axes = axes.flatten()  # Aplanar el arreglo de ejes para iterar fácilmente


# Iterar sobre cada ejercicio y graficar
for idx, ejercicio in enumerate(ejercicios_unicos):
    ax = axes[idx]
    ax.set_facecolor('#313754')  # Fondo del gráfico

    # 1. Filtrar los datos por ejercicio
    df_ejercicio = data_filtrado[data_filtrado["ejercicio"] == ejercicio].copy()
    
    if df_ejercicio.empty:
        continue

    # 2. Encontrar el peso máximo por día
    # Creamos una columna temporal con la fecha (sin hora) para agrupar
    df_ejercicio['fecha_dia'] = df_ejercicio['fecha'].dt.date
    max_kilos_por_dia = df_ejercicio.groupby('fecha_dia')['kilos'].transform('max')

    # 3. Filtrar para quedarnos SOLO con los sets que alcanzaron ese peso máximo
    df_sets_max = df_ejercicio[df_ejercicio['kilos'] == max_kilos_por_dia].copy()

    # 4. Agrupar para obtener estadísticas de esos sets por día
    # Necesitamos: Kilos (el valor), Reps Min, Reps Max y Reps Promedio
    df_stats = df_sets_max.groupby('fecha').agg(
        kilos=('kilos', 'first'),
        reps_min=('reps', 'min'),
        reps_max=('reps', 'max'),
        reps_mean=('reps', 'mean')
    ).reset_index().sort_values("fecha")

    # --- GRAFICAR KILOS (Eje Izquierdo - Azul) ---
    ax.plot(df_stats["fecha"], df_stats["kilos"], color="#5CD5DD", linewidth=4, label="Kilos Máx", zorder=3)
    ax.set_ylabel("Kilos", fontsize=12, color="#5CD5DD")
    ax.tick_params(axis="y", labelcolor="#5CD5DD", labelsize=12)

    # Etiquetar solo el primer y último punto de kilos
    primer = df_stats.iloc[0]
    ultimo = df_stats.iloc[-1]
    ax.text(primer["fecha"], primer["kilos"], f'{primer["kilos"]:.1f} kg', color="#5CD5DD", 
            fontsize=10, ha='right', va='bottom', fontweight='bold')
    ax.text(ultimo["fecha"], ultimo["kilos"], f'{ultimo["kilos"]:.1f} kg', color="#5CD5DD", 
            fontsize=10, ha='left', va='bottom', fontweight='bold')

    # --- GRAFICAR REPS (Eje Secundario - Rosa con Banda) ---
    ax2 = ax.twinx()
    
    # Dibujar la BANDA (relleno entre el mínimo y máximo de reps)
    ax2.fill_between(
        df_stats["fecha"], 
        df_stats["reps_min"], 
        df_stats["reps_max"], 
        color="#DB7DE4", 
        alpha=0.3,          # Transparencia para que se vea como una sombra/banda
        label="Dispersión Reps"
    )
    
    # Dibujar la línea central (promedio) para que la banda tenga una "guía"
    ax2.plot(df_stats["fecha"], df_stats["reps_mean"], color="#DB7DE4", linewidth=1.5, label="Reps Media")
    
    ax2.set_ylabel("Reps (en peso máx)", fontsize=12, color="#DB7DE4")
    ax2.tick_params(axis="y", labelcolor="#DB7DE4", labelsize=12)

    # Formatear fechas en el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.tick_params(axis="x", rotation=45, labelsize=8, labelcolor="white")

    # Cuadrícula
    ax.grid(visible=True, axis='y', which='major', linestyle='--', linewidth=0.5, color="#595D73")
    for fecha in df_stats["fecha"]:
        ax.axvline(x=fecha, linestyle=':', linewidth=0.4, color="#595D73")

    ax.set_title(f"{ejercicio}", fontsize=18, color="white", pad=20)

# Ocultar subplots vacíos
for idx in range(len(ejercicios_unicos), len(axes)):
    fig.delaxes(axes[idx])

st.pyplot(fig)



