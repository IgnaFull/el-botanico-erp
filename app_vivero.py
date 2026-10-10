import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuración de credenciales de Supabase
SUPABASE_URL = "https://jsdxfzanbgtswtmhfusy.supabase.co"
SUPABASE_KEY = "sb_publishable__3S6FIS90u29Niw5Mfn6kw_t0p51K7S"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración inicial de la página en ancho completo
st.set_page_config(page_title="El Botánico - ERP", page_icon="🌱", layout="wide")

# Cargar datos desde Supabase
def cargar_datos():
    try:
        response = supabase.table("inventario").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return pd.DataFrame()

df = cargar_datos()

# Asegurar columnas numéricas y cálculos de margen para el inventario
if not df.empty:
    if "costo_unitario" not in df.columns:
        df["costo_unitario"] = 0.0
    if "precio_venta" not in df.columns:
        df["precio_venta"] = 0.0
        
    df["costo_unitario"] = pd.to_numeric(df["costo_unitario"], errors="coerce").fillna(0.0)
    df["precio_venta"] = pd.to_numeric(df["precio_venta"], errors="coerce").fillna(0.0)
    
    # Calcular Margen Neto ($ y %)
    df["margen_neto"] = df["precio_venta"] - df["costo_unitario"]
    df["margen_pct"] = df.apply(
        lambda row: f"{((row['precio_venta'] - row['costo_unitario']) / row['precio_venta'] * 100):.1f}%" 
        if row['precio_venta'] > 0 else "0.0%", axis=1
    )
    
    # Columna combinada interna para los selectores
    df["opcion_display"] = df["id_item"].astype(str) + " - " + df["producto"].astype(str) + " (" + df["contenedor"].astype(str) + ")"

# --- PESTAÑAS SUPERIORES TIPO NAVEGADOR ---
tab_inv, tab_ventas, tab_stock, tab_precios, tab_config = st.tabs([
    "📦 Inventario General", 
    "🛒 Registro de Ventas", 
    "📊 Control de Stock", 
    "🏷️ Actualizar Precios",
    "⚙️ Configuración"
])

with tab_inv:
    st.header("📦 Inventario General y Stock en Tiempo Real")
    st.markdown("Consulta general de plantas, insumos, costos, precios y márgenes de ganancia.")
    
    if not df.empty and "familia" in df.columns:
        familias = ["Todas"] + list(df["familia"].dropna().unique())
        familia_seleccionada = st.selectbox("Filtrar por Familia", familias, key="filtro_fam_inv")
        
        if familia_seleccionada != "Todas":
            df_filtrado = df[df["familia"] == familia_seleccionada]
        else:
            df_filtrado = df
            
        busqueda = st.text_input("🔍 Buscar por nombre, especie o ID:", key="busqueda_inv")
        if busqueda:
            df_filtrado = df_filtrado[
                df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            ]
            
        # Aplicar las columnas seleccionadas en el módulo de Configuración
        columnas_disponibles = [col for col in df.columns if col != "opcion_display"]
        columnas_por_defecto = [c for c in ["id_item", "familia", "producto", "contenedor", "stock_actual", "precio_venta", "margen_neto"] if c in columnas_disponibles]
        
        cols_a_mostrar = st.session_state.get("columnas_visibles", columnas_por_defecto)
        cols_validas = [c for c in cols_a_mostrar if c in df_filtrado.columns]
        
        if cols_validas:
            df_tabla_mostrar = df_filtrado[cols_validas]
        else:
            df_tabla_mostrar = df_filtrado

        # Tabla interactiva con selección de filas habilitada
        evento_seleccion = st.dataframe(
            df_tabla_mostrar, 
            use_container_width=True, 
            selection_mode="single-row", 
            on_select="rerun",
            key="tabla_inventario_general"
        )
        
        # Mostrar detalle instantáneo del producto seleccionado en la tabla
        filas_seleccionadas = evento_seleccion.selection.rows if hasattr(evento_seleccion, 'selection') else []
        if filas_seleccionadas:
            idx = filas_seleccionadas[0]
            prod_sel = df_filtrado.iloc[idx]
            st.success(f"📌 **Producto seleccionado en tabla:** {prod_sel['producto']} (ID: `{prod_sel['id_item']}`) | Stock actual: **{prod_sel['stock_actual']} un.** | Precio Venta: **${float(prod_sel['precio_venta']):,.2f}**")

        st.info(f"Total de registros mostrados: {len(df_tabla_mostrar)}")
    else:
        st.warning("La tabla de inventario se encuentra vacía o faltan columnas.")

