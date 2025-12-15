import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator 

# Configurar credenciales para acceder a Google Sheets usando st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_creds"], scope)
gc = gspread.authorize(credentials)
spreadsheet_id = st.secrets["google_creds"]["spreadsheet_id"]
worksheet = gc.open_by_key(spreadsheet_id).worksheet("Hoja 1")

# Crear un DataFrame vacío para almacenar los datos
data = pd.DataFrame(columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps"])

# Listado de lugares
lugares_dict = {
    "Libres": "Libres",
    "Otro": "Otro",
    "SmartFit": "SmartFit",
    "Pedregal": "Pedregal",
    "Patio": "Patio"

}

# Listado de Ejercicios

ejercicios_dict = {
    "Push": [
        # Pecho
        "Bench Press",
        "Bench Press Machine",
        "Incline Bench Press",
        "Incline Bench Machine",
        "Chest Fly",
        "Machine Chest Press",
        "Dips",
        # Hombros
        "Shoulder Press",
        "Lateral Raises",
        "Front Raises",
        "Shrugs",
        # Tríceps
        "Close-Grip Press",
        "Tricep Extension",
        "Overhead Tricep Extension"
    ],
    "Upper": [
        # Espalda,
        "Pull-Ups",
        "Pull-Ups BW",
        "Lat Pulldowns",
        "Pendlay Row",
        "Pull Over",
        # Bíceps
        "Bayesian Curl",
        "Preacher Curl",
        "Preacher Curl (Dumbell)",
        "Spider Curl"
    ],

    "Pull": [
        # Espalda
        "Chin-Ups",
        "Pull-Ups",
        "Pull-Ups BW",
        "Lat Pulldowns",
        "Pendlay Row",
        "Pull Over",
        # Bíceps
        "Bayesian Curl",
        "Preacher Curl",
        "Preacher Curl (Dumbell)"
    ],

    "Legs": [
        "Squat",
        "Hack Squat",
        "Bulgarian Split Squat",
        "Leg Press",
        "Romanian Deadlifts",
        "Seated Leg Curl",
        "Leg Extension",
        "Hip Thrust",
        "Hip Extension",
        "Calf Raises",
        "Deadlift"   # Puede usarse también en Pull
    ],

    "Abs": [
        "Crunch Acostado",
        "Crunch Cables",
        "Crunch Machine",
        "L-Pull",
        "L-Sits",
        "Oblique Crunch"
    ]
}


# Función para obtener datos de Google Sheets
def obtener_datos():
    registros = worksheet.get_all_records()
    df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def graficar_progreso(ejercicio_seleccionado, location_seleccionado):
    df = obtener_datos()
    df_filtrado = df[(df["ejercicio"] == ejercicio_seleccionado) & (df["location"] == location_seleccionado)]
    if df_filtrado.empty:
        st.warning("No hay datos para este ejercicio.")
        return

    # Filtrar solo los últimos 5 días con observaciones
    fechas_unicas = sorted(df_filtrado["fecha"].unique())[-5:]
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_unicas)]
    
    # Definir colores para los sets
    colores_sets = {1: '#58E04F', 2: '#4FD1E0', 3: '#F23F9E', 4: '#F2933F'}
    
    # Crear la figura y los ejes
    fig, ax = plt.subplots(figsize=(10, 6), dpi=500, constrained_layout=True)
    fig.patch.set_facecolor('#0F1116')  # Fondo de la figura
    ax.set_facecolor('#313754')  # Fondo del área del gráfico
    ax2 = ax.twinx()
    
    # Obtener sets únicos y graficar
    sets_unicos = sorted(df_filtrado["set"].unique())
    handles_libras = []
    handles_reps = []
    labels_libras = []
    labels_reps = []
    
    for set_num in sets_unicos:
        df_set = df_filtrado[df_filtrado["set"] == set_num].sort_values(by="fecha")
        color = colores_sets.get(set_num, '#FFFFFF')  # Color por defecto si hay más sets
        
        line_libras, = ax.plot(df_set["fecha"], df_set["libras"], marker='o', color=color, label=f"Set {set_num} - Libras")
        line_reps, = ax2.plot(df_set["fecha"], df_set["reps"], linestyle='dashed', marker='x', color=color, label=f"Set {set_num} - Reps")
        
        # Agregar texto con el valor en la última observación de cada set
        ultima_fila = df_set.iloc[-1]
        ax.text(ultima_fila["fecha"], ultima_fila["libras"], f"{ultima_fila['libras']:.1f}",
                fontsize=10, color=color, ha='right', va='bottom')
        
        handles_libras.append(line_libras)
        labels_libras.append(f"Set {set_num} - Libras")
        handles_reps.append(line_reps)
        labels_reps.append(f"Set {set_num} - Reps")
    
    # Formateo del eje X con fechas únicas
    fechas_con_datos = sorted(df_filtrado["fecha"].unique())
    ax.set_xticks(fechas_con_datos)
    ax.set_xticklabels([fecha.strftime("%d/%m") for fecha in fechas_con_datos], rotation=90, fontsize=12, color='white')

    # Grid vertical solo en fechas con datos
    for fecha in fechas_con_datos:
        ax.axvline(x=fecha, linestyle='--', linewidth=0.5, color="#60657C")
    
    # Etiquetas y título
    ax.set_xlabel("Fecha", fontsize=12, color='white')
    ax.set_ylabel("Peso (libras)", fontsize=12, color='white')
    ax2.set_ylabel("Repeticiones", fontsize=12, color='white')
    ax.set_title(f"Progreso de {ejercicio_seleccionado}", fontsize=14, color='white')
    
    # Ticks
    ax.tick_params(axis='y', labelsize=10, labelcolor='white')
    ax2.tick_params(axis='y', labelsize=10, labelcolor='white')
    
    # Ajustar el eje Y secundario (reps) y mostrar solo su grid
    max_reps = df_filtrado["reps"].max()
    ax2.set_ylim(0, max(20, max_reps + 2))
    ax2.yaxis.set_major_locator(MultipleLocator(1))

    # Mostrar grid horizontal cada rep solo en el eje derecho (ax2)
    for y in range(0, max(21, max_reps + 2)):
        ax2.axhline(y=y, linestyle='--', linewidth=0.5, color="#60657C")

    # Leyendas
    legend1 = plt.legend(handles_libras, labels_libras, loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=len(sets_unicos), fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    legend2 = plt.legend(handles_reps, labels_reps, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=len(sets_unicos), fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    plt.gca().add_artist(legend1)
    
    # Mostrar gráfico en Streamlit
    st.pyplot(fig)



# Función para actualizar las opciones de ejercicio dependiendo del grupo seleccionado
def actualizar_ejercicios(grupo):
    return ejercicios_dict.get(grupo, [])

# Función para generar resumen de los datos por día (con asterisco en el set más alto)
def generar_resumen_con_asterisco(dataframe):
    dataframe['fecha'] = pd.to_datetime(dataframe['fecha'])
    resumen = ""
    fecha_mas_reciente = dataframe['fecha'].max().date()
    df_ultimo_dia = dataframe[dataframe['fecha'].dt.date == fecha_mas_reciente]
    resumen += f"Registro {fecha_mas_reciente}:\n"

    for ejercicio in df_ultimo_dia['ejercicio'].unique():
        resumen += f"Ejercicio: {ejercicio}\n"
        df_ejercicio = df_ultimo_dia[df_ultimo_dia['ejercicio'] == ejercicio]
        max_set = df_ejercicio['set'].max()

        for _, row in df_ejercicio.iterrows():
            set_text = f"Set {row['set']}: {row['kilos']} kg, {row['libras']} lb, {row['reps']} reps"
            if row['set'] == max_set:
                set_text = "* " + set_text
            resumen += set_text + "\n"

    resumen += "\n"
    return resumen

# Función para generar resumen de los datos de los últimos dos días sin asterisco
def generar_resumen_sin_asterisco(dataframe):
    dataframe['fecha'] = pd.to_datetime(dataframe['fecha'])
    resumen = ""

    dias_unicos = dataframe['fecha'].dt.date.unique()
    for dia in dias_unicos[-2:]:
        resumen += f"DIA {dia}:\n"
        df_dia = dataframe[dataframe['fecha'].dt.date == dia]

        for ejercicio in df_dia['ejercicio'].unique():
            resumen += f"Ejercicio: {ejercicio}\n"
            df_ejercicio = df_dia[df_dia['ejercicio'] == ejercicio]
            
            for _, row in df_ejercicio.iterrows():
                set_text = f"Set {row['set']}: {row['kilos']} kg, {row['libras']} lb, {row['reps']} reps"
                resumen += set_text + "\n"
        
        resumen += "\n"

    return resumen

# Función para agregar datos y generar el resumen
def agregar_datos(fecha, grupo, ejercicio, set, kilos, libras, reps, location):
    global data
    if kilos and not libras:
        libras = round(kilos * 2.20462, 1)
    elif libras and not kilos:
        kilos = round(libras / 2.20462, 1)

    nuevo_registro = {
        "fecha": fecha,
        "grupo": grupo,
        "ejercicio": ejercicio,
        "set": set,
        "kilos": kilos,
        "libras": libras,
        "reps": reps,
        "location": location
    }
    
    data = pd.concat([data, pd.DataFrame([nuevo_registro])], ignore_index=True)
    fila = [str(fecha), grupo, ejercicio, set, kilos, libras, reps, location]
    worksheet.append_row(fila)
    return generar_resumen_con_asterisco(data)

# Función para obtener resumen de los últimos dos días por grupo
def obtener_resumen_por_grupo(grupo):
    registros = worksheet.get_all_records()
    df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])

    df["fecha"] = pd.to_datetime(df["fecha"])
    df_grupo = df[df["grupo"] == grupo]

    if df_grupo.empty:
        return "No hay datos para el grupo seleccionado."

    ultimos_dias = df_grupo["fecha"].drop_duplicates().nlargest(2)
    df_ultimos_dias = df_grupo[df_grupo["fecha"].isin(ultimos_dias)]
    return generar_resumen_sin_asterisco(df_ultimos_dias)

