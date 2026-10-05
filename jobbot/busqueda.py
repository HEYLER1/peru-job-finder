"""Lectura de fuentes y evaluación conservadora, sin inferir aptitud profesional."""
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import json
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor
import requests
from .modelo import normalizar, palabras

LIMA = ZoneInfo('America/Lima')
FUENTES = {'practicas': 'https://www.practicas.pe/', 'convocatorias': 'https://www.convocatoriasdetrabajo.com/'}

def texto_busqueda(value):
    return re.sub(r'\bingenier(?:o|a|os|as|ia)\b','ingenieria',normalizar(value))
MESES = dict(zip(['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'], range(1,13)))
MESES['setiembre'] = 9
MESES.update({m[:3]:v for m,v in list(MESES.items())})

class Pagina(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.textos=[]; self.enlaces=[]; self.datos=[]; self.actual=None; self.script=False; self.buffer=''; self.oculto=0; self.h1=''; self.en_h1=False
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag in ('script','style'): self.oculto += 1
        if tag=='script' and attrs.get('type')=='application/ld+json': self.script=True; self.buffer=''
        if tag=='a': self.actual=[attrs.get('href',''), '']
        if tag=='h1': self.en_h1=True
        if tag in ('p','div','li','h1','h2','h3','br'): self.textos.append('\n')
    def handle_endtag(self, tag):
        if tag=='h1': self.en_h1=False
        if tag=='a' and self.actual: self.enlaces.append(self.actual); self.actual=None
        if tag=='script' and self.script:
            try: self.datos.append(json.loads(self.buffer))
            except ValueError: pass
            self.script=False
        if tag in ('script','style'): self.oculto=max(0,self.oculto-1)
    def handle_data(self, data):
        if self.script: self.buffer += data
        if not self.oculto:
            self.textos.append(data)
            if self.en_h1: self.h1+=data
            if self.actual: self.actual[1] += data
    @property
    def texto(self): return re.sub(r'[ \t]+',' ', ''.join(self.textos))

def leer(url):
    # Sólo destinos explícitos de las tres fuentes; sin seguir redirecciones a otros hosts.
    allowed={'www.practicas.pe','practicas.pe','www.convocatoriasdetrabajo.com','convocatoriasdetrabajo.com','www.linkedin.com','linkedin.com'}
    for _ in range(4):
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in allowed: raise ValueError('URL fuera de las fuentes permitidas')
        r=requests.get(url,timeout=15,allow_redirects=False,headers={'User-Agent':'Mozilla/5.0 (compatible; EmpleoPersonal/1.0)'})
        if r.is_redirect: url=urljoin(url,r.headers['Location']); continue
        r.raise_for_status(); r.encoding=r.apparent_encoding
        if len(r.content)>8_000_000: raise ValueError('Página demasiado grande')
        return Pagina(r.text)
    raise ValueError('Demasiadas redirecciones')

def objetos(value):
    if isinstance(value,dict):
        yield value
        for v in value.values(): yield from objetos(v)
    elif isinstance(value,list):
        for v in value: yield from objetos(v)

def fecha_iso(value):
    if not value: return None
    try:
        dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return (dt.replace(tzinfo=LIMA) if dt.tzinfo is None else dt.astimezone(LIMA)).isoformat()
    except ValueError: return None

def fecha_texto(texto):
    n=normalizar(texto)
    m=re.search(r'\b(\d{1,2})\s+(?:de\s+)?([a-z]+)\s+(?:de[l]?\s+)?(20\d{2})\b',n)
    if m and m[2] in MESES:
        try: return date(int(m[3]),MESES[m[2]],int(m[1])).isoformat()
        except ValueError: return None
    m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})\b',texto)
    if m:
        try: return date(int(m[3]) if len(m[3])==4 else 2000+int(m[3]),int(m[2]),int(m[1])).isoformat()
        except ValueError: pass
    return None

def plazo_texto(raw):
    matches=list(re.finditer(r'Plazo para postular\s*:',raw,re.I))
    if not matches: matches=list(re.finditer(r'Puede postular hasta|Finaliza el',raw,re.I))
    for m in matches:
        block=raw[m.end():m.end()+300]
        # No tomar fechas de recomendaciones o anuncios distintos.
        block=re.split(r'COMO POSTULAR|¿Cómo Postular|Recomendaciones|PUBLICIDAD',block,flags=re.I)[0]
        value=fecha_texto(block)
        if not value: continue
        hm=re.findall(r'\b(\d{1,2}):(\d{2})(?::\d{2})?\b',block)
        if hm:
            hour,minute=map(int,hm[-1])
            if re.search(r'p\.?\s*m',block,re.I) and hour<12: hour+=12
            if hour<24 and minute<60: value=f'{value}T{hour:02}:{minute:02}:00-05:00'
        return value
    return None

