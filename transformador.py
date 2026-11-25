import re


def limpiar_linea(linea):
    # se eliminan códigos de color y formato de terminal
    linea = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", linea)
    # se eliminan secuencias ansi incompletas al final de la línea
    linea = re.sub(r"\x1B\[[0-?]*[ -/]*", "", linea)
    # se eliminan caracteres de control invisibles campana, escape, retorno y nulo
    linea = (
        linea.replace("\x07", "")  # campana
        .replace("\x1b", "")  # escape
        .replace("\r", "")  # retorno
        .replace("\x00", "")  # nulo
    )
    # se eliminan saltos de línea al final de la línea
    linea = linea.rstrip("\n")

    # se simula el borrado cuando se encuentran caracteres de retroceso
    resultado = []  # lista para caracteres finales
    for caracter in linea:  # se itera sobre cada caracter de la línea
        # se verifica si el carácter corresponde a un retroceso
        if caracter == "\x08":
            # se borra el último carácter guardado si la lista no está vacía
            if len(resultado) > 0:
                resultado.pop()  # se elimina el último carácter de la lista
        else:
            # se agrega el carácter a la lista de resultado
            resultado.append(caracter)

    # se reconstruye la línea final a partir de la lista de caracteres
    return "".join(resultado)


def escapar_caracteres(texto):
    # se escapan caracteres especiales para evitar interpretaciones erróneas en quarto o markdown
    caracteres = ["\\", "*", "_", "`", "~", "|", "<", ">", "$"]
    for caracter in caracteres:
        # se agrega una barra invertida antes del carácter especial para compatibilidad con markdown y quarto
        texto = texto.replace(caracter, "\\" + caracter)
    return texto


def leer_y_separar_sesion(ruta_sesion="session.txt"):
    # se leen las líneas del archivo de sesión de forma segura con contexto
    with open(ruta_sesion, "r", encoding="utf-8", errors="replace") as archivo:
        lineas = archivo.readlines()

    comandos = []
    comando_actual = None
    numero_comando = 0

    for linea_original in lineas:
        # se limpia cada línea antes de analizarla
        linea = limpiar_linea(linea_original)

        # se omiten las líneas automáticas de inicio y fin de script
        if linea.startswith("Script started on ") or linea.startswith("Script done on "):
            continue

        # se eliminan espacios al inicio y final de la línea
        linea_sin_espacios = linea.strip()
        es_comando = False
        texto_comando = ""

        # se verifica si la línea comienza con prompt simple de usuario
        if linea_sin_espacios.startswith("$ "):
            es_comando = True
            texto_comando = linea_sin_espacios[2:].strip()
        # se verifica si la línea comienza con prompt simple de root
        elif linea_sin_espacios.startswith("# "):
            es_comando = True
            texto_comando = linea_sin_espacios[2:].strip()
        # se verifica si contiene prompt completo con usuario y equipo seguido de signo de dólar
        elif "$ " in linea_sin_espacios and "@" in linea_sin_espacios:
            es_comando = True
            texto_comando = linea_sin_espacios.split("$ ", 1)[1].strip()
        # se verifica si contiene prompt completo con usuario y equipo seguido de numeral
        elif "# " in linea_sin_espacios and "@" in linea_sin_espacios:
            es_comando = True
            texto_comando = linea_sin_espacios.split("# ", 1)[1].strip()

        # si se identifica un comando válido, se crea un nuevo registro numerado
        if es_comando and texto_comando != "":
            numero_comando += 1
            comando_actual = {
                "numero": numero_comando,
                "comando": texto_comando,
                "salida": [],
            }
            # se agrega el nuevo comando a la lista de comandos
            comandos.append(comando_actual)
        else:
            # si no es comando y ya existe uno previo, se agrega la línea a su salida
            if comando_actual is not None:
                comando_actual["salida"].append(linea)

    # se eliminan líneas vacías sobrantes al final de cada salida
    for item in comandos:
        while len(item["salida"]) > 0 and item["salida"][-1].strip() == "":
            item["salida"].pop()

    if comandos and comandos[-1]["comando"] == "exit":
        comandos.pop()

    return comandos


def crear_contenido_qmd(comandos, titulo="ShellDoc Web"):
    # se agrega la configuración inicial de quarto reveal.js con mejor legibilidad
    contenido = [
        "---",
        f'title: "{titulo}"',
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
        # se evitan triples comillas invertidas que cierren el bloque de código antes de tiempo
        comando_limpio = item["comando"].replace("```", "` ` `")
        titulo_diapositiva = escapar_caracteres(f"Comando {numero}")

        contenido.append(f"## {titulo_diapositiva}")
        contenido.append("")
        contenido.append(f"`{comando_limpio}`")
        contenido.append("")
        contenido.append("```bash")
        contenido.append(f"$ {comando_limpio}")

        # se agregan todas las líneas de salida dentro del mismo bloque
        for linea_salida in item["salida"]:
            linea_segura = linea_salida.replace("```", "` ` `")
            contenido.append(linea_segura)

        contenido.append("```")
        contenido.append("")

    # se unen todas las líneas con salto de línea para formar el archivo qmd
    return "\n".join(contenido)


def transformar_sesion_a_qmd(ruta_sesion="session.txt", ruta_salida="presentacion.qmd"):
    # se obtienen los comandos y sus salidas desde el archivo de sesión
    comandos = leer_y_separar_sesion(ruta_sesion)

    # se lanza un error si no se detectan comandos en el archivo
    if len(comandos) == 0:
        raise ValueError("No se encontraron comandos en session.txt.")

    # se construye el texto completo de la presentación en formato qmd
    texto_qmd = crear_contenido_qmd(comandos)

    # se escribe el contenido final en el archivo de salida de forma segura
    with open(ruta_salida, "w", encoding="utf-8") as archivo_salida:
        archivo_salida.write(texto_qmd)

    # se retorna la cantidad total de comandos transformados
    return len(comandos)