# Función para obtener los datos más recientes de Google Sheets y calcular estadísticas normalizadas a 8 reps
def obtener_estadisticas_recientes():
    try:
        registros = worksheet.get_all_records()
        df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])
        df["fecha"] = pd.to_datetime(df["fecha"])
        
        # Filtrar por el grupo más reciente
        grupo_mas_reciente = df["grupo"].iloc[-1]
        df_grupo = df[df["grupo"] == grupo_mas_reciente]
        
        # Obtener el registro más reciente
        fecha_mas_reciente = df_grupo["fecha"].max()
        df_reciente = df_grupo[df_grupo["fecha"] == fecha_mas_reciente]
        
        # Obtener la última fecha en que se trabajó este mismo grupo
        ultimas_fechas = df_grupo["fecha"].drop_duplicates().nlargest(2)
        fecha_anterior = ultimas_fechas.min()
        df_anterior = df_grupo[df_grupo["fecha"] == fecha_anterior]
        
        # Normalizar los kilos a 8 reps para ambos DataFrames
        df_reciente["kilos_normalizados"] = df_reciente.apply(lambda row: (row["kilos"] / row["reps"]) * 8 if row["reps"] > 0 else 0, axis=1)
        df_anterior["kilos_normalizados"] = df_anterior.apply(lambda row: (row["kilos"] / row["reps"]) * 8 if row["reps"] > 0 else 0, axis=1)
        
        # Calcular estadísticas para el día más reciente (sin normalizar y normalizado)
        total_kilos = df_reciente["kilos"].sum(skipna=True)
        total_sets = len(df_reciente)  # Contamos las entradas, no la suma de los sets
        total_reps = df_reciente["reps"].sum(skipna=True)
        kilos_por_set = total_kilos / total_sets if total_sets > 0 else 0
        total_kilos_normalizados = df_reciente["kilos_normalizados"].sum(skipna=True)
        kilos_normalizados_por_set = total_kilos_normalizados / total_sets if total_sets > 0 else 0
        
        # Calcular estadísticas del día anterior (sin normalizar y normalizado)
        total_kilos_anterior = df_anterior["kilos"].sum(skipna=True)
        total_sets_anterior = len(df_anterior)
        total_reps_anterior = df_anterior["reps"].sum(skipna=True)
        kilos_por_set_anterior = total_kilos_anterior / total_sets_anterior if total_sets_anterior > 0 else 0
        total_kilos_normalizados_anterior = df_anterior["kilos_normalizados"].sum(skipna=True)
        kilos_normalizados_por_set_anterior = total_kilos_normalizados_anterior / total_sets_anterior if total_sets_anterior > 0 else 0
        
        # Calcular el porcentaje de aumento en kilos y repeticiones
        porcentaje_kilos = ((total_kilos - total_kilos_anterior) / total_kilos_anterior) * 100 if total_kilos_anterior > 0 else 0
        porcentaje_reps = ((total_reps - total_reps_anterior) / total_reps_anterior) * 100 if total_reps_anterior > 0 else 0
        porcentake_kilos_porset = ((kilos_normalizados_por_set - kilos_normalizados_por_set_anterior) / kilos_normalizados_por_set_anterior) * 100 if kilos_normalizados_por_set_anterior > 0 else 0

        return (f"**Estadísticas del día más reciente ({fecha_mas_reciente.date()}):**\n"
                f"- Total de kilos (no normalizado): {total_kilos:.2f}\n"
                f"- Total de sets: {total_sets}\n"
                f"- Total de reps: {total_reps}\n"
                f"- Kilos por set: {kilos_por_set:.2f}\n"
                f"- Kilos normalizados a 8 reps: {total_kilos_normalizados:.2f}\n"
                f"- Kilos normalizados por set: {kilos_normalizados_por_set:.2f}\n\n"
                f"**Estadísticas del día anterior ({fecha_anterior.date()}):**\n"
                f"- Total de kilos (no normalizado): {total_kilos_anterior:.2f}\n"
                f"- Total de sets: {total_sets_anterior}\n"
                f"- Total de reps: {total_reps_anterior}\n"
                f"- Kilos por set: {kilos_por_set_anterior:.2f}\n"
                f"- Kilos normalizados a 8 reps: {total_kilos_normalizados_anterior:.2f}\n"
                f"- Kilos normalizados por set: {kilos_normalizados_por_set_anterior:.2f}\n\n"
                f"**Comparación con el último día del mismo grupo ({fecha_anterior.date()}):**\n"
                f"- Kilos aumentados: {porcentaje_kilos:.2f}%\n"
                f"- Repeticiones aumentadas: {porcentaje_reps:.2f}%\n"
                f"- Kilos Norm. por set: {porcentake_kilos_porset:.2f}%\n\n")

    
    except Exception as e:
        print(f"Error al obtener los datos recientes de Google Sheets: {str(e)}")
        return "Error al obtener los datos."