def detalle(url, fuente, titulo=''):
    p=leer(url); raw=p.texto
    jd=next((o for d in p.datos for o in objetos(d) if o.get('@type')=='JobPosting'),{})
    titulo=jd.get('title') or p.h1.strip() or titulo or 'Oferta importada'
    publicado=fecha_iso(jd.get('datePosted')); cierre=fecha_iso(jd.get('validThrough'))
    if not publicado:
        label=re.search(r'Fecha de publicaci[oó]n\s*:?\s*([^\n]+)',raw,re.I)
        if label: publicado=fecha_iso(fecha_texto(label[1]))
    if not cierre:
        cierre=plazo_texto(raw)
    org=jd.get('hiringOrganization') or {}
    loc=jd.get('jobLocation') or {}
    if isinstance(loc,list): loc=loc[0] if loc else {}
    address=loc.get('address',{}) if isinstance(loc,dict) else {}
    ubicacion=address.get('addressLocality','') if isinstance(address,dict) else ''
    def campo(label):
        m=re.search(r'(?:^|\n)\s*'+label+r'\s*:\s*([^\n]{1,300})',raw,re.I)
        return m[1].strip() if m else ''
    descripcion=jd.get('description') or raw
    descripcion=Pagina(descripcion).texto if '<' in descripcion else descripcion
    # Para portales peruanos, reducir navegación previa a la sección del anuncio.
    if not jd:
        m=re.search(r'\bRequisitos\b',descripcion,re.I)
        if m: descripcion=descripcion[m.start():]
        end=re.search(r'(?:Recomendaciones para postular|Te sugerimos|Te recomendamos|www\.practicas)',descripcion,re.I)
        if end: descripcion=descripcion[:end.start()]
    n=normalizar(descripcion)
    salary=campo('(?:Remuneración|Subvención(?: económica)?)')
    amount=re.search(r'S\s*/\.?\s*([\d,]+(?:\.\d{1,2})?)',salary)
    salario=float(amount[1].replace(',','')) if amount else None
    return {'id':hashlib.sha256(url.encode()).hexdigest()[:16], 'fuente':fuente,'url':url,'titulo':titulo,
        'empresa':(org.get('name','') if isinstance(org,dict) else '') or campo('Organización') or (p.h1.split('Convocatoria')[0].strip() if 'Convocatoria' in p.h1 else ''), 'ubicacion':ubicacion or campo('Lugar de (?:trabajo|prácticas|prestación del servicio)'),
        'descripcion':descripcion[:20000], 'publicado':publicado, 'cierre':cierre,
        'detectado':datetime.now(LIMA).isoformat(),'revisado':datetime.now(LIMA).isoformat(), 'modalidad':'remoto' if re.search(r'(?:modalidad|trabajo|practicas)\s+(?:de\s+trabajo\s+)?(?:remot[oa]|virtual)|\bremote\b',n) else 'hibrido' if 'hibrid' in n else 'presencial' if 'presencial' in n else '',
        'tipo':'preprofesional' if 'preprofesional' in n or 'pre profesional' in n else 'profesional' if fuente=='practicas' else 'empleo',
        'salario':salario,'moneda':'PEN','periodo':'mensual', 'cerrada':bool(re.search(r'\b(?:Concluido|Convocatoria finalizada)\b',descripcion,re.I))}

def buscar_fuente(fuente, termino, ubicacion="", limite=30):
    p=leer(FUENTES[fuente]); links={}
    # Priorizar secciones observadas de carrera y ubicación, sin inventar direcciones.
    pages=[p]; wanted=palabras(texto_busqueda(termino))|palabras(ubicacion)
    categories=[]
    for href,title in p.enlaces:
        u=urljoin(FUENTES[fuente],href)
        if urlparse(u).hostname!=urlparse(FUENTES[fuente]).hostname: continue
        if re.search(r'/(?:oferta-|convocatoria-|oportunidad-laboral-)',u): continue
        if wanted and wanted & palabras(texto_busqueda(title+' '+u.replace('-',' '))): categories.append(u)
    for u in list(dict.fromkeys(categories))[:2]:
        try: pages.insert(0,leer(u))
        except Exception: pass
    for href,title in [link for page in pages for link in page.enlaces]:
        url=urljoin(FUENTES[fuente],href)
        if re.search(r'/(?:oferta-|convocatoria-|oportunidad-laboral-)',url) and urlparse(url).hostname==urlparse(FUENTES[fuente]).hostname:
            links.setdefault(url,title.strip())
    candidates=list(links.items())
    # Los listados principales enlazan convocatorias agrupadas. Buscar sus vacantes individuales.
    direct=[(u,t) for u,t in candidates if '/oferta-convocatoria-' in u or '/oportunidad-laboral-' in u]
    if not direct:
        for parent,title in candidates[:8]:
            try:
                group=leer(parent)
                for href,t in group.enlaces:
                    u=urljoin(parent,href)
                    if re.search(r'/(?:oferta-|oportunidad-laboral-)',u) and urlparse(u).hostname==urlparse(parent).hostname:
                        if u not in dict(direct): direct.append((u,t.strip()))
            except Exception: pass
            if len(direct)>=limite: break
    candidates=direct or candidates
    def get(item):
        try: return detalle(item[0],fuente,item[1]),None
        except Exception: return None,'No se pudo leer un detalle de '+fuente
    with ThreadPoolExecutor(max_workers=2) as pool: result=list(pool.map(get,candidates[:limite]))
    words=palabras(texto_busqueda(termino))
    jobs=[j for j,e in result if j]
    errors=list(dict.fromkeys(e for j,e in result if e))
    errors.append(f'{fuente}: {len(jobs)} vacantes leídas, con límite de {limite}. Se revisan secciones relacionadas; la cobertura no es exhaustiva.')
    return jobs,errors

