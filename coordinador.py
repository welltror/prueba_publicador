import os
import threading
import time

semaforo_transformacion = threading.Semaphore(0)
semaforo_renderizacion = threading.Semaphore(0)
semaforo_publicacion = threading.Semaphore(0)

evento_error = threading.Event()
evento_detener = threading.Event()

bloqueo = threading.Lock()
errores = []


def registrar_error(nombre_hilo, mensaje):
    with bloqueo:
        errores.append(f"{nombre_hilo}: {mensaje}")
        print(f"[ERROR] {nombre_hilo}: {mensaje}")
        evento_error.set()


def mostrar_estado(nombre_hilo, mensaje):
    with bloqueo:
        print(f"[{nombre_hilo}] {mensaje}")


def esperar_semaforo(semaforo, nombre, quien):
    while not semaforo.acquire(timeout=0.5):
        if evento_error.is_set() or evento_detener.is_set():
            mostrar_estado(nombre, f"Espera cancelada: {quien} no completo su etapa.")
            return False

    if evento_error.is_set() or evento_detener.is_set():
        mostrar_estado(nombre, "Senal recibida, pero el sistema se esta deteniendo.")
        return False

    mostrar_estado(nombre, f"Senal recibida de {quien}.")
    return True


def _llamar_transformador():
    import transformador

    if hasattr(transformador, "transformar_sesion"):
        return transformador.transformar_sesion()
    if hasattr(transformador, "transformar_sesion_a_qmd"):
        return transformador.transformar_sesion_a_qmd()
    raise AttributeError(
        "transformador.py no define 'transformar_sesion' ni 'transformar_sesion_a_qmd'."
    )


def hilo_transformador():
    nombre = "HILO 1 - TRANSFORMADOR"
    try:
        mostrar_estado(nombre, "Iniciando transformacion...")
        _llamar_transformador()

        if evento_error.is_set():
            return

        if not os.path.isfile("presentacion.qmd"):
            raise FileNotFoundError("No se genero presentacion.qmd")

        mostrar_estado(nombre, "Transformacion completada correctamente.")
        mostrar_estado(nombre, "Liberando semaforo de transformacion (signal).")
        semaforo_transformacion.release()
    except Exception as e:
        registrar_error(nombre, str(e))


def hilo_renderizador():
    nombre = "HILO 2 - RENDERIZADOR"
    try:
        mostrar_estado(nombre, "Esperando al HILO 1 (wait)...")

        if not esperar_semaforo(semaforo_transformacion, nombre, "HILO 1"):
            return

        mostrar_estado(nombre, "Iniciando renderizacion...")

        if not os.path.isfile("presentacion.qmd"):
            raise FileNotFoundError("No existe presentacion.qmd")

        from renderizador import renderizar_presentacion

        renderizar_presentacion()

        if evento_error.is_set():
            return

        if not os.path.isfile("presentacion.html"):
            raise FileNotFoundError("No se genero presentacion.html")

        mostrar_estado(nombre, "Renderizacion completada correctamente.")
        mostrar_estado(nombre, "Liberando semaforos de renderizacion y publicacion (signal).")
        semaforo_renderizacion.release()
        semaforo_publicacion.release()
    except Exception as e:
        registrar_error(nombre, str(e))


def hilo_servidor():
    nombre = "HILO 3 - SERVIDOR"
    try:
        mostrar_estado(nombre, "Esperando al HILO 2 (wait)...")

        if not esperar_semaforo(semaforo_renderizacion, nombre, "HILO 2"):
            return

        mostrar_estado(nombre, "Iniciando servidor web...")
        from servidor import iniciar_servidor

        iniciar_servidor(evento_detener)
        mostrar_estado(nombre, "Servidor finalizado.")
    except Exception as e:
        registrar_error(nombre, str(e))


def hilo_publicador():
    nombre = "HILO 4 - PUBLICADOR"
    try:
        mostrar_estado(nombre, "Esperando al HILO 2 para publicar (wait)...")

        if not esperar_semaforo(semaforo_publicacion, nombre, "HILO 2"):
            return

        if evento_error.is_set() or evento_detener.is_set():
            mostrar_estado(nombre, "Publicacion cancelada por estado del sistema.")
            return

        if not os.path.isfile("presentacion.html"):
            raise FileNotFoundError("No existe presentacion.html para publicar.")

        mostrar_estado(nombre, "Iniciando publicacion en GitHub Pages...")
        from publicador import publicar_presentacion

        publicar_presentacion()
        mostrar_estado(nombre, "Publicacion completada correctamente.")
    except Exception as e:
        registrar_error(nombre, str(e))


def ejecutar_sistema(incluir_publicador=True):
    print("=== SHELLDOC WEB ===")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    for archivo in ("presentacion.qmd", "presentacion.html"):
        if os.path.isfile(archivo):
            os.remove(archivo)

    hilo1 = threading.Thread(target=hilo_transformador, name="HILO 1")
    hilo2 = threading.Thread(target=hilo_renderizador, name="HILO 2")
    hilo3 = threading.Thread(target=hilo_servidor, name="HILO 3")
    hilos = [hilo1, hilo2, hilo3]

    if incluir_publicador:
        hilo4 = threading.Thread(target=hilo_publicador, name="HILO 4")
        hilos.append(hilo4)

    for hilo in hilos:
        hilo.start()

    try:
        while any(hilo.is_alive() for hilo in hilos):
            if evento_error.is_set():
                evento_detener.set()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[MAIN] Interrupcion del usuario. Deteniendo el sistema...")
        evento_detener.set()

    for hilo in hilos:
        hilo.join()

    with bloqueo:
        if errores:
            print("\n=== EL SISTEMA TERMINO CON ERRORES ===")
            for error in errores:
                print(f" - {error}")
        else:
            print("\n=== EL SISTEMA TERMINO CORRECTAMENTE ===")

    return not evento_error.is_set()
