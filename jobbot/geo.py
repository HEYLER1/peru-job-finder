"""Geolocalización y cálculo de cercanía sin depender de APIs con clave."""

from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path

from .modelo import normalizar

CACHE = Path(__file__).resolve().parent.parent / "data" / "cache" / "geo.json"

# localized -> (lat, lon, country code)
CIUDADES: dict[str, tuple[float, float, str]] = {}


def _cargar(nombre: str, lat: float, lon: float, pais: str) -> None:
    CIUDADES.setdefault(normalizar(nombre), (lat, lon, pais))


_TABLAS: dict[str, tuple[tuple[str, float, float, str], ...]] = {
    "ES": (
        ("madrid", 40.4168, -3.7038, "ES"), ("barcelona", 41.3874, 2.1686, "ES"),
        ("valencia", 39.4699, -0.3763, "ES"), ("sevilla", 37.3891, -5.9845, "ES"),
        ("zaragoza", 41.6488, -0.8891, "ES"), ("malaga", 36.7213, -4.4214, "ES"),
        ("murcia", 37.9922, -1.1307, "ES"), ("palma", 39.5696, 2.6502, "ES"),
        ("bilbao", 43.2630, -2.9350, "ES"), ("alicante", 38.3452, -0.4810, "ES"),
        ("cordoba", 37.8882, -4.7794, "ES"), ("valladolid", 41.6523, -4.7245, "ES"),
        ("vigo", 42.2406, -8.7207, "ES"), ("granada", 37.1773, -3.5986, "ES"),
        ("elche", 38.2699, -0.7126, "ES"), ("oviedo", 43.3619, -5.8494, "ES"),
        ("tenerife", 28.4636, -16.2516, "ES"), ("las palmas", 28.1235, -15.4363, "ES"),
        ("gran canaria", 28.1235, -15.4363, "ES"), ("a coruna", 43.3623, -8.4115, "ES"),
        ("burgos", 42.3439, -3.6969, "ES"), ("castellon", 39.9864, -0.0513, "ES"),
        ("sabadell", 41.5433, 2.1094, "ES"), ("pamplona", 42.8125, -1.6458, "ES"),
        ("albacete", 38.9943, -1.8585, "ES"), ("jaen", 37.7796, -3.7849, "ES"),
        ("ourense", 42.3358, -7.8639, "ES"), ("gijon", 43.5322, -5.6611, "ES"),
        ("leganes", 40.3272, -3.7635, "ES"), ("getafe", 40.3082, -3.7325, "ES"),
        ("mostoles", 40.3223, -3.8649, "ES"), ("alcorcon", 40.3439, -3.7810, "ES"),
        ("donostia", 43.3183, -1.9812, "ES"), ("san sebastian", 43.3183, -1.9812, "ES"),
        ("santander", 43.4623, -3.8100, "ES"), ("toledo", 39.8628, -4.0273, "ES"),
        ("lerida", 41.6176, 0.6200, "ES"), ("tarragona", 41.1189, 1.2445, "ES"),
        ("leon", 42.5987, -5.5671, "ES"), ("cadiz", 36.5271, -6.2886, "ES"),
        ("logrono", 42.4627, -2.4450, "ES"), ("huelva", 37.2614, -6.9447, "ES"),
        ("lugo", 43.0120, -7.5560, "ES"), ("salamanca", 40.9701, -5.6635, "ES"),
        ("merida", 38.9166, -6.3437, "ES"), ("melilla", 35.2923, -2.9381, "ES"),
        ("ceuta", 35.8894, -5.3213, "ES"), ("spain", 40.4168, -3.7038, "ES"),
        ("espana", 40.4168, -3.7038, "ES"),
    ),
    "MX": (
        ("ciudad de mexico", 19.4326, -99.1332, "MX"), ("cdmx", 19.4326, -99.1332, "MX"),
        ("guadalajara", 20.6597, -103.3496, "MX"), ("monterrey", 25.6866, -100.3161, "MX"),
        ("puebla", 19.0414, -98.2063, "MX"), ("tijuana", 32.5149, -117.0382, "MX"),
        ("merida", 20.9674, -89.5926, "MX"), ("queretaro", 20.5888, -100.3899, "MX"),
        ("cancun", 21.1619, -86.8515, "MX"), ("aguascalientes", 21.8853, -102.2916, "MX"),
        ("hermosillo", 29.0729, -110.9559, "MX"), ("saltillo", 25.4232, -101.0053, "MX"),
        ("durango", 24.0277, -104.6532, "MX"), ("san luis potosi", 22.1565, -100.9855, "MX"),
        ("toluca", 19.2826, -99.6557, "MX"), ("oaxaca", 17.0732, -96.7266, "MX"),
        ("mexico", 19.4326, -99.1332, "MX"),
    ),
    "IT": (
        ("roma", 41.9028, 12.4964, "IT"), ("milano", 45.4642, 9.1900, "IT"),
        ("napoli", 40.8518, 14.2681, "IT"), ("torino", 45.0703, 7.6869, "IT"),
        ("palermo", 38.1157, 13.3615, "IT"), ("genova", 44.4056, 8.9463, "IT"),
        ("bologna", 44.4949, 11.3426, "IT"), ("firenze", 43.7696, 11.2558, "IT"),
        ("bari", 41.1171, 16.8719, "IT"), ("catania", 37.5079, 15.0830, "IT"),
        ("venezia", 45.4408, 12.3155, "IT"), ("verona", 45.4384, 10.9916, "IT"),
        ("padua", 45.4064, 11.8768, "IT"), ("trieste", 45.6495, 13.7768, "IT"),
        ("brescia", 45.5416, 10.2192, "IT"), ("parma", 44.8015, 10.3279, "IT"),
        ("bergamo", 45.6983, 9.6773, "IT"), ("sassari", 40.7273, 8.5602, "IT"),
        ("latina", 41.4671, 12.9038, "IT"), ("monza", 45.5845, 9.2744, "IT"),
        ("italy", 41.9028, 12.4964, "IT"), ("italia", 41.9028, 12.4964, "IT"),
    ),
    "GB": (
        ("london", 51.5074, -0.1278, "GB"), ("manchester", 53.4808, -2.2426, "GB"),
        ("birmingham", 52.4862, -1.8904, "GB"), ("glasgow", 55.8642, -4.2518, "GB"),
        ("edinburgh", 55.9533, -3.1883, "GB"), ("liverpool", 53.4084, -2.9916, "GB"),
        ("leeds", 53.8008, -1.5491, "GB"), ("bristol", 51.4545, -2.5879, "GB"),
        ("cardiff", 51.4816, -3.1791, "GB"), ("belfast", 54.5973, -5.9301, "GB"),
        ("sheffield", 53.3811, -1.4701, "GB"), ("brighton", 50.8225, -0.1372, "GB"),
        ("cambridge", 52.2053, 0.1218, "GB"), ("oxford", 51.7520, -1.2577, "GB"),
        ("nottingham", 52.9548, -1.1581, "GB"), ("leicester", 52.6369, -1.1398, "GB"),
        ("coventry", 52.4068, -1.5197, "GB"), ("newcastle", 54.9783, -1.6178, "GB"),
        ("united kingdom", 51.5074, -0.1278, "GB"), ("england", 51.5074, -0.1278, "GB"),
    ),
    "DE": (
        ("berlin", 52.5200, 13.4050, "DE"), ("munich", 48.1351, 11.5820, "DE"),
        ("hamburg", 53.5511, 9.9937, "DE"), ("cologne", 50.9375, 6.9603, "DE"),
        ("frankfurt", 50.1109, 8.6821, "DE"), ("stuttgart", 48.7758, 9.1829, "DE"),
        ("dusseldorf", 51.2277, 6.7735, "DE"), ("dortmund", 51.5136, 7.4653, "DE"),
        ("germany", 51.1657, 10.4515, "DE"), ("alemania", 51.1657, 10.4515, "DE"),
    ),
    "FR": (
        ("paris", 48.8566, 2.3522, "FR"), ("lyon", 45.7640, 4.8357, "FR"),
        ("marseille", 43.2965, 5.3698, "FR"), ("toulouse", 43.6047, 1.4442, "FR"),
        ("bordeaux", 44.8378, -0.5792, "FR"), ("lille", 50.6292, 3.0573, "FR"),
        ("france", 46.2276, 2.2137, "FR"), ("francia", 46.2276, 2.2137, "FR"),
    ),
    "RESTO": (
        ("amsterdam", 52.3676, 4.9041, "NL"), ("rotterdam", 51.9244, 4.4777, "NL"),
        ("utrecht", 52.0907, 5.1214, "NL"), ("netherlands", 52.1326, 5.2913, "NL"),
        ("warsaw", 52.2297, 21.0122, "PL"), ("krakow", 50.0647, 19.9450, "PL"),
        ("krakow", 50.0647, 19.9450, "PL"), ("wroclaw", 51.1079, 17.0385, "PL"),
        ("poland", 51.9194, 19.1451, "PL"), ("lisbon", 38.7223, -9.1393, "PT"),
        ("porto", 41.1579, -8.6291, "PT"), ("portugal", 39.3999, -8.2245, "PT"),
        ("zurich", 47.3769, 8.5417, "CH"), ("geneva", 46.2044, 6.1432, "CH"),
        ("vienna", 48.2082, 16.3738, "AT"), ("brussels", 50.8503, 4.3517, "BE"),
        ("stockholm", 59.3293, 18.0686, "SE"), ("oslo", 59.9139, 10.7522, "NO"),
        ("copenhagen", 55.6761, 12.5683, "DK"), ("helsinki", 60.1699, 24.9384, "FI"),
        ("dublin", 53.3498, -6.2603, "IE"),
        ("new york", 40.7128, -74.0060, "US"), ("new york city", 40.7128, -74.0060, "US"),
        ("nyc", 40.7128, -74.0060, "US"), ("san francisco", 37.7749, -122.4194, "US"),
        ("los angeles", 34.0522, -118.2437, "US"), ("chicago", 41.8781, -87.6298, "US"),
        ("austin", 30.2672, -97.7431, "US"), ("seattle", 47.6062, -122.3321, "US"),
        ("boston", 42.3601, -71.0589, "US"), ("miami", 25.7617, -80.1918, "US"),
        ("denver", 39.7392, -104.9903, "US"), ("atlanta", 33.7490, -84.3880, "US"),
        ("dallas", 32.7767, -96.7970, "US"), ("houston", 29.7604, -95.3698, "US"),
        ("washington dc", 38.9072, -77.0369, "US"),
        ("philadelphia", 39.9526, -75.1652, "US"), ("phoenix", 33.4484, -112.0740, "US"),
        ("san diego", 32.7157, -117.1611, "US"), ("united states", 39.8283, -98.5795, "US"),
        ("usa", 39.8283, -98.5795, "US"), ("toronto", 43.6532, -79.3832, "CA"),
        ("montreal", 45.5017, -73.5673, "CA"), ("vancouver", 49.2827, -123.1207, "CA"),
        ("canada", 56.1304, -106.3468, "CA"), ("sao paulo", -23.5505, -46.6333, "BR"),
        ("rio de janeiro", -22.9068, -43.1729, "BR"), ("brazil", -14.2350, -51.9253, "BR"),
        ("buenos aires", -34.6037, -58.3816, "AR"), ("argentina", -38.4161, -63.6167, "AR"),
        ("santiago", -33.4489, -70.6693, "CL"), ("chile", -35.6751, -71.5430, "CL"),
        ("bogota", 4.7110, -74.0721, "CO"), ("medellin", 6.2442, -75.5812, "CO"),
        ("colombia", 4.5709, -74.2973, "CO"), ("lima", -12.0464, -77.0428, "PE"),
        ("peru", -9.1900, -75.0152, "PE"), ("montevideo", -34.9011, -56.1645, "UY"),
        ("bangalore", 12.9716, 77.5946, "IN"), ("bengaluru", 12.9716, 77.5946, "IN"),
        ("mumbai", 19.0760, 72.8777, "IN"), ("hyderabad", 17.3850, 78.4867, "IN"),
        ("india", 20.5937, 78.9629, "IN"), ("singapore", 1.3521, 103.8198, "SG"),
        ("tokyo", 35.6762, 139.6503, "JP"), ("sydney", -33.8688, 151.2093, "AU"),
        ("melbourne", -37.8136, 144.9631, "AU"), ("auckland", -36.8485, 174.7633, "NZ"),
        ("cape town", -33.9249, 18.4241, "ZA"), ("johannesburg", -26.2041, 28.0473, "ZA"),
    ),
}

