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

  cursor.execute("SELECT COUNT(*) FROM categorias")
  if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO categorias (nombre, categoria_padre_id) VALUES (?, ?)",
        [
            ("Plantas", None),
            ("Macetas e Insumos", None),
            ("Interior", 1),
            ("Exterior", 1),
            ("Suculentas", 1),
            ("Plástico", 2),
            ("Sustratos", 2),
        ],
    )
    conn.commit()

  cursor.execute("SELECT COUNT(*) FROM productos")
  if cursor.fetchone()[0] == 0:
    productos_iniciales = [
        (3, "PLT-INT-001", "Monstera Deliciosa (N15)", 8500.0, 10),
        (3, "PLT-INT-002", "Ficus Lyrata (N20)", 13000.0, 6),
        (5, "SUC-001", "Echeveria (Maceta 10)", 2500.0, 25),
        (7, "INS-SUS-001", "Sustrato Premium 5dm3", 4200.0, 15),
    ]
    cursor.executemany(
        """INSERT INTO productos (categoria_id, sku, nombre, precio_venta,
        stock_actual) 
               VALUES (?, ?, ?, ?, ?)""",
        productos_iniciales,
    )
    conn.commit()

  conn.close()


inicializar_bd()

# --- 2. TÍTULO PRINCIPAL ---
st.title("🌿 El Botánico - Sistema de Gestión")
st.markdown("---")

# --- 3. PESTAÑAS HORIZONTALES DIRECTAS ---
tab_dash, tab_pos, tab_stock, tab_nuevo, tab_cat = st.tabs([
    "📊 Dashboard",
    "🛒 Registrar Venta (POS)",
    "📦 Control de Stock",
    "➕ Nuevo Producto",
    "🗂️ Gestión de Categorías",
])

conn = sqlite3.connect(DB_NAME)

# ==================== 1. DASHBOARD ====================
with tab_dash:
  st.subheader("Panel de Indicadores Generales")

  df_ventas = pd.read_sql("SELECT * FROM ventas", conn)
  df_productos = pd.read_sql(
      """
        SELECT p.sku, p.nombre, p.precio_venta, p.stock_actual, c.nombre as categoria 
        FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id
    """,
      conn,
  )

  total_recaudado = df_ventas["total"].sum() if not df_ventas.empty else 0.0
  cant_ventas = len(df_ventas)

  # Cálculo seguro de valor de inventario forzando tipos numéricos
  if not df_productos.empty:
    df_productos["precio_venta"] = pd.to_numeric(
        df_productos["precio_venta"], errors="coerce"
    ).fillna(0)
    df_productos["stock_actual"] = pd.to_numeric(
        df_productos["stock_actual"], errors="coerce"
    ).fillna(0)
    valor_stock = (
        df_productos["precio_venta"] * df_productos["stock_actual"]
    ).sum()
    stock_bajo = len(df_productos[df_productos["stock_actual"] < 5])
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
    st.warning("No hay productos disponibles para la venta.")
  else:
    opciones_prod = {
        f"{row['nombre']} (Stock: {row['stock_actual']} - ${row['precio_venta']})": row[
            "id"
        ]
        for _, row in df_productos.iterrows()
    }

    prod_seleccionado_str = st.selectbox(
        "Seleccionar Producto:", list(opciones_prod.keys())
    )
    prod_id = opciones_prod[prod_seleccionado_str]

    prod_info = df_productos[df_productos["id"] == prod_id].iloc[0]
    stock_disponible = int(prod_info["stock_actual"])
    precio_unitario = float(prod_info["precio_venta"])

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

# ==================== 3. CONTROL DE STOCK ====================
with tab_stock:
  st.subheader("Auditoría de Inventario")
  df_stock = pd.read_sql(
      """
        SELECT p.sku as SKU, p.nombre as Producto, c.nombre as Categoría, 
               p.precio_venta as 'Precio ($)', p.stock_actual as 'Stock Disponible'
        FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id
    """,
      conn,
  )
  st.dataframe(df_stock, use_container_width=True)

# ==================== 4. NUEVO PRODUCTO ====================
with tab_nuevo:
  st.subheader("Agregar Planta o Insumo")

  df_cat = pd.read_sql("SELECT id, nombre FROM categorias", conn)
  opciones_cat = {row["nombre"]: row["id"] for _, row in df_cat.iterrows()}

  cat_elegida = st.selectbox("Categoría:", list(opciones_cat.keys()))
  cat_id = opciones_cat[cat_elegida]

  sku = st.text_input("Código SKU (Ej: PLT-INT-05):")
  nombre_prod = st.text_input("Nombre de la Planta o Producto:")
  precio = st.number_input("Precio de Venta ($):", min_value=0.0, step=100.0)
  stock = st.number_input("Stock Inicial:", min_value=0, step=1)

  if st.button("💾 Guardar Producto", type="primary"):
    if not sku or not nombre_prod:
      st.error("Por favor completa el código SKU y el nombre.")
    else:
      try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO productos (categoria_id, sku, nombre, precio_venta,
            stock_actual) 
                   VALUES (?, ?, ?, ?, ?)""",
            (cat_id, sku, nombre_prod, precio, stock),
        )
        conn.commit()
        st.success("¡Producto guardado correctamente!")
        st.rerun()
      except sqlite3.IntegrityError:
        st.error(f"El código SKU '{sku}' ya existe. Ingresá otro.")

# ==================== 5. GESTIÓN DE CATEGORÍAS ====================
with tab_cat:
  st.subheader("Administrar Categorías y Subcategorías")

  col1, col2 = st.columns(2)

  with col1:
    st.markdown("### Crear Nueva Categoría")
    nueva_cat = st.text_input("Nombre de la categoría:")
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

    if st.button("➕ Crear Categoría"):
      if nueva_cat:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categorias (nombre, categoria_padre_id) VALUES (?, ?)",
            (nueva_cat, padre_id),
        )
        conn.commit()
        st.success("Categoría creada con éxito.")
        st.rerun()
      else:
        st.warning("Escribí un nombre.")

  with col2:
    st.markdown("### Categorías Existentes")
    df_cat_show = pd.read_sql("SELECT id, nombre FROM categorias", conn)
    st.dataframe(df_cat_show, use_container_width=True)

conn.close()
