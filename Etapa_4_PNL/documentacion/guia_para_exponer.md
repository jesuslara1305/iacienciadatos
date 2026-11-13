# Explicación para exposición — Etapa 4 (PNL)

**Pregunta: ¿Por qué no usamos los CSV NASA PROMISE para PNL?**  
Porque los CSV son métricas de código y etiquetas binarias; no contienen descripciones lingüísticas de incidencias. El PNL utiliza reportes escritos como fuente complementaria, no vinculada módulo a módulo.

**Pregunta: ¿Cómo obtenemos los textos?**  
Mediante el endpoint público de issues de un repositorio de software (por defecto VS Code), filtrados por la etiqueta `bug`, excluyendo PR. Guardamos la URL de la fuente para trazabilidad y redactamos algunos patrones sensibles; si cambia GitHub usamos un CSV proporcionado con título y descripción.

**Pregunta: ¿Qué hace TF-IDF?**  
Construye una matriz numérica con importancia relativa de palabras y pares de palabras por documento, ponderando los términos frecuentes en un documento y menos frecuentes en el corpus. No es una predicción de defectos ni requiere etiquetas supervisadas.

**Pregunta: ¿Qué significa la clasificación de sentimiento?**  
Es una regla transparente sobre expresiones como `crash`, `error` o `fixed`. Estima tono lexical, no gravedad ni prioridad. Puede equivocarse en negaciones, ironía, descripciones neutrales y términos técnicos.

**Pregunta: ¿Qué NER utilizaron?**  
Reglas y expresiones regulares para sistemas operativos, tecnologías, componentes, archivos, versiones y códigos de error. A diferencia de un modelo profundo, los patrones son auditables y no requieren internet en inferencia.

**Pregunta: ¿Entrenaron un modelo de lenguaje?**  
No. La generación de informes se hace con plantillas que integran conteos y palabras destacadas. Esto está permitido siempre que se describa correctamente el mecanismo.

**Pregunta: ¿Está conectado a Machine Learning?**  
Está integrado a nivel de arquitectura de sistema y outputs, pero no existe una unión registro a registro con el modelo NASA PROMISE. El ML clasifica un módulo mediante métricas; PNL resume un reporte de texto. La interfaz puede ofrecer ambas funciones sin inventar vínculos.

**Pregunta: ¿Qué pruebas hicieron?**  
Se ejecutaron 8 pruebas automáticas sin internet y un análisis de 24 reportes sintéticos. Falta ejecutar sobre issues reales en la computadora del equipo para completar esa evidencia, y revisar manualmente una muestra real.

**Pregunta: ¿Qué entregar al responsable del prototipo?**  
La función `procesar_reporte(titulo, descripcion) -> dict` de `analizar_texto.py`, que retorna texto limpio, tokens, sentimiento, entidades, resumen y advertencia; el dashboard podrá consumir este diccionario mediante backend.
