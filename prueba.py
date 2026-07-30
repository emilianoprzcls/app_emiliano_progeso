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
        "Dips",
        # Hombros
        "Shoulder Press",
        "Lateral Raises",
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
        "Spider Curl",
        # Pecho
        "Bench Press",
        "Bench Press Machine",
        "Incline Bench Press",
        "Incline Bench Machine",
        "Chest Fly",
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

    "Pull": [
        # Espalda
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

    "Legs": [
        "Squat",
        "Hack Squat",
        "Bulgarian Split Squat",
        "Leg Press",
        "Romanian Deadlifts",
        "Seated Leg Curl",
        "Leg Extension",
        "Hip Thrust",
        "Hip Adduction (C)",
        "Hip Abduction (A)",# Puede usarse también en Pull
    ],

    "Abs": [
        "Crunch Cables",
        "Reverse Crunch Cables",
        "Crunch Machine",
        "L-Sits",
    ]
}


# Función para obtener datos de Google Sheets
def obtener_datos():
    registros = worksheet.get_all_records()
    df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def graficar_progresolb(ejercicio_seleccionado, location_seleccionado):
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

def graficar_progresokg(ejercicio_seleccionado, location_seleccionado):
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
    handles_kilos = []  # Cambiado de libras a kilos
    handles_reps = []
    labels_kilos = []   # Cambiado de libras a kilos
    labels_reps = []
    
    for set_num in sets_unicos:
        df_set = df_filtrado[df_filtrado["set"] == set_num].sort_values(by="fecha")
        color = colores_sets.get(set_num, '#FFFFFF')
        
        # Graficar usando la columna "kilos"
        line_kilos, = ax.plot(df_set["fecha"], df_set["kilos"], marker='o', color=color, label=f"Set {set_num} - Kg")
        line_reps, = ax2.plot(df_set["fecha"], df_set["reps"], linestyle='dashed', marker='x', color=color, label=f"Set {set_num} - Reps")
        
        # Agregar texto con el valor en la última observación (ahora en kilos)
        ultima_fila = df_set.iloc[-1]
        ax.text(ultima_fila["fecha"], ultima_fila["kilos"], f"{ultima_fila['kilos']:.1f} kg",
                fontsize=10, color=color, ha='right', va='bottom')
        
        handles_kilos.append(line_kilos)
        labels_kilos.append(f"Set {set_num} - Kg")
        handles_reps.append(line_reps)
        labels_reps.append(f"Set {set_num} - Reps")
    
    # Formateo del eje X
    fechas_con_datos = sorted(df_filtrado["fecha"].unique())
    ax.set_xticks(fechas_con_datos)
    ax.set_xticklabels([fecha.strftime("%d/%m") for fecha in fechas_con_datos], rotation=90, fontsize=12, color='white')

    # Grid vertical
    for fecha in fechas_con_datos:
        ax.axvline(x=fecha, linestyle='--', linewidth=0.5, color="#60657C")
    
    # Etiquetas y título actualizados a Kilos
    ax.set_xlabel("Fecha", fontsize=12, color='white')
    ax.set_ylabel("Peso (kg)", fontsize=12, color='white')
    ax2.set_ylabel("Repeticiones", fontsize=12, color='white')
    ax.set_title(f"Progreso de {ejercicio_seleccionado} (Kg)", fontsize=14, color='white')
    
    # Ticks
    ax.tick_params(axis='y', labelsize=10, labelcolor='white')
    ax2.tick_params(axis='y', labelsize=10, labelcolor='white')
    
    # Ajustar el eje Y secundario (reps)
    max_reps = df_filtrado["reps"].max()
    ax2.set_ylim(0, max(20, max_reps + 2))
    ax2.yaxis.set_major_locator(MultipleLocator(1))

    # Grid horizontal
    for y in range(0, max(21, max_reps + 2)):
        ax2.axhline(y=y, linestyle='--', linewidth=0.5, color="#60657C")

    # Leyendas actualizadas
    legend1 = plt.legend(handles_kilos, labels_kilos, loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=len(sets_unicos), fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    legend2 = plt.legend(handles_reps, labels_reps, loc='lower center', bbox_to_anchor=(0.5, -0.4), ncol=len(sets_unicos), fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    plt.gca().add_artist(legend1)
    
    st.pyplot(fig)

# Función para actualizar las opciones de ejercicio dependiendo del grupo seleccionado
def actualizar_ejercicios(grupo):
    return ejercicios_dict.get(grupo, [])

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
    
# Función para generar resumen de los datos por día (con asterisco en el set más alto)
def generar_resumen_con_asterisco(dataframe):
    registros = worksheet.get_all_records()
    df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])

    df["fecha"] = pd.to_datetime(df["fecha"])
    df_grupo = df[df["grupo"] == grupo & (df["ejercicio"] == ejercicio)]

    if df_grupo.empty:
        return "No hay datos para el grupo seleccionado."

    ultimos_dias = df_grupo["fecha"].drop_duplicates().nlargest(1)
    df_ultimos_dias = df_grupo[df_grupo["fecha"].isin(ultimos_dias)]

    return resumen
