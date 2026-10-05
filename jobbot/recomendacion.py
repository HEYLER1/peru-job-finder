"""Ranking explicable y aprendizaje local a partir de valoraciones explícitas."""
import math
import re
from collections import Counter
from .modelo import normalizar

STOP={'de','del','la','el','los','las','en','y','o','un','una','para','con','por','al','the','and','of','to','in','se','que','es','su','como'}
AREAS={
    'tecnologia': ['sistemas','informatica','software','programacion','desarrollador','developer','tecnologia','technology','soporte tecnico','ti','it','computacion','sap','odoo'],
    'datos':['datos','data','analista de datos','business intelligence','power bi','sql','analytics'],
    'administracion':['administracion','administrativo','gestion empresarial'],
    'contabilidad':['contabilidad','contable','contador','cuentas por pagar'],
}
ALIASES={'excel':['excel','hojas de calculo'], 'python':['python'], 'sql':['sql'], 'power bi':['power bi','powerbi'], 'javascript':['javascript','js'], 'c++':['c++'], 'c#':['c#'], 'atencion al cliente':['atencion al cliente','servicio al cliente']}
LIMA_DISTRITOS=['san isidro','miraflores','surquillo','surco','la molina','lurin','san borja','santa anita','ate','barranco','chorrillos','lima metropolitan']

def canon(v):
    return re.sub(r'\bingenier(?:o|a|os|as|ia)\b','ingenieria',normalizar(v))

def tokens(v):
    return {w for w in canon(v).split() if len(w)>2 and w not in STOP and w not in {'ingenieria','profesional','requisitos','convocatoria','trabajo'}}

def contiene(texto, termino):
    # Conservar los símbolos que distinguen lenguajes como C++ y C#.
    if '+' in termino or '#' in termino:
        return bool(re.search(r'(?<!\w)'+re.escape(termino.lower())+r'(?!\w)',texto.lower()))
    return bool(re.search(r'\b'+re.escape(canon(termino))+r'\b',canon(texto)))

def afinidad(query,text):
    q=tokens(query); t=tokens(text)
    if not q: return 0.0
    literal=len(q&t)/len(q)
    groups=[a for a,terms in AREAS.items() if any(contiene(query,w) for w in terms)]
    related=any(any(contiene(text,w) for w in AREAS[a]) for a in groups)
    return max(literal,0.6 if related else 0)

def relevancia(query,j):
    title=afinidad(query,j.get('titulo',''))
    desc=j.get('descripcion','')
    # Una herramienta mencionada en funciones no convierte un cargo de otra área
    # en una profesión afín. Admitir la carrera requiere una mención de formación.
    education=re.findall(r'(?:formaci[oó]n\s+acad[eé]mica|carreras?\s+(?:de\s+)?|estudiante[s]?\s+(?:universitarios?\s+)?de)\s*:?\s*([^\n.]{1,250})',desc,re.I)
    academic=max((afinidad(query,text) for text in education),default=0)
    return max(title,academic*0.8)

def clasificar_tipo(j):
    title=canon(j.get('titulo','')); description=canon(j.get('descripcion',''))
    if re.search(r'pre\s*profesional',title): return 'preprofesional'
    if re.search(r'practicante\s+profesional|practicas\s+profesionales',title): return 'profesional'
    is_intern=bool(re.search(r'practic|\bintern\b|\binternship\b',title)) or j.get('job_type')=='internship'
    if is_intern or j.get('fuente')=='practicas':
        student=bool(re.search(r'\bestudiante[s]?\b',description)); graduate=bool(re.search(r'\begresad[oa]s?\b',description))
        if re.search(r'pre\s*profesional',description) or student and not graduate: return 'preprofesional'
        if re.search(r'practicas?\s+profesionales',description) or graduate and not student: return 'profesional'
        return 'practicas'
    return j.get('tipo') if j.get('tipo') in ('preprofesional','profesional') else 'empleo'

def normalizar_oferta(j):
    j=dict(j)
    if j.get('fuente') in ('practicas','convocatorias'):
        text=j.get('descripcion','')
        start=re.search(r'\b(?:Requisitos|RESUMEN DE LA CONVOCATORIA)\b',text,re.I)
        if start: text=text[start.start():]
        end=re.search(r'Recomendaciones para postular|Te sugerimos|Te recomendamos|Únete a nuestros grupos',text,re.I)
        if end: text=text[:end.start()]
        j['descripcion']=text
        prefix=j.get('titulo','').split('Convocatoria')[0].strip()
        if prefix and 'Convocatoria' in j.get('titulo','') and len(prefix)<100: j['empresa']=prefix
    j['tipo']=clasificar_tipo(j)
    if j.get('is_remote'): j['modalidad']='remoto'
    return j

