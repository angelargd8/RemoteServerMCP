# RemoteServerMCP

- Requisitos: 
tener instalado gcloud y docker




cd "C:\Users\angel\OneDrive\Documentos\.universidad\.2025\s2\redes\RemoteServerMCP\zts-cloudrun"


gcloud config set project manifest-surfer-471622-n4
gcloud services enable run.googleapis.com cloudbuild.googleapis.com


gcloud run deploy zts --source=. --region=us-central1 --platform=managed --port=1969 --allow-unauthenticated --memory=1Gi --timeout=300

Service URL: https://zts-990598886898.us-central1.run.app

https://zts-990598886898.us-central1.run.app
https://zts-nezqm2fvdq-uc.a.run.app

cd.. 

$ZTS_URL =  https://zts-nezqm2fvdq-uc.a.run.app

$ZTS_URL = (gcloud run services describe zts --region us-central1 --format "value(status.url)")
$ZTS_URL

gcloud run deploy ztrmcp `
   --source=. `
   --region=us-central1 `
   --platform=managed `
   --allow-unauthenticated `
   --set-env-vars "ZTS_URL=$ZTS_URL,CLOUD_RUN=1" `
   --memory=512Mi `
   --timeout=300 `

http://127.0.0.1:8080/healthz

Service [ztrmcp] revision [ztrmcp-00008-crx] has been deployed and is serving 100 percent of traffic.
Service URL: https://ztrmcp-990598886898.us-central1.run.app

https://ztrmcp-990598886898.us-central1.run.app

Invoke-WebRequest -Uri "https://ztrmcp-990598886898.us-central1.run.app" -Method GET

iwr "$ZTR_URL/demo?url=https://academia-lab.com/enciclopedia/modelo-basado-en-agentes/" -Method Get



Invoke-RestMethod -Uri "$MCP_URL/openapi.json" -Method GET 


Invoke-WebRequest -Uri "$MCP_URL/docs" -Method GET


http://127.0.0.1:8080/demo?url=https://academia-lab.com/enciclopedia/modelo-basado-en-agentes/


gcloud run deploy ztrmcp `
   --source=. `
   --region=us-central1 `
   --platform=managed `
   --allow-unauthenticated `
   --set-env-vars "ZTS_URL=$ZTS_URL,CLOUD_RUN=1" `
   --memory=512Mi `
   --timeout=300 `

https://ztrmcp-990598886898.us-central1.run.app


iwr -Headers @{Accept="text/event-stream"} -Uri "https://ztrmcp-990598886898.us-central1.run.app/mcp/sse?version=1.0" -Method GET


Invoke-WebRequest -Uri "https://ztrmcp-990598886898.us-central1.run.app/mcp/sse?version=1.0" -Method Head