# Función para generar resumen de los datos de los últimos dos días sin asterisco


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

def eliminar_ultimo_registro():
    try:
        # Obtener todos los valores para saber cuántas filas hay
        total_filas = len(worksheet.get_all_values())
        if total_filas > 1:  # Evitar borrar el encabezado (fila 1)
            worksheet.delete_rows(total_filas)
            return True
        return False
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

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

def obtener_estadisticas_recientes():
    try:
        registros = worksheet.get_all_records()
        df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])
        df["fecha"] = pd.to_datetime(df["fecha"])
        
        # 1. Filtrar por el grupo y ubicación más reciente
        ultimo_registro = df.iloc[-1]
        grupo_actual = ultimo_registro["grupo"]
        location_actual = ultimo_registro["location"]
        
        df_contexto = df[(df["grupo"] == grupo_actual) & (df["location"] == location_actual)]
        
        # 2. Identificar fechas
        fechas_disponibles = df_contexto["fecha"].drop_duplicates().nlargest(2).tolist()
        if len(fechas_disponibles) < 2:
            return "No hay suficientes entrenamientos previos para este grupo y ubicación para comparar."
        
        fecha_mas_reciente = fechas_disponibles[0]
        fecha_anterior = fechas_disponibles[1]
        
        df_reciente = df_contexto[df_contexto["fecha"] == fecha_mas_reciente].copy()
        df_anterior_completo = df_contexto[df_contexto["fecha"] == fecha_anterior].copy()

        # 3. Normalización (Función auxiliar para limpiar el apply)
        def normalizar(row):
            return (row["kilos"] / row["reps"]) * 8 if row["reps"] > 0 else 0

        df_reciente["kilos_norm"] = df_reciente.apply(normalizar, axis=1)
        df_anterior_completo["kilos_norm"] = df_anterior_completo.apply(normalizar, axis=1)

        # 4. Emparejamiento Dinámico (Cruzar sets actuales vs anteriores)
        # Usamos un merge 'left' para que manden los ejercicios y sets que hiciste HOY
        df_comparativo = pd.merge(
            df_reciente[['ejercicio', 'set', 'kilos', 'reps', 'kilos_norm']], 
            df_anterior_completo[['ejercicio', 'set', 'kilos', 'reps', 'kilos_norm']], 
            on=['ejercicio', 'set'], 
            how='left', 
            suffixes=('_hoy', '_ant')
        )

        # 5. Cálculos de Hoy
        total_kilos = df_comparativo["kilos_hoy"].sum()
        total_reps = df_comparativo["reps_hoy"].sum()
        total_sets = len(df_comparativo)
        total_norm_hoy = df_comparativo["kilos_norm_hoy"].sum()
        norm_por_set_hoy = total_norm_hoy / total_sets if total_sets > 0 else 0

        # 6. Cálculos del Pasado (Solo de los sets que coinciden con hoy)
        # Usamos fillna(0) por si hoy hiciste un ejercicio o set que no existía la vez pasada
        total_kilos_ant = df_comparativo["kilos_ant"].fillna(0).sum()
        total_reps_ant = df_comparativo["reps_ant"].fillna(0).sum()
        total_norm_ant = df_comparativo["kilos_norm_ant"].fillna(0).sum()
        norm_por_set_ant = total_norm_ant / total_sets if total_sets > 0 else 0

        # 7. Porcentajes de mejora
        def calc_pc(actual, anterior):
            return ((actual - anterior) / anterior) * 100 if anterior > 0 else 0

        p_kilos = calc_pc(total_kilos, total_kilos_ant)
        p_reps = calc_pc(total_reps, total_reps_ant)
        p_norm_set = calc_pc(norm_por_set_hoy, norm_por_set_ant)

        return (f"**Resumen: {grupo_actual} @ {location_actual}**\n"
                f"Comparando {total_sets} sets actuales vs mismos sets sesión anterior\n"
                f"--- \n"
                f"**Hoy ({fecha_mas_reciente.date()}):**\n"
                f"- Volumen Total: {total_kilos:.2f} kg\n"
                f"- Reps Totales: {total_reps}\n"
                f"- Norm. por Set: {norm_por_set_hoy:.2f} kg\n\n"
                f"**Día Anterior ({fecha_anterior.date()}):**\n"
                f"- Volumen (mismos sets): {total_kilos_ant:.2f} kg\n"
                f"- Reps (mismos sets): {total_reps_ant}\n"
                f"- Norm. por Set: {norm_por_set_ant:.2f} kg\n\n"
                f"**Progreso Real:**\n"
                f"- Δ Volumen: {p_kilos:+.2f}%\n"
                f"- Δ Reps: {p_reps:+.2f}%\n"
                f"- Δ Fuerza (Norm): {p_norm_set:+.2f}%\n")

    except Exception as e:
        return f"Error al procesar: {str(e)}"
    
