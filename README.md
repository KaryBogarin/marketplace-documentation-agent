# Marketplace Documentation Agent

An AI agent that answers natural-language questions about a marketplace's internal documentation (policies, procedures, and internal data), built with Retrieval-Augmented Generation (RAG). Developed as the final project for Alura's "Challenge Alura Agente" (Oracle Next Education, Tech AI Builder track).

## Overview

Mercado Central 24h is a fictional 24-hour marketplace whose policies and procedures are spread across several PDF documents and one Excel spreadsheet. Employees and customers who need an answer usually have to search through long documents manually. This project solves that: a simple web interface where anyone can type a question in plain language and get an accurate answer grounded in the actual documentation, with the source file cited.

## Architecture

The system follows a classic RAG pipeline:

1. **Document ingestion**: PDFs are read with `pypdf`, and the Excel file is read with `pandas`. All content is split into overlapping text chunks (~1000 characters each).
2. **Embeddings**: each chunk is converted into a vector embedding using Google's Gemini Embedding API (`gemini-embedding-001`). Embeddings are cached locally in `embeddings_cache.json` so they only need to be generated once.
3. **Retrieval**: when a user asks a question, the question itself is embedded, then compared against all cached chunk embeddings using cosine similarity. The top 5 most relevant chunks are selected.
4. **Generation**: those chunks are passed as context to Claude (Anthropic API, Claude Haiku 4.5), which writes a natural-language answer in Spanish, citing which source documents it used.
5. **Interface**: a Flask web app exposes a chat-style UI with two collapsible FAQ panels (customer questions and employee questions) alongside a persistent chat window.

Flow:
User question
-> Gemini embedding (query)
-> cosine similarity search against cached document embeddings
-> top 5 relevant chunks
-> Claude Haiku 4.5 (answer generation, grounded in those chunks)
-> Flask API -> browser
## Tech stack

- **Language**: Python 3.12
- **Web framework**: Flask, served with Gunicorn in production
- **LLM (answer generation)**: Claude Haiku 4.5, via the Anthropic API
- **Embeddings (semantic search)**: Google Gemini (`gemini-embedding-001`), via the `google-genai` SDK
- **Document parsing**: `pypdf` (PDF), `pandas` + `openpyxl` (Excel)
- **Vector search**: `numpy` (cosine similarity; no vector database needed at this scale)
- **Frontend**: vanilla HTML, CSS and JavaScript, with `marked.js` (CDN) to render Markdown responses
- **Deployment**: Render

**Note on deployment**: the challenge suggests Oracle Cloud Infrastructure (OCI) as one deployment option. This project was deployed on Render instead, a platform with a free tier, since the challenge explicitly allows using whichever tools make the most sense for the person building the project.

## Project structure
marketplace-documentation-agent/
├── agente/
│ ├── lector_documentos.py # reads and chunks PDFs and Excel files
│ ├── embeddings.py # generates and caches embeddings, semantic search
│ └── agente_ia.py # combines retrieval + Claude to answer questions
├── documentos/ # source PDFs and Excel file
├── templates/
│ └── index.html # web interface
├── static/
├── app.py # Flask server
├── embeddings_cache.json # cached embeddings (generated once)
├── requirements.txt
├── runtime.txt
├── .env.example
└── README.md
## Running locally

1. Clone the repository
git clone https://github.com/KaryBogarin/marketplace-documentation-agent.git
cd marketplace-documentation-agent
2. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. Set up API keys

Copy `.env.example` to `.env` and add your own keys:
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here
- Get an Anthropic key at console.anthropic.com
- Get a Gemini key at aistudio.google.com/apikey

4. Add your documents

Place your PDF and/or Excel files inside the `documentos/` folder.

5. Generate embeddings (only needed once, or whenever documents change)
cd agente
python embeddings.py
cd ..
6. Run the app
python app.py
Open http://localhost:5000 in your browser.

## Example questions and answers

**Q: Cual es el horario de atencion al cliente?**

A: Mercado Central 24h ofrece atencion al cliente las 24 horas, los 7 dias de la semana, pero los horarios varian segun el canal: modulo presencial en tienda (24 hrs, 365 dias), linea gratuita 800-CENTRAL (lunes a domingo 07:00-23:00 hrs), WhatsApp Business (bot 24 hrs, agente humano 08:00-22:00), app (24 horas, autoservicio), correo electronico (recepcion 24 hrs), redes sociales (monitoreo entre 08:00 y 21:00 segun la plataforma).

Sources: b9abdeaf-ffcb-46c4-8e1b-16935a594875.pdf, c0a37625-c8ee-44f2-885f-7b30480d3017.pdf

**Q: Que debo hacer si un pedido llega danado?**

A: Reportar el problema dentro de las 2 horas siguientes a la recepcion (por la app o WhatsApp Business); se genera un folio de incidencia automaticamente; un agente contacta en un maximo de 30 minutos; se ofrece reposicion el mismo dia (si hay repartidor disponible) o un credito equivalente al valor del producto mas un 15% de bonificacion. Para productos perecederos, una foto por WhatsApp es suficiente como evidencia.

Sources: b9abdeaf-ffcb-46c4-8e1b-16935a594875.pdf, c0a37625-c8ee-44f2-885f-7b30480d3017.pdf

## Deployment

Live app: https://marketplace-documentation-agent.onrender.com/

The app is deployed on Render's free tier. Note: on the free plan, the service spins down after periods of inactivity, so the first request after idle time may take 30-60 seconds to respond while it wakes up.

![Agent running in production](screenshots/screenshots0101demo.png)

## Design notes

- Embeddings use Gemini instead of a paid alternative to stay within a free tier; batches are kept small and requests are spaced out to respect the free-tier rate limits.
- Claude Haiku 4.5 was chosen over larger models to keep the cost per question very low while keeping answer quality high for this use case.
- No vector database was used; with under 500 chunks, an in-memory cosine similarity search with `numpy` is fast enough and keeps the project simple to deploy.
