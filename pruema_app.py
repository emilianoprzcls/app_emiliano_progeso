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
        return f"Calorías consumidas hoy: {calorias_total} kcal"

# Función para graficar los datos de peso y grasa
def graficar_datos():
    worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_peso"])
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=["Fecha", "Porcentaje de grasa", "Peso en kg"])
    df['Porcentaje de grasa'] = pd.to_numeric(df['Porcentaje de grasa'])
    df['Peso en kg'] = pd.to_numeric(df['Peso en kg'])
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    ax1.plot(df['Fecha'], df['Peso en kg'], 'g-')
    ax2.plot(df['Fecha'], df['Porcentaje de grasa'], 'b-')
    
    ax1.set_xlabel('Fecha')
    ax1.set_ylabel('Peso en kg', color='g')
    ax2.set_ylabel('Porcentaje de grasa', color='b')
    plt.title('Evolución de Peso y Porcentaje de Grasa')
    
    st.pyplot(fig)

# Función para calcular las calorías del día más reciente
def calcular_calorias_dia_reciente():
    worksheet = cargar_hoja(st.secrets["google_creds"]["spreadsheet_id_calorias"])
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=["Fecha", "Calorías"])
    df['Fecha'] = pd.to_datetime(df['Fecha'])  # Convertir a formato datetime para manejar fechas
    df['Calorías'] = pd.to_numeric(df['Calorías'])
    fecha_reciente = df['Fecha'].dt.date.max()
    calorias_total = df[df['Fecha'].dt.date == fecha_reciente]["Calorías"].sum()
    return f"Calorías consumidas el día más reciente ({fecha_reciente}): {calorias_total} kcal"

# Streamlit app
st.title("Registro de Peso, Calorías y Entrenamiento de Gimnasio")
opcion = st.radio("Selecciona una opción", ("Peso", "Calorías", "Gimnasio"))

if opcion == "Peso":
    grasa = st.number_input("Porcentaje de grasa", min_value=0.0, max_value=100.0, step=0.1)
    peso = st.number_input("Peso en kg", min_value=0.0, max_value=300.0, step=0.1)
    if st.button("Registrar Peso"):
        resultado = registrar_datos(opcion, porcentaje_grasa=grasa, peso_kg=peso)
        st.success(resultado)

elif opcion == "Calorías":
    calorias = st.number_input("Calorías consumidas", min_value=0.0, step=1.0)
    if st.button("Registrar Calorías"):
        resultado = registrar_datos(opcion, calorias=calorias)
        st.success(resultado)

    if st.button("Calcular Calorías del Día Más Reciente"):
        resultado_calorias = calcular_calorias_dia_reciente()
        st.info(resultado_calorias)

elif opcion == "Gimnasio":
    st.write("Cargando la aplicación de gimnasio...")
    # Ejecuta el código de prueba.py
    runpy.run_path("prueba.py")

if st.button("Graficar Evolución"):
    graficar_datos()
