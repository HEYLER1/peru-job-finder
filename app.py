"""Aplicación local de empleo personal. Ejecutar: .venv/bin/python app.py"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import json
import threading
from jobbot.busqueda import buscar_fuente,buscar_linkedin,evaluar
ROOT=Path(__file__).resolve().parent
STORE=ROOT/'data'/'app.json'
LOCK=threading.RLock()

def cargar():
    if not STORE.exists(): return {'perfil':{},'ofertas':[]}
    return json.loads(STORE.read_text())
def guardar(data):
    with LOCK:
        STORE.parent.mkdir(exist_ok=True); tmp=STORE.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)); tmp.replace(STORE)

class Handler(BaseHTTPRequestHandler):
    def respuesta(self,data,status=200):
        body=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/api/datos':
            data=cargar(); data['ofertas']=[evaluar(j,data['perfil']) for j in data['ofertas']]; return self.respuesta(data)
        paths={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        path=paths.get(self.path)
        if not path: return self.respuesta({'error':'No encontrado'},404)
        self.send_response(200); self.send_header('Content-Type',{'html':'text/html','js':'text/javascript','css':'text/css'}[path.split('.')[-1]]+'; charset=utf-8'); self.end_headers(); self.wfile.write((ROOT/'web'/path).read_bytes())
    def do_POST(self):
        if self.headers.get('Origin') and self.headers['Origin'] not in ('http://127.0.0.1:8765','http://localhost:8765'): return self.respuesta({'error':'Origen no permitido'},403)
        try:
            length=int(self.headers.get('Content-Length',0))
            if length>250000: return self.respuesta({'error':'Contenido demasiado grande'},413)
            body=json.loads(self.rfile.read(length)); data=cargar()
            if self.path=='/api/perfil': data['perfil']=body; guardar(data); return self.respuesta({'ok':True})
            if self.path=='/api/importar':
                job=body; job['id']=__import__('uuid').uuid4().hex; job['fuente']='manual'
                job['salario']=None; data['ofertas'].append(job); guardar(data); return self.respuesta({'ok':True})
            if self.path=='/api/buscar':
                sources=body.get('fuentes',[])
                if not sources or any(s not in ['practicas','convocatorias','linkedin'] for s in sources): raise ValueError('Selecciona una fuente válida')
                def run(s):
                    try: return buscar_linkedin(body.get('cargo',''),body.get('ubicacion','')) if s=='linkedin' else buscar_fuente(s,body.get('cargo',''))
                    except Exception: return [],[s+': no se pudo consultar. Comprueba la conexión o prueba más tarde.']
                with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(run,sources))
                with LOCK:
                    data=cargar()
                    jobs={j['id']:j for j in data['ofertas']}; errors=[]; count=0
                    for found,notes in results:
                        errors.extend(notes)
                        for j in found:
                            if j['id'] in jobs: j['detectado']=jobs[j['id']].get('detectado',j['detectado'])
                            jobs[j['id']]=j; count+=1
                    data['ofertas']=list(jobs.values()); guardar(data)
                return self.respuesta({'cantidad':count,'avisos':errors})
            return self.respuesta({'error':'No encontrado'},404)
        except (ValueError,TypeError,KeyError): return self.respuesta({'error':'Datos inválidos'},400)
        except Exception: return self.respuesta({'error':'No se pudo completar la operación'},500)
if __name__=='__main__':
    print('Abre http://127.0.0.1:8765',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
