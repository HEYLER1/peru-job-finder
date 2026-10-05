import unittest
from unittest.mock import patch
import importlib.util
HAS_CONNECTOR = importlib.util.find_spec("pandas") is not None and importlib.util.find_spec("jobspy") is not None
if HAS_CONNECTOR:
    import pandas as pd
from jobbot.busqueda import buscar_linkedin

@unittest.skipUnless(HAS_CONNECTOR, "Conector opcional de LinkedIn no instalado")
class LinkedIn(unittest.TestCase):
    def test_descripciones_clasificacion_y_limite(self):
        frame=pd.DataFrame([{'job_url':'https://www.linkedin.com/jobs/view/'+str(i),'title':'Practicante Pre Profesional de TI','description':'Estudiante de sistemas. Python.','location':'Lima, Peru','is_remote':False,'date_posted':'2026-10-05','job_type':'internship'} for i in range(10)])
        with patch('jobspy.scrape_jobs',return_value=frame) as scrape:
            jobs,notes=buscar_linkedin('ingeniero de sistemas','Lima','preprofesional',10)
        self.assertEqual(len(jobs),10);self.assertEqual(notes,[])
        self.assertEqual(scrape.call_count,1)
        self.assertTrue(scrape.call_args.kwargs['fetch_description'])
        self.assertEqual(scrape.call_args.kwargs['location'],'Lima, Peru')
        self.assertTrue(all(j['tipo']=='preprofesional' for j in jobs))
    def test_sin_resultados_tiene_explicacion(self):
        with patch('jobspy.scrape_jobs',return_value=pd.DataFrame()):
            jobs,notes=buscar_linkedin('sistemas','Puno','preprofesional',10)
        self.assertEqual(jobs,[]);self.assertIn('no devolvió',notes[-1])
    def test_fallo_no_se_presenta_como_exito(self):
        with patch('jobspy.scrape_jobs',side_effect=RuntimeError('bloqueo')):
            jobs,notes=buscar_linkedin('sistemas','Puno','preprofesional',10)
        self.assertEqual(jobs,[]);self.assertTrue(any('no se pudo' in s for s in notes))
if __name__=='__main__': unittest.main()
