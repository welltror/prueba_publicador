import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def renderizar_presentacion(
    archivo_qmd_nombre: str = "presentacion.qmd",
    archivo_html_nombre: str = "presentacion.html",
) -> str:
    """Convierte presentacion.qmd en HTML utilizando Quarto."""

    base_dir = Path(__file__).resolve().parent
    archivo_qmd = base_dir / archivo_qmd_nombre
    archivo_html = base_dir / archivo_html_nombre

    # 1. Verificar el archivo de entrada
    if not archivo_qmd.is_file():
        raise FileNotFoundError(f"No se encontro {archivo_qmd.name}")

    if archivo_qmd.stat().st_size == 0:
        raise ValueError(f"El archivo {archivo_qmd.name} esta vacio")

    print("[RENDERIZADOR] Preparando renderizacion...")

    # 2. Crear un directorio temporal dentro del proyecto
    with tempfile.TemporaryDirectory(
        prefix=".shelldoc_",
        dir=base_dir,
    ) as directorio:
        temporal = Path(directorio)
        qmd_temporal = temporal / archivo_qmd.name
        shutil.copy2(archivo_qmd, qmd_temporal)

        # 3. Ejecutar Quarto
        comando = [
            "quarto",
            "render",
            qmd_temporal.name,
            "--to",
            "revealjs",
        ]

        try:
            subprocess.run(
                comando,
                cwd=temporal,
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "Quarto no esta instalado o no esta en PATH"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                "Quarto excedio el tiempo limite"
            ) from error
        except subprocess.CalledProcessError as error:
            detalle = (error.stderr or error.stdout or str(error)).strip()
            raise RuntimeError(
                f"Error al renderizar con Quarto:\n{detalle}"
            ) from error

        # 4. Verificar el HTML temporal
        html_temporal = temporal / archivo_html.name

        if not html_temporal.is_file():
            raise FileNotFoundError(f"Quarto no genero {archivo_html.name}")

        if html_temporal.stat().st_size == 0:
            raise RuntimeError("El HTML generado esta vacio")

        # 5. Copiar recursos auxiliares de Reveal.js
        base_stem = archivo_html.stem
        for carpeta in (f"{base_stem}_files", "site_libs"):
            origen = temporal / carpeta
            destino = base_dir / carpeta

            if origen.is_dir():
                if destino.exists():
                    shutil.rmtree(destino)
                shutil.copytree(origen, destino)

        # 6. Reemplazar el HTML definitivo de forma segura
        shutil.move(str(html_temporal), str(archivo_html))

    print("[RENDERIZADOR] Renderizacion exitosa.")
    print(f"[RENDERIZADOR] Archivo: {archivo_html}")

    return str(archivo_html)
