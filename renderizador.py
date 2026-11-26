
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def renderizar_presentacion():
    """Convierte presentacion.qmd en HTML utilizando Quarto."""

    proyecto = Path.cwd()
    archivo_qmd = proyecto / "presentacion.qmd"
    archivo_html = proyecto / "presentacion.html"

    # 1. Verificar el archivo de entrada
    if not archivo_qmd.is_file():
        raise FileNotFoundError(
            "No se encontro presentacion.qmd"
        )

    if archivo_qmd.stat().st_size == 0:
        raise ValueError("El archivo QMD esta vacio")

    print("[RENDERIZADOR] Preparando renderizacion...")

    # 2. Crear un directorio temporal
    with tempfile.TemporaryDirectory(
        prefix=".shelldoc_",
        dir=proyecto
    ) as directorio:

        temporal = Path(directorio)

        shutil.copy2(
            archivo_qmd,
            temporal / "presentacion.qmd"
        )

        # 3. Ejecutar Quarto
        comando = [
            "quarto",
            "render",
            "presentacion.qmd",
            "--to",
            "revealjs"
        ]

        try:
            resultado = subprocess.run(
                comando,
                cwd=temporal,
                capture_output=True,
                text=True,
                check=True,
                timeout=120
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
            detalle = error.stderr or error.stdout or str(error)
            raise RuntimeError(
                f"Error al renderizar con Quarto:\n{detalle}"
            ) from error

        # 4. Verificar el HTML temporal
        html_temporal = temporal / "presentacion.html"

        if not html_temporal.is_file():
            raise FileNotFoundError(
                "Quarto no genero presentacion.html"
            )

        if html_temporal.stat().st_size == 0:
            raise RuntimeError(
                "El HTML generado esta vacio"
            )

        # 5. Copiar recursos auxiliares de Reveal.js
        for carpeta in ("presentacion_files", "site_libs"):
            origen = temporal / carpeta
            destino = proyecto / carpeta

            if origen.is_dir():
                shutil.copytree(
                    origen,
                    destino,
                    dirs_exist_ok=True
                )

        # 6. Reemplazar el HTML definitivo
        os.replace(html_temporal, archivo_html)

    print("[RENDERIZADOR] Renderizacion exitosa.")
    print(f"[RENDERIZADOR] Archivo: {archivo_html}")

    return str(archivo_html)
