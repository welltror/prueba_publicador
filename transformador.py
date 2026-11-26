import re


def limpiar_linea(linea):
    # Se eliminan códigos de color y formato de terminal con ESC (\x1B)
    linea = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", linea)
    # Se eliminan secuencias ANSI incompletas o residuales (ej. [?2004h, [?2004l, [01;34m)
    linea = re.sub(r"\x1B\[[0-?]*[ -/]*", "", linea)
    linea = re.sub(r"\[(?:\?[0-9;]*[a-zA-Z]|[0-9;]*m)", "", linea)
    # Se eliminan caracteres de control invisibles (campana, escape, retorno de carro y nulo)
    linea = (
        linea.replace("\x07", "")
        .replace("\x1b", "")
        .replace("\r", "")
        .replace("\x00", "")
    )
    # Se eliminan saltos de línea al final de la línea
    linea = linea.rstrip("\n")

    # Se simula el borrado cuando se encuentran caracteres de retroceso (\x08 o \x7f)
    resultado = []
    for caracter in linea:
        if caracter in ("\x08", "\x7f"):
            if len(resultado) > 0:
                resultado.pop()
        else:
            resultado.append(caracter)

    return "".join(resultado)


def escapar_caracteres(texto):
    # Se escapan caracteres especiales para texto normal fuera de bloques de código
    caracteres = ["\\", "*", "_", "`", "~", "|", "<", ">", "$"]
    for caracter in caracteres:
        texto = texto.replace(caracter, "\\" + caracter)
    return texto


def leer_y_separar_sesion(ruta_sesion="session.txt"):
    # Se leen las líneas del archivo de sesión de forma segura
    with open(ruta_sesion, "r", encoding="utf-8", errors="replace") as archivo:
        lineas = archivo.readlines()

    comandos = []
    comando_actual = None
    numero_comando = 0

    for linea_original in lineas:
        linea = limpiar_linea(linea_original)

        # Se omiten las líneas automáticas de inicio y fin de 'script'
        if linea.startswith("Script started on ") or linea.startswith("Script done on "):
            continue

        linea_sin_espacios = linea.strip()
        es_comando = False
        texto_comando = ""

        if linea_sin_espacios.startswith("$ "):
            es_comando = True
            texto_comando = linea_sin_espacios[2:].strip()
        elif linea_sin_espacios.startswith("# "):
            es_comando = True
            texto_comando = linea_sin_espacios[2:].strip()
        elif "$ " in linea_sin_espacios and "@" in linea_sin_espacios:
            es_comando = True
            texto_comando = linea_sin_espacios.split("$ ", 1)[1].strip()
        elif "# " in linea_sin_espacios and "@" in linea_sin_espacios:
            es_comando = True
            texto_comando = linea_sin_espacios.split("# ", 1)[1].strip()

        if es_comando and texto_comando != "":
            if texto_comando == "exit":
                comando_actual = None
                continue

            numero_comando += 1
            comando_actual = {
                "numero": numero_comando,
                "comando": texto_comando,
                "salida": [],
            }
            comandos.append(comando_actual)
        else:
            if comando_actual is not None:
                comando_actual["salida"].append(linea)

    # Se eliminan líneas vacías sobrantes al inicio y final de cada salida
    for item in comandos:
        while len(item["salida"]) > 0 and item["salida"][0].strip() == "":
            item["salida"].pop(0)
        while len(item["salida"]) > 0 and item["salida"][-1].strip() == "":
            item["salida"].pop()

    return comandos


def crear_contenido_qmd(comandos, titulo="ShellDoc Web"):
    titulo_seguro = titulo.replace('"', '\\"')
    contenido = [
        "---",
        f'title: "{titulo_seguro}"',
        "format:",
        "  revealjs:",
        "    theme: dark",
        "    highlight-style: monokai",
        "    slide-number: true",
        "    scrollable: true",
        "    center: false",
        "    transition: slide",
        "    code-line-numbers: false",
        "    width: 1280",
        "    height: 720",
        "---",
        "",
    ]

    for item in comandos:
        numero = item["numero"]
        comando_limpio = item["comando"].replace("```", "` ` `")
        titulo_diapositiva = escapar_caracteres(f"Comando {numero}")

        contenido.append(f"## {titulo_diapositiva}")
        contenido.append("")
        contenido.append("```bash")
        contenido.append(f"$ {comando_limpio}")

        for linea_salida in item["salida"]:
            linea_segura = linea_salida.replace("```", "` ` `")
            contenido.append(linea_segura)

        contenido.append("```")
        contenido.append("")

    return "\n".join(contenido)


def transformar_sesion_a_qmd(ruta_sesion="session.txt", ruta_salida="presentacion.qmd"):
    comandos = leer_y_separar_sesion(ruta_sesion)

    if len(comandos) == 0:
        raise ValueError("No se encontraron comandos en session.txt.")

    texto_qmd = crear_contenido_qmd(comandos)

    with open(ruta_salida, "w", encoding="utf-8") as archivo_salida:
        archivo_salida.write(texto_qmd)

    return len(comandos)


def transformar_sesion(ruta_sesion="session.txt", ruta_salida="presentacion.qmd"):
    # Alias compatible con la llamada sin argumentos de coordinador.py
    return transformar_sesion_a_qmd(ruta_sesion=ruta_sesion, ruta_salida=ruta_salida)
