import sys
from coordinador import ejecutar_sistema


def main():
    exito = ejecutar_sistema()

    if exito:
        print("[MAIN] Proceso finalizado sin errores.")
        sys.exit(0)
    else:
        print("[MAIN] El proceso finalizo con errores.")
        sys.exit(1)


if __name__ == "__main__":
    main()
