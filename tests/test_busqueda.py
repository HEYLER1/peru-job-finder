import unittest
from datetime import datetime
from jobbot.busqueda import evaluar,fecha_texto,LIMA,Pagina
class Fechas(unittest.TestCase):
    def test_fecha_peru(self):
        self.assertEqual(fecha_texto('29 de Setiembre de 2026'),'2026-09-29')
        self.assertIsNone(fecha_texto('31/02/2026'))
    def test_vencimiento_supera_etiqueta(self):
        j=evaluar({'cierre':'2026-09-29','publicado':None},{},datetime(2026,10,2,tzinfo=LIMA))
        self.assertEqual(j['estado'],'vencida');self.assertIsNone(j['antiguedad'])
    def test_cierre_incluye_dia_completo(self):
        j=evaluar({'cierre':'2026-10-02'},{},datetime(2026,10,2,18,tzinfo=LIMA))
        self.assertEqual(j['estado'],'en plazo')
    def test_hora_cierre(self):
        j=evaluar({'cierre':'2026-10-02T16:45:00-05:00'},{},datetime(2026,10,2,18,tzinfo=LIMA))
        self.assertEqual(j['estado'],'vencida')
    def test_habilidades_no_subcadenas(self):
        j=evaluar({'descripcion':'JavaScript y Excel'},{'habilidades':'Java, Excel'})
        self.assertEqual(j['coincidencias'],['Excel'])
    def test_jsonld(self):
        p=Pagina('<script type="application/ld+json">{"@type":"JobPosting"}</script><h1>Oferta</h1>')
        self.assertEqual(p.datos[0]['@type'],'JobPosting');self.assertNotIn('JobPosting',p.texto)
if __name__=='__main__':unittest.main()
