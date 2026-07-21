"""
Módulo principal del agente de IA.
Combina la búsqueda semántica (Gemini) con la generación de respuestas (Claude)
para responder preguntas sobre la documentación del marketplace.
"""

import os
import anthropic
from dotenv import load_dotenv

from embeddings import cargar_cache, buscar_fragmentos_relevantes

RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RUTA_PROYECTO, ".env"))

cliente_claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODELO_CLAUDE = "claude-haiku-4-5-20251001"

# Cargamos el cache de embeddings una sola vez, al iniciar la aplicación
_fragmentos_con_embeddings = None


def obtener_fragmentos():
    """Carga el cache de embeddings en memoria (solo la primera vez que se llama)."""
    global _fragmentos_con_embeddings
    if _fragmentos_con_embeddings is None:
        _fragmentos_con_embeddings = cargar_cache()
        if _fragmentos_con_embeddings is None:
            raise RuntimeError(
                "No se encontró embeddings_cache.json. "
                "Corre primero: python agente/embeddings.py"
            )
    return _fragmentos_con_embeddings


def construir_contexto(fragmentos_relevantes):
    """Arma un bloque de texto con los fragmentos encontrados, citando la fuente."""
    bloques = []
    for fragmento in fragmentos_relevantes:
        bloques.append(f"[Fuente: {fragmento['fuente']}]\n{fragmento['texto']}")
    return "\n\n---\n\n".join(bloques)


def responder_pregunta(pregunta, top_n=5):
    """
    Función principal: recibe una pregunta y devuelve la respuesta del agente,
    basada en el contenido de los documentos.
    """
    fragmentos = obtener_fragmentos()
    fragmentos_relevantes = buscar_fragmentos_relevantes(pregunta, fragmentos, top_n=top_n)
    contexto = construir_contexto(fragmentos_relevantes)

    mensaje_sistema = (
        "Eres un asistente que responde preguntas sobre la documentación interna "
        "de un marketplace 24 horas, basándote únicamente en los fragmentos de "
        "documentos que se te proporcionan a continuación. "
        "Responde de forma clara, breve y en español. "
        "Si la información no está en los fragmentos, dilo honestamente en vez "
        "de inventar una respuesta.\n\n"
        f"FRAGMENTOS DE LA DOCUMENTACIÓN:\n\n{contexto}"
    )

    respuesta = cliente_claude.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=1000,
        system=mensaje_sistema,
        messages=[{"role": "user", "content": pregunta}],
    )

    texto_respuesta = respuesta.content[0].text
    fuentes_usadas = sorted(set(f["fuente"] for f in fragmentos_relevantes))

    return {
        "respuesta": texto_respuesta,
        "fuentes": fuentes_usadas,
    }


if __name__ == "__main__":
    preguntas_de_prueba = [
        "¿Cuál es el horario de atención al cliente?",
        "¿Qué debo hacer si un pedido llega dañado?",
    ]

    for pregunta in preguntas_de_prueba:
        print(f"\n{'='*60}")
        print(f"❓ Pregunta: {pregunta}")
        resultado = responder_pregunta(pregunta)
        print(f"\n💬 Respuesta:\n{resultado['respuesta']}")
        print(f"\n📄 Fuentes: {', '.join(resultado['fuentes'])}")