for _filas in _TABLAS.values():
    for _nombre, _lat, _lon, _pais in _filas:
        _cargar(_nombre, _lat, _lon, _pais)

_SINONIMOS = {
    "valencia es": "valencia", "valencia spain": "valencia", "valencia espana": "valencia",
    "madrid spain": "madrid", "barcelona spain": "barcelona", "sevilla spain": "sevilla",
    "malaga spain": "malaga", "bilbao spain": "bilbao", "milan": "milano",
    "naples": "napoli", "turin": "torino", "florence": "firenze", "venice": "venezia",
    "lyon france": "lyon", "paris france": "paris", "berlin germany": "berlin",
    "munich germany": "munich", "san jose": "san francisco", "sf bay area": "san francisco",
    "mexico df": "ciudad de mexico", "bogota colombia": "bogota", "washington": "washington dc",
}
for _alias, _destino in _SINONIMOS.items():
    if normalizar(_destino) in CIUDADES:
        CIUDADES[normalizar(_alias)] = CIUDADES[normalizar(_destino)]

PAISES: dict[str, str] = {
    "spain": "ES", "espana": "ES", "españa": "ES", "es": "ES", "estados unidos": "US",
    "united states": "US", "usa": "US", "us": "US", "uk": "GB", "gb": "GB",
    "reino unido": "GB", "united kingdom": "GB", "england": "GB", "scotland": "GB",
    "mexico": "MX", "mexico": "MX", "mx": "MX", "italy": "IT", "italia": "IT",
    "it": "IT", "germany": "DE", "alemania": "DE", "de": "DE", "france": "FR",
    "francia": "FR", "netherlands": "NL", "holanda": "NL", "paises bajos": "NL",
    "poland": "PL", "polonia": "PL", "portugal": "PT", "switzerland": "CH", "suiza": "CH",
    "austria": "AT", "belgium": "BE", "belgica": "BE", "canada": "CA", "brazil": "BR",
    "brasil": "BR", "argentina": "AR", "chile": "CL", "colombia": "CO", "peru": "PE",
    "india": "IN", "singapore": "SG", "japan": "JP", "australia": "AU",
    "new zealand": "NZ", "south africa": "ZA", "ireland": "IE", "irlanda": "IE",
    "remote": "XX", "remoto": "XX", "remota": "XX", "worldwide": "XX", "anywhere": "XX",
    "global": "XX", "world": "XX", "mundo": "XX", "todo el mundo": "XX",
    "europe": "EU", "europa": "EU", "emea": "EU", "european union": "EU",
    "union europea": "EU", "latam": "LA", "latin america": "LA", "america latina": "LA",
    "apac": "AP", "apj": "AP", "africa": "AF", "middle east": "ME", "oriente medio": "ME",
    "north america": "NA", "america del norte": "NA", "south america": "SA",
    "america del sur": "SA", "oceania": "OC", "caribbean": "LA", "asiapacific": "AP",
    "eastern europe": "EU", "western europe": "EU", "southern europe": "EU",
    "northern europe": "EU", "central europe": "EU", "b2b": "", "b2c": "",
}