def buscar_linkedin(termino, ubicacion, tipo='', limite=30):
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return [], ['LinkedIn: el conector no está instalado. Instala requirements-linkedin.txt.']
    from .recomendacion import normalizar_oferta
    target=texto_busqueda(termino).strip()
    # Buscar el área, en vez de exigir un título literal que excluye puestos afines.
    if 'sistemas' in target or 'informatica' in target: target='sistemas'
    queries=[target or ('practicante' if 'profesional' in tipo or tipo=='practicas' else 'empleo')]
    if tipo in ('preprofesional','profesional','practicas') and target:
        queries=[f'practicante {target}',target]
    location=(ubicacion.strip()+', Peru') if ubicacion and 'peru' not in normalizar(ubicacion) else ubicacion or 'Peru'
    jobs={}; notes=[]
    for query in queries[:2]:
        if len(jobs)>=limite: break
        try:
            df=scrape_jobs(site_name=['linkedin'], search_term=query, location=location,
                results_wanted=min(int(limite)-len(jobs),40), fetch_description=True,
                job_type='internship' if tipo in ('preprofesional','profesional','practicas') else None,
                verbose=0)
            for record in json.loads(df.to_json(orient='records',date_format='iso')):
                url=record.get('job_url') or ''
                if not url: continue
                is_remote=record.get('is_remote') is True
                job={'id':hashlib.sha256(url.encode()).hexdigest()[:16], 'fuente':'linkedin','url':url,
                    'titulo':record.get('title') or '', 'empresa':record.get('company') or '',
                    'descripcion':record.get('description') or '', 'ubicacion':record.get('location') or '',
                    'modalidad':'remoto' if is_remote else '', 'is_remote':is_remote,
                    'job_type':record.get('job_type') or '', 'tipo':'empleo',
                    'publicado':fecha_iso(record.get('date_posted')), 'cierre':None,
                    'detectado':datetime.now(LIMA).isoformat(), 'revisado':datetime.now(LIMA).isoformat(),
                    'cerrada':False,'salario':record.get('min_amount'), 'moneda':record.get('currency') or '',
                    'periodo':record.get('interval') or ''}
                jobs[job['id']]=normalizar_oferta(job)
        except Exception:
            notes.append('LinkedIn: no se pudo completar una consulta; puede haber un bloqueo o un problema de conexión.')
    if not jobs:
        notes.append(f'LinkedIn no devolvió anuncios para {target or "la consulta"} en {location}. Prueba otra ubicación o un cargo más amplio; no significa que no existan vacantes.')
    return list(jobs.values())[:limite], list(dict.fromkeys(notes))

def evaluar(oferta,perfil,ahora=None):
    ahora=ahora or datetime.now(LIMA)
    cierre=oferta.get('cierre')
    limite=None
    if cierre:
        try:
            limite=datetime.combine(date.fromisoformat(cierre),time.max,LIMA) if len(cierre)==10 else datetime.fromisoformat(cierre)
            if limite.tzinfo is None: limite=limite.replace(tzinfo=LIMA)
        except (ValueError,TypeError): limite=None
    estado='vencida' if limite and limite<ahora else 'cerrada' if oferta.get('cerrada') else 'en plazo' if limite else 'vigencia desconocida'
    pub=fecha_iso(oferta.get('publicado'))
    edad=max(0,(ahora-datetime.fromisoformat(pub)).total_seconds()/86400) if pub else None
    texto=normalizar(oferta.get('descripcion','')+' '+oferta.get('titulo',''))
    skills=[s.strip() for s in perfil.get('habilidades','').split(',') if s.strip()]
    presentes=[s for s in skills if ' '+normalizar(s)+' ' in ' '+texto+' ']
    return {**oferta,'estado':estado,'antiguedad':edad, 'dias_restantes':(limite-ahora).total_seconds()/86400 if limite else None,
        'coincidencias':presentes,'puntaje':round(100*len(presentes)/len(skills)) if skills else None,
        'aviso':'Coincidencia textual de tus habilidades; los requisitos completos aún requieren revisión.'}
