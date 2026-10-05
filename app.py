"""Aplicación local de empleo personal. Ejecutar: .venv/bin/python app.py."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import threading
from jobbot.busqueda import buscar_fuente, buscar_linkedin, evaluar
from jobbot.recomendacion import resultados

ROOT = Path(__file__).resolve().parent
STORE = ROOT / 'data' / 'app.json'
LOCK = threading.RLock()

def cargar():
    if not STORE.exists(): return {'perfil': {}, 'ofertas': [], 'feedback': {}}
    data=json.loads(STORE.read_text()); data.setdefault('feedback', {}); return data

def guardar(data):
    with LOCK:
        STORE.parent.mkdir(exist_ok=True)
        tmp=STORE.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)); tmp.replace(STORE)

def vista(data,p):
    return resultados(data['ofertas'],data['perfil'],p,data.get('feedback',{}),evaluar)

class Handler(BaseHTTPRequestHandler):
    def respuesta(self,data,status=200):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path=='/api/datos':
            data=cargar()
            return self.respuesta({'perfil':data['perfil'],'busquedas':data.get('busquedas',{}),**vista(data,data['perfil'].get('preferencias',{}))})
        paths={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        path=paths.get(self.path)
        if not path: return self.respuesta({'error':'No encontrado'},404)
        self.send_response(200)
        self.send_header('Content-Type',{'html':'text/html','js':'text/javascript','css':'text/css'}[path.split('.')[-1]]+'; charset=utf-8')
        self.send_header('Cache-Control','no-cache'); self.end_headers(); self.wfile.write((ROOT/'web'/path).read_bytes())

    def do_POST(self):
        if self.headers.get('Origin') and self.headers['Origin'] not in ('http://127.0.0.1:8765','http://localhost:8765'):
            return self.respuesta({'error':'Origen no permitido'},403)
        try:
            length=int(self.headers.get('Content-Length',0))
            if length>250000: return self.respuesta({'error':'Contenido demasiado grande'},413)
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict): raise ValueError()
            if self.path=='/api/filtrar': return self.respuesta(vista(cargar(),body))
            if self.path=='/api/perfil':
                for field in ('meses_experiencia','ciclo'):
                    if body.get(field) not in (None,'') and (float(body[field])<0 or float(body[field])>1200): raise ValueError()
                with LOCK:
                    data=cargar(); data['perfil']=body; guardar(data)
                return self.respuesta({'ok':True})
            if self.path=='/api/feedback':
                if body.get('valor') not in ('interesa','no_interesa',''): raise ValueError()
                with LOCK:
                    data=cargar()
                    if body.get('id') not in {j['id'] for j in data['ofertas']}: raise ValueError()
                    if body['valor']: data['feedback'][body['id']]=body['valor']
                    else: data['feedback'].pop(body['id'],None)
                    guardar(data)
                return self.respuesta({'ok':True})
            if self.path=='/api/importar':
                if not body.get('titulo') or not body.get('descripcion'): raise ValueError()
                job=body; job['id']=__import__('uuid').uuid4().hex; job['fuente']='manual'; job['salario']=None
                with LOCK:
                    data=cargar(); data['ofertas'].append(job); guardar(data)
                return self.respuesta({'ok':True})
            if self.path=='/api/buscar':
                sources=body.get('fuentes',[])
                if not sources or any(s not in ['practicas','convocatorias','linkedin'] for s in sources): raise ValueError('Selecciona una fuente válida')
                sources=list(dict.fromkeys(sources)); limit=min(40,max(10,int(body.get('limite',30))))
                data=cargar(); profile=data['perfil']
                query=body.get('cargo') or profile.get('cargos_objetivo') or profile.get('carrera') or ''
                def run(s):
                    try:
                        result=buscar_linkedin(query,body.get('ubicacion',''),body.get('tipo',''),limit) if s=='linkedin' else buscar_fuente(s,query,body.get('ubicacion',''),limit)
                        return s,*result
                    except Exception as exc:
                        # Aviso visible; no tratar el fallo como una búsqueda exitosa sin ofertas.
                        return s,[],[s+': la consulta falló ('+type(exc).__name__+'). Comprueba la conexión o prueba más tarde.']
                with ThreadPoolExecutor(max_workers=3) as pool: found=list(pool.map(run,sources))
                with LOCK:
                    data=cargar(); jobs={j['id']:j for j in data['ofertas']}; errors=[]; count=0
                    for source,items,notes in found:
                        errors.extend(notes)
                        data.setdefault('busquedas',{})[source]={'encontradas':len(items),'avisos':notes,'consulta':query,'ubicacion':body.get('ubicacion','')}
                        for j in items:
                            if j['id'] in jobs: j['detectado']=jobs[j['id']].get('detectado',j['detectado'])
                            jobs[j['id']]=j; count+=1
                    data['ofertas']=list(jobs.values()); guardar(data)
                return self.respuesta({'cantidad':count,'avisos':errors,'busquedas':data.get('busquedas',{}),**vista(data,body)})
            return self.respuesta({'error':'No encontrado'},404)
        except (ValueError,TypeError,KeyError): return self.respuesta({'error':'Revisa los datos y selecciona al menos una fuente de búsqueda.'},400)
        except Exception: return self.respuesta({'error':'No se pudo completar la operación'},500)

if __name__=='__main__':
    print('Abre http://127.0.0.1:8765',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
