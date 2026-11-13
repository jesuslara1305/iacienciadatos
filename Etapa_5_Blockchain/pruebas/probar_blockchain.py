import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blockchain_core import cadena_nueva, agregar, validar, guardar, cargar, comparar_archivo, registro_desde_csv

class PruebasCadena(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz=Path(self.tmp.name)
        self.csv=self.raiz/'predicciones.csv'
        self.csv.write_text('prediccion,interpretacion\n1,Posible defecto\n0,Sin defecto previsto\n',encoding='utf-8')
        self.cadena=cadena_nueva()
        agregar(self.cadena,registro_desde_csv(self.csv))

    def test_génesis_y_registro_validos(self):
        self.assertEqual([],validar(self.cadena))
        self.assertEqual(2,len(self.cadena['bloques']))

    def test_guardado_carga_y_comparacion(self):
        ruta=self.raiz/'cadena.json';guardar(ruta,self.cadena)
        self.assertTrue(comparar_archivo(cargar(ruta),self.csv)['integro'])

    def test_manipulacion_contenido_detectada(self):
        copia=copy.deepcopy(self.cadena)
        copia['bloques'][1]['dato']['predicciones'][0]['prediccion']='0'
        self.assertTrue(validar(copia))

    def test_manipulacion_encadenado_detectada(self):
        copia=copy.deepcopy(self.cadena)
        copia['bloques'][1]['hash_anterior']='0'*64
        self.assertTrue(validar(copia))

    def test_manipulacion_fuente_detectada(self):
        self.csv.write_text('prediccion,interpretacion\n0,Posible defecto\n0,Sin defecto previsto\n',encoding='utf-8')
        self.assertFalse(comparar_archivo(self.cadena,self.csv)['integro'])

    def test_registro_no_acepta_cadena_corrupta(self):
        self.cadena['bloques'][1]['dato']['cantidad_predicciones']=999
        with self.assertRaises(ValueError):
            agregar(self.cadena,{'tipo':'prediccion','valor':1})

    def test_csv_etiqueta_invalida(self):
        self.csv.write_text('prediccion\n2\n',encoding='utf-8')
        with self.assertRaises(ValueError):
            registro_desde_csv(self.csv)

    def test_agregar_varios_bloques(self):
        agregar(self.cadena,{'tipo':'prediccion','prediccion':1})
        self.assertEqual(3,len(self.cadena['bloques']))
        self.assertEqual([],validar(self.cadena))

if __name__=='__main__':unittest.main()
