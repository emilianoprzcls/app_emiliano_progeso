import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import runpy  # Importar runpy para ejecutar prueba.py

# Configurar credenciales para acceder a Google Sheets usando st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_creds"], scope)
gc = gspread.authorize(credentials)

# Función para cargar hoja de Google Sheets usando el ID desde st.secrets
def cargar_hoja(spreadsheet_id):
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("Hoja 1")  # Cambia "Hoja 1" al nombre de la pestaña si es diferente
    return worksheet

# Función para registrar los datos en Google Sheets según la opción seleccionada
def registrar_datos(opcion, porcentaje_grasa=None, peso_kg=None, calorias=None):
    mexico_city_tz = pytz.timezone('America/Mexico_City')
    fecha_actual = datetime.now(mexico_city_tz).strftime("%Y-%m-%d %H:%M:%S")  # Fecha y hora para ambos

    if opcion == "Peso":
        worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_peso"])
        fila = [fecha_actual, porcentaje_grasa, peso_kg]
        worksheet.append_row(fila)
        return f"Datos registrados: Fecha: {fecha_actual}, Porcentaje de grasa: {porcentaje_grasa}, Peso: {peso_kg} kg"
    
    elif opcion == "Calorías":
        worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_calorias"])
        data = worksheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=["Fecha", "Calorías"])
        calorias_total = df[df["Fecha"] == fecha_actual]["Calorías"].astype(float).sum() + calorias
        worksheet.append_row([fecha_actual, calorias])
        return f"Calorías registradas: {calorias_total} kcal"

