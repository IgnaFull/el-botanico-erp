import streamlit as st
import pandas as pd
from supabase import create_client, Client

SUPABASE_URL = "https://jsdxfzanbgtswtmhfusy.supabase.co"
SUPABASE_KEY = "sb_publishable__3S6FIS90u29Niw5Mfn6kw_t0p51K7S"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="El Botánico - ERP", page_icon="🌱", layout="wide")

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
            
            if familia_seleccionada != "Todas":
                df_filtrado = df[df["familia"] == familia_seleccionada]
            else:
                df_filtrado = df
                
            busqueda = st.text_input("🔍 Buscar por nombre, especie o ID:")
            if busqueda:
                df_filtrado = df_filtrado[
                    df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
                ]
                
            st.dataframe(df_filtrado, use_container_width=True)
            st.info(f"Total de registros mostrados: {len(df_filtrado)}")
        else:
            st.warning("La tabla de inventario se encuentra vacía o faltan columnas.")

    elif menu == "Control de Stock":
        st.header("📊 Control de Stock, Altas y Gestión de Ítems")
        st.markdown("Administrá el stock actual, creá nuevos productos o da de baja ítems erróneos.")
        
        if df.empty:
            st.warning("No hay productos disponibles en la base de datos.")
            return

        tab_actualizar, tab_crear, tab_eliminar = st.tabs(["🔄 Actualizar Stock", "➕ Nuevo Ítem", "🗑️ Eliminar Ítem"])
        
        with tab_actualizar:
            df["opcion_display"] = df["id_item"].astype(str) + " - " + df["producto"].astype(str) + " (" + df["contenedor"].astype(str) + ")"
            producto_elegido = st.selectbox("Seleccionar Producto / Insumo para actualizar", df["opcion_display"].tolist())
            
            match_df = df[df["opcion_display"] == producto_elegido]
            if not match_df.empty:
                prod_data = match_df.iloc[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="ID de Ítem", value=str(prod_data["id_item"]))
                    st.metric(label="Familia", value=str(prod_data["familia"]))
                with col2:
                    st.metric(label="Producto / Especie", value=str(prod_data["producto"]))
                    st.metric(label="Contenedor / Medida", value=str(prod_data["contenedor"]))
                with col3:
                    stock_actual_actual = int(prod_data["stock_actual"]) if pd.notna(prod_data["stock_actual"]) else 0
                    st.metric(label="Stock Actual en BD", value=stock_actual_actual)
                
                st.markdown("---")
                with st.form("form_actualizar_stock"):
                    nuevo_stock = st.number_input("Nuevo valor de Stock", min_value=0, value=stock_actual_actual, step=1)
                    actualizar_btn = st.form_submit_button("💾 Guardar Nuevo Stock en Supabase")
                    
                    if actualizar_btn:
                        try:
                            supabase.table("inventario").update({"stock_actual": nuevo_stock}).eq("id_item", str(prod_data["id_item"])).execute()
                            st.success("¡Stock actualizado con éxito!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar el stock: {e}")

        with tab_crear:
            st.markdown("### ➕ Registrar Nuevo Producto o Insumo")
            with st.form("form_nuevo_item"):
                col_a, col_b = st.columns(2)
                with col_a:
                    id_item = st.text_input("ID de Ítem (Ej: PL-SUC-999)")
                    familia = st.text_input("Familia (Ej: PLANTAS, INSUMOS)")
                    categoria = st.text_input("Categoría (Ej: SUCULENTAS Y CACTUS)")
                    subcategoria = st.text_input("Subcategoría (Ej: -, Macetas)", value="-")
                with col_b:
                    producto = st.text_input("Producto / Especie / Modelo")
                    contenedor = st.text_input("Contenedor / Medida (Ej: M15, 5L)")
                    stock_actual = st.number_input("Stock Inicial", min_value=0, value=0, step=1)
                    costo_unitario = st.number_input("Costo Unitario ($)", min_value=0.0, value=0.0, step=0.1)
                    precio_venta = st.number_input("Precio de Venta ($)", min_value=0.0, value=0.0, step=0.1)
                
                guardar_nuevo_btn = st.form_submit_button("🚀 Dar de Alta en Supabase")
                
                if guardar_nuevo_btn:
                    if id_item and producto:
                        try:
                            nuevo_registro = {
                                "id_item": id_item.strip().upper(),
                                "familia": familia.strip().upper(),
                                "categoria": categoria.strip().upper(),
                                "subcategoria": subcategoria.strip(),
                                "producto": producto.strip().upper(),
                                "contenedor": contenedor.strip().upper(),
                                "stock_actual": stock_actual,
                                "costo_unitario": costo_unitario,
                                "precio_venta": precio_venta
                            }
                            supabase.table("inventario").insert(nuevo_registro).execute()
                            st.success(f"¡El producto '{producto}' fue creado con éxito!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar el ítem: {e}")
                    else:
                        st.error("Los campos 'ID de Ítem' y 'Producto' son obligatorios.")

        with tab_eliminar:
            df["opcion_display"] = df["id_item"].astype(str) + " - " + df["producto"].astype(str) + " (" + df["contenedor"].astype(str) + ")"
            producto_a_borrar = st.selectbox("Seleccionar Producto para eliminar", df["opcion_display"].tolist(), key="select_borrar")
            match_borrar = df[df["opcion_display"] == producto_a_borrar]
            if not match_borrar.empty:
                prod_borrar_data = match_borrar.iloc[0]
                
                st.warning(f"⚠️ Vas a eliminar el ítem: **{prod_borrar_data['id_item']} - {prod_borrar_data['producto']}**")
                confirmar_borrado = st.checkbox("Confirmo que deseo eliminar este ítem definitivamente")
                
                if st.button("❌ Eliminar Ítem de Supabase", type="primary"):
                    if confirmar_borrado:
                        try:
                            supabase.table("inventario").delete().eq("id_item", str(prod_borrar_data["id_item"])).execute()
                            st.success("¡El ítem fue eliminado correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar: {e}")
                    else:
                        st.error("Debes tildar la casilla de confirmación.")

    elif menu == "Gestión de Costos":
        st.header("💰 Márgenes y Costos")
