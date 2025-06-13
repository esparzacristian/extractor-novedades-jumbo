import streamlit as st
import pandas as pd
import tempfile
import fitz  # PyMuPDF
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Extractor Jumbo", layout="centered")

st.title("📄 Extractor de información - Novedades J633")
st.write("Sube el archivo PDF de Novedades para analizar su información y para generar un Excel con los datos procesados.")

# Subir archivo PDF
uploaded_file = st.file_uploader("📤 Sube o arrastra aquí el archivo PDF", type=["pdf"])

if uploaded_file:
    st.success("✅ PDF subido correctamente.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = tmp.name

    doc = fitz.open(pdf_path)
    productos = []

    for page in doc:
        text = page.get_text()
        lines = text.split('\n')

        for i in range(len(lines) - 6):
            bloque = lines[i:i+7]
            if (
                bloque[1].strip().isdigit() and 11 <= len(bloque[1].strip()) <= 13 and
                bloque[2].strip().replace('.', '').isdigit() and
                bloque[3].strip().replace('.', '').isdigit() and
                len(bloque[4].strip()) == 11 and
                bloque[5].strip().isdigit() and
                bloque[6].strip() in ['Si', 'No']
            ):
                descripcion = bloque[0].strip()
                cod_barras = bloque[1].strip()
                precio_oferta = bloque[2].strip()
                precio_original = bloque[3].strip()
                cod_material = bloque[4].strip()
                cantidad = bloque[5].strip()
                imprimir = bloque[6].strip()

                productos.append({
                    "Código Material": cod_material,
                    "Código Barras": cod_barras,
                    "Descripción": descripcion,
                    "Precio Oferta": precio_oferta,
                    "Precio Original": precio_original,
                    "Cantidad": cantidad,
                    "¿Imprimir?": imprimir
                })

    # 🚨 Mostrar mensaje si no se detectan productos
    if not productos:
        st.error("❌ No se detectaron productos válidos en este PDF. Verifica que el documento tenga el formato estructurado de lista de novedades.")
    else:
        # Crear DataFrame completo
        df_original = pd.DataFrame(productos)

        # Seleccionar columnas necesarias
        df = df_original[["Código Barras", "Descripción", "Precio Oferta", "Precio Original"]].copy()

        # Convertir precios a float
        df["Precio Oferta"] = df["Precio Oferta"].str.replace(".", "", regex=False).astype(float)
        df["Precio Original"] = df["Precio Original"].str.replace(".", "", regex=False).astype(float)

        # Filtrar solo productos con rebaja real
        df_filtrado = df[(df["Precio Original"] > df["Precio Oferta"]) & (df["Precio Original"] > 0)]

        # Mostrar resumen
        total = len(df)
        ofertas = len(df_filtrado)
        st.write(f"📊 Se encontraron **{ofertas} productos en oferta** de un total de **{total} productos leídos** del PDF.")

        if not df_filtrado.empty:
            # Mostrar tabla
            st.dataframe(df_filtrado)

            # Exportar a Excel
            @st.cache_data
            def convert_df_to_excel(dataframe):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    dataframe.to_excel(writer, index=False, sheet_name="Productos")
                return output.getvalue()

            now = datetime.now().strftime("%Y-%m-%d_%H-%M")
            excel_filename = f"productos_oferta_{now}.xlsx"
            excel_data = convert_df_to_excel(df_filtrado)

            st.download_button(
                label="📥 Descargar Excel",
                data=excel_data,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 👉 Generar texto para copiar con salto cada 4 filas y precios como enteros
            lineas = []
            filas = df_filtrado.values.tolist()

            for i, fila in enumerate(filas, start=1):
                cod_barras = fila[0]
                descripcion = fila[1]
                precio_oferta = int(fila[2])
                precio_original = int(fila[3])

                linea = f"{cod_barras}\t{descripcion}\t{precio_oferta}\t{precio_original}"
                lineas.append(linea)

                if i % 4 == 0:
                    lineas.append("")  # línea vacía cada 4 productos

            texto_para_copiar = '\n'.join(lineas)

            # Mostrar caja de texto para copiar con botón
            st.markdown("### 📋 Copiar los productos filtrados (sin encabezado, separados cada 4 filas)")
            st.markdown(
                f"""
                <textarea id="copiarTexto" rows="15" style="width:100%; border-radius: 5px;">{texto_para_copiar}</textarea>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ No se detectaron productos en oferta. Puede que todos tengan precio igual o mayor al original.")

    # Firma personal
    st.markdown("""---""")
    st.markdown(
        """
        <div style="text-align: center; font-size: 13px; color: gray;">
            Este modelo solo analiza texto mediante el lenguaje de Python. En ningún caso registra ni almacena información en la nube.<br>
            Generado y proporcionado a la organización para fines educativos practicos por <strong>Cristian Esparza Torrealba</strong>,<br>
            Estudiante de Ingeniería en Información y Control de Gestión, Universidad Católica de la Santísima Concepción.<br>
            Contacto: <a href="mailto:cesparza@iicg.ucsc.cl">cesparza@iicg.ucsc.cl</a>
        </div>
        """,
        unsafe_allow_html=True
    )


