# ChambaMatch Perú · Peru Job Finder

**Buscador de empleos y prácticas en Perú con filtros personales, comparación de habilidades y revisión de fechas.**

Buscar trabajo suele implicar abrir varias páginas, leer requisitos repetidos y descubrir demasiado tarde que una convocatoria ya cerró. ChambaMatch Perú nació para reunir esas tareas en una app local: encontrar oportunidades, compararlas con tu perfil y decidir cuáles vale la pena revisar.

La idea es que puedas buscar según tus preferencias, ver cuánto tiempo lleva publicado un anuncio cuando la fuente lo informa y conocer su plazo para postular. El proyecto está en una primera versión funcional: conecta fuentes reales y ofrece una comparación básica de habilidades, con sus límites visibles.

## Fuentes de empleo

- [Convocatorias de Trabajo](https://www.convocatoriasdetrabajo.com/): convocatorias y vacantes del sector público.
- [Prácticas.pe](https://www.practicas.pe/): oportunidades de prácticas profesionales y preprofesionales.
- [LinkedIn](https://www.linkedin.com/jobs/): búsqueda pública mediante el conector [JobSpy](https://github.com/speedyapply/JobSpy).
- Ofertas que añadas manualmente pegando su descripción y enlace.

Los conectores peruanos revisan hasta **12 vacantes del listado principal por búsqueda**, siguiendo los enlaces a vacantes individuales cuando están disponibles. Esta versión no recorre todas las categorías ni todas las páginas de los portales.

## Qué puedes hacer

- Guardar un perfil con carrera, situación académica, habilidades y experiencia.
- Guardar tus preferencias y volver a utilizarlas en futuras búsquedas.
- Filtrar por cargo o palabras clave, ubicación, modalidad, tipo de oportunidad y fuente.
- Elegir anuncios de las últimas 24 horas, 3, 7, 14 o 30 días.
- Filtrar por sueldo mínimo mensual en soles cuando la oferta tiene datos comparables.
- Decidir si incluyes ofertas con fechas, ubicación, modalidad o sueldo desconocidos.
- Ocultar anuncios vencidos o cerrados y ordenar por antigüedad, próximo cierre o coincidencia de habilidades.
- Leer los requisitos y abrir el anuncio original para postular por el medio indicado.

## Cómo interpreta las ofertas

La app busca coincidencias textuales entre las habilidades que declaraste y la descripción del puesto. Por ejemplo, si registras Excel y Python, muestra cuáles aparecen en el anuncio. El porcentaje representa la proporción de tus habilidades mencionadas: **no indica la probabilidad de contratación ni confirma que cumplas todos los requisitos**.

La carrera, los años de experiencia, los idiomas, el ciclo académico y los requisitos obligatorios se guardan o pueden revisarse en la descripción, pero aún no se validan automáticamente contra tu perfil.

Para las fechas, la app distingue la publicación, la primera detección y el cierre cuando esos datos están disponibles. Si una fuente no indica cuándo publicó la oferta, muestra una fecha desconocida; no utiliza el momento de detección como publicación. Calcula el vencimiento en la zona horaria de Lima y toma en cuenta la hora de cierre cuando consigue extraerla. Si solo hay una fecha de cierre, la considera hasta el final de ese día.

## Instalar y ejecutar

Necesitas Python 3.10 o superior. La versión inicial se probó con Python 3.14 en macOS.

```sh
git clone git@github.com:HEYLER1/peru-job-finder.git
cd peru-job-finder
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-linkedin.txt
python app.py
```

Abre **http://127.0.0.1:8765** en tu navegador.

Si solo quieres usar los portales peruanos y la importación manual, instala `requirements.txt` en lugar de `requirements-linkedin.txt`.

En Windows, crea el entorno con `py -m venv .venv` y actívalo con `.venv\Scripts\Activate.ps1` desde PowerShell. Después ejecuta los mismos pasos de instalación y arranque con `python`.

## Primer uso

1. Abre **Editar mi perfil**, escribe tus habilidades separadas por comas y guarda tus datos.
2. Configura cargo, ubicación y los demás filtros en **Mis preferencias**.
3. Pulsa **Guardar preferencias** para conservar tu selección en este equipo.
4. Pulsa **Buscar en las fuentes**. La app mostrará los resultados y cualquier problema al consultar una fuente.
5. Revisa la descripción, los requisitos y el plazo en el anuncio original antes de postular.

También puedes usar **Añadir oferta** para pegar una descripción y comparar una vacante que encontraste por tu cuenta.

## Datos locales

El perfil, las preferencias y las ofertas se almacenan en `data/app.json`. Ese archivo, el entorno de Python y las capturas locales están excluidos del repositorio.

La búsqueda envía las palabras clave y la ubicación a las fuentes correspondientes. Esta versión no envía el contenido de tu perfil a un servicio de inteligencia artificial. El servidor se inicia en `127.0.0.1`, para uso local; no incluye autenticación para un despliegue público.

## Estado y próximos pasos

Esta versión ya permite consultar fuentes, importar ofertas, guardar preferencias, filtrar resultados y revisar antigüedad y vencimiento. Queda pendiente:

- Ampliar la búsqueda a más páginas y categorías de los portales peruanos.
- Importar un CV en PDF o Word y permitir corregir los datos extraídos.
- Comparar requisitos obligatorios y deseables con evidencia de experiencia, formación y habilidades.
- Mejorar la extracción de sueldo, modalidad y fechas en distintos formatos.
- Leer las bases y cronogramas de las convocatorias cuando sean necesarios.

Los portales pueden cambiar su estructura, bloquear solicitudes o mostrar información incompleta. La app muestra avisos cuando una consulta falla; una búsqueda sin resultados no demuestra que no existan oportunidades en todo el portal.

## Tecnología y pruebas

Python, Requests, HTMLParser y una interfaz en HTML, CSS y JavaScript. LinkedIn utiliza JobSpy como dependencia opcional. La app no necesita una clave de IA para funcionar.

```sh
python -m unittest discover -s tests
```

Las pruebas cubren fechas peruanas, vencimiento por día y hora, fechas desconocidas, extracción de sueldo, exclusión de texto relacionado y coincidencias de habilidades sin confundir subcadenas.

## Referencias del proyecto

La investigación inicial está en [REFERENCIAS.md](REFERENCIAS.md). Tomamos como referencias conceptuales los flujos de JobSync, el conector JobSpy y los enfoques de Resume Matcher y AI Resume Matcher. El código de la app local se desarrolló en este proyecto; las referencias no implican que todas sus funciones estén implementadas aquí.

**Palabras clave:** buscador de empleo Perú, prácticas profesionales, prácticas preprofesionales, Peru job finder, job search, LinkedIn, resume matching, Python.
