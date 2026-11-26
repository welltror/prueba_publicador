import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def _ejecutar_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Git no esta instalado o no esta en PATH.") from error
    except subprocess.CalledProcessError as error:
        detalle = (error.stderr or error.stdout or str(error)).strip()
        raise RuntimeError(f"Error en comando git ({' '.join(args)}): {detalle}") from error


def publicar_presentacion(
    archivo_html: str = "presentacion.html",
    carpeta_docs: str = "docs",
    rama: str = "main",
    hacer_push: bool = True,
) -> str:
    """
    Hilo 4: Copia presentacion.html y recursos auxiliares de Quarto/Reveal.js
    hacia la carpeta de GitHub Pages (por defecto docs/) y publica mediante Git.
    """
    base_dir = Path(__file__).resolve().parent
    origen_html = base_dir / archivo_html

    if not origen_html.is_file():
        raise FileNotFoundError(f"No existe '{origen_html.name}' para publicar.")

    if origen_html.stat().st_size == 0:
        raise RuntimeError(f"El archivo '{origen_html.name}' esta vacio.")

    print("[PUBLICADOR] Preparando archivos para GitHub Pages...")

    destino_docs = base_dir / carpeta_docs
    destino_docs.mkdir(parents=True, exist_ok=True)

    # En GitHub Pages sirviendo desde /docs, index.html es la entrada principal
    destino_html = destino_docs / "index.html"
    shutil.copy2(origen_html, destino_html)

    # Copiar carpetas auxiliares generadas por Quarto/Reveal.js si existen
    base_stem = origen_html.stem
    for carpeta_aux in (f"{base_stem}_files", "site_libs"):
        origen_aux = base_dir / carpeta_aux
        destino_aux = destino_docs / carpeta_aux

        if origen_aux.is_dir():
            if destino_aux.exists():
                shutil.rmtree(destino_aux)
            shutil.copytree(origen_aux, destino_aux)
        elif destino_aux.exists():
            shutil.rmtree(destino_aux)

    print(f"[PUBLICADOR] Archivos copiados a '{carpeta_docs}/index.html'.")

    if not hacer_push:
        print("[PUBLICADOR] hacer_push=False: publicacion local preparada sin 'git push'.")
        return str(destino_html)

    # Verificar repositorio Git y publicar solo si hay cambios en docs/
    _ejecutar_git(["rev-parse", "--is-inside-work-tree"], cwd=base_dir)
    _ejecutar_git(["add", carpeta_docs], cwd=base_dir)

    estado_git = _ejecutar_git(
        ["status", "--porcelain", carpeta_docs], cwd=base_dir
    ).stdout.strip()

    if not estado_git:
        print(f"[PUBLICADOR] Sin cambios nuevos en '{carpeta_docs}/'. Nada que publicar.")
        return str(destino_html)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_commit = f"Publicar presentacion ShellDoc Web ({timestamp})"
    _ejecutar_git(["commit", "-m", mensaje_commit], cwd=base_dir)
    _ejecutar_git(["push", "origin", rama], cwd=base_dir)

    print(f"[PUBLICADOR] Publicacion completada en 'origin/{rama}' ({carpeta_docs}/).")
    return str(destino_html)
