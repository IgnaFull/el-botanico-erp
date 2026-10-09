import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configuración de credenciales de Supabase
SUPABASE_URL = "https://jsdxfzanbgtswtmhfusy.supabase.co"
SUPABASE_KEY = "sb_publishable__3S6FIS90u29Niw5Mfn6kw_t0p51K7S"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="El Botánico - ERP", page_icon="🌱", layout="wide")

# Control de estado de sesión
if "user" not in st.session_state:
    st.session_state["user"] = None

def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 El Botánico - ERP")
        st.markdown("### Sistema de Gestión e Inventario")
        
        with st.form("login_form"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema")
            
            if submit:
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state["user"] = response.user
                    st.success("¡Bienvenido!")
                    st.rerun()
                except Exception as e:
                    st.error("Credenciales inválidas o usuario no registrado.")

def main_dashboard():
    user_email = st.session_state["user"].email if st.session_state["user"] else "Administrador"
    st.sidebar.title("🌿 El Botánico")
    st.sidebar.write(f"Usuario: **{user_email}**")
    
    menu = st.sidebar.radio("Navegación", ["Inventario General", "Control de Stock", "Gestión de Costos"])
    
    if st.sidebar.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.rerun()

    # Cargar datos desde Supabase
    def cargar_datos():
        try:
            response = supabase.table("inventario").select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            st.error(f"Error al conectar con Supabase: {e}")
            return pd.DataFrame()

    df = cargar_datos()

    if menu == "Inventario General":
        st.header("📦 Inventario General de Plantas e Insumos")
        st.markdown("Consulta en tiempo real de todos los productos cargados en la base de datos.")
        
        if not df.empty and "familia" in df.columns:
            familias = ["Todas"] + list(df["familia"].dropna().unique())
            familia_seleccionada = st.selectbox("Filtrar por Familia", familias)
            
            if familia_seleccion
