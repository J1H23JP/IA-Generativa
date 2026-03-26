"""
Script para ejecutar el pipeline ETL de ingesta de documentos.

Uso:
  python scripts/run_etl.py           # Ingesta incremental
  python scripts/run_etl.py --reset   # Borra vectorstore y re-indexa todo
"""
import sys
import os

# Asegurar que el root del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.ingest import run_etl

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    if reset:
        print("MODO RESET: Se eliminará el vectorstore existente.\n")
    run_etl(reset=reset)