# Función para graficar los datos de peso y grasa
def graficar_datos():
    worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_peso"])
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=["Fecha", "Porcentaje de grasa", "Peso en kg"])
    df['Porcentaje de grasa'] = pd.to_numeric(df['Porcentaje de grasa'])
    df['Peso en kg'] = pd.to_numeric(df['Peso en kg'])
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Crear la figura y los ejes
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=500, constrained_layout=True)
    fig.patch.set_facecolor('#0F1116')  # Fondo de la figura
    ax1.set_facecolor('#313754')  # Fondo del área del gráfico
    
    # Crear un segundo eje Y
    ax2 = ax1.twinx()
    
    # Graficar los datos
    ax1.plot(
        df['Fecha'], 
        df['Peso en kg'], 
        color='#5CD5DD', 
        linestyle='-', 
        label='Peso en kg'
    )
    ax2.plot(
        df['Fecha'], 
        df['Porcentaje de grasa'], 
        color='#DB7DE4', 
        linestyle='-', 
        label='Porcentaje de grasa'
    )
    
    # Etiquetas y colores
    ax1.set_xlabel('Fecha', fontsize=12, color='white')
    ax1.set_ylabel('Peso en kg', fontsize=12, color='#5CD5DD')
    ax2.set_ylabel('Porcentaje de grasa', fontsize=12, color='#DB7DE4')
    
    # Título
    plt.title('Evolución de Peso y Porcentaje de Grasa', fontsize=14, color='white')
    
    # Personalizar los ticks
    ax1.tick_params(axis='x', rotation=45, labelsize=10, labelcolor='white')
    ax1.tick_params(axis='y', labelsize=10, labelcolor='#5CD5DD')
    ax2.tick_params(axis='y', labelsize=10, labelcolor='#DB7DE4')
    
    # Agregar cuadrícula
    ax1.grid(visible=True, which='major', linestyle='--', linewidth=0.5, color='#595D73')
    
    # Agregar leyendas
    ax1.legend(loc='upper left', fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    ax2.legend(loc='upper right', fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    
    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)


def graficar_promedio_semanal_peso():
    worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_peso"])
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=["Fecha", "Porcentaje de grasa", "Peso en kg"])
    df['Porcentaje de grasa'] = pd.to_numeric(df['Porcentaje de grasa'])
    df['Peso en kg'] = pd.to_numeric(df['Peso en kg'])
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Agrupamos los datos por semana y calculamos los promedios
    df.set_index('Fecha', inplace=True)
    df_semanal_peso = df['Peso en kg'].resample('W').mean()
    df_semanal_grasa = df['Porcentaje de grasa'].resample('W').mean()

    # Calculamos la variación semanal del peso
    cambio_semanal = df_semanal_peso.diff()

    # Crear la figura
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=500, constrained_layout=True)
    fig.patch.set_facecolor('#0F1116')  # Fondo de la figura
    ax1.set_facecolor('#313754')  # Fondo del área del gráfico

    # Segundo eje Y para el porcentaje de grasa
    ax2 = ax1.twinx()

    # Graficar la línea del promedio semanal de peso
    ax1.plot(
        df_semanal_peso.index, 
        df_semanal_peso.values, 
        marker='o', 
        linestyle='-', 
        color='#5CD5DD',  # Azul claro para el peso
        label="Promedio de Peso"
    )

    # Agregar etiquetas con la variación semanal de peso
    for i, (x, y) in enumerate(zip(df_semanal_peso.index, df_semanal_peso.values)):
        if i > 0:  # Omitimos la primera porque no hay comparación
            cambio = cambio_semanal.iloc[i]
            ax1.text(x, y, f"{cambio:+.1f} kg", fontsize=10, color="white", ha='center')

    # Graficar la línea del promedio semanal del porcentaje de grasa
    ax2.plot(
        df_semanal_grasa.index, 
        df_semanal_grasa.values, 
        marker='s', 
        linestyle='-', 
        color='#DB7DE4',  # Morado para el porcentaje de grasa
        label="Promedio de Grasa"
    )

    # Etiquetas y títulos
    ax1.set_xlabel('Semana', fontsize=12, color='white')
    ax1.set_ylabel('Promedio de Peso (kg)', fontsize=12, color='#5CD5DD')
    ax2.set_ylabel('Promedio de Porcentaje de Grasa (%)', fontsize=12, color='#DB7DE4')
    ax1.set_title('Promedio Semanal de Peso y Porcentaje de Grasa', fontsize=14, color='white')

    # Personalizar los ticks
    ax1.tick_params(axis='x', labelsize=10, labelcolor='white', rotation=45)
    ax1.tick_params(axis='y', labelsize=10, labelcolor='#5CD5DD')
    ax2.tick_params(axis='y', labelsize=10, labelcolor='#DB7DE4')

    # Agregar cuadrícula
    ax1.grid(visible=True, which='major', linestyle='--', linewidth=0.5, color="#595D73")

    # Agregar leyenda
    ax1.legend(loc='upper left', fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')
    ax2.legend(loc='upper right', fontsize=10, facecolor='#313754', edgecolor='white', labelcolor='white')

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)
    
def calcular_calorias_dia_reciente():
    worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_calorias"])
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=["Fecha", "Calorías"])
    df['Fecha'] = pd.to_datetime(df['Fecha'])  # Convertir a formato datetime
    df['Calorías'] = pd.to_numeric(df['Calorías'])

    fecha_reciente = df['Fecha'].dt.date.max()
    calorias_total = df[df['Fecha'].dt.date == fecha_reciente]["Calorías"].sum()

    return f"Calorías consumidas el día más reciente ({fecha_reciente}): {calorias_total} kcal"