with tab_ventas:
    st.header("🛒 Módulo de Registro de Ventas")
    st.markdown("Seleccioná un producto, verificá su precio y stock, y registrá la venta al instante.")

    sub_tab_reg, sub_tab_hist = st.tabs(["💰 Realizar Venta", "📋 Historial y Facturación"])

    with sub_tab_reg:
        if df.empty:
            st.warning("No hay productos disponibles en el inventario para vender.")
        else:
            producto_venta = st.selectbox("Seleccionar Producto / Insumo a Vender", df["opcion_display"].tolist(), key="select_venta_tab")
            
            match_v = df[df["opcion_display"] == producto_venta]
            if not match_v.empty:
                p_data = match_v.iloc[0]
                stock_disponible = int(p_data["stock_actual"]) if pd.notna(p_data["stock_actual"]) else 0
                precio_registrado = float(p_data["precio_venta"]) if pd.notna(p_data["precio_venta"]) else 0.0
                
                col_info1, col_info2, col_info3 = st.columns(3)
                col_info1.metric("📦 ID de Ítem", str(p_data["id_item"]))
                col_info2.metric("🌱 Stock Disponible", f"{stock_disponible} un.")
                col_info3.metric("💲 Precio Sugerido", f"${precio_registrado:,.2f}")
                
                st.markdown("---")
                with st.form("form_registrar_venta_tab"):
                    cant_a_vender = st.number_input("Cantidad a vender", min_value=1, max_value=max(1, stock_disponible), value=1, step=1)
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

    with sub_tab_hist:
        st.markdown("### 📈 Historial Completo y Resumen de Facturación")
        try:
            resp_ventas = supabase.table("ventas").select("*").execute()
            df_ventas = pd.DataFrame(resp_ventas.data)
            
            if not df_ventas.empty:
                total_facturado = pd.to_numeric(df_ventas["total"], errors="coerce").sum()
                total_unidades = pd.to_numeric(df_ventas["cantidad"], errors="coerce").sum()
                cantidad_transacciones = len(df_ventas)

                col_1, col_2, col_3 = st.columns(3)
                col_1.metric(label="Facturación Total Acumulada", value=f"${total_facturado:,.2f}")
                col_2.metric(label="Unidades Vendidas Totales", value=f"{total_unidades:,}")
                col_3.metric(label="Cantidad de Ventas", value=f"{cantidad_transacciones}")

                st.markdown("---")
                st.dataframe(df_ventas, use_container_width=True)
            else:
                st.info("Todavía no hay ventas registradas en Supabase.")
        except Exception as e:
            st.warning("No se pudo cargar el historial. Asegurate de tener creada la tabla 'ventas' en Supabase.")

