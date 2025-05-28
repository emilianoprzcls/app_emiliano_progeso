import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from oauth2client.service_account import ServiceAccountCredentials
import gspread

lugares_dict = {
    "CIDE": "CIDE",
    "Libres": "Libres",
    "Otro": "Otro",
    "SmartFit": "SmartFit"
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
    "Primavera ME2": ("2025-02-01", data["fecha"].max()),
    "2025": ("2025-01-01", data["fecha"].max()),
    "Otoño ME1": ("2024-09-30", "2024-12-18"),
    "Smartfit Invierno": ("2024-12-18", pd.Timestamp("today").date()),
    "Todo": (data["fecha"].min(), data["fecha"].max()),
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

    # Filtrar los datos por ejercicio
    df_filtrado = data_filtrado[data_filtrado["ejercicio"] == ejercicio]

    # Obtener el máximo de 'kilos' por día
    df_max_kilos_por_dia = df_filtrado.loc[df_filtrado.groupby(df_filtrado["fecha"].dt.date)["kilos"].idxmax()]

    # Ordenar por fecha
    df_max_kilos_por_dia = df_max_kilos_por_dia.sort_values(by="fecha")

    # Graficar los kilos en el eje izquierdo
    ax.plot(df_max_kilos_por_dia["fecha"], df_max_kilos_por_dia["kilos"], color="#5CD5DD", label="Kilos")
    ax.set_ylabel("Kilos", fontsize=12, color="#5CD5DD")
    ax.tick_params(axis="y", labelcolor="#5CD5DD", labelsize=12)

    # Etiquetar solo el primer y último punto
    if not df_max_kilos_por_dia.empty:
        primer = df_max_kilos_por_dia.iloc[0]
        ultimo = df_max_kilos_por_dia.iloc[-1]
        ax.text(primer["fecha"], primer["kilos"], f'{primer["kilos"]:.1f} kg', color="#5CD5DD", fontsize=10, ha='right', va='bottom')
        ax.text(ultimo["fecha"], ultimo["kilos"], f'{ultimo["kilos"]:.1f} kg', color="#5CD5DD", fontsize=10, ha='left', va='bottom')

    # Crear eje secundario para reps
    ax2 = ax.twinx()
    ax2.plot(df_max_kilos_por_dia["fecha"], df_max_kilos_por_dia["reps"], linestyle='--', color="#DB7DE4", label="Reps")
    ax2.set_ylabel("Reps", fontsize=12, color="#DB7DE4")
    ax2.tick_params(axis="y", labelcolor="#DB7DE4", labelsize=12)

    # Remover etiquetas numéricas del eje derecho (pero mantener la línea)
    ax2.set_yticklabels([])

    # Formatear fechas en el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.tick_params(axis="x", rotation=90, labelsize=8, labelcolor="white")

    # Cuadrícula: horizontal para kilos (izquierda), vertical para fechas
    ax.grid(visible=True, axis='y', which='major', linestyle='--', linewidth=1, color="#595D73")  # Horizontal
    for fecha in df_max_kilos_por_dia["fecha"]:
        ax.axvline(x=fecha, linestyle='--', linewidth=0.5, color="#595D73")  # Vertical

    # Título del gráfico
    ax.set_title(f"{ejercicio}", fontsize=20, color="white")

# Ocultar cualquier subplot vacío
for idx in range(len(ejercicios_unicos), len(axes)):
    fig.delaxes(axes[idx])

# Mostrar en Streamlit
st.pyplot(fig)