REMOTO = re.compile(
    r"(remote|remoto|remota|teletrabajo|home\s?office|wfh|work\s?from\s?home|anywhere|"
    r"worldwide|fully\s?remote|100\s?%\s?remote|distributed|teletrabajar)",
    re.I,
)


def es_remoto(texto: str | None) -> bool:
    return bool(REMOTO.search(texto or ""))


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distancia en kilómetros entre dos coordenadas."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def _guardar(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    try:
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def _nominatim(consulta: str) -> tuple[float, float, str] | None:
    cache = _cache()
    clave = normalizar(consulta)
    if clave in cache:
        v = cache[clave]
        return (v[0], v[1], v[2]) if v else None
    try:
        import requests

        time.sleep(1.0)
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": consulta, "format": "json", "limit": 1},
            headers={"User-Agent": "JobBot/1.0 (filtro local de ofertas de empleo)"},
            timeout=12,
        )
        r.raise_for_status()
        datos = r.json()
        v = [float(datos[0]["lat"]), float(datos[0]["lon"]), "??"] if datos else None
    except Exception:
        return None
    cache[clave] = v
    _guardar(cache)
    return (v[0], v[1], v[2]) if v else None


def geocodificar(texto: str) -> tuple[float, float, str] | None:
    """Resuelve un texto de ubicación libre a (latitud, longitud, país)."""
    if not texto:
        return None
    clave = normalizar(texto)
    if clave in CIUDADES:
        return CIUDADES[clave]

    partes = [p for p in re.split(r"[,/|()\-\s]+", clave) if len(p) > 2]
    for tam in range(min(len(partes), 3), 0, -1):
        for i in range(len(partes) - tam + 1):
            frag = " ".join(partes[i:i + tam])
            if frag in CIUDADES:
                return CIUDADES[frag]

    for parte in partes:
        if parte in PAISES and PAISES[parte]:
            entrada = CIUDADES.get(PAISES[parte].lower())
            if entrada:
                return (entrada[0], entrada[1], entrada[2])

    if 2 < len(clave) < 60:
        return _nominatim(texto)
    return None


def pais_de(texto: str) -> str:
    """Código de país aproximado a partir de un texto de ubicación."""
    if not texto:
        return ""
    clave = normalizar(texto)
    if clave in CIUDADES:
        return CIUDADES[clave][2]
    partes = [p for p in re.split(r"[,/|()\s]+", clave) if p]
    for parte in partes:
        if parte in PAISES and PAISES[parte]:
            return PAISES[parte]
    for parte in partes:
        for frag, (_, _, p) in CIUDADES.items():
            if len(frag) > 3 and frag in clave:
                return p
    return ""
