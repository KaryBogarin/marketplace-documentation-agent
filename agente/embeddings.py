"""
Módulo para generar embeddings de los fragmentos de texto usando Google Gemini,
y para buscar los fragmentos más relevantes dada una pregunta (búsqueda semántica).
"""

import os
import json
import time
import re
import numpy as np
from google import genai
from google.genai.types import EmbedContentConfig
from dotenv import load_dotenv

RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RUTA_PROYECTO, ".env"))

cliente_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

RUTA_CACHE = os.path.join(RUTA_PROYECTO, "embeddings_cache.json")
MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSIONES = 768

TAMANO_LOTE = 10  # lotes más chicos para ir seguro con el límite gratuito
ESPERA_ENTRE_LOTES_SEGUNDOS = 10
ESPERA_POR_LIMITE_SEGUNDOS = 65  # un poco más que los 42-58s que sugiere Google


def generar_embeddings(fragmentos):
    textos = [fragmento["texto"] for fragmento in fragmentos]
    todos_los_embeddings = []
    total_lotes = (len(textos) + TAMANO_LOTE - 1) // TAMANO_LOTE

    for numero_lote, inicio in enumerate(range(0, len(textos), TAMANO_LOTE), start=1):
        lote = textos[inicio:inicio + TAMANO_LOTE]
        print(f"Generando embeddings — lote {numero_lote}/{total_lotes} "
              f"({inicio + 1}-{inicio + len(lote)} de {len(textos)})...")

        intentos = 0
        while True:
            try:
                respuesta = cliente_gemini.models.embed_content(
                    model=MODELO_EMBEDDING,
                    contents=lote,
                    config=EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=DIMENSIONES,
                    ),
                )
                todos_los_embeddings.extend([e.values for e in respuesta.embeddings])
                break
            except Exception as error:
                intentos += 1
                if intentos > 8:
                    raise

                mensaje_error = str(error)
                if "RESOURCE_EXHAUSTED" in mensaje_error or "429" in mensaje_error:
                    print(f"  ⏳ Límite de cuota gratuita alcanzado, esperando "
                          f"{ESPERA_POR_LIMITE_SEGUNDOS}s (intento {intentos}/8)...")
                    time.sleep(ESPERA_POR_LIMITE_SEGUNDOS)
                else:
                    print(f"  ⏳ Error temporal, esperando 10s antes de reintentar "
                          f"(intento {intentos}/8): {error}")
                    time.sleep(10)

        if numero_lote < total_lotes:
            time.sleep(ESPERA_ENTRE_LOTES_SEGUNDOS)

    for fragmento, embedding in zip(fragmentos, todos_los_embeddings):
        fragmento["embedding"] = embedding

    return fragmentos


def guardar_cache(fragmentos_con_embeddings, ruta=RUTA_CACHE):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(fragmentos_con_embeddings, archivo)
    print(f"✅ Cache guardado en {ruta}")


def cargar_cache(ruta=RUTA_CACHE):
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def buscar_fragmentos_relevantes(pregunta, fragmentos_con_embeddings, top_n=5):
    respuesta = cliente_gemini.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=[pregunta],
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=DIMENSIONES,
        ),
    )
    embedding_pregunta = np.array(respuesta.embeddings[0].values)

    similitudes = []
    for fragmento in fragmentos_con_embeddings:
        embedding_fragmento = np.array(fragmento["embedding"])
        similitud_coseno = np.dot(embedding_pregunta, embedding_fragmento) / (
            np.linalg.norm(embedding_pregunta) * np.linalg.norm(embedding_fragmento)
        )
        similitudes.append(similitud_coseno)

    indices_ordenados = np.argsort(similitudes)[::-1][:top_n]
    return [fragmentos_con_embeddings[i] for i in indices_ordenados]


if __name__ == "__main__":
    from lector_documentos import procesar_carpeta_documentos

    cache_existente = cargar_cache()

    if cache_existente:
        print(f"Usando cache existente ({len(cache_existente)} fragmentos)")
        fragmentos = cache_existente
    else:
        print("Generando embeddings desde cero (puede tardar varios minutos, es normal)...")
        fragmentos = procesar_carpeta_documentos()
        fragmentos = generar_embeddings(fragmentos)
        guardar_cache(fragmentos)

    pregunta_prueba = "¿Cuál es el horario de atención?"
    resultados = buscar_fragmentos_relevantes(pregunta_prueba, fragmentos, top_n=3)

    print(f"\n🔍 Pregunta de prueba: {pregunta_prueba}")
    print(f"\nLos {len(resultados)} fragmentos más relevantes:")
    for i, r in enumerate(resultados, 1):
        print(f"\n{i}. Fuente: {r['fuente']}")
        print(f"   Texto: {r['texto'][:150]}...")