import os, json, logging, re
from typing import List, Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import threading, uvicorn

from fastmcp import FastMCP
from citeproc import CitationStylesStyle, CitationStylesBibliography, formatter, CitationItem  
from citeproc.source.json import CiteProcJSON
from citeproc import Citation, CitationItem  

# Configuracion
# ZTS_URL = os.getenv("ZTS_URL")
ZTS_URL = "https://zts-nezqm2fvdq-uc.a.run.app"
APA_STYLE_DEFAULT = "apa"
LOCALE_DEFAULT = "es-ES"
HTTP_TIMEOUT = 30.0

log = logging.getLogger("ztr")
logging.basicConfig(level=logging.INFO)

mcp = FastMCP("APA citations")

# Helpers ZTS 
async def _zts_require():
    if not ZTS_URL:
        raise HTTPException(status_code=500, detail="ZTS_URL no está configurado")

async def _zts_post_json(path: str, payload: Any, timeout: float = HTTP_TIMEOUT) -> httpx.Response:
    await _zts_require()
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(f"{ZTS_URL}{path}", json=payload,
                                 headers={"Content-Type": "application/json"})

async def _zts_post_text(path: str, text: str, timeout: float = HTTP_TIMEOUT) -> httpx.Response:
    await _zts_require()
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(f"{ZTS_URL}{path}", content=text,
                                 headers={"Content-Type": "text/plain"})

# Devuelve siempre una lista de dict (CSL-JSON items)
def _normalize_items(data: Any) -> List[Dict]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return items
        if isinstance(items, dict) and items:
            first_key = next(iter(items))
            return [items[first_key]]
    raise HTTPException(status_code=502, detail=f"ZTS /web no devolvió lista de items válida: {str(data)[:200]}")

