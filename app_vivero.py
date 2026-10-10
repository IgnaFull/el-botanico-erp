import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Configuración de credenciales de Supabase
SUPABASE_URL = "https://jsdxfzanbgtswtmhfusy.supabase.co"
SUPABASE_KEY = "sb_publishable__3S6FIS90u29Niw5Mfn6kw_t0p51K7S"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="El Botánico - ERP", page_icon="🌱", layout="wide")

st.sidebar.title("🌿 El Botánico")
menu = st.sidebar.radio("Navegación", [
    "Inventario General", 
    "Control de Stock", 
    "Registro de Ventas", 
    "Actualizar Precios"
])

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
    st.markdown("Consulta en tiempo real de todos los productos cargados, costos, precios y margen neto.")
    
    if not df.empty and "familia" in df.columns:
        if "costo_unitario" not in df.columns:
            df["costo_unitario"] = 0.0
        if "precio_venta" not in df.columns:
            df["precio_venta"] = 0.0
            
        df["costo_unitario"] = pd.to_numeric(df["costo_unitario"], errors="coerce").fillna(0.0)
        df["precio_venta"] = pd.to_numeric(df["precio_venta"], errors="coerce").fillna(0.0)
        
        # Calcular Margen Neto
        df["margen_neto"] = df["precio_venta"] - df["costo_unitario"]
        df["margen_pct"] = df.apply(
            lambda row: f"{((row['precio_venta'] - row['costo_unitario']) / row['precio_venta'] * 100):.1f}%" 
            if row['precio_venta'] > 0 else "0.0%", axis=1
        )

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
    st.markdown("Administrá el stock actual, creá nuevos productos, da de baja ítems o blanqueá los valores a cero.")
    
    if df.empty:
        st.warning("No hay productos disponibles en la base de datos.")
    else:
        tab_actualizar, tab_crear, tab_eliminar, tab_reset = st.tabs([
            "🔄 Actualizar Stock", 
            "➕ Nuevo Ítem", 
            "🗑️ Eliminar Ítem", 
            "⚠️ Reiniciar Inventario (A Cero)"
        ])
        
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
                                "costo_unitario": 0.0,
                                "precio_venta": 0.0
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

        with tab_reset:
            st.warning("⚠️ **Atención:** Esta acción pondrá el **Stock en 0**, el **Costo Unitario en $0.0** y el **Precio de Venta en $0.0** para **todos** los productos registrados en la base de datos.")
            confirmar_reset = st.checkbox("Confirmo que quiero reiniciar todo el inventario a cero")
            
            if st.button("🔄 Blanquear Todo el Inventario a 0", type="primary"):
                if confirmar_reset:
                    try:
                        supabase.table("inventario").update({
                            "stock_actual": 0,
                            "costo_unitario": 0.0,
                            "precio_venta": 0.0
                        }).neq("id_item", "ESTO_ES_UN_FILTRO_FALTO_QUE_APLICA_A_TODOS").execute()
                        
                        st.success("¡Todo el inventario fue reiniciado a cero con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al reiniciar el inventario: {e}")
                else:
                    st.error("Debes tildar la casilla de confirmación para ejecutar el reinicio.")

