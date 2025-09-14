# RemoteServerMCP

## Requirements: 
- Google Cloud SDK (`gcloud`)
- Docker (only needed if you build manually)

## 1. Deploy ZTS
To create the remote connection server, go to file zts-docker 

```
cd "C:\Users\angel\OneDrive\Documentos\.universidad\.2025\s2\redes\RemoteServerMCP\zts-cloudrun"
```

And run the following commands:
```
gcloud config set project manifest-surfer-471622-n4
```

```
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

```
gcloud run deploy zts --source=. --region=us-central1 --platform=managed --port=1969 --allow-unauthenticated --memory=1Gi --timeout=300
```

And this will show the service URL: https://zts-990598886898.us-central1.run.app

https://zts-nezqm2fvdq-uc.a.run.app

## 2. Deploy server
Then, back to project root

```
cd.. 
```

ask cloud run witch is the URL of zts

```
$ZTS_URL = (gcloud run services describe zts --region us-central1 --format "value(status.url)")
```

see the URL
```
$ZTS_URL
```

This will return your MCP server URL, for example:
```
$ZTS_URL =  https://zts-nezqm2fvdq-uc.a.run.app
```

Deploy server:
```
gcloud run deploy ztrmcp `
   --source=. `
   --region=us-central1 `
   --platform=managed `
   --allow-unauthenticated `
   --set-env-vars "ZTS_URL=$ZTS_URL,CLOUD_RUN=1" `
   --memory=512Mi `
   --timeout=300 `
```



with the gcloud server will show you something like this:
```
https://ztrmcp-990598886898.us-central1.run.app
```

## 3. Verify deployment
```
Invoke-RestMethod -Uri "$MCP_URL/openapi.json" -Method GET 
```

```
Invoke-WebRequest -Uri "$MCP_URL/docs" -Method GET
```


## local server
try server on browser with local server:
```
http://127.0.0.1:8080/healthz
```

Try to create a reference:
```
http://127.0.0.1:8080/demo?url=https://academia-lab.com/enciclopedia/modelo-basado-en-agentes/
```