async def _zts_web(url: str) -> List[Dict]:
    await _zts_require()

    async def _handle_300(resp_json: Dict) -> List[Dict]:
        items_dict = (resp_json or {}).get("items") or {}
        if not items_dict:
            raise HTTPException(status_code=502, detail=f"ZTS 300 sin 'items': {json.dumps(resp_json)[:300]}")
        first_key = next(iter(items_dict))
        for sel in (
            {"url": resp_json.get("url"), "session": resp_json.get("session"), "items": {first_key: items_dict[first_key]}},
            {"url": resp_json.get("url"), "session": resp_json.get("session"), "item": first_key},
        ):
            r2 = await _zts_post_json("/web", sel)
            if r2.is_success:
                return _normalize_items(r2.json())
        raise HTTPException(status_code=502, detail="ZTS selección 300 falló")

    # POST text
    try:
        r = await _zts_post_text("/web", url)
        if r.status_code == 300:
            return await _handle_300(r.json())
        r.raise_for_status()
        return _normalize_items(r.json())
    except Exception as e_first:
        log.warning("ZTS /web (text) falló: %s", e_first)

    # Fallback
    try:
        r = await _zts_post_json("/web", [url])
        if r.status_code == 300:
            return await _handle_300(r.json())
        r.raise_for_status()
        return _normalize_items(r.json())
    except Exception as e_second:
        log.error("Error ZTS /web: %s", e_second, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error ZTS /web: {e_second}")

# Normalización para CiteProc 
def _parse_date_to_dateparts(s: str) -> Optional[Dict]:
    try:
        parts = [int(p) for p in s.split("-") if p]
        if not parts:
            return None
        return {"date-parts": [parts]}
    except Exception:
        return None

# Normaliza a CSL-JSON válido: id, type, autores, fechas, y mapea campos Zotero->CSL
def _normalize_csl_items_for_citeproc(items: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for i, raw in enumerate(items):
        it = dict(raw or {})

        # map campos Zotero comunes a CSL
        if "itemType" in it and not it.get("type"):
            it["type"] = it.pop("itemType")
        if "url" in it and not it.get("URL"):
            it["URL"] = it["url"]  # CSL usa 'URL' en mayúsculas
        if "accessDate" in it and not it.get("accessed"):
            dp = _parse_date_to_dateparts(str(it["accessDate"]))
            if dp:
                it["accessed"] = dp
            it.pop("accessDate", None)

        # id
        it.setdefault("id", it.get("id") or it.get("DOI") or it.get("doi") or it.get("URL") or f"item-{i}")

        # type por defecto
        t = it.get("type")
        if not isinstance(t, str) or not t.strip():
            if it.get("container-title") or it.get("DOI") or it.get("doi"):
                it["type"] = "article-journal"
            else:
                it["type"] = "webpage"

        # autores a lista de objetos CSL
        if "author" in it:
            if isinstance(it["author"], list):
                it["author"] = [
                    a if isinstance(a, dict) else {"literal": str(a)}
                    for a in it["author"]
                ]
            elif isinstance(it["author"], str):
                it["author"] = [{"literal": it["author"]}]

        # fechas string a date-parts
        for key in ("issued", "accessed", "event-date", "original-date"):
            v = it.get(key)
            if isinstance(v, str):
                dp = _parse_date_to_dateparts(v)
                if dp:
                    it[key] = dp

        out.append(it)
    return out

# Genera la bibliografía APA con citeproc-py para todos los items
def _format_bibliography_citeproc(csl_items: List[Dict], style: str, locale: str) -> List[str]:
    """"""
    # Normaliza antes de pasar a CiteProc
    csl_items = _normalize_csl_items_for_citeproc(csl_items)

    style_obj = CitationStylesStyle(style, locale=locale)
    source = CiteProcJSON(csl_items)
    bib = CitationStylesBibliography(style_obj, source, formatter.plain)

    # Registrar cada ítem por su id usando Citation + CitationItem
    for it in csl_items:
        bib.register(Citation([CitationItem(it["id"])]))

    # devolver lineas de bibliografía
    return [str(b) for b in bib.bibliography()]


async def _zts_export(items: List[Dict], format_: str, style: Optional[str] = None) -> str | List[Dict]:
    await _zts_require()
    params = f"?format={format_}"
    if style:
        params += f"&style={style}"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(f"{ZTS_URL}/export{params}",
                              json=items, headers={"Content-Type": "application/json"})

    if not r.is_success:
        raise HTTPException(status_code=502, detail=f"ZTS /export {r.status_code}: {r.text[:300]}")

    if format_.lower() == "csljson":
        try:
            return r.json()
        except Exception:
            raise HTTPException(status_code=502, detail=f"ZTS /export devolvió CSL-JSON no válido: {r.text[:300]}")
    return r.text

# MCP tool 
@mcp.tool()
async def apa_from_url(url: str, style: str = APA_STYLE_DEFAULT, locale: str = LOCALE_DEFAULT) -> Dict[str, Any]:
    items = await _zts_web(url)
    if not items:
        return {"error": "No se pudieron extraer metadatos"}
    try:
        zts_citation = await _zts_export(items, "citation", style=style)
        if isinstance(zts_citation, str) and zts_citation.strip():
            return {"via": "zts-citation", "references": [zts_citation.strip()], "items": items, "style": style, "locale": locale}
    except Exception:
        pass

    #  CiteProc local 
    try:
        apa_refs = _format_bibliography_citeproc(items, style, locale)
        return {"via": "local-citeproc", "references": apa_refs, "items": items, "style": style, "locale": locale}
    except Exception as e:
        return {"error": f"No se pudo formatear con CiteProc: {e}", "items": items}

# FastAPI HTTP 
api = FastAPI(title="ZTR MCP ")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar el ASGI del MCP 
mcp_asgi = mcp.sse_app()
api.mount("/mcp", mcp_asgi)

#verificar el server
@api.get("/healthz")
async def healthz():
    ok = {"ok": True, "zts": bool(ZTS_URL)}
    if ZTS_URL:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(ZTS_URL + "/")
                ok["zts_status"] = r.status_code
        except Exception as e:
            ok["zts_error"] = str(e)
    return ok

# para probar local sin montar aun a un mcp
@api.get("/demo")
async def demo(url: str, request: Request):
    try:
        items = await _zts_web(url)
        try:
            zts_citation = await _zts_export(items, "citation", style="apa")
            if isinstance(zts_citation, str) and zts_citation.strip():
                return {"via": "zts-citation", "apa": zts_citation.strip(), "items": items}
        except Exception as e:
            log.warning("ZTS /export falló: %s", e)

        # Fallback CiteProc local
        apa_refs = _format_bibliography_citeproc(items, APA_STYLE_DEFAULT, LOCALE_DEFAULT)
        return {"via": "local-citeproc", "apa": apa_refs, "items": items}
    except HTTPException as he:
        return {"error": True, "status": he.status_code, "detail": he.detail}
    except Exception as e:
        log.error("demo error: %s", e, exc_info=True)
        return {"error": True, "status": 500, "detail": str(e)}


# Entrypoint Cloud Run y local
app = api

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))

    if os.environ.get("CLOUD_RUN") == "1":
        # Cloud Run
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif os.environ.get("RUN_MCP_STDIO") == "1":
        import threading
        t = threading.Thread(
            target=lambda: uvicorn.run(app, host="0.0.0.0", port=port),
            daemon=False,  
        )
        t.start()
        #local
        mcp.run()
    else:
        uvicorn.run(app, host="0.0.0.0", port=port)