elif menu == "Registro de Ventas":
    st.header("🛒 Módulo de Registro de Ventas")
    st.markdown("Registrá nuevas salidas de productos (descontando stock al instante) y consultá el historial y totales.")

    tab_registrar, tab_historial = st.tabs(["💰 Registrar Venta", "📋 Historial y Totales"])

    with tab_registrar:
        if df.empty:
            st.warning("No hay productos disponibles en el inventario para vender.")
        else:
            df["opcion_display"] = df["id_item"].astype(str) + " - " + df["producto"].astype(str) + " (" + df["contenedor"].astype(str) + ")"
            producto_venta = st.selectbox("Seleccionar Producto a Vender", df["opcion_display"].tolist(), key="select_venta")
            
            match_v = df[df["opcion_display"] == producto_venta]
            if not match_v.empty:
                p_data = match_v.iloc[0]
                stock_disponible = int(p_data["stock_actual"]) if pd.notna(p_data["stock_actual"]) else 0
                
                # Obtener el precio de venta cargado en el inventario para traerlo por defecto
                precio_registrado = float(p_data["precio_venta"]) if "precio_venta" in p_data and pd.notna(p_data["precio_venta"]) else 0.0
                
                st.info(f"Stock disponible actualmente: **{stock_disponible} unidades** | Precio oficial sugerido: **${precio_registrado:,.2f}**")
                
                with st.form("form_registrar_venta"):
                    cant_a_vender = st.number_input("Cantidad a vender", min_value=1, max_value=max(1, stock_disponible), value=1, step=1)
                    
                    # El campo se completa automáticamente con el precio de venta de la base y se puede editar manualmente
                    precio_cobrado = st.number_input("Precio unitario de venta ($) [Editable]", min_value=0.0, value=precio_registrado, step=10.0)
                    cliente = st.text_input("Cliente (Opcional)", value="General")
                    
                    completar_venta_btn = st.form_submit_button("✅ Confirmar Venta y Descontar Stock")
                    
                    if completar_venta_btn:
                        if cant_a_vender > stock_disponible:
                            st.error("No hay suficiente stock para realizar esta venta.")
                        else:
                            try:
                                nuevo_stock = stock_disponible - cant_a_vender
                                total_venta = cant_a_vender * precio_cobrado
                                
                                from datetime import timedelta
                                fecha_hora_actual = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                                
                                supabase.table("inventario").update({"stock_actual": nuevo_stock}).eq("id_item", str(p_data["id_item"])).execute()
                                
                                venta_registro = {
                                    "id_item": str(p_data["id_item"]),
                                    "producto": str(p_data["producto"]),
                                    "cantidad": cant_a_vender,
                                    "precio_unitario": precio_cobrado,
                                    "total": total_venta,
                                    "cliente": cliente.strip(),
                                    "fecha": fecha_hora_actual
                                }
                                supabase.table("ventas").insert(venta_registro).execute()
                                
                                st.success(f"¡Venta registrada con éxito! Total: ${total_venta:,.2f}. Stock actualizado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al procesar la venta: {e}. Recordá tener creada la tabla 'ventas' en Supabase.")

    with tab_historial:
        st.markdown("### 📈 Historial Completo y Resumen de Facturación")
        try:
            resp_ventas = supabase.table("ventas").select("*").execute()
            df_ventas = pd.DataFrame(resp_ventas.data)
            
            if not df_ventas.empty:
                total_facturado = pd.to_numeric(df_ventas["total"], errors="coerce").sum()
                total_unidades = pd.to_numeric(df_ventas["cantidad"], errors="coerce").sum()
                cantidad_transacciones = len(df_ventas)

                col_1, col_2, col_3 = st.columns(3)
                with col_1:
                    st.metric(label="Facturación Total Acumulada", value=f"${total_facturado:,.2f}")
                with col_2:
                    st.metric(label="Unidades Vendidas Totales", value=f"{total_unidades:,}")
                with col_3:
                    st.metric(label="Cantidad de Ventas", value=f"{cantidad_transacciones}")

                st.markdown("---")
                st.dataframe(df_ventas, use_container_width=True)
            else:
                st.info("Todavía no hay ventas registradas en Supabase.")
        except Exception as e:
            st.warning("No se pudo cargar el historial. Asegurate de tener creada la tabla 'ventas' en tu base de datos de Supabase.")

elif menu == "Actualizar Precios":
    st.header("🏷️ Módulo de Actualización de Precios")
    st.markdown("Modificá de forma directa el Costo Unitario y el Precio de Venta de cualquier producto en el Inventario General.")

    if df.empty:
        st.warning("No hay productos cargados en el inventario.")
    else:
        if "costo_unitario" not in df.columns:
            df["costo_unitario"] = 0.0
        if "precio_venta" not in df.columns:
            df["precio_venta"] = 0.0

        df["opcion_precio"] = df["id_item"].astype(str) + " - " + df["producto"].astype(str) + " (" + df["contenedor"].astype(str) + ")"
        prod_precio_elegido = st.selectbox("Seleccionar producto del Inventario General", df["opcion_precio"].tolist(), key="select_mod_precio")
        
        match_p = df[df["opcion_precio"] == prod_precio_elegido]
        if not match_p.empty:
            p_item = match_p.iloc[0]
            costo_actual = float(p_item["costo_unitario"]) if pd.notna(p_item["costo_unitario"]) else 0.0
            precio_actual = float(p_item["precio_venta"]) if pd.notna(p_item["precio_venta"]) else 0.0
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric(label="Costo Unitario Actual", value=f"${costo_actual:,.2f}")
            with col_m2:
                st.metric(label="Precio de Venta Actual", value=f"${precio_actual:,.2f}")

            st.markdown("---")
            with st.form("form_editar_precios"):
                nuevo_costo = st.number_input("Nuevo Costo Unitario ($)", min_value=0.0, value=costo_actual, step=10.0)
                nuevo_precio_venta = st.number_input("Nuevo Precio de Venta ($)", min_value=0.0, value=precio_actual, step=10.0)
                
                guardar_precios_btn = st.form_submit_button("💾 Guardar Nuevos Precios en Supabase")
                
                if guardar_precios_btn:
                    try:
                        supabase.table("inventario").update({
                            "costo_unitario": nuevo_costo,
                            "precio_venta": nuevo_precio_venta
                        }).eq("id_item", str(p_item["id_item"])).execute()
                        
                        st.success("¡Precios actualizados con éxito en el inventario general!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar los precios: {e}")