def obtener_estadisticas_entrenamiento():
    try:
        # 1. Cargar datos y preparar DataFrame
        registros = worksheet.get_all_records()
        df = pd.DataFrame(registros, columns=["fecha", "grupo", "ejercicio", "set", "kilos", "libras", "reps", "location"])
        df["fecha"] = pd.to_datetime(df["fecha"])
        
        # 2. Identificar el día más reciente (hoy)
        fecha_hoy = df["fecha"].max()
        df_hoy = df[df["fecha"] == fecha_hoy].copy()
        
        # Identificador de set secuencial para hoy (1, 2, 3...)
        df_hoy["set_num"] = df_hoy.groupby("ejercicio").cumcount() + 1
        
        # --- NUEVO: Extraer Location y Ejercicios ---
        locations = ", ".join(df_hoy["location"].dropna().unique())
        ejercicios_hoy = df_hoy["ejercicio"].unique()
        nombres_ejercicios = ", ".join(ejercicios_hoy)
        
        # 3. Buscar historial de TODOS los ejercicios realizados hoy
        df_pasado = df[(df["ejercicio"].isin(ejercicios_hoy)) & (df["fecha"] < fecha_hoy)].copy()
        
        if df_pasado.empty:
            return (f"### Entrenamiento del {fecha_hoy.date()}\n\n"
                    f"- **Location(s):** {locations}\n"
                    f"- **Ejercicios:** {nombres_ejercicios}\n\n"
                    f"*Entrenamiento registrado. No hay datos previos para comparar estos ejercicios.*")

        # Obtener la fecha de la última vez que se hizo CADA ejercicio
        ultimas_fechas = df_pasado.groupby("ejercicio")["fecha"].max().reset_index()
        df_antes = pd.merge(df_pasado, ultimas_fechas, on=["ejercicio", "fecha"])
        
        # Identificador secuencial para la sesión anterior
        df_antes["set_num"] = df_antes.groupby("ejercicio").cumcount() + 1

        # 4. Normalización a 8 reps
        def normalizar(row):
            return (row["kilos"] / row["reps"]) * 8 if row["reps"] > 0 else 0

        df_hoy["norm"] = df_hoy.apply(normalizar, axis=1)
        df_antes["norm"] = df_antes.apply(normalizar, axis=1)

        # 5. EL MERGE
        comparativa = pd.merge(
            df_hoy[["grupo", "ejercicio", "set_num", "norm", "kilos", "reps", "fecha"]],
            df_antes[["ejercicio", "set_num", "norm", "kilos", "reps", "fecha"]],
            on=["ejercicio", "set_num"],
            how="left",
            suffixes=("_hoy", "_antes")
        )

        # 6. Construcción del encabezado (Sin emojis, corrección de espacios en negritas)
        resultado = (f"### RESUMEN DEL ENTRENAMIENTO ({fecha_hoy.date()})\n\n"
                     f"- **Location(s):** {locations}\n"
                     f"- **Ejercicios:** {nombres_ejercicios}\n"
                     f"---\n\n")

        # 7. CÁLCULO POR GRUPO MUSCULAR (Dinámico)
        for grupo in comparativa["grupo"].dropna().unique():
            data = comparativa[comparativa["grupo"] == grupo]
            
            k_hoy = data["kilos_hoy"].sum()
            r_hoy = data["reps_hoy"].sum()
            n_hoy = data["norm_hoy"].sum()
            
            k_antes = data["kilos_antes"].sum(skipna=True)
            r_antes = data["reps_antes"].sum(skipna=True)
            n_antes = data["norm_antes"].sum(skipna=True)
            
            f_hoy_str = fecha_hoy.strftime('%d/%m')
            f_antes_val = data["fecha_antes"].dropna()
            f_antes_str = f_antes_val.iloc[0].strftime('%d/%m') if not f_antes_val.empty else "N/A"
            
            pct_k = ((k_hoy - k_antes) / k_antes * 100) if k_antes > 0 else 0
            pct_r = ((r_hoy - r_antes) / r_antes * 100) if r_antes > 0 else 0
            pct_n = ((n_hoy - n_antes) / n_antes * 100) if n_antes > 0 else 0

            resultado += (f"#### Grupo: {grupo.upper()} ({f_hoy_str} vs {f_antes_str})\n"
                          f"- **Kilos:** {k_hoy:.1f} hoy vs {k_antes:.1f} antes ({pct_k:+.1f}%)\n"
                          f"- **Reps:** {int(r_hoy)} hoy vs {int(r_antes)} antes ({pct_r:+.1f}%)\n"
                          f"- **Norm:** {n_hoy:.1f} hoy vs {n_antes:.1f} antes ({pct_n:+.1f}%)\n\n")

        # 8. CÁLCULO TOTAL DEL DÍA
        t_k_hoy = comparativa["kilos_hoy"].sum()
        t_k_antes = comparativa["kilos_antes"].sum(skipna=True)
        t_r_hoy = comparativa["reps_hoy"].sum()
        t_r_antes = comparativa["reps_antes"].sum(skipna=True)
        t_n_hoy = comparativa["norm_hoy"].sum()
        t_n_antes = comparativa["norm_antes"].sum(skipna=True)
        
        total_pct_k = ((t_k_hoy - t_k_antes) / t_k_antes * 100) if t_k_antes > 0 else 0
        total_pct_r = ((t_r_hoy - t_r_antes) / t_r_antes * 100) if t_r_antes > 0 else 0
        total_pct_n = ((t_n_hoy - t_n_antes) / t_n_antes * 100) if t_n_antes > 0 else 0
        
        sets_comparados = int(comparativa['kilos_antes'].count())
        sets_totales = len(df_hoy)

        resultado += (f"---\n\n"
                      f"#### TOTAL DEL ENTRENAMIENTO:\n"
                      f"- Mejora Carga Total (Kilos): **{total_pct_k:+.2f}%**\n"
                      f"- Mejora Volumen (Reps): **{total_pct_r:+.2f}%**\n"
                      f"- Mejora Fuerza (Norm): **{total_pct_n:+.2f}%**\n"
                      f"- Sets comparados: {sets_comparados} de {sets_totales}\n\n"
                      f"> *Nota: Solo se comparan los sets realizados hoy con sus pares exactos de la sesión anterior.*")
        
        return resultado

    except Exception as e:
        return f"Error al procesar estadísticas: {str(e)}"
    
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
# Crear columnas para los botones de acción principal
col_reg, col_del = st.columns(2)

