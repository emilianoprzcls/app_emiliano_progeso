import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Configurar credenciales para acceder a Google Sheets usando st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_creds"], scope)
gc = gspread.authorize(credentials)

# Abrir el documento
spreadsheet_id = st.secrets["google_creds"]["spreadsheet_id"]
doc = gc.open_by_key(spreadsheet_id)

# 1. Obtener los datos de los entrenamientos (Hoja 1)
worksheet_datos = doc.worksheet("Hoja 1")
registros = worksheet_datos.get_all_records()
data = pd.DataFrame(registros)
data["fecha"] = pd.to_datetime(data["fecha"])

# 2. Obtener los datos de configuración (Nueva pestaña)
worksheet_config = doc.worksheet("Configuracion")
config_registros = worksheet_config.get_all_records()
df_config = pd.DataFrame(config_registros)

# Título de la app
st.title("Gráficas por Grupo de Ejercicios")

# Selección del grupo (Ahora estático basado en tus columnas)
grupos_disponibles = ["Push", "Pull", "Legs", "Upper"]
grupo_seleccionado = st.selectbox("Selecciona un grupo", grupos_disponibles)

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

# 3. Extraer los ejercicios y lugares del grupo seleccionado desde la hoja de configuración
col_ejercicio = f"{grupo_seleccionado}_Ejercicio"
col_lugar = f"{grupo_seleccionado}_Lugar"

# Filtramos filas vacías de esa configuración específica
df_grupo_config = df_config[[col_ejercicio, col_lugar]].replace('', pd.NA).dropna()

# 4. Preparar los datos válidos a graficar
graficos_data = []

for index, row in df_grupo_config.iterrows():
    ejercicio_actual = row[col_ejercicio]
    lugar_actual = row[col_lugar]
    
    # Filtrar datos principales por ejercicio, lugar configurado y fechas
    df_ejercicio = data[
        (data["ejercicio"] == ejercicio_actual) & 
        (data["location"] == lugar_actual) & 
        (data["fecha"] >= fecha_inicio) & 
        (data["fecha"] <= fecha_fin)
    ].copy()
    
    if not df_ejercicio.empty:
        graficos_data.append({
            "ejercicio": ejercicio_actual,
            "lugar": lugar_actual,
            "df": df_ejercicio
        })

# 5. Configurar el mosaico
num_ejercicios = len(graficos_data)

if num_ejercicios == 0:
    st.warning(f"No hay datos registrados para el grupo {grupo_seleccionado} en este rango de fechas.")
else:
    cols = 2
    rows = (num_ejercicios + cols - 1) // cols  # Redondear hacia arriba

    fig, axes = plt.subplots(rows, cols, figsize=(20, 7 * rows), dpi=500, constrained_layout=True)
    fig.patch.set_facecolor('#0F1116')
    
    # Si solo hay 1 fila y 1 columna, axes no es un arreglo, lo convertimos para evitar errores
    if num_ejercicios == 1 and rows == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Iterar sobre los datos válidos y graficar
    for idx, item in enumerate(graficos_data):
        ax = axes[idx]
        ax.set_facecolor('#313754')

        df_ejercicio = item["df"]
        nombre_ejercicio = item["ejercicio"]
        
        # Encontrar el peso máximo por día
        df_ejercicio['fecha_dia'] = df_ejercicio['fecha'].dt.date
        max_kilos_por_dia = df_ejercicio.groupby('fecha_dia')['kilos'].transform('max')

        # Filtrar para quedarnos SOLO con los sets que alcanzaron ese peso máximo
        df_sets_max = df_ejercicio[df_ejercicio['kilos'] == max_kilos_por_dia].copy()

        # Agrupar para obtener estadísticas
        df_stats = df_sets_max.groupby('fecha').agg(
            kilos=('kilos', 'first'),
            reps_min=('reps', 'min'),
            reps_max=('reps', 'max'),
            reps_mean=('reps', 'mean')
        ).reset_index().sort_values("fecha")

        # --- GRAFICAR KILOS ---
        ax.plot(df_stats["fecha"], df_stats["kilos"], color="#5CD5DD", linewidth=4, label="Kilos Máx", zorder=3)
        ax.set_ylabel("Kilos", fontsize=12, color="#5CD5DD")
        ax.tick_params(axis="y", labelcolor="#5CD5DD", labelsize=12)

        # Etiquetar primer y último punto
        primer = df_stats.iloc[0]
        ultimo = df_stats.iloc[-1]
        ax.text(primer["fecha"], primer["kilos"], f'{primer["kilos"]:.1f} kg', color="#5CD5DD", 
                fontsize=10, ha='right', va='bottom', fontweight='bold')
        ax.text(ultimo["fecha"], ultimo["kilos"], f'{ultimo["kilos"]:.1f} kg', color="#5CD5DD", 
                fontsize=10, ha='left', va='bottom', fontweight='bold')

        # --- GRAFICAR REPS ---
        ax2 = ax.twinx()
        ax2.fill_between(
            df_stats["fecha"], df_stats["reps_min"], df_stats["reps_max"], 
            color="#DB7DE4", alpha=0.3, label="Dispersión Reps"
        )
        ax2.plot(df_stats["fecha"], df_stats["reps_mean"], color="#DB7DE4", linewidth=1.5, label="Reps Media")
        ax2.set_ylabel("Reps (en peso máx)", fontsize=12, color="#DB7DE4")
        ax2.tick_params(axis="y", labelcolor="#DB7DE4", labelsize=12)

        # Formato eje X
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.tick_params(axis="x", rotation=45, labelsize=8, labelcolor="white")

        # Cuadrícula
        ax.grid(visible=True, axis='y', which='major', linestyle='--', linewidth=0.5, color="#595D73")
        for fecha in df_stats["fecha"]:
            ax.axvline(x=fecha, linestyle=':', linewidth=0.4, color="#595D73")

        # Título del gráfico indicando también el lugar configurado
        ax.set_title(f"{nombre_ejercicio} ({item['lugar']})", fontsize=18, color="white", pad=20)

    # Ocultar subplots vacíos
    for idx in range(num_ejercicios, len(axes)):
        fig.delaxes(axes[idx])

    st.pyplot(fig)