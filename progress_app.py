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
grupo_seleccionado = st.selectbox("Selecciona un grupo", grupos_unicos)
location_seleccionado = st.selectbox("Lugar", options=list(lugares_dict.values()))
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

# Filtrar datos por rango de fechas seleccionado
data_filtrado = data[
    (data["fecha"] >= fecha_inicio) & 
    (data["fecha"] <= fecha_fin)
]
data_filtrado = data_filtrado[(data_filtrado["grupo"] == grupo_seleccionado) & (data_filtrado["location"] == location_seleccionado)]
# Crear una lista de ejercicios únicos dentro del grupo seleccionado
ejercicios_unicos = data_filtrado["ejercicio"].unique()

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
    ax.set_facecolor('#313754')  # Cambiar el fondo del gráfico a un gris oscuro
    
    # Filtrar los datos por ejercicio
    df_filtrado = data_filtrado[data_filtrado["ejercicio"] == ejercicio]
    
    # Obtener el máximo de 'kilos' por día
    df_max_kilos_por_dia = df_filtrado.loc[df_filtrado.groupby(df_filtrado["fecha"].dt.date)["kilos"].idxmax()]
    
    # Ordenar por fecha
    df_max_kilos_por_dia = df_max_kilos_por_dia.sort_values(by="fecha")
    
    # Graficar los kilos en el eje izquierdo
    ax.plot(df_max_kilos_por_dia["fecha"], df_max_kilos_por_dia["kilos"], color="#5CD5DD", label="Kilos")
    ax.set_ylabel("Kilos", fontsize=12, color="#5CD5DD")  # Etiqueta del eje Y en blanco
    ax.tick_params(axis="y", labelcolor="white")  # Color de los ticks en blanco
    
    # Crear un segundo eje Y para las repeticiones
    ax2 = ax.twinx()
    ax2.plot(df_max_kilos_por_dia["fecha"], df_max_kilos_por_dia["reps"], color="#DB7DE4", label="Reps")
    ax2.set_ylabel("Reps", fontsize=12, color="#DB7DE4")  # Etiqueta del eje Y2 en blanco
    ax2.tick_params(axis="y", labelcolor="white")  # Color de los ticks en blanco
    
    # Formatear las fechas en el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))  # Formato DD/MM/AAAA
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Ajuste automático de intervalos
    ax.tick_params(axis="x", rotation=90, labelsize=8, labelcolor="white")  # Color de las etiquetas de fecha en blanco
    
    # Agregar cuadrícula
    ax.grid(visible=True, which='major', linestyle='--', linewidth=1, color="#595D73")  # Cuadrícula en blanco
    
    # Título del gráfico
    ax.set_title(f"{ejercicio}", fontsize=20, color="white")  # Título en blanco

# Ocultar cualquier subplot vacío
for idx in range(len(ejercicios_unicos), len(axes)):
    fig.delaxes(axes[idx])

# Mostrar el gráfico en Streamlit
st.pyplot(fig)
