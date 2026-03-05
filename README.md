Este proyecto contiene una api rest que permite realizar consultas sobre documentos utilizando un sistema de rag

La api permite:

- Ingestar documentos
- Indexarlos en una base vectorial
- Realizar consultas semánticas
- Devolver respuestas junto con las fuentes utilizadas

Tecnologías q utilice

- Python
- FastAPI
- LlamaIndex
- ChromaDB (base vectorial)


La api permite:

- Ingestar documentos
- Indexarlos en una base vectorial
- Realizar consultas semánticas
- Devolver respuestas junto con las fuentes utilizadas


Tecnologías q utilice

- Python
- FastAPI
- LlamaIndex
- ChromaDB 

Instalación.

Crear entorno virtual:
python -m venv venv

Activar entorno virtual:
venv\Scripts\activate

Instalar dependencias:
pip install -r requirements.txt

ejecutar api:
uvicorn app.main:app --reload

ver: 
http://127.0.0.1:8000

Verifica que el servicio esté funcionando:
GET /health

subir documentos para ser indexados:
POST /ingest

Ejemplo usando curl:

curl -X POST "http://127.0.0.1:8000/ingest" -F "files=@messi.txt"

Respuesta

{
 "ingested": 1,
 "skipped": 0,
 "errors": []
}


Pregunta sobre doc:
POST /query

request:

{
 "q": "¿Quién ganó el mundial 2022?",
 "top_k": 5
}

Respuesta: 

{
 "answer": "...",
 "sources": [
   {
     "filename": "messi.txt",
     "score": 0.82,
     "snippet": "..."
   }
 ],
 "retrieval_params": {
   "top_k": 5
 }
}
