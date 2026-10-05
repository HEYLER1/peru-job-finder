import unittest
from jobbot.recomendacion import clasificar_tipo, resultados, entrenar, recomendar, normalizar_oferta, afinidad
from jobbot.busqueda import evaluar

class Recomendaciones(unittest.TestCase):
    def job(self,id='a',title='Practicante de sistemas',desc='Estudiante de Ingeniería de Sistemas. Python y SQL.'):
        return {'id':id,'fuente':'linkedin','titulo':title,'descripcion':desc,'tipo':'empleo','ubicacion':'San Isidro, Peru','publicado':None,'cierre':None}
    def test_reclasifica_practicas_antiguas(self):
        self.assertEqual(clasificar_tipo(self.job(title='Practicante Pre Profesional de TI')),'preprofesional')
        self.assertEqual(clasificar_tipo(self.job(title='Practicante profesional de TI')),'profesional')
    def test_practica_no_es_empleo_por_falta_de_nivel(self):
        self.assertEqual(clasificar_tipo(self.job(desc='Soporte técnico')),'practicas')
    def test_lima_incluye_distritos_y_cargo_relacionado(self):
        prefs={'fuentes':['linkedin'],'cargo':'ingeniero de sistemas','ubicacion':'Lima','tipo':'preprofesional','sinfecha':True,'desconocidos':True}
        out=resultados([self.job()],{},prefs,{},evaluar)
        self.assertEqual(len(out['ofertas']),1)
    def test_puno_no_se_convierte_en_lima_silenciosamente(self):
        out=resultados([self.job()],{}, {'fuentes':['linkedin'],'ubicacion':'Puno'}, {},evaluar)
        self.assertEqual(out['ofertas'],[]);self.assertEqual(out['ocultas']['ubicacion'],1)
        self.assertIn('ubicacion',out['alternativas'][0]['excluida_por'])
    def test_datos_desconocidos_no_son_cumplimiento(self):
        j=normalizar_oferta(self.job(title='Practicante preprofesional',desc='Experiencia mínima de 2 años.'))
        r=recomendar(j,{},({},0))
        self.assertTrue(all(c['estado']=='por confirmar' for c in r['requisitos']))
    def test_brecha_limita_puntuacion(self):
        j=normalizar_oferta(self.job(title='Practicante preprofesional',desc='Experiencia mínima de 2 años. Python'))
        r=recomendar(j,{'situacion':'Egresado','habilidades':'Python','meses_experiencia':'0'},({},0))
        self.assertLessEqual(r['puntaje'],45)
        self.assertIn('brecha',[c['estado'] for c in r['requisitos']])
    def test_aprendizaje_generaliza_y_puede_deshacerse(self):
        jobs=[self.job('a'),self.job('b','Practicante de marketing','Publicidad campañas ventas'),self.job('c')]
        positive=entrenar(jobs,{'a':'interesa','b':'no_interesa'})
        candidate=normalizar_oferta(jobs[2]); before=recomendar(candidate,{},({},0)); after=recomendar(candidate,{},positive)
        self.assertGreater(after['aprendizaje'],0);self.assertIsNone(before['puntaje'])
        self.assertEqual(entrenar(jobs,{}),({},0))
    def test_semantica_limitada_y_alias(self):
        self.assertGreater(afinidad('ingeniero de sistemas','Practicante de soporte técnico'),0.3)
        self.assertEqual(afinidad('ingeniero de sistemas','Practicante contable'),0)
    def test_mencion_incidental_no_vuelve_tecnico_un_puesto_contable(self):
        j=self.job(title='Practicante de contabilidad',desc='Usar sistemas contables y realizar pagos.')
        out=resultados([j],{}, {'fuentes':['linkedin'],'cargo':'ingeniero de sistemas'}, {},evaluar)
        self.assertEqual(out['ofertas'],[])
    def test_perfil_incompleto_no_recibe_cien_por_ciento(self):
        j=normalizar_oferta(self.job())
        r=recomendar(j,{'cargos_objetivo':'ingeniero de sistemas'},({},0))
        self.assertLessEqual(r['puntaje'],30)
    def test_no_confunde_c_con_cpp(self):
        j=normalizar_oferta(self.job(desc='JavaScript y C++'))
        r=recomendar(j,{'habilidades':'Java, C++, C#'},({},0))
        self.assertEqual(r['coincidencias'],['C++'])
if __name__=='__main__': unittest.main()
