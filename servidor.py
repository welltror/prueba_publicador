
import subprocess
from pathlib import Path


def iniciar_servidor(evento_detener):
    """Inicia el servidor web de Quarto y controla su cierre."""

    proyecto = Path.cwd()
    archivo_html = proyecto / "presentacion.html"
    archivo_qmd = proyecto / "presentacion.qmd"

    # 1. Verificar archivos necesarios
    if not archivo_html.is_file():
        raise FileNotFoundError(
            "No existe presentacion.html"
        )

    if archivo_html.stat().st_size == 0:
        raise RuntimeError(
            "La presentacion HTML esta vacia"
        )

    if not archivo_qmd.is_file():
        raise FileNotFoundError(
            "No existe presentacion.qmd"
        )

    # 2. Configurar el servidor
    puerto = 8765

    comando = [
        "quarto",
        "preview",
        "presentacion.qmd",
        "--no-browser",
        "--no-watch-inputs",
        "--host",
        "0.0.0.0",
        "--port",
        str(puerto)
    ]

    print("[SERVIDOR] Iniciando Quarto...")

    # 3. Iniciar proceso externo
    try:
        proceso = subprocess.Popen(
            comando,
            cwd=proyecto
        )

    except FileNotFoundError as error:
        raise RuntimeError(
            "No se encontro el ejecutable de Quarto"
        ) from error

    print(f"[SERVIDOR] Puerto solicitado: {puerto}")
    print("[SERVIDOR] Esperando señal de finalizacion...")

    # 4. Mantener activo y supervisar el proceso
    try:
        while not evento_detener.wait(timeout=0.5):

            if proceso.poll() is not None:
                raise RuntimeError(
                    "El servidor Quarto finalizo inesperadamente. "
                    f"Codigo: {proceso.returncode}"
                )

    finally:
        # 5. Detener el servidor de forma controlada
        if proceso.poll() is None:
            print("[SERVIDOR] Deteniendo servidor...")

            proceso.terminate()

            try:
                proceso.wait(timeout=5)

            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait()

        print("[SERVIDOR] Proceso finalizado.")
