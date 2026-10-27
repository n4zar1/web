# Lee de la API de Gumroad el precio de cada producto (con el descuento automático aplicado, si hay uno)
# y lo guarda en precios.json para que las webs fuera de Gumroad (n4zar1.com, datoaldia.es) lo enseñen.
# Necesita el secreto GUMROAD_TOKEN en el repositorio. Los precios van sin IVA, como en Gumroad.
import json, os, urllib.request
from datetime import datetime, timezone

API = "https://api.gumroad.com/v2"
TOKEN = os.environ["GUMROAD_TOKEN"]
# La API no dice qué código es el descuento por defecto de una ficha («aplicar automáticamente»): sus nombres van en
# la variable CODIGOS_AUTO del repositorio (GitHub > Settings > Variables), separados por comas. Ej.: RETO
AUTO = {c.strip().upper() for c in os.environ.get("CODIGOS_AUTO", "").split(",") if c.strip()}

def get(ruta):
    with urllib.request.urlopen(f"{API}/{ruta}?access_token={TOKEN}", timeout=30) as r:
        return json.load(r)

def vigente(o, ahora):
    ini, fin = o.get("valid_at"), o.get("expires_at")
    if ini and datetime.fromisoformat(ini.replace("Z", "+00:00")) > ahora: return False
    if fin and datetime.fromisoformat(fin.replace("Z", "+00:00")) < ahora: return False
    return True

ahora = datetime.now(timezone.utc)
precios = {}
for p in get("products")["products"]:
    if not p.get("published"): continue
    clave = p.get("custom_permalink") or p.get("short_url", "").rsplit("/", 1)[-1]
    normal = p["price"] / 100
    if not normal:  # suscripciones: el precio está en la primera opción, por periodo (yearly, monthly…)
        for v in p.get("variants") or []:
            for op in v.get("options") or []:
                for per in (op.get("recurrence_prices") or {}).values():
                    normal = normal or per.get("price_cents", 0) / 100
    hoy = normal
    for o in get(f"products/{p['id']}/offer_codes").get("offer_codes", []):
        if not (o.get("auto_apply") or o.get("name", "").upper() in AUTO) or not vigente(o, ahora): continue
        if o.get("percent_off"): hoy = min(hoy, normal * (1 - o["percent_off"] / 100))
        elif o.get("amount_cents"): hoy = min(hoy, max(0, normal - o["amount_cents"] / 100))
    precios[clave] = {"nombre": p["name"], "precio": round(hoy, 2), "normal": round(normal, 2) if hoy < normal else None,
                      "moneda": (p.get("currency") or "eur").lower()}
with open("precios.json", "w", encoding="utf-8") as f:
    json.dump(precios, f, ensure_ascii=False, indent=1)
print(json.dumps(precios, ensure_ascii=False))
