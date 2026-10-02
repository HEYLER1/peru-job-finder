import unittest
from unittest.mock import patch
from jobbot.busqueda import Pagina,detalle,plazo_texto
class Portales(unittest.TestCase):
    def test_encabezado_no_oculta_plazo_real(self):
        text='7 oct 2026\nPlazo para postular\nPUBLICIDAD\nPlazo para postular:\n07 de Octubre del 2026, De 08:00 am a 12:00 m.\n¿Cómo Postular?'
        self.assertEqual(plazo_texto(text),'2026-10-07T12:00:00-05:00')
    def test_no_usa_fechas_de_anuncio_relacionado(self):
        self.assertIsNone(plazo_texto('Plazo para postular:\nNo especifica\nPUBLICIDAD\n07 de Octubre del 2026'))
    def test_detalle_excluye_footer_y_extrae_sueldo(self):
        html='<h1>Convocatoria de prueba</h1><h2>Requisitos</h2><p>Excel</p><p>Lugar de prácticas: Lima</p><p>Subvención económica: S/ 1,130.00</p><p>Plazo para postular: 09 de Octubre del 2026</p><h2>Te sugerimos</h2><p>Ingeniería de sistemas Puno</p>'
        with patch('jobbot.busqueda.leer',return_value=Pagina(html)):
            j=detalle('https://www.practicas.pe/oferta-prueba.html','practicas')
        self.assertEqual(j['cierre'],'2026-10-09');self.assertEqual(j['salario'],1130)
        self.assertNotIn('Puno',j['descripcion'])
        self.assertEqual(j['titulo'],'Convocatoria de prueba')
if __name__=='__main__':unittest.main()