def ubicacion_coincide(ubicacion,preferencia):
    if contiene(ubicacion,preferencia): return True
    return canon(preferencia)=='lima' and any(contiene(ubicacion,w) for w in LIMA_DISTRITOS)

def requisitos(j,perfil):
    desc=j.get('descripcion',''); n=canon(desc); checks=[]
    def add(nombre,estado,evidencia): checks.append({'nombre':nombre,'estado':estado,'evidencia':evidencia})
    situacion=canon(perfil.get('situacion',''))
    if j['tipo']=='preprofesional':
        add('Situación académica','por confirmar' if not situacion else 'compatible' if situacion=='estudiante' else 'brecha','Prácticas preprofesionales; revisa si las bases admiten tu condición.')
    elif j['tipo']=='profesional':
        add('Situación académica','por confirmar' if not situacion else 'brecha' if situacion=='estudiante' else 'compatible','Prácticas profesionales; revisar condición de egreso y plazo desde el egreso.')
    # Extraer sólo experiencia general / no calificada. La específica requiere otro dato.
    pattern=r'(?:experiencia\s+general\s*:?|experiencia\s+(?:minima\s+)?(?:de\s+)?|minimo\s+)(?:.{0,45}?)(\d+(?:[.,]\d+)?)\s*(?:\(\d+\)\s*)?(anos|meses)'
    m=re.search(pattern,n)
    if m and 'experiencia' in n[max(0,m.start()-25):m.end()]:
        required=float(m[1].replace(',','.'))*(12 if m[2]=='anos' else 1)
        available=perfil.get('meses_experiencia','')
        try: actual=float(available) if available!='' else None
        except (ValueError,TypeError): actual=None
        add('Experiencia general','por confirmar' if actual is None else 'compatible' if actual>=required else 'brecha',f'La descripción menciona {required:g} meses; declaraste {actual:g}.' if actual is not None else f'La descripción menciona {required:g} meses; completa tu experiencia.')
    cycle=re.search(r'(?:a\s+partir\s+del?\s+|desde\s+el\s+|minimo\s+)(\d{1,2})(?:vo|to|mo|do|ro)?\s+ciclo',n)
    if cycle:
        actual=perfil.get('ciclo','')
        add('Ciclo académico','por confirmar' if actual=='' else 'compatible' if int(actual)>=int(cycle[1]) else 'brecha',f'Se menciona un mínimo de ciclo {cycle[1]}.')
    field=re.search(r'(?:formaci[oó]n\s+acad[eé]mica|carreras?\s+(?:de\s+)?|estudiante[s]?\s+de)\s*:?\s*([^\n]{1,400})',desc,re.I)
    if field and perfil.get('carrera'):
        score=afinidad(perfil['carrera'],field[1])
        add('Carrera','compatible' if score>=0.8 else 'por confirmar','Formación publicada: '+field[1][:250])
    return checks

def vector(j):
    # Título y características del empleo pesan más que el texto común de requisitos.
    parts=list(tokens(j.get('titulo','')))*3+list(tokens(j.get('descripcion','')[:6000]))
    parts+=['tipo:'+j.get('tipo',''),'modalidad:'+j.get('modalidad','')]
    c=Counter(parts); length=math.sqrt(sum(v*v for v in c.values())) or 1
    return {k:v/length for k,v in c.items()}

def entrenar(ofertas,feedback):
    """Regresión logística local con SGD y regularización; reconstruida al cambiar etiquetas."""
    by_id={j['id']:j for j in ofertas}; samples=[]
    for key,value in sorted(feedback.items()):
        if key in by_id and value in ('interesa','no_interesa'): samples.append((vector(normalizar_oferta(by_id[key])),1 if value=='interesa' else 0))
    if not samples: return {},0
    weights={}
    for _ in range(25):
        for x,y in samples:
            z=max(-20,min(20,sum(weights.get(k,0)*v for k,v in x.items())))
            error=y-1/(1+math.exp(-z))
            for k,v in x.items(): weights[k]=weights.get(k,0)*0.998+0.25*error*v
    return weights,len(samples)