with tab_stock:
    st.header("📊 Control de Stock, Altas y Gestión de Ítems")
    st.markdown("Administrá el stock, da de alta nuevos productos, elimina registros o blanquea el inventario.")
    
    if df.empty:
        st.warning("No hay productos disponibles en la base de datos.")
    else:
        sub_tab_act, sub_tab_alta, sub_tab_del, sub_tab_res = st.tabs([
            "🔄 Actualizar Stock", 
            "➕ Nuevo Ítem", 
            "🗑️ Eliminar Ítem", 
            "⚠️ Reiniciar Inventario"
        ])
        
        with sub_tab_act:
            prod_stock_elegido = st.selectbox("Seleccionar Producto para actualizar stock", df["opcion_display"].tolist(), key="select_stock_tab")
            match_s = df[df["opcion_display"] == prod_stock_elegido]
            if not match_s.empty:
                s_data = match_s.iloc[0]
                stock_actual_val = int(s_data["stock_actual"]) if pd.notna(s_data["stock_actual"]) else 0
                
                st.info(f"Stock actual en base de datos para **{s_data['producto']}**: **{stock_actual_val} unidades**")
                
                with st.form("form_act_stock_tab"):
                    nuevo_stock = st.number_input("Nuevo valor de Stock", min_value=0, value=stock_actual_val, step=1)
                    if st.form_submit_button("💾 Guardar Nuevo Stock"):
                        try:
                            supabase.table("inventario").update({"stock_actual": nuevo_stock}).eq("id_item", str(s_data["id_item"])).execute()
                            st.success("¡Stock actualizado con éxito!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")

        with sub_tab_alta:
            st.markdown("### ➕ Registrar Nuevo Producto (ID autogenerado)")
            with st.form("form_alta_tab"):
                col_a, col_b = st.columns(2)
                with col_a:
                    familia = st.text_input("Familia (Ej: PLANTA, INSUMO)")
                    categoria = st.text_input("Categoría (Ej: SUCULENTA, MACETA)")
                with col_b:
                    subcategoria = st.text_input("Subcategoría (Ej: COLGANTE, 3L)", value="GEN")
                    contenedor = st.text_input("Contenedor / Medida (Ej: M15, 5L)")
                
                st.markdown("---")
                col_c, col_d = st.columns(2)
                with col_c:
                    producto = st.text_input("Producto / Especie / Modelo (Ej: MONSTERA)")
                with col_d:
                    stock_actual = st.number_input("Stock Inicial", min_value=0, value=0, step=1)
                
                if st.form_submit_button("🚀 Generar ID y Dar de Alta en Supabase"):
                    if familia and categoria and producto:
                        try:
                            # Autogenerar ID único basado en las iniciales de Familia, Categoría, Subcategoría y Contenedor + Número aleatorio
                            f_code = familia.strip()[:3].upper()
                            c_code = categoria.strip()[:3].upper()
                            s_code = subcategoria.strip()[:3].upper()
                            cnt_code = contenedor.strip()[:3].upper() if contenedor else "GEN"
                            rand_num = random.randint(100, 999)
                            
                            id_generado = f"{f_code}-{c_code}-{s_code}-{cnt_code}-{rand_num}"
                            
                            nuevo_reg = {
                                "id_item": id_generado,
                                "familia": familia.strip().upper(),
                                "categoria": categoria.strip().upper(),
                                "subcategoria": subcategoria.strip().upper(),
                                "producto": producto.strip().upper(),
                                "contenedor": contenedor.strip().upper() if contenedor else "-",
                                "stock_actual": stock_actual,
                                "costo_unitario": 0.0,
                                "precio_venta": 0.0
                            }
                            supabase.table("inventario").insert(nuevo_reg).execute()
                            st.success(f"¡Producto creado con éxito! ID asignado automáticamente: `{id_generado}`")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar: {e}")
                    else:
                        st.error("Los campos 'Familia', 'Categoría' y 'Producto' son obligatorios.")

        with sub_tab_del:
            prod_del_elegido = st.selectbox("Seleccionar Producto para eliminar", df["opcion_display"].tolist(), key="select_del_tab")
            match_d = df[df["opcion_display"] == prod_del_elegido]
            if not match_d.empty:
                d_data = match_d.iloc[0]
                st.warning(f"⚠️ Vas a eliminar el ítem: **{d_data['id_item']} - {d_data['producto']}**")
                conf_del = st.checkbox("Confirmo que deseo eliminar este ítem definitivamente", key="chk_del_tab")
                
                if st.button("❌ Eliminar Ítem", type="primary", key="btn_del_tab"):
                    if conf_del:
                        try:
                            supabase.table("inventario").delete().eq("id_item", str(d_data["id_item"])).execute()
                            st.success("¡Ítem eliminado correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar: {e}")
                    else:
                        st.error("Debes tildar la casilla de confirmación.")

        with sub_tab_res:
            st.warning("⚠️ **Atención:** Esto pondrá el **Stock en 0**, Costo en $0.0 y Precio en $0.0 para **todos** los productos.")
            conf_res = st.checkbox("Confirmo que quiero reiniciar todo el inventario a cero", key="chk_res_tab")
            
            if st.button("🔄 Blanquear Todo el Inventario a 0", type="primary", key="btn_res_tab"):
                if conf_res:
                    try:
                        supabase.table("inventario").update({
                            "stock_actual": 0,
                            "costo_unitario": 0.0,
                            "precio_venta": 0.0
                        }).neq("id_item", "ESTO_ES_UN_FILTRO_FALTO").execute()
                        st.success("¡Inventario reiniciado a cero con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Debes tildar la casilla de confirmación.")