elif menu == "Gestión de Costos":
        st.header("💰 Gestión de Costos, Márgenes y Precios")
        st.markdown("Analizá la rentabilidad de tus productos, calcula márgenes de ganancia y actualiza precios.")

        if df.empty:
            st.warning("No hay productos disponibles en la base de datos.")
            return

        # Asegurarnos de que existan las columnas de costos y precios, o crearlas limpias
        if "costo_unitario" not in df.columns:
            df["costo_unitario"] = 0.0
        if "precio_venta" not in df.columns:
            df["precio_venta"] = 0.0

        tab_calculadora, tab_resumen = st.tabs(["🧮 Simulador y Actualizador de Precios", "📊 Inventario Valorizado (Capital y Venta)"])

        with tab_calculadora:
            st.markdown("### 🏷️ Ajuste de Márgenes por Producto")
            
            df["opcion_display"] = df["id_item"].astype(str) + " - " + df["producto"].astype(str) + " (" + df["contenedor"].astype(str) + ")"
            producto_costo = st.selectbox("Seleccionar producto para analizar costo y precio", df["opcion_display"].tolist(), key="select_costo")
            
            match_costo = df[df["opcion_display"] == producto_costo]
            if not match_costo.empty:
                prod_c = match_costo.iloc[0]
                
                costo_actual = float(prod_c["costo_unitario"]) if pd.notna(prod_c["costo_unitario"]) else 0.0
                precio_actual = float(prod_c["precio_venta"]) if pd.notna(prod_c["precio_venta"]) else 0.0
                
                # Cálculos automáticos
                ganancia_pesos = precio_actual - costo_actual
                margen_porcentaje = ((ganancia_pesos / costo_actual) * 100) if costo_actual > 0 else 0.0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Costo Unitario ($)", value=f"${costo_actual:,.2f}")
                with col2:
                    st.metric(label="Precio de Venta Actual ($)", value=f"${precio_actual:,.2f}", delta=f"${ganancia_pesos:,.2f} ganancia")
                with col3:
                    st.metric(label="Margen de Ganancia", value=f"{margen_porcentaje:.1f}%")

                st.markdown("---")
                with st.form("form_actualizar_precios"):
                    st.markdown("#### ✏️ Modificar Costo o Precio de Venta")
                    nuevo_costo = st.number_input("Nuevo Costo Unitario ($)", min_value=0.0, value=float(costo_actual), step=10.0)
                    nuevo_precio = st.number_input("Nuevo Precio de Venta ($)", min_value=0.0, value=float(precio_actual), step=10.0)
                    
                    guardar_precio_btn = st.form_submit_button("💾 Guardar Cambios de Costos y Precios")
                    
                    if guardar_precio_btn:
                        try:
                            supabase.table("inventario").update({
                                "costo_unitario": nuevo_costo,
                                "precio_venta": nuevo_precio
                            }).eq("id_item", str(prod_c["id_item"])).execute()
                            
                            st.success("¡Costos y precios actualizados con éxito en Supabase!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar precios: {e}")

        with tab_resumen:
            st.markdown("### 📈 Resumen Financiero del Vivero")
            
            # Limpiar datos numéricos para cálculos
            df["stock_num"] = pd.to_numeric(df["stock_actual"], errors="fillna").fillna(0)
            df["costo_num"] = pd.to_numeric(df["costo_unitario"], errors="fillna").fillna(0.0)
            df["precio_num"] = pd.to_numeric(df["precio_venta"], errors="fillna").fillna(0.0)
            
            capital_total = (df["stock_num"] * df["costo_num"]).sum()
            valor_venta_total = (df["stock_num"] * df["precio_num"]).sum()
            ganancia_potencial = valor_venta_total - capital_total

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric(label="Capital Invertido (Costo Total)", value=f"${capital_total:,.2f}")
            with col_b:
                st.metric(label="Valor de Venta Potencial", value=f"${valor_venta_total:,.2f}")
            with col_c:
                st.metric(label="Ganancia Bruta Estimada", value=f"${ganancia_potencial:,.2f}")

            st.markdown("---")
            st.dataframe(df[["id_item", "familia", "producto", "contenedor", "stock_num", "costo_num", "precio_num"]], use_container_width=True)
        

if st.session_state["user"] is None:
    login_screen()
else:
    main_dashboard()
