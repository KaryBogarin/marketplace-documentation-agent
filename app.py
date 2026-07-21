"""
Servidor web Flask para el agente de IA.
Expone una interfaz simple donde cualquiera puede hacer preguntas
sobre la documentación del marketplace.
"""

import os
import sys

RUTA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
RUTA_AGENTE = os.path.join(RUTA_PROYECTO, "agente")
sys.path.insert(0, RUTA_AGENTE)  # para poder importar agente_ia.py

from flask import Flask, render_template, request, jsonify
from agente_ia import responder_pregunta

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/preguntar", methods=["POST"])
def preguntar():
    datos = request.get_json()
    pregunta = (datos or {}).get("pregunta", "").strip()

    if not pregunta:
        return jsonify({"error": "Por favor escribe una pregunta."}), 400

    try:
        resultado = responder_pregunta(pregunta)
        return jsonify(resultado)
    except Exception as error:
        return jsonify({"error": f"Ocurrió un error: {str(error)}"}), 500


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=True)
    