with tab_precios:
    st.header("🏷️ Módulo de Actualización de Precios")
    st.markdown("Modificá de forma directa el Costo Unitario y el Precio de Venta de cualquier producto.")

    if df.empty:
        st.warning("No hay productos cargados.")
    else:
        prod_precio_elegido = st.selectbox("Seleccionar producto", df["opcion_display"].tolist(), key="select_precio_tab")
        match_p = df[df["opcion_display"] == prod_precio_elegido]
        if not match_p.empty:
            p_item = match_p.iloc[0]
            costo_actual = float(p_item["costo_unitario"]) if pd.notna(p_item["costo_unitario"]) else 0.0
            precio_actual = float(p_item["precio_venta"]) if pd.notna(p_item["precio_venta"]) else 0.0
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Costo Unitario Actual", f"${costo_actual:,.2f}")
            col_m2.metric("Precio de Venta Actual", f"${precio_actual:,.2f}")

            st.markdown("---")
            with st.form("form_precios_tab"):
                nuevo_costo = st.number_input("Nuevo Costo Unitario ($)", min_value=0.0, value=costo_actual, step=10.0)
                nuevo_precio_venta = st.number_input("Nuevo Precio de Venta ($)", min_value=0.0, value=precio_actual, step=10.0)
                
                if st.form_submit_button("💾 Guardar Nuevos Precios"):
                    try:
                        supabase.table("inventario").update({
                            "costo_unitario": nuevo_costo,
                            "precio_venta": nuevo_precio_venta
                        }).eq("id_item", str(p_item["id_item"])).execute()
                        st.success("¡Precios actualizados con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar precios: {e}")

with tab_config:
    st.header("⚙️ Módulo de Configuración General")
    st.markdown("Personalizá la apariencia visual y las columnas visibles de la tabla en pantalla.")
    
    st.subheader("🛠️ Personalizar Columnas del Inventario General")
    st.markdown("Tildá o destildá las columnas que querés que aparezcan en la tabla principal para optimizar el espacio:")
    
    if not df.empty:
        all_cols = [c for c in df.columns if c != "opcion_display"]
        default_cols = [c for c in ["id_item", "familia", "producto", "contenedor", "stock_actual", "precio_venta", "margen_neto"] if c in all_cols]
        
        cols_elegidas = st.multiselect(
            "Columnas visibles en el Inventario General:",
            options=all_cols,
            default=st.session_state.get("columnas_visibles", default_cols)
        )
        st.session_state["columnas_visibles"] = cols_elegidas
    else:
        st.info("Cargá datos en el inventario para poder configurar las columnas.")
        
    st.markdown("---")
    st.subheader("🎨 Apariencia Visual (Tema)")
    tema_seleccionado = st.radio(
        "Modo de Pantalla", 
        ["🌙 Modo Oscuro (Dark)", "☀️ Modo Claro (Light)"],
        index=0,
        key="radio_tema"
    )
    
    if "Modo Claro" in tema_seleccionado:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #FFFFFF;
                color: #111111;
            }
            .stMarkdown, p, span, label, h1, h2, h3, h4, h5, h6 {
                color: #111111 !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        st.info("☀️ Modo Claro aplicado correctamente con fuentes de alta visibilidad.")
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }
            .stMarkdown, p, span, label, h1, h2, h3, h4, h5, h6 {
                color: #FAFAFA !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        st.info("🌙 Modo Oscuro aplicado correctamente.")