def calcular_promedio_dos_semanas():
    worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_calorias"])
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=["Fecha", "Calorías"])
    df['Fecha'] = pd.to_datetime(df['Fecha'])  # Convertir a formato datetime
    df['Calorías'] = pd.to_numeric(df['Calorías'])

    # Sumar calorías por día
    df_diario = df.groupby(df['Fecha'].dt.date)['Calorías'].sum().reset_index()
    df_diario['Fecha'] = pd.to_datetime(df_diario['Fecha'])  # Asegurar que la columna es datetime
    df_diario.set_index('Fecha', inplace=True)  # Convertir a índice de fecha

    # Obtener el lunes más reciente como fecha máxima
    fecha_max = df_diario.index.max()
    fecha_max_lunes = fecha_max - pd.Timedelta(days=fecha_max.weekday())  # Último lunes
    fecha_inicio_semana_1 = fecha_max_lunes  # Inicio de la semana más reciente
    fecha_inicio_semana_2 = fecha_inicio_semana_1 - pd.Timedelta(days=7)  # Inicio de la semana anterior
    fecha_fin_semana_1 = fecha_inicio_semana_1 + pd.Timedelta(days=6)  # Domingo de la semana más reciente
    fecha_fin_semana_2 = fecha_inicio_semana_2 + pd.Timedelta(days=6)  # Domingo de la semana anterior

    # Filtrar solo los días con más de 1500 calorías
    df_filtrado = df_diario[df_diario["Calorías"] > 1500]
    
    # Filtrar las dos semanas
    df_semana_1 = df_filtrado.loc[(df_filtrado.index >= fecha_inicio_semana_1) & (df_filtrado.index <= fecha_fin_semana_1)]
    df_semana_2 = df_filtrado.loc[(df_filtrado.index >= fecha_inicio_semana_2) & (df_filtrado.index <= fecha_fin_semana_2)]

    # Calcular los promedios de cada semana considerando solo los días con más de 1500 calorías
    promedio_semana_1 = df_semana_1["Calorías"].mean() if not df_semana_1.empty else None
    promedio_semana_2 = df_semana_2["Calorías"].mean() if not df_semana_2.empty else None
    dias_semana_1 = df_semana_1.shape[0]
    dias_semana_2 = df_semana_2.shape[0]

    # Construir el mensaje de salida
    mensaje = ""
    if promedio_semana_1 is not None:
        mensaje += f" **Última semana ({fecha_inicio_semana_1.date()} - {fecha_fin_semana_1.date()}):** {promedio_semana_1:.2f} kcal/día ({dias_semana_1} días considerados)\n"
    else:
        mensaje += "No hay suficientes datos para calcular el promedio de la última semana.\n\n"

    # Agregar un salto de línea entre las semanas
    mensaje += "\n"

    if promedio_semana_2 is not None:
        mensaje += f" **Semana anterior ({fecha_inicio_semana_2.date()} - {fecha_fin_semana_2.date()}):** {promedio_semana_2:.2f} kcal/día ({dias_semana_2} días considerados)"
    else:
        mensaje += "No hay suficientes datos para calcular el promedio de la semana anterior."

    return mensaje


# Streamlit app
st.title("Registro de Peso, Calorías y Entrenamiento de Gimnasio")
opcion = st.radio("Selecciona una opción", ("Peso", "Calorías", "Gimnasio", "Progreso"))

if opcion == "Peso":
    grasa = st.number_input("Porcentaje de grasa", min_value=0.0, max_value=100.0, step=0.1)
    peso = st.number_input("Peso en kg", min_value=0.0, max_value=300.0, step=0.1)

    if st.button("Registrar Peso"):
        resultado = registrar_datos(opcion, porcentaje_grasa=grasa, peso_kg=peso)
        st.success(resultado)

    if st.button("Graficar Promedio Semanal de Peso"):
        graficar_promedio_semanal_peso()

    if st.button("Graficar Evolución"):
        graficar_datos()

elif opcion == "Calorías":
    calorias = st.number_input("Calorías consumidas", min_value=0.0, step=1.0)
    
    if st.button("Registrar Calorías"):
        resultado = registrar_datos(opcion, calorias=calorias)
        st.success(resultado)

    if st.button("Calcular Calorías del Día Más Reciente"):
        resultado_calorias = calcular_calorias_dia_reciente()
        st.info(resultado_calorias)

    if st.button("Calcular Promedio de Calorías en las Últimas 2 Semanas"):
        resultado_promedio = calcular_promedio_dos_semanas()
        st.info(resultado_promedio)

elif opcion == "Gimnasio":
    runpy.run_path("prueba.py")

elif opcion == "Progreso":
    runpy.run_path("progress_app.py")