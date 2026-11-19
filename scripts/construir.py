"""Regenera los datos y copia la web estática lista para alojar en dist/."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Ejecuta ETL, análisis y copia de la web en ese orden. Si falla un paso, se detiene.
    subprocess.run([sys.executable, str(ROOT / "scripts/etl.py"), *sys.argv[1:]], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/analisis.py")], check=True)
    shutil.copytree(ROOT / "web", ROOT / "dist", dirs_exist_ok=True)
    print("Web construida en dist/.")


if __name__ == "__main__":
    main()
