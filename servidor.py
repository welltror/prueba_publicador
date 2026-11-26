import subprocess
from pathlib import Path


def iniciar_servidor(evento_detener, puerto: int = 8765):
    """Inicia el servidor web de Quarto y controla su cierre."""

    base_dir = Path(__file__).resolve().parent
    archivo_html = base_dir / "presentacion.html"
    archivo_qmd = base_dir / "presentacion.qmd"

    # 1. Verificar archivos necesarios
    if not archivo_html.is_file():
        raise FileNotFoundError("No existe presentacion.html")

    if archivo_html.stat().st_size == 0:
        raise RuntimeError("La presentacion HTML esta vacia")

    if not archivo_qmd.is_file():
        raise FileNotFoundError("No existe presentacion.qmd")

    comando = [
        "quarto",
        "preview",
        archivo_qmd.name,
        "--no-browser",
        "--no-watch-inputs",
        "--host",
        "0.0.0.0",
        "--port",
        str(puerto),
    ]

    print("[SERVIDOR] Iniciando Quarto...")

    # 2. Iniciar proceso externo
    try:
        proceso = subprocess.Popen(
            comando,
            cwd=str(base_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "No se encontro el ejecutable de Quarto"
        ) from error

    print(f"[SERVIDOR] Puerto solicitado: {puerto}")
    print("[SERVIDOR] Esperando señal de finalizacion...")

    # 3. Mantener activo y supervisar el proceso
    try:
        while not evento_detener.wait(timeout=0.5):
            codigo_salida = proceso.poll()
            if codigo_salida is not None:
                salida_err = ""
                if proceso.stderr is not None:
                    salida_err = proceso.stderr.read().strip()
                detalle = f"\nDetalle: {salida_err}" if salida_err else ""
                raise RuntimeError(
                    "El servidor Quarto finalizo inesperadamente. "
                    f"Codigo: {codigo_salida}{detalle}"
                )
    finally:
        # 4. Detener el servidor de forma controlada
        if proceso.poll() is None:
            print("[SERVIDOR] Deteniendo servidor...")
            proceso.terminate()
            try:
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait()

        if proceso.stderr is not None:
            proceso.stderr.close()

        print("[SERVIDOR] Proceso finalizado.")
