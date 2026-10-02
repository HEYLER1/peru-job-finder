# Referencias para la app de empleo

Investigación inicial: 2 de octubre de 2026. Se revisó documentación pública; no se instalaron ni probaron estos proyectos.

## Repositorios seleccionados

| Repositorio | Qué aporta | Idea para nuestra app |
| --- | --- | --- |
| [JobSync](https://github.com/Gsync/jobsync) | Gestión de postulaciones, importación de CV, comparación con ofertas y descubrimiento mediante APIs de bolsas de empresas. Licencia MIT. | Panel de ofertas recomendadas, perfil editable y seguimiento de postulaciones. |
| [JobSpy](https://github.com/speedyapply/JobSpy) | Biblioteca Python que reúne ofertas de LinkedIn, Indeed y otras fuentes. Licencia MIT. | Adaptadores de fuentes que conviertan las ofertas a nuestro modelo `Oferta`. |
| [Resume Matcher](https://github.com/srbhr/Resume-Matcher) | CV maestro, análisis de coincidencias y adaptación del CV a una oferta; modelos locales o remotos. Licencia Apache-2.0. | Perfil único y explicación de coincidencias; adaptación del CV como etapa posterior. |
| [AI Resume Matcher](https://github.com/Jismeet/AI-Resume-Matcher) | Ranking híbrido con habilidades, similitud textual y semántica, experiencia y educación. | Evaluación por dimensiones y lista de habilidades presentes y faltantes. |

JobSpy documenta soporte para Perú en Indeed y búsquedas globales por ubicación en LinkedIn. También documenta bloqueos y límites de solicitudes; el soporte declarado no confirma que una búsqueda funcione hoy. Antes de integrarlo, probar consultas pequeñas y conservar importación manual como alternativa.

## Propuesta de primera versión

### Fuentes prioritarias y antigüedad

Por solicitud del usuario, buscar en estas tres fuentes:

- [Convocatorias de Trabajo](https://www.convocatoriasdetrabajo.com/).
- [Prácticas.pe](https://www.practicas.pe/).
- LinkedIn, evaluando JobSpy como conector.

Crear un adaptador independiente para cada fuente y unificar los resultados. Revisar el detalle de cada anuncio y sus bases cuando sean necesarias para conocer los requisitos completos. En prácticas, comparar carrera, ciclo, condición de estudiante/egresado y tiempo desde el egreso.

Registrar por separado fecha de publicación, precisión de esa fecha (exacta/aproximada/desconocida), fecha de primera detección, fecha de última revisión, inicio y cierre de postulaciones (incluida hora si existe), estado declarado por la fuente y enlace original. Calcular antigüedad y tiempo restante usando America/Lima para fuentes peruanas. No presentar la fecha de primera detección como fecha de publicación ni usar la fecha del buscador como prueba de antigüedad.

Mostrar filtros de últimas 24 horas, 3, 7, 14 y 30 días, además de anuncios sin fecha conocida. Mostrar estados: próxima apertura, en plazo, vencida, cerrada por la fuente o vigencia desconocida. Si hay discrepancias, señalarla y revisar el cronograma original. Ocultar vencidas por defecto, conservándolas para consulta. Separar compatibilidad, antigüedad y urgencia; permitir ordenar por cada una.

En resultados indexados de Prácticas.pe se observó una etiqueta «Vigente» junto a un plazo ya pasado al 2 de octubre de 2026. Esto puede deberse a una copia desactualizada: la app debe consultar la página y calcular el plazo, sin depender únicamente de la etiqueta o del buscador. Ejemplo: https://www.practicas.pe/oferta-convocatoria-011-practicante-centro-estudios-constitucionales-tribunal-constitucional-lima-69538.html

1. Cargar un CV o completar un perfil: experiencia por cargo, habilidades, estudios, idiomas y preferencias.
2. Revisar y corregir los datos extraídos antes de utilizarlos.
3. Importar ofertas pegando su descripción o desde una fuente conectada.
4. Comparar cada requisito con evidencia del perfil y marcar: cumple, no cumple o falta información.
5. Separar requisitos obligatorios de deseables. Una coincidencia textual alta no debe ocultar un requisito obligatorio incumplido.
6. Ordenar las ofertas compatibles y permitir filtrar por ubicación, modalidad, salario, idioma y experiencia.
7. Mostrar motivos, requisitos faltantes, enlace original y estado de postulación.

La puntuación debe expresar compatibilidad estimada, no probabilidad de contratación. No inventar habilidades ni considerar cumplido un requisito sin evidencia. Los requisitos ausentes en la oferta se distinguen de los datos desconocidos del candidato.

## Dirección recomendada

Tomar JobSync como referencia del flujo, JobSpy como posible conector y AI Resume Matcher como referencia conceptual del ranking. Construir sobre los módulos Python existentes en `jobbot/modelo.py` y `jobbot/geo.py`, después de revisar su comportamiento. Empezar con comparación de perfil y ofertas importadas; conectar búsquedas reales después.

Pendiente para personalizar: CV o experiencia y habilidades, cargos objetivo, países o ciudades, modalidad e idiomas. Antes de reutilizar código, revisar la licencia del archivo y versión concretos.