# Interfaz en Streamlit
st.title("Registro de Entrenamiento")
st.markdown("[Consulta el registro completo en Google Sheets](https://docs.google.com/spreadsheets/d/1gCJRvjkOS-kfy9KwXAsv3BYHoQCwv8tWMgBJIRXb4g0/edit?usp=sharing)")

# Selección de fecha y grupo
fecha = st.date_input("Fecha", datetime.today())
location = st.selectbox("Lugar", options=list(lugares_dict.values()))
grupo = st.selectbox("Grupo", options=list(ejercicios_dict.keys()))
ejercicio = st.selectbox("Ejercicio", options=actualizar_ejercicios(grupo))
set_num = st.number_input("Set", min_value=1, step=1)
kilos = st.number_input("Kilos", min_value=0.0, step=0.5)
libras = st.number_input("Libras", min_value=0.0, step=0.5)
reps = st.number_input("Reps", min_value=1, step=1)

# Botón para registrar datos
if st.button("Registrar"):
    resumen = agregar_datos(fecha, grupo, ejercicio, set_num, kilos, libras, reps, location)
    st.success("Datos registrados correctamente.")
    st.text_area("Resumen del entrenamiento", resumen, height=300)

if st.button("Graficar Progreso"):
    graficar_progreso(ejercicio, location)

# Botón para obtener resumen de los últimos dos días por grupo
if st.button("Obtener Resumen de los Últimos Dos Días por Grupo"):
    resumen_dos_dias = obtener_resumen_por_grupo(grupo)
    st.text_area("Resumen de los últimos dos días", resumen_dos_dias, height=300)

# Botón para ver estadísticas del día más reciente
if st.button("Día Terminado"):
    estadisticas = obtener_estadisticas_recientes()
    st.text_area("Estadísticas del Día", estadisticas, height=300)
