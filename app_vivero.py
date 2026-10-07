import io
import sqlite3
import pandas as pd
import streamlit as st

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="El Botánico - ERP Vivero", page_icon="🌿", layout="wide"
)

DB_NAME = "vivero_web.db"


def inicializar_bd():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria_padre_id INTEGER
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER,
            sku TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio_venta REAL NOT NULL,
            stock_actual INTEGER NOT NULL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            medio_pago TEXT NOT NULL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            subtotal REAL
        )
    """)

  # --- CARGAR CATEGORÍAS Y FAMILIAS DEL INVENTARIO POR DEFECTO SI LA TABLA ESTÁ VACÍA ---
  cursor.execute("SELECT COUNT(*) FROM categorias")
  if cursor.fetchone()[0] == 0:
    familias_inventario = {
        "HERBACEAS PERENNES/CADUCAS": [
            "AGAVE AMERICANO",
            "AGAVE AMERICANO VARIEGADO",
            "AGAVE ANGUSTIFOLIA MAGUEY",
            "AGAVE ATENUATA",
            "AGAVE DESMETTIANA",
            "AGAVE DESMETTIANA VARIEGADO",
            "AGLONEMA FREEDMAN",
            "AGLONEMA PATTAYA",
            "AGLONEMA PINK",
            "ALEGRIA DEL HOGAR",
            "ALISO DE MAR (LOBULARIA MARITIMA)",
            "ALPINIA",
            "ALTERNANTHERA BRASILIANA",
            "ALTERNANTHERA FICOIDEA RED",
            "ALTERNANTHERA FICOIDEA VERDE",
            "ALOCACIA (OREJA DE ELEFANTE) CHICA",
            "ALOCACIA (OREJA DE ELEFANTE) MEDIANA",
            "ALOCACIA (OREJA DE ELEFANTE) GRANDE",
            "ANTHURIUM",
            "ANTHURIUM ROJO",
            "ASTA DE CIERVO",
            "ASCLEPIA",
            "AZUCENA DE MEXICO",
            "BEGONIA ALA DE ANGEL",
            "BEGONIA DRAGON",
            "BEGONIA HIRTELLA",
            "BEGONIA BOOMER",
            "BEGONIA RED",
            "BEGONIA REY (PLATEADA)",
            "BROMELIA (LAGRIMA DE REINA)",
            "BROMELIA FOSFORITO",
            "CALA BLANCA",
            "CALATHEA MACOYANA",
            "CALATHEA MACOYANA CHICA",
            "CALATHEA MIL RAYAS",
            "CALATHEA ZEBRINA",
            "CALISTEMO",
            "CLAVELINA",
            "CRISANTEMO",
            "COPETITO",
            "CORTADERIA SELLOANA",
            "COLOCACIA ESCULENTA",
            "CUARESMERO 7L",
            "CUARESMERO 5L",
            "DIANELA",
            "DIEFFENBACHIA MARIANA",
            "DIETE",
            "DIMORFOTECA (MARGARITA DEL CABO)",
            "DRACENA RUBRA",
            "DRACENA TRICOLOR",
            "DRACENA LEMON",
            "DRACENA WARNECKI",
            "DRACENA KIWI",
            "DRACENA BABY",
            "ESCUDO PERSA",
            "ESPATIFILO",
            "ESPATIFILO SENSACIÒN",
            "FITONIA",
            "FLOR DE CARTON (DORSTENIA ELATA)",
            "FLORALES",
            "GAURA",
            "GIRASOL",
            "HELECHO MONO",
            "HELECHO PIEDRA",
            "HELECHO ESPARRAGO",
            "HELICONIA CHICA",
            "HELICONIA GRANDE",
            "HIPOESTES",
            "LAZO DE AMOR",
            "LILIUM",
            "LIRIO DEL AMAZONAS",
            "LIRIO MATIZADO",
            "LOBELIA",
            "MARANTA",
            "MARANTA ORACIÒN",
            "MARGARITA",
            "MELINI",
            "MONEDA VARIEGADA",
            "MONSTERA",
            "MONSTERA GRANDE",
            "PALMA DEL VIAJERO",
            "PENACHO",
            "PENNICETUM",
            "PENSAMIENTO",
            "PENTA",
            "PETUNIA",
            "PETUNIA AMARILLA COLGANTE",
            "PHILODENDRO SANGUINEA",
            "PHILODENDRO VERDE",
            "PHILODENDRO WHITE PRINCESS",
            "PIEL DE LEOPARDO (DRIMIOPSIS MACULATA)",
            "PORTULACA",
            "POTUS",
            "POTUS LEMON",
            "POTUS VARIEGADO BLANCO",
            "POTUS VARIEGADO VERDE",
            "PORTULACA (VERDOLAGA)",
            "RETAMA",
            "RUPELLI",
            "SOL DE SUDAFRICA",
            "STRELITZIA NICOLAI (FLOR BALNCA Y NEGRO)",
            "STRELITZIA REGINAE (FLOR NARANJA)",
            "STROMANTHE",
            "STROMANTHE GRANDE",
            "STROMANTHE CHICO",
            "TRADESCANTIA",
            "TREBOL ROJO",
            "TUMBERGIA",
            "VINCA",
            "ZAMIOCULCA",
            "ZAMIOCULCA BLACK",
            "ZINNIA",
        ],
        "JAZMINES": [
            "JAZMIN CHINO (JASMINUM POLYANTHUM)",
            "JAZMIN DEL CIELO (PLUMBAGO AURICULATA)",
            "JAZMIN DE LECHE (TRACHELOSPERMUM JASMINOIDES)",
            "JAZMIN DEL CABO (GARDENIA JASMINOIDES)",
            "JAZMIN DEL PAIS (JASMINUM GRANDIFLORUM)",
            "JAZMIN AMARILLO (JASMINUM MENSYI)",
            "JAZMIN DE MADAGASCAR (STEPHANOTIS FLORIBUNDA)",
            "JAZMIN ESTRELLA",
            "JAZMIN CAROLINA",
            "JAZMIN MAGNO (PLUMERIA RUBRA )",
            "JAZMIN BRASILERO (CUMBRETUM INDICUM)",
            "JAZMIN PARAGUAYO (BRUNFELSIA AUSTRALIS)",
        ],
        "AROMATICAS": [
            "AJENJO",
            "ALBAHACA",
            "ANIZ",
            "BURRITO",
            "CEDRON PARAGUAYO",
            "CITRONELA",
            "CURRY",
            "LAVANDA",
            "MENTA CUBANA",
            "MENTA NUESTRA",
            "MENTA NEGRA",
            "OREGANO",
            "POLEO",
            "ROMERO",
            "ROMERO PEQUEÑO",
            "RUDA",
            "SALVIA",
            "STEVIA",
            "TOMILLO",
        ],
        "PALMERAS": [
            "AREKA",
            "CYCAS REVOLUTA",
            "IMPERIAL (ROYSTONEA REGIA)",
            "PALMA BAMBU ( RHAPIS EXCELSA)",
            "PALMITO (EUTERPE EDULIS )",
            "PHOENIX CANARIENSIS",
            "PINDO (SYAGRUS ROMANZOFFIANA)",
            "SEAFORTIA ALEJANDRA (ARCHONTOPHOENIX ALEXANDRAE)",
            "WASHINGTONIA ROBUSTA",
        ],
        "ARBUSTOS/ ENREDADERAS": [
            "AMARANTHUS",
            "ARALIA ELEGANTISIMA",
            "ARALIA GERALIO",
            "ARALIA VARIEGADA",
            "AZALEA",
            "BUXUS",
            "BUXUS TERRON",
            "CLERODENDRO",
            "CAMPANITA PLATEADA (Convolvulus)",
            "COLEUS SCUTELLARIOIDES",
            "CRATAEGUS",
            "CROTO GOLD STAR",
            "CROTÒN",
            "CROTO PETRA",
            "CROTO LENGUA DE FUEGO",
            "CROTO TIRABUZON",
            "CROTO ASIATICO",
            "DURANTA",
            "DURANTA ERECTA",
            "DURANTA VARIEGADA",
            "DURANTA.SP",
            "ENAMORADA DEL MURO",
            "ENAMORADA DEL MURO VARIEGADA",
            "ESTRELLA FEDERAL",
            "EUPHORBIA VARIEGATA",
            "LANTANA",
            "MADRE SELVA",
            "OLEO TEXANO",
            "PALO DE AGUA",
            "POLIGALA",
            "PERESKIA ACULEATA",
            "ROSA",
            "ROSA AISBERG",
            "ROSA CHINA",
            "ROSA MINI",
            "ROSA TREPADORA",
            "SANTA RITA",
            "CORONITA DE NOVIA (SPIRAEA CANTONIENSIS)",
            "WESTRINGIA",
            "YUCA",
        ],
        "ÀRBOLES": [
            "AGUARIBAY (SCHINUS MOLLE)",
            "FICUS PANDURATA",
            "GOMERO COMUN",
            "GOMERO COMUN 1L",
            "GOMERO DISCIPLINADO",
            "GOMERO PINK",
            "GOMERO VARIEGADO",
            "LAUREL BLANCO",
            "LAUREL DE JARDIN",
            "PATA DE BUEY (BAUHINIA FORTICATA)",
            "PANDURATA",
            "TACUARITA",
            "VIRARÒ",
        ],
        "SUCULENTAS": [
            "ALOE VERA",
            "KALANCHOE DOBLE",
            "KALANCHOE MINI",
            "NOLINA CHICA",
            "NOLINA MEDIANA",
            "NOLINA GRANDE",
        ],
        "FRUTALES": [
            "CIRUELO",
            "DURAZNERO",
            "GUAJABA",
            "LIMON EUREKA",
            "MAMON RED LEDY",
            "MANGO",
            "MORA",
            "NISPERO",
            "NOGAL COMUN",
            "NOGAL PECAN",
            "OLIVO",
            "PALTO",
        ],
    }

    for familia, especies in familias_inventario.items():
      cursor.execute(
          "INSERT INTO categorias (nombre, categoria_padre_id) VALUES (?, NULL)",
          (familia,),
      )
      familia_id = cursor.lastrowid
      for especie in especies:
        cursor.execute(
            "INSERT INTO categorias (nombre, categoria_padre_id) VALUES (?,"
            " ?)",
            (especie, familia_id),
        )

  # --- PRECARGAR PRODUCTOS INICIALES DESDE EL INVENTARIO DEL EXCEL SI LA TABLA PRODUCTOS ESTÁ VACÍA ---
  cursor.execute("SELECT COUNT(*) FROM productos")
  if cursor.fetchone()[0] == 0:
    try:
      df_inv = pd.read_excel(
          "El_Botanico_Gestion_Integral 17-09.xlsx", sheet_name="INVENTARIO"
      )
      cat_default_id = 1
      for _, row in df_inv.iterrows():
        esp = row.get("ESPECIE")
        if pd.isna(esp):
          continue
        precio = row.get("Precio Venta", 0)
        stock = row.get("Existencias", 0)
        try:
          precio = float(precio)
        except:
          precio = 0.0
        try:
          stock = int(float(stock))
        except:
          stock = 0

        # Generar SKU automático único basado en las primeras letras
        sku_gen = "".join([c for c in str(esp) if c.isalnum()])[
            :6
        ].upper() + str(_)
        cursor.execute(
            """INSERT OR IGNORE INTO productos (categoria_id, sku, nombre, precio_venta, stock_actual)
                   VALUES (?, ?, ?, ?, ?)""",
            (cat_default_id, sku_gen, str(esp).strip(), precio, stock),
        )
    except Exception as e:
      print("Aviso al precargar inventario:", e)

  # --- PRECARGAR VENTAS HISTÓRICAS DESDE LA SOLAPA VENTAS SI LA TABLA VENTAS ESTÁ VACÍA ---
  cursor.execute("SELECT COUNT(*) FROM ventas")
  if cursor.fetchone()[0] == 0:
    try:
      df_ventas_excel = pd.read_excel(
          "El_Botanico_Gestion_Integral 17-09.xlsx", sheet_name="Ventas"
      )
      df_ventas_excel = df_ventas_excel.dropna(subset=["Especie"])

      for _, row in df_ventas_excel.iterrows():
        fecha_val = str(row.get("Fecha", "2026-08-09"))[:10]
        total_val = row.get("Total", 0)
        try:
          total_val = float(total_val)
        except:
          total_val = 0.0

        cursor.execute(
            "INSERT INTO ventas (fecha, total, medio_pago) VALUES (?, ?, ?)",
            (fecha_val, total_val, "Efectivo"),
        )
        venta_id = cursor.lastrowid

        # Buscar producto relacionado o crear uno genérico temporal
        prod_nombre = str(row.get("Especie", "Planta General")).strip()
        cant_val = row.get("Cantidad", 1)
        try:
          cant_val = int(float(cant_val))
        except:
          cant_val = 1

        cursor.execute(
            "SELECT id FROM productos WHERE nombre = ?", (prod_nombre,)
        )
        res_p = cursor.fetchone()
        if res_p:
          prod_id = res_p[0]
        else:
          # Insertar producto rápido si no estaba en inventario
          sku_v = "".join([c for c in prod_nombre if c.isalnum()])[
              :6
          ].upper() + str(_)
          cursor.execute(
              """INSERT OR IGNORE INTO productos (categoria_id, sku, nombre, precio_venta, stock_actual)
                       VALUES (1, ?, ?, ?, 0)""",
              (sku_v, prod_nombre, total_val / max(1, cant_val)),
          )
          prod_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, subtotal)
                   VALUES (?, ?, ?, ?)""",
            (venta_id, prod_id, cant_val, total_val),
        )
    except Exception as e:
      print("Aviso al precargar ventas históricas:", e)

  conn.commit()
  conn.close()


inicializar_bd()

# --- 2. SISTEMA DE LOGIN / CONTRASEÑA ---
CLAVE_ACCESO = "botanico2026"

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if not st.session_state.autenticado:
  st.title("🌿 El Botánico - Acceso Restringido")
  st.markdown("---")
  st.info(
      "🔒 Este sistema es privado para la administración de El Botánico."
      " Ingresá la contraseña para continuar."
  )

  password_ingresada = st.text_input("Contraseña de acceso:", type="password")

  if st.button("🔑 Ingresar", type="primary"):
    if password_ingresada == CLAVE_ACCESO:
      st.session_state.autenticado = True
      st.success("¡Acceso concedido!")
      st.rerun()
    else:
      st.error("❌ Contraseña incorrecta. Intentá nuevamente.")

  st.stop()

# --- 3. TÍTULO PRINCIPAL (Una vez logueado) ---
st.title("🌿 El Botánico - Sistema de Gestión")
st.markdown("---")

if st.sidebar.button("🔒 Cerrar Sesión"):
  st.session_state.autenticado = False
  st.rerun()

# --- 4. PESTAÑAS HORIZONTALES DIRECTAS ---
tab_dash, tab_pos, tab_historial, tab_stock, tab_nuevo, tab_eliminar, tab_cat = (
    st.tabs([
        "📊 Dashboard",
        "🛒 Registrar Venta (POS)",
        "📜 Historial",
        "📦 Control de Stock",
        "➕ Nuevo Producto",
        "🗑️ Eliminar Producto",
        "🗂️ Gestión de Categorías",
    ])
)

conn = sqlite3.connect(DB_NAME)

# ==================== 1. DASHBOARD ====================
with tab_dash:
  st.subheader("Panel de Indicadores Generales")

  df_ventas = pd.read_sql("SELECT * FROM ventas", conn)
  df_productos = pd.read_sql(
      """
        SELECT p.sku as 'Código de Producto', p.nombre as 'Producto', 
               p.precio_venta as 'Precio ($)', p.stock_actual as 'Stock Actual', 
               c.nombre as 'Categoría' 
        FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id
    """,
      conn,
  )

  total_recaudado = df_ventas["total"].sum() if not df_ventas.empty else 0.0
  cant_ventas = len(df_ventas)

  if not df_productos.empty:
    df_productos["Precio ($)"] = pd.to_numeric(
        df_productos["Precio ($)"], errors="coerce"
    ).fillna(0)
    df_productos["Stock Actual"] = pd.to_numeric(
        df_productos["Stock Actual"], errors="coerce"
    ).fillna(0)
    valor_stock = (
        df_productos["Precio ($)"] * df_productos["Stock Actual"]
    ).sum()
    stock_bajo = len(df_productos[df_productos["Stock Actual"] < 5])
  else:
    valor_stock = 0.0
    stock_bajo = 0

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("💰 Facturación Total", f"${total_recaudado:,.2f}")
  col2.metric("🛒 Ventas Realizadas", cant_ventas)
  col3.metric("📦 Valor del Inventario", f"${valor_stock:,.2f}")
  col4.metric("⚠️ Alertas Stock Bajo", stock_bajo)

  st.markdown("---")
  st.subheader("Inventario Actual")
  if not df_productos.empty:
    st.dataframe(df_productos, use_container_width=True)
  else:
    st.info("No hay productos cargados todavía.")