with col_reg:
    if st.button("Registrar", use_container_width=True):
        resumen = agregar_datos(fecha, grupo, ejercicio, set_num, kilos, libras, reps, location)
        st.success("Datos registrados correctamente.")

with col_del:
    if st.button("Eliminar Último", use_container_width=True, type="primary"):
        if eliminar_ultimo_registro():
            st.warning("Se ha eliminado la última fila del registro.")
        else:
            st.error("No hay datos para eliminar o la hoja está vacía.")

if "unidad" not in st.session_state:
    st.session_state.unidad = None

# 2. Crear las columnas solo para los botones
col1, col2 = st.columns(2)

with col1:
    if st.button("📈 Graficar en Kilos", use_container_width=True):
        st.session_state.unidad = "kg"

with col2:
    if st.button("📉 Graficar en Libras", use_container_width=True):
        st.session_state.unidad = "lb"

# 3. Lógica de graficado fuera de las columnas (ocupa el ancho total)
if st.session_state.unidad == "kg":
    graficar_progresokg(ejercicio, location)
elif st.session_state.unidad == "lb":
    graficar_progresolb(ejercicio, location)

# Botón para obtener resumen de los últimos dos días por grupo
if st.button("Obtener Resumen de los Últimos Dos Días por Grupo"):
    resumen_dos_dias = obtener_resumen_por_grupo(grupo)
    st.text_area("Resumen de los últimos dos días", resumen_dos_dias, height=300)

if st.button("Día Terminado"):
    estadisticas = obtener_estadisticas_entrenamiento()
    
    st.markdown("### Estadísticas del Día")
    # Lo envuelve en un cuadro con fondo de color suave
    st.info(estadisticas)