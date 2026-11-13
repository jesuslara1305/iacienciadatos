"""Pruebas locales sin internet. Ejecutar desde cualquier directorio."""
import csv
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pnl_core import limpiar_texto, tokens, sentimiento_heuristico, extraer_entidades
from analizar_texto import procesar_reporte
from analizar_pnl import analizar


class PruebasPNL(unittest.TestCase):
    def test_limpieza_y_datos_sensibles(self):
        x = limpiar_texto("**Error** para test@example.com en [sitio](https://test.org)  \n")
        self.assertIn("[CORREO_OCULTO]", x)
        self.assertNotIn("test@example.com", x)
        self.assertNotIn("https://", x)

    def test_tokenizacion(self):
        self.assertIn("python", tokens("Python crashes while debugging."))

    def test_negatividad_tecnica(self):
        self.assertEqual(sentimiento_heuristico("Application crashes with exception")['sentimiento'], 'negativo')

    def test_positividad_tecnica(self):
        self.assertEqual(sentimiento_heuristico("Bug fixed and tests passed successfully")['sentimiento'], 'positivo')

    def test_entidades(self):
        ents = extraer_entidades("Windows 11 Python 3.12 fails in main.py: HTTP 500")
        tipos = {x['tipo'] for x in ents}
        for k in ('SISTEMA_OPERATIVO','TECNOLOGIA','VERSION','CODIGO_ERROR','ARCHIVO'):
            self.assertIn(k, tipos)

    def test_analizar_reporte_individual(self):
        r = procesar_reporte("Terminal crashes", "Windows 11 error E1204 in app.py")
        self.assertIn('sentimiento', r)
        self.assertIn('entidades', r)
        self.assertIn('reporte_generado', r)

    def test_integracion_corpus_sintetico(self):
        with tempfile.TemporaryDirectory() as d:
            info = analizar(ROOT / 'ejemplos' / 'reportes_sinteticos.csv', Path(d))
            self.assertEqual(info['filas_analizadas'], 24)
            self.assertTrue(info['ejemplo_simulado'])
            self.assertEqual(info['tfidf_dimensiones'][0], 24)
            self.assertTrue((Path(d) / 'reportes_analizados.csv').exists())
            self.assertTrue((Path(d) / 'distribucion_sentimiento.png').exists())

    def test_no_permite_csv_vacio(self):
        with tempfile.TemporaryDirectory() as d:
            entrada = Path(d) / 'empty.csv'
            entrada.write_text('titulo,descripcion\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                analizar(entrada, Path(d) / 'salida')


if __name__ == '__main__':
    unittest.main(verbosity=2)
