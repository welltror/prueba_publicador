import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def _ejecutar_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=True,
    )


def publicar_presentacion(
    archivo_html: str = "presentacion.html",
    carpeta_docs: str = "docs",
    rama: str = "main",
    hacer_push: bool = True,
) -> str:
    """
    Hilo 4: Copia presentacion.html y recursos de Quarto (presentacion_files, site_libs)
    hacia la carpeta de GitHub Pages (por defecto docs/) y publica mediante Git.
    """
    proyecto = Path.cwd()
    origen_html = proyecto / archivo_html

    if not origen_html.is_file():
        raise FileNotFoundError(f"No existe '{archivo_html}' para publicar.")

    if origen_html.stat().st_size == 0:
        raise RuntimeError(f"El archivo '{archivo_html}' esta vacio.")

    print("[PUBLICADOR] Preparando archivos para GitHub Pages...")

    destino_docs = proyecto / carpeta_docs
    destino_docs.mkdir(parents=True, exist_ok=True)

    # En GitHub Pages con carpeta /docs, index.html es la entrada principal del sitio
    destino_html = destino_docs / "index.html"
    shutil.copy2(origen_html, destino_html)

    # Copiar carpetas auxiliares generadas por Quarto/Reveal.js si existen
    base_nombre = origen_html.stem
    for carpeta_aux in (f"{base_nombre}_files", "site_libs"):
        origen_aux = proyecto / carpeta_aux
        if origen_aux.is_dir():
            destino_aux = destino_docs / carpeta_aux
            if destino_aux.exists():
                shutil.rmtree(destino_aux)
            shutil.copytree(origen_aux, destino_aux)

    print(f"[PUBLICADOR] Archivos copiados a '{carpeta_docs}/index.html'.")

    if not hacer_push:
        print("[PUBLICADOR] hacer_push=False: publicacion local preparada sin 'git push'.")
        return str(destino_html)

    # Verificar que el directorio sea un repositorio Git válido
    _ejecutar_git(["rev-parse", "--is-inside-work-tree"], cwd=proyecto)

    _ejecutar_git(["add", carpeta_docs], cwd=proyecto)
    estado_git = _ejecutar_git(["status", "--porcelain", carpeta_docs], cwd=proyecto).stdout.strip()

    if not estado_git:
        print(f"[PUBLICADOR] Sin cambios nuevos en '{carpeta_docs}/'. Nada que publicar.")
        return str(destino_html)

    mensaje_commit = f"Publicar presentacion ShellDoc Web ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    _ejecutar_git(["commit", "-m", mensaje_commit], cwd=proyecto)
    _ejecutar_git(["push", "origin", rama], cwd=proyecto)

    print(f"[PUBLICADOR] Publicacion completada en 'origin/{rama}' ({carpeta_docs}/).")
    return str(destino_html)
