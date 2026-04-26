# Adipa — Extractor de Preguntas

Aplicación web para extraer y estructurar preguntas desde documentos de evaluación (PDF, DOCX, XLSX) usando Groq AI.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose
- Clave de API de Groq ([obtener aquí](https://console.groq.com/keys))

## Instalación y puesta en marcha

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd AdipaPrueba
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y completar los valores:

```env
GROQ_API_KEY=tu_clave_api_aqui
GROQ_MODEL=llama-3.3-70b-versatile
```

### 3. Levantar el proyecto

```bash
docker compose up --build
```

La primera vez descarga las imágenes base y construye los contenedores. Las ejecuciones siguientes son más rápidas:

```bash
docker compose up
```

Para correr en segundo plano:

```bash
docker compose up -d
```

### 4. Detener el proyecto

```bash
docker compose down
```

## Variables de entorno

| Variable | Requerida | Descripción | Valor por defecto |
|---|---|---|---|
| `GROQ_API_KEY` | Sí | Clave de API de Groq | — |
| `GROQ_MODEL` | No | Modelo de Groq a utilizar | `llama-3.3-70b-versatile` |

## URL de acceso

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost |
| API (Swagger UI) | http://localhost/docs |

## Formatos soportados

- **PDF** — Documentos PDF con texto seleccionable
- **DOCX** — Documentos Word
- **XLSX** — Hojas de cálculo Excel

## Uso

1. Abrir http://localhost en el navegador
2. Arrastrar un archivo o hacer clic para seleccionarlo
3. Esperar el procesamiento
4. Ver las preguntas extraídas y descargar el JSON si es necesario

## Despliegue en Render (gratis)

Render requiere tarjeta de crédito registrada en la cuenta para crear Web Services, pero **no cobra** dentro del tier gratuito:

- **Web Service (API):** 750 horas/mes gratis — suficiente para un servicio corriendo todo el mes
- **Static Site (frontend):** siempre gratis, sin límite

### Opción A — Blueprint automático (recomendado)

1. Agregar tarjeta en [dashboard.render.com/billing](https://dashboard.render.com/billing) (no genera cargos dentro del tier gratis).
2. Push del repo a GitHub.
3. En Render: **New** → **Blueprint** → conectar el repo.
4. Render detecta `render.yaml` y crea ambos servicios. El wizard pedirá `GROQ_API_KEY` y `CORS_ORIGINS`; ingresá `*` como placeholder para `CORS_ORIGINS` (lo corregís en el paso 6).
5. Una vez desplegados, anotar las URLs públicas:
   - API: ej. `https://adipa-api.onrender.com`
   - Frontend: ej. `https://adipa-frontend.onrender.com`
6. En **adipa-api** → **Environment**, actualizar `CORS_ORIGINS` con la URL real del frontend → **Save Changes** (redeploy automático).
7. Editar `frontend/static/env.js` y reemplazar `API_BASE_URL: ''` por:
   ```javascript
   API_BASE_URL: 'https://adipa-api.onrender.com'
   ```
8. Commit + push: el frontend se redeploya automáticamente.

### Opción B — Manual (sin blueprint)

1. **Web Service** (API): Root Directory `api`, Runtime Docker.
   - Env vars: `GROQ_API_KEY`, `GROQ_MODEL=llama-3.3-70b-versatile`, `CORS_ORIGINS=*`.
   - Health check path: `/api/health`.
2. Anotar la URL del API → editar `frontend/static/env.js` con esa URL → commit + push.
3. **Static Site** (frontend): Publish Directory `frontend/static`, Build Command vacío.
4. Actualizar `CORS_ORIGINS` del API con la URL real del frontend.

### Variables de entorno en Render

| Variable | Servicio | Valor |
|----------|----------|-------|
| `GROQ_API_KEY` | adipa-api | tu API key de Groq |
| `GROQ_MODEL` | adipa-api | `llama-3.3-70b-versatile` (pre-configurado) |
| `CORS_ORIGINS` | adipa-api | URL del frontend en Render |
| `PORT` | adipa-api | inyectada automáticamente por Render |

### Tier gratuito

- Los Web Services se duermen tras 15 minutos sin tráfico (~30-60 s de cold start en la primera petición).
- 750 horas/mes de ejecución por cuenta (una instancia corriendo 24/7 = ~744 h/mes).
- Static Sites no se duermen (CDN).
