"""
Módulo para leer y procesar documentos PDF y Excel.
Extrae el contenido y lo divide en fragmentos manejables para el agente de IA.
"""

from pypdf import PdfReader
import pandas as pd
import os


def leer_pdf(ruta_archivo):
    lector = PdfReader(ruta_archivo)
    texto_completo = ""

    for numero_pagina, pagina in enumerate(lector.pages, start=1):
        texto_pagina = pagina.extract_text()
        if texto_pagina:
            texto_completo += f"\n\n--- Página {numero_pagina} ---\n{texto_pagina}"

    return texto_completo


def leer_excel(ruta_archivo):
    hojas = pd.read_excel(ruta_archivo, sheet_name=None)
    texto_completo = ""

    for nombre_hoja, dataframe in hojas.items():
        texto_completo += f"\n\n--- Hoja: {nombre_hoja} ---\n"
        texto_completo += f"Columnas: {', '.join(dataframe.columns.astype(str))}\n\n"

        for indice_fila, fila in dataframe.iterrows():
            texto_fila = ", ".join(
                f"{columna}: {valor}" for columna, valor in fila.items()
            )
            texto_completo += f"Fila {indice_fila + 1} — {texto_fila}\n"

    return texto_completo


def dividir_en_fragmentos(texto, tamano_fragmento=1000, superposicion=200):
    fragmentos = []
    inicio = 0

    while inicio < len(texto):
        fin = inicio + tamano_fragmento
        fragmento = texto[inicio:fin]
        fragmentos.append(fragmento.strip())
        inicio += tamano_fragmento - superposicion

    return [f for f in fragmentos if f]


def procesar_carpeta_documentos(carpeta=None):
    if carpeta is None:
        raiz_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        carpeta = os.path.join(raiz_proyecto, "documentos")

    todos_los_fragmentos = []

    for nombre_archivo in os.listdir(carpeta):
        ruta_completa = os.path.join(carpeta, nombre_archivo)
        texto = None

        if nombre_archivo.lower().endswith(".pdf"):
            print(f"Leyendo PDF: {nombre_archivo}")
            texto = leer_pdf(ruta_completa)

        elif nombre_archivo.lower().endswith((".xlsx", ".xls")):
            print(f"Leyendo Excel: {nombre_archivo}")
            texto = leer_excel(ruta_completa)

        if texto:
            fragmentos = dividir_en_fragmentos(texto)
            for fragmento in fragmentos:
                todos_los_fragmentos.append({
                    "texto": fragmento,
                    "fuente": nombre_archivo
                })

    return todos_los_fragmentos


if __name__ == "__main__":
    fragmentos = procesar_carpeta_documentos()
    print(f"\n✅ Se generaron {len(fragmentos)} fragmentos en total.")
    if fragmentos:
        print("\nEjemplo del primer fragmento:")
        print(f"Fuente: {fragmentos[0]['fuente']}")
        print(f"Texto: {fragmentos[0]['texto'][:200]}...")