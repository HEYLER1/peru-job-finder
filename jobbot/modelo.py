"""Modelo de datos unificado para las ofertas de empleo."""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from dataclasses import dataclass, field

_RE_ETIQUETAS = re.compile(r"<[^>]+>")
_RE_ESPACIOS = re.compile(r"\s+")
_RE_NO_ALFANUM = re.compile(r"[^a-z0-9 ]+")

_NO_PALABRAS = {
    "de", "del", "la", "el", "los", "las", "y", "en", "para", "con", "the", "and",
    "of", "in", "a", "an", "to", "at", "on", "for", "senior", "junior", "mid",
    "sr", "jr", "i", "ii", "iii",
}

_MONEDAS_SIMBOLO = {
    "€": "EUR", "$": "USD", "£": "GBP", "₹": "INR", "zł": "PLN", "kr": "SEK",
    "R$": "BRL", "MX$": "MXN", "C$": "CAD", "A$": "AUD", "CHF": "CHF",
}


def limpiar_html(texto: str | None) -> str:
    """Convierte HTML entities y etiquetas en texto plano."""
    if not texto:
        return ""
    texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", texto, flags=re.S | re.I)
    texto = _RE_ETIQUETAS.sub(" ", texto)
    texto = html.unescape(texto)
    return _RE_ESPACIOS.sub(" ", texto).strip()


def normalizar(texto: str | None) -> str:
    """Minúsculas, sin acentos y sin puntuación: para comparar palabras."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return _RE_ESPACIOS.sub(" ", _RE_NO_ALFANUM.sub(" ", texto)).strip()


def palabras(texto: str | None, min_len: int = 2) -> set[str]:
    """Conjunto de palabras significativas de un texto."""
    return {
        p for p in normalizar(texto).split()
        if len(p) >= min_len and p not in _NO_PALABRAS and not p.isdigit()
    }


@dataclass
class Oferta:
    """Una oferta de empleo, venga de donde venga."""

    id: str
    fuente: str
    titulo: str
    empresa: str
    url: str
    descripcion: str = ""
    ubicacion: str = ""
    remoto: bool = False
    url_aplicacion: str = ""
    etiquetas: list[str] = field(default_factory=list)
    tipo_contrato: str = ""
    seniority: str = ""
    categoria: str = ""
    idioma: str = ""

    coords: tuple[float, float] | None = None
    fecha: str | None = None

    salario_min: float | None = None
    salario_max: float | None = None
    moneda: str = ""
    periodo: str = ""
    salario_texto: str = ""

    def texto(self) -> str:
        return " ".join(
            [self.titulo, self.empresa, self.descripcion, " ".join(self.etiquetas)]
        )

    def clave(self) -> str:
        """Identificador estable para deduplicar entre fuentes."""
        base = normalizar(f"{self.empresa} {self.titulo}")
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]

    def es_remota(self) -> bool:
        return self.remoto
