import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.ingest import run_etl

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    if reset:
        print("MODO RESET: Se eliminará el vectorstore existente.\n")
    run_etl(reset=reset)