# ==================== 2. REGISTRAR VENTA (POS) ====================
with tab_pos:
  st.subheader("Caja Rápida / Punto de Venta")

  df_productos = pd.read_sql(
      "SELECT id, sku, nombre, precio_venta, stock_actual FROM productos", conn
  )

  if df_productos.empty:
    st.warning(
        "⚠️ No hay productos disponibles para la venta. Cargá productos"
        " primero."
    )
  else:
    opciones_prod = {
        f"[{row['sku']}] {row['nombre']} (Stock: {row['stock_actual']} - ${row['precio_venta']})": row[
            "id"
        ]
        for _, row in df_productos.iterrows()
    }

    prod_seleccionado_str = st.selectbox(
        "Seleccionar Producto:", list(opciones_prod.keys())
    )
    prod_id = opciones_prod[prod_seleccionado_str]

    prod_info = df_productos[df_productos["id"] == prod_id].iloc[0]

    stock_disponible = int(
        pd.to_numeric(
            pd.Series([prod_info["stock_actual"]]), errors="coerce"
        ).fillna(0)[0]
    )
    precio_unitario = float(
        pd.to_numeric(
            pd.Series([prod_info["precio_venta"]]), errors="coerce"
        ).fillna(0)[0]
    )

    cantidad = st.number_input(
        "Cantidad a llevar:",
        min_value=1,
        max_value=max(1, stock_disponible),
        step=1,
    )
    medio_pago = st.radio(
        "Medio de Pago:",
        ["Efectivo", "Transferencia", "Tarjeta Débito/Crédito"],
        horizontal=True,
    )

    subtotal = precio_unitario * cantidad
    st.info(f"**Total a Pagar:** ${subtotal:,.2f}")

    if st.button("✅ Confirmar Venta", type="primary"):
      if stock_disponible <= 0:
        st.error("No hay stock disponible de este producto.")
      else:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ventas (total, medio_pago) VALUES (?, ?)",
            (subtotal, medio_pago),
        )
        venta_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO detalle_ventas (venta_id, producto_id, cantidad,"
            " subtotal) VALUES (?, ?, ?, ?)",
            (venta_id, prod_id, cantidad, subtotal),
        )

        nuevo_stock = stock_disponible - cantidad
        cursor.execute(
            "UPDATE productos SET stock_actual = ? WHERE id = ?",
            (nuevo_stock, prod_id),
        )

        conn.commit()
        st.success(f"¡Venta registrada con éxito! Total cobrado: ${subtotal:,.2f}")
        st.rerun()