def recomendar(j,perfil,modelo):
    skills=[x.strip() for x in perfil.get('habilidades','').split(',') if x.strip()]
    matched=[s for s in skills if any(contiene(j.get('descripcion','')+' '+j.get('titulo',''),a) for a in ALIASES.get(canon(s),[s]))]
    query=' '.join([perfil.get('carrera',''),perfil.get('cargos_objetivo',''),perfil.get('experiencia','')])
    dimensions=[]; reasons=[]
    if skills:
        dimensions.append((len(matched)/len(skills),0.45))
        if matched: reasons.append('Habilidades mencionadas: '+', '.join(matched))
    if query.strip():
        related=relevancia(query,j)
        dimensions.append((related,0.3))
        if related: reasons.append('Afinidad con tus cargos, carrera o experiencia declarados.')
    checks=requisitos(j,perfil)
    known=[c for c in checks if c['estado']!='por confirmar']
    if known:
        dimensions.append((sum(c['estado']=='compatible' for c in known)/len(known),0.25))
    # Los campos desconocidos no se redistribuyen como si fueran evidencia positiva.
    base=sum(v*w for v,w in dimensions) if dimensions else None
    weights,count=modelo; adjust=0
    if count:
        signal=sum(weights.get(k,0)*v for k,v in vector(j).items())
        adjust=15*math.tanh(signal)*min(count/5,1)
        if abs(adjust)>0.5: reasons.append('Tu historial de “Me interesa” y “No me interesa” ajusta su posición.')
    score=round(max(0,min(100,(base*100 if base is not None else 50)+adjust))) if base is not None or count else None
    if any(c['estado']=='brecha' for c in checks):
        score=min(score,45) if score is not None else None
        reasons.append('Hay un requisito declarado que no coincide con tu perfil.')
    return {**j,'coincidencias':matched,'puntaje':score,'razones':reasons,'requisitos':checks,'aprendizaje':round(adjust,1), 'aviso':'Compatibilidad orientativa. Revisa los requisitos completos y las bases antes de postular.'}

def motivos_filtro(j,p):
    reasons=[]
    if j.get('fuente') not in p.get('fuentes',['practicas','convocatorias','linkedin','manual']): reasons.append('fuente')
    if not p.get('vencidas',False) and j['estado'] in ('vencida','cerrada'): reasons.append('vigencia')
    unknown=p.get('desconocidos',True)
    if j.get('antiguedad') is None:
        if not p.get('sinfecha',True): reasons.append('fecha desconocida')
    elif p.get('dias') and j['antiguedad']>float(p['dias']): reasons.append('antigüedad')
    for field in ('modalidad','ubicacion'):
        wanted=p.get(field)
        if not wanted: continue
        value=j.get(field,'')
        if not value:
            if not unknown: reasons.append(field+' desconocida')
        elif not (ubicacion_coincide(value,wanted) if field=='ubicacion' else value==wanted): reasons.append(field)
    if p.get('tipo'):
        if j.get('tipo')=='practicas' and p['tipo'] in ('preprofesional','profesional','practicas'):
            if not unknown and p['tipo']!='practicas': reasons.append('tipo por confirmar')
        elif not (p['tipo']=='practicas' and j.get('tipo') in ('preprofesional','profesional') or p['tipo']==j.get('tipo')): reasons.append('tipo')
    if p.get('sueldo'):
        valid=j.get('moneda')=='PEN' and j.get('periodo') in ('mensual','monthly') and j.get('salario') is not None
        if not valid:
            if not unknown: reasons.append('sueldo desconocido')
        elif j['salario']<float(p['sueldo']): reasons.append('sueldo')
    if p.get('cargo') and relevancia(p['cargo'],j)<0.3: reasons.append('cargo')
    return reasons

def resultados(ofertas,perfil,p,feedback,evaluar):
    model=entrenar(ofertas,feedback); counts=Counter(); sources={}; visible=[]; excluded=[]
    perfil={**perfil,'cargos_objetivo':perfil.get('cargos_objetivo') or p.get('cargo','')}
    for raw in ofertas:
        j=evaluar(normalizar_oferta(raw),perfil); j=recomendar(j,perfil,model); j['valoracion']=feedback.get(j['id'],'')
        reasons=motivos_filtro(j,p); j['excluida_por']=reasons
        sources.setdefault(j['fuente'],{'guardadas':0,'visibles':0}); sources[j['fuente']]['guardadas']+=1
        if reasons: counts.update(set(reasons)); excluded.append(j)
        else: visible.append(j); sources[j['fuente']]['visibles']+=1
    def order(j):
        if p.get('orden')=='recientes': return -(j['antiguedad'] if j['antiguedad'] is not None else 1e9)
        if p.get('orden')=='cierre': return -(j['dias_restantes'] if j['dias_restantes'] is not None else 1e9)
        return j['puntaje'] if j['puntaje'] is not None else -1
    visible.sort(key=order,reverse=True); excluded.sort(key=order,reverse=True)
    return {'ofertas':visible,'alternativas':[j for j in excluded if j['excluida_por'] and not set(j['excluida_por'])&{'fuente','vigencia'}][:8], 'total':len(ofertas),'ocultas':dict(counts),'fuentes':sources,'valoraciones':model[1]}