# ==================== 3. HISTORIAL DE VENTAS ====================
with tab_historial:
  st.subheader("📜 Registro Detallado de Ventas")

  df_historial = pd.read_sql(
      """
        SELECT v.id as 'ID Venta', v.fecha as 'Fecha y Hora', 
               p.nombre as 'Producto', d.cantidad as 'Cantidad', 
               d.subtotal as 'Subtotal ($)', v.medio_pago as 'Medio de Pago'
        FROM ventas v
        JOIN detalle_ventas d ON v.id = d.venta_id
        JOIN productos p ON d.producto_id = p.id
        ORDER BY v.id DESC
    """,
      conn,
  )

  if not df_historial.empty:
    st.dataframe(df_historial, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
      df_historial.to_excel(writer, index=False, sheet_name="Historial de Ventas")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Descargar Historial en Excel",
        data=excel_data,
        file_name="historial_ventas_el_botanico.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
  else:
    st.info("Aún no se han registrado ventas.")

# ==================== 4. CONTROL DE STOCK ====================
with tab_stock:
  st.subheader("Auditoría de Inventario")
  df_stock = pd.read_sql(
      """
        SELECT p.sku as 'Código de Producto', p.nombre as 'Producto', c.nombre as 'Categoría', 
               p.precio_venta as 'Precio ($)', p.stock_actual as 'Stock Disponible'
        FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id
    """,
      conn,
  )
  if not df_stock.empty:
    st.dataframe(df_stock, use_container_width=True)

    output_stock = io.BytesIO()
    with pd.ExcelWriter(output_stock, engine="xlsxwriter") as writer:
      df_stock.to_excel(writer, index=False, sheet_name="Inventario")
    excel_stock_data = output_stock.getvalue()

    st.download_button(
        label="📥 Descargar Inventario en Excel",
        data=excel_stock_data,
        file_name="inventario_el_botanico.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
  else:
    st.info("El inventario está vacío.")

# ==================== 5. NUEVO PRODUCTO ====================
with tab_nuevo:
  st.subheader("➕ Agregar Planta o Insumo")

  df_cat = pd.read_sql("SELECT id, nombre FROM categorias", conn)

  if df_cat.empty:
    st.warning("⚠️ No hay categorías disponibles.")
  else:
    opciones_cat = {row["nombre"]: row["id"] for _, row in df_cat.iterrows()}

    cat_elegida = st.selectbox("Categoría:", list(opciones_cat.keys()))
    cat_id = opciones_cat[cat_elegida]

    sku = st.text_input(
        "Código de Producto:",
        placeholder="Ej: MONS-01, SUC-10, MAC-PLAS-12",
        key="input_sku",
    )
    nombre_prod = st.text_input(
        "Nombre de la Planta o Producto:",
        placeholder="Ej: Monstera Deliciosa N15",
        key="input_nombre_prod",
    )
    precio = st.number_input(
        "Precio de Venta ($):", min_value=0.0, step=100.0, key="input_precio"
    )
    stock = st.number_input(
        "Stock Inicial:", min_value=0, step=1, key="input_stock"
    )

    if "confirmar_nuevo_prod" not in st.session_state:
      st.session_state.confirmar_nuevo_prod = False

    if not st.session_state.confirmar_nuevo_prod:
      if st.button("💾 Guardar Producto", type="primary"):
        if not sku or not nombre_prod:
          st.error("Por favor completa el código de producto y el nombre.")
        else:
          st.session_state.confirmar_nuevo_prod = True
          st.rerun()
    else:
      st.warning(
          f"⚠️ ¿Confirmás que deseás registrar el producto **{nombre_prod}** con"
          f" código **{sku}** por un precio de **${precio:,.2f}** y stock"
          f" inicial de **{stock}**?"
      )
      col_c1, col_c2 = st.columns(2)
      with col_c1:
        if st.button(
            "✅ Sí, guardar producto", type="primary", use_container_width=True
        ):
          try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO productos (categoria_id, sku, nombre, precio_venta, stock_actual) 
                       VALUES (?, ?, ?, ?, ?)""",
                (cat_id, sku, nombre_prod, precio, stock),
            )
            conn.commit()
            st.session_state.confirmar_nuevo_prod = False
            st.success("¡Producto guardado correctamente!")
            st.rerun()
          except sqlite3.IntegrityError:
            st.session_state.confirmar_nuevo_prod = False
            st.error(
                f"El código de producto '{sku}' ya existe. Ingresá otro."
            )
      with col_c2:
        if st.button("❌ Cancelar", use_container_width=True):
          st.session_state.confirmar_nuevo_prod = False
          st.rerun()

# ==================== 6. ELIMINAR PRODUCTO ====================
with tab_eliminar:
  st.subheader("🗑️ Eliminar Producto del Inventario")

  df_productos_del = pd.read_sql(
      "SELECT id, sku, nombre FROM productos", conn
  )

  if df_productos_del.empty:
    st.info("No hay productos cargados para eliminar.")
  else:
    opciones_borrar = {
        f"[{row['sku']}] {row['nombre']}": row["id"]
        for _, row in df_productos_del.iterrows()
    }

    prod_a_borrar_str = st.selectbox(
        "Seleccioná el producto a eliminar:", list(opciones_borrar.keys())
    )
    id_a_borrar = opciones_borrar[prod_a_borrar_str]

    if "confirmar_del_prod" not in st.session_state:
      st.session_state.confirmar_del_prod = False

    if not st.session_state.confirmar_del_prod:
      if st.button("❌ Eliminar Producto", type="secondary"):
        st.session_state.confirmar_del_prod = True
        st.rerun()
    else:
      st.warning(
          f"⚠️ **ATENCIÓN:** ¿Estás seguro de eliminar permanentemente el"
          f" producto **{prod_a_borrar_str}**?"
      )
      col_d1, col_d2 = st.columns(2)
      with col_d1:
        if st.button(
            "🔴 Sí, eliminar definitivamente",
            type="primary",
            use_container_width=True,
        ):
          cursor = conn.cursor()
          cursor.execute("DELETE FROM productos WHERE id = ?", (id_a_borrar,))
          conn.commit()
          st.session_state.confirmar_del_prod = False
          st.success("¡El producto ha sido eliminado con éxito!")
          st.rerun()
      with col_d2:
        if st.button("❌ Cancelar", use_container_width=True):
          st.session_state.confirmar_del_prod = False
          st.rerun()

# ==================== 7. GESTIÓN DE CATEGORÍAS ====================
with tab_cat:
  st.subheader("🗂️️ Administrar Categorías y Subcategorías")

  col1, col2 = st.columns(2)

  with col1:
    st.markdown("### Crear Nueva Categoría")
    nueva_cat = st.text_input(
        "Nombre de la categoría o subcategoría:",
        placeholder="Ej: Plantas de Exterior, Sustratos, Macetas",
        key="input_nueva_cat",
    )

    df_padres = pd.read_sql(
        "SELECT id, nombre FROM categorias WHERE categoria_padre_id IS NULL",
        conn,
    )
    opciones_padres = {"-- Ninguna (Principal) --": None}
    for _, row in df_padres.iterrows():
      opciones_padres[row["nombre"]] = row["id"]

    padre_elegido = st.selectbox(
        "Pertenece a (Opcional):", list(opciones_padres.keys())
    )
    padre_id = opciones_padres[padre_elegido]

    if "confirmar_nueva_cat" not in st.session_state:
      st.session_state.confirmar_nueva_cat = False

    if not st.session_state.confirmar_nueva_cat:
      if st.button("➕ Crear Categoría"):
        if not nueva_cat.strip():
          st.warning("Escribí un nombre para la categoría.")
        else:
          st.session_state.confirmar_nueva_cat = True
          st.rerun()
    else:
      st.warning(
          f"⚠️️ ¿Confirmás que deseás crear la categoría **{nueva_cat.strip()}**?"
      )
      col_e1, col_e2 = st.columns(2)
      with col_e1:
        if st.button(
            "✅ Sí, crear categoría", type="primary", use_container_width=True
        ):
          cursor = conn.cursor()
          cursor.execute(
              "SELECT COUNT(*) FROM categorias WHERE LOWER(nombre) = LOWER(?)",
              (nueva_cat.strip(),),
          )
          existe = cursor.fetchone()[0]

          if existe > 0:
            st.session_state.confirmar_nueva_cat = False
            st.error(
                f"⚠ La categoría '{nueva_cat.strip()}' ya existe en el sistema."
            )
          else:
            cursor.execute(
                "INSERT INTO categorias (nombre, categoria_padre_id) VALUES"
                " (?, ?)",
                (nueva_cat.strip(), padre_id),
            )
            conn.commit()
            st.session_state.confirmar_nueva_cat = False
            st.success(f"¡Categoría '{nueva_cat.strip()}' creada con éxito!")
            st.rerun()
      with col_e2:
        if st.button("❌ Cancelar", use_container_width=True):
          st.session_state.confirmar_nueva_cat = False
          st.rerun()

    st.markdown("---")
    st.markdown("### Eliminar Categoría")
    df_cat_del = pd.read_sql("SELECT id, nombre FROM categorias", conn)
    if df_cat_del.empty:
      st.info("No hay categorías para eliminar.")
    else:
      opciones_cat_del = {
          f"{row['nombre']} (ID: {row['id']})": row["id"]
          for _, row in df_cat_del.iterrows()
      }
      cat_a_borrar_str = st.selectbox(
          "Seleccioná la categoría a borrar:", list(opciones_cat_del.keys())
      )
      id_cat_borrar = opciones_cat_del[cat_a_borrar_str]

      if "confirmar_del_cat" not in st.session_state:
        st.session_state.confirmar_del_cat = False

      if not st.session_state.confirmar_del_cat:
        if st.button("❌ Eliminar Categoría", type="secondary"):
          st.session_state.confirmar_del_cat = True
          st.rerun()
      else:
        st.warning(
            f"⚠️ **ATENCIÓN:** ¿Estás seguro de eliminar la categoría"
            f" **{cat_a_borrar_str}**?"
        )
        col_f1, col_f2 = st.columns(2)
        with col_f1:
          if st.button(
              "🔴 Sí, eliminar categoría",
              type="primary",
              use_container_width=True,
          ):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categorias WHERE id = ?", (id_cat_borrar,))
            conn.commit()
            st.session_state.confirmar_del_cat = False
            st.success("¡Categoría eliminada con éxito!")
            st.rerun()
        with col_f2:
          if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.confirmar_del_cat = False
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Zona de Mantenimiento")

    if "confirmar_reinicio" not in st.session_state:
      st.session_state.confirmar_reinicio = False

    if not st.session_state.confirmar_reinicio:
      if st.button("🔄 Reinicio de Fábrica"):
        st.session_state.confirmar_reinicio = True
        st.rerun()
    else:
      st.error(
          "⚠️ **¡ADVERTENCIA DE REINICIO DE FÁBRICA!** ⚠️\n\nEstás a punto de"
          " borrar **absolutamente todo**: productos, historial de ventas y"
          " categorías. Esta acción no se puede deshacer."
      )

      col_a, col_b = st.columns(2)
      with col_a:
        if st.button(
            "🔴 SÍ, BORRAR TODO", type="primary", use_container_width=True
        ):
          cursor = conn.cursor()
          cursor.execute("DELETE FROM detalle_ventas")
          cursor.execute("DELETE FROM ventas")
          cursor.execute("DELETE FROM productos")
          cursor.execute("DELETE FROM categorias")
          conn.commit()
          st.session_state.confirmar_reinicio = False
          st.success("¡Sistema reiniciado de fábrica con éxito!")
          st.rerun()
      with col_b:
        if st.button("❌ Cancelar", use_container_width=True):
          st.session_state.confirmar_reinicio = False
          st.rerun()

  with col2:
    st.markdown("### Categorías Existentes")
    df_cat_show = pd.read_sql("SELECT id, nombre FROM categorias", conn)
    if not df_cat_show.empty:
      st.dataframe(df_cat_show, use_container_width=True)
    else:
      st.info("No hay categorías creadas todavía.")

conn.close()
