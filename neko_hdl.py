from deltachat2 import MsgData, events
from deltabot_cli import BotCli
import requests
from bs4 import BeautifulSoup
import os
import zipfile
import py7zr
import re
cli = BotCli("Hdl")
imagen_descargada = None
def tag(bot, accid, msg, code):
    global imagen_descargada  
    print("Buscando info")
    baselink = "nhentai.net/g"
    url = f"https://{baselink}/{code}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al descargar el HTML: {e}"))
        return
    soup = BeautifulSoup(html_content, 'html.parser')
    data = {
        "title_h1": [],
        "title_h2": [],
        "gallery_id": "",
        "tags": {},
        "extra": {}
    }
    titles_h1 = soup.find_all("h1", class_="title")
    titles_h2 = soup.find_all("h2", class_="title")
    data["title_h1"] = [title.get_text(strip=True) for title in titles_h1]
    data["title_h2"] = [title.get_text(strip=True) for title in titles_h2]
    gallery_id = soup.find("h3", id="gallery_id")
    if gallery_id:
        data["gallery_id"] = gallery_id.get_text(strip=True)
    tag_containers = soup.find_all("div", class_="tag-container")
    for tag in tag_containers:
        field_name = tag.text.split(":")[0].strip()
        tags = tag.find_all("a", class_="tag")
        if tags:
            data["tags"][field_name] = [
                tag.find("span", class_="name").text.strip()
                for tag in tags
            ]
    pages = soup.find("div", class_="field-name", string="Pages:")
    if pages:
        page_tag = pages.find("a", class_="tag")
        data["extra"]["pages"] = page_tag.get_text(strip=True) if page_tag else "N/A"
    uploaded = soup.find("div", class_="field-name", string="Uploaded:")
    if uploaded:
        time_tag = uploaded.find("time")
        data["extra"]["uploaded"] = time_tag.get_text(strip=True) if time_tag else "N/A"
    page_url = f"https://{baselink}/{code}/1/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        page_response = requests.get(page_url, headers=headers)
        page_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al acceder a la página de imagen: {str(e)}"))
        return
    page_soup = BeautifulSoup(page_response.content, 'html.parser')
    img_tag = page_soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
    if not img_tag:
        bot.rpc.send_msg(accid, msg.chat_id, MsgData(text="No se encontró ninguna imagen en la página."))
        return
    img_url = img_tag['src']
    img_extension = os.path.splitext(img_url)[1]
    try:
        img_data = requests.get(img_url, headers=headers).content
        imagen_descargada = f"1{img_extension}"
        with open(imagen_descargada, 'wb') as img_file:
            img_file.write(img_data)
    except Exception as e:
        bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al descargar la imagen: {str(e)}"))
    addr = cli.get_address(bot.rpc, accid)
    message = ""
    if data["title_h1"]:
        message += "**"+{data["title_h1"]}+"**\n\n"
    #if data["title_h2"]:
        #message += "Título Original :\n" + "\n".join(data["title_h2"]) + "\n\n"
    if data["gallery_id"]:
        gallery_id = data["gallery_id"]
        message += f"[🆔{gallery_id}](mailto:{addr}?body=%2Fnh%20{code})\n"
    if data["tags"]:
        message += "🏷️Etiquetas:\n"
        for category, tags in data["tags"].items():
            message += f"{category.capitalize()}:\n"
            for tag in tags:
                tag_encoded = tag.replace(" ", "%20")
                message += f"[{tag}](mailto:{addr}?body=%2Ftagnh%20{tag_encoded}), "
    if data["extra"]:
        message += "\nℹ️Información Extra:\n"
        for key, value in data["extra"].items():
            message += f"{key.capitalize()}: {value}\n"
    return message.strip()
def tag3h(bot, accid, msg, code):
    global imagen_descargada, info
    baselink = "es.3hentai.net"
    paginas = 1  
    info_url = f"https://{baselink}/d/{code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        info_response = requests.get(info_url, headers=headers)
        info_response.raise_for_status()
        soup = BeautifulSoup(info_response.content, 'html.parser')
        title = soup.find("h1", class_="text-left font-weight-bold")
        title_text = title.get_text(strip=True) if title else "Sin título"
        gallery_id = soup.find("h3", class_="js-clipboard")
        gallery_id_text = gallery_id.find("strong").get_text(strip=True) if gallery_id else "Sin ID"
        categories = ['artists', 'groups', 'characters', 'series', 'tags']
        resultados = {cat.capitalize(): [] for cat in categories}
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith(f"https://{baselink}/"):
                for cat in categories:
                    if f"/{cat}/" in href:
                        datos = href.split(f"/{cat}/")[-1]
                        if datos not in resultados[cat.capitalize()]:
                            resultados[cat.capitalize()].append(datos)
                        break
    except requests.exceptions.RequestException as e:
        bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al acceder a la página de información: {str(e)}"))
        return
    first_page_url = f"https://{baselink}/d/{code}/1/"
    try:
        first_page_response = requests.get(first_page_url, headers=headers)
        first_page_response.raise_for_status()
        first_page_soup = BeautifulSoup(first_page_response.content, 'html.parser')
        img_tag = first_page_soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            try:
                img_data = requests.get(img_url, headers=headers).content
                imagen_descargada = f"1{img_extension}"
                with open(imagen_descargada, 'wb') as img_file:
                    img_file.write(img_data)
            except Exception as e:
                bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al descargar la imagen: {str(e)}"))
        else:
            bot.rpc.send_msg(accid, msg.chat_id, MsgData(text="No se encontró ninguna imagen en la primera página."))
    except requests.exceptions.RequestException as e:
        bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al acceder a la primera página: {str(e)}"))
    while True:
        page_url = f"https://{baselink}/d/{code}/{paginas}/"
        try:
            response = requests.get(page_url, headers=headers)
            if response.status_code == 404:  
                paginas -= 1  
                break
            paginas += 1
        except requests.exceptions.RequestException as e:
            print(f"Error al acceder a la página {paginas}: {e}")
            break
    addr = cli.get_address(bot.rpc, accid)
    series = "\n".join(resultados.get('Series', []))
    personajes = "\n".join(resultados.get('Characters', []))
    artistas = "\n".join(resultados.get('Artists', []))
    grupos = "\n".join(resultados.get('Groups', []))
    tags = " ".join(f"#[{tag}](mailto:{addr}?body=%2Ftag3h%20{tag})" for tag in resultados.get('Tags', []))
    gallery_id_text = gallery_id_text.replace("d", "")
    gallery_id_text_temp = f"[{gallery_id_text}](mailto:{addr}?body=%2F3h%20{gallery_id_text})"
    gallery_id_text = gallery_id_text_temp
    info = f"""
**{title_text}**
🆔{gallery_id_text}
🎥Series:
{series}
👥Personajes:
{personajes}
🎨Artistas:
{artistas}
🫂Grupos:
{grupos}
🏷️Tags:
{tags}
📃Páginas:
{paginas}
""".strip()
    return info
def compressfile(file_path, part_size):
    parts = []
    part_size *= 1024 * 1024  
    archive_path = f"{file_path}.7z"
    with py7zr.SevenZipFile(archive_path, 'w') as archive:
        archive.write(file_path, os.path.basename(file_path))
    try:
        with open(archive_path, 'rb') as archive:
            part_num = 1
            while True:
                part_data = archive.read(part_size)
                if not part_data:
                    break
                part_file = f"{archive_path}.{part_num:03d}"
                with open(part_file, 'wb') as part:
                    part.write(part_data)
                parts.append(part_file)
                part_num += 1
    finally:
        os.remove(file_path)
        os.remove(archive_path)
    return parts
@cli.on(events.NewMessage(command="/3h"))
def download_photos(bot, accid, event):
    msg = event.msg
    payload = event.payload
    codes = payload.split(",")  
    base_url = "es.3hentai.net/d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    print("Descargando")
    for code in codes:
        url = f"https://{base_url}/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"El código {code} es erróneo: {str(e)}"))
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        name = title_tag.text.strip() if title_tag else code
        folder_name = os.path.join("h3dl", name)
        try:
            os.makedirs(folder_name, exist_ok=True)
        except OSError as e:
            if "File name too long" in str(e):
                folder_name = folder_name[:50]
                os.makedirs(folder_name, exist_ok=True)
            else:
                bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al crear el directorio: {str(e)}"))
                continue
        page_number = 1
        while True:
            page_url = f"https://{base_url}/{code}/{page_number}/"
            try:
                response = requests.get(page_url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                if page_number == 1:
                    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al acceder a la página: {str(e)}"))
                break
            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if not img_tag:
                break
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content
            img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)
            page_number += 1
        zip_filename = os.path.join(f"{folder_name}.cbz")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
        if os.path.getsize(zip_filename) > 15 * 1024 * 1024:
            parts = compressfile(zip_filename, 15)
            for part in parts:
                bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Parte: {part}", file=part))
                os.remove(part)
        else:
            bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Archivo: {zip_filename}", file=zip_filename))
            os.remove(zip_filename)
        for file in os.listdir(folder_name):
            os.remove(os.path.join(folder_name, file))
        os.rmdir(folder_name)
@cli.on(events.NewMessage(command="/nh"))
def download_photos(bot, accid, event):
    msg = event.msg
    payload = event.payload
    codes = payload.split(",")  
    base_url = "nhentai.net/g"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    print("Descargando")
    for code in codes:
        url = f"https://{base_url}/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"El código {code} es erróneo: {str(e)}"))
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        name = title_tag.text.strip() if title_tag else code
        folder_name = os.path.join("h3dl", name)
        try:
            os.makedirs(folder_name, exist_ok=True)
        except OSError as e:
            if "File name too long" in str(e):
                folder_name = folder_name[:50]
                os.makedirs(folder_name, exist_ok=True)
            else:
                bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al crear el directorio: {str(e)}"))
                continue
        page_number = 1
        while True:
            page_url = f"https://{base_url}/{code}/{page_number}/"
            try:
                response = requests.get(page_url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                if page_number == 1:
                    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Error al acceder a la página: {str(e)}"))
                break
            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if not img_tag:
                break
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content
            img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)
            page_number += 1
        zip_filename = os.path.join(f"{folder_name}.cbz")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
        if os.path.getsize(zip_filename) > 15 * 1024 * 1024:
            parts = compressfile(zip_filename, 15)
            for part in parts:
                bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Parte: {part}", file=part))
                os.remove(part)
        else:
            bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"Archivo: {zip_filename}", file=zip_filename))
            os.remove(zip_filename)
        for file in os.listdir(folder_name):
            os.remove(os.path.join(folder_name, file))
        os.rmdir(folder_name)
@cli.on(events.NewMessage(command="/info3h"))
def download_photos(bot, accid, event):
    msg = event.msg
    payload = event.payload
    code = payload
    info = tag3h(bot, accid, msg, code)
    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"{info}", file=imagen_descargada))
    os.remove(imagen_descargada)
@cli.on(events.NewMessage(command="/infonh"))
def download_photos(bot, accid, event):
    msg = event.msg
    payload = event.payload
    code = payload
    info = tag(bot, accid, msg, code)
    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=f"{info}", file=imagen_descargada))
    os.remove(imagen_descargada)
@cli.on(events.NewMessage(command="/tag3h"))
def scan_web(bot, accid, event):
    msg = event.msg
    payload = event.payload.strip()  
    payload = payload.replace(" ", "-")  
    print(f"Escaneando")
    base = "es.3hentai.net"
    try:
        if "," in payload:
            tag, page_range = payload.split(",")
            tag = tag.strip()  
            page_range = page_range.strip()  
            if "-" in page_range:
                start_page, end_page = map(int, page_range.split("-"))
            else:
                start_page, end_page = int(page_range), int(page_range)  
        else:
            tag = payload.strip()  
            start_page, end_page = 1, 1  
        results = []
        for page in range(start_page, end_page + 1):  
            url = f"https://{base}/tags/{tag}/{page}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if "/d/" in href:
                    gallery_id = href.split("/d/")[1].split("/")[0]  
                    detail_url = f"https://{base}/d/{gallery_id}"
                    detail_response = requests.get(detail_url)
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    title = detail_soup.title.string if detail_soup.title else "Sin título"
                    addr = cli.get_address(bot.rpc, accid)
                    results.append(f"{title} = [{gallery_id}](mailto:{addr}?body=%2Finfo3h%20{gallery_id})\n\n")
        for i in range(0, len(results), 10):
            chunk = results[i:i + 10]  
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="\n".join(chunk))
            )
        if not results:
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="No se encontraron resultados.")
            )
    except Exception as e:
        bot.rpc.send_msg(
            accid,
            msg.chat_id,
            MsgData(text=f"Ha ocurrido un error: {e}")
        )
@cli.on(events.NewMessage(command="/tagnh"))
def scan_web(bot, accid, event):
    msg = event.msg
    payload = event.payload.strip()  
    payload = payload.replace(" ", "-")  
    base = "nhentai.net"
    try:
        if "," in payload:
            tag, range_part = payload.split(",")
            tag = tag.strip()  
            range_part = range_part.strip()  
        else:
            tag = payload.strip()  
            range_part = "1"  
        pages = []
        if "-" in range_part:  
            start, end = map(int, range_part.split("-"))
            pages.extend(range(start, end + 1))  
        elif "," in range_part:  
            pages.extend(map(int, range_part.split(",")))  
        else:  
            pages.append(int(range_part))
        pages = sorted(set(pages))
        results = []
        print("Escaneando")
        for page in pages:
            url = f"https://{base}/tag/{tag}/?page={page}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            gallery_links = soup.find_all("a", href=True)
            for link in gallery_links:
                href = link['href']
                if "/g/" in href:
                    gallery_id = href.split("/g/")[1].split("/")[0]
                    gallery_url = f"https://{base}/g/{gallery_id}"
                    gallery_response = requests.get(gallery_url)
                    gallery_response.raise_for_status()
                    gallery_soup = BeautifulSoup(gallery_response.text, 'html.parser')
                    title_tag = gallery_soup.find("h1", class_="title")
                    title_h1 = title_tag.get_text(strip=True) if title_tag else "Sin título"
                    addr = cli.get_address(bot.rpc, accid)
                    results.append(f"{title_h1} = [{gallery_id}](mailto:{addr}?body=%2Finfonh%20{gallery_id})\n\n")
        for i in range(0, len(results), 13):
            chunk = results[i:i + 13]  
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="\n".join(chunk))
            )
        if not results:
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="No se encontraron resultados.")
            )
    except Exception as e:
        bot.rpc.send_msg(
            accid,
            msg.chat_id,
            MsgData(text=f"Ha ocurrido un error: {e}")
        )
@cli.on(events.NewMessage(command="/searchnh"))
def scan_web(bot, accid, event):
    msg = event.msg
    payload = event.payload.strip()  
    payload = payload.replace(" ", "+")  
    base = "nhentai.net"
    try:
        if "," in payload:
            tag, range_part = payload.split(",")
            tag = tag.strip()  
            range_part = range_part.strip()  
        else:
            tag = payload.strip()  
            range_part = "1"  
        pages = []
        if "-" in range_part:  
            start, end = map(int, range_part.split("-"))
            pages.extend(range(start, end + 1))  
        elif "," in range_part:  
            pages.extend(map(int, range_part.split(",")))  
        else:  
            pages.append(int(range_part))
        pages = sorted(set(pages))
        results = []
        print("Escaneando")
        for page in pages:
            url = f"https://{base}/search/?q={tag}&page={page}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            gallery_links = soup.find_all("a", href=True)
            for link in gallery_links:
                href = link['href']
                if "/g/" in href:
                    gallery_id = href.split("/g/")[1].split("/")[0]
                    gallery_url = f"https://{base}/g/{gallery_id}"
                    gallery_response = requests.get(gallery_url)
                    gallery_response.raise_for_status()
                    gallery_soup = BeautifulSoup(gallery_response.text, 'html.parser')
                    title_tag = gallery_soup.find("h1", class_="title")
                    title_h1 = title_tag.get_text(strip=True) if title_tag else "Sin título"
                    addr = cli.get_address(bot.rpc, accid)
                    results.append(f"{title_h1} = [{gallery_id}](mailto:{addr}?body=%2Finfonh%20{gallery_id})\n\n")
        for i in range(0, len(results), 13):
            chunk = results[i:i + 13]  
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="\n".join(chunk))
            )
        if not results:
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="No se encontraron resultados.")
            )
    except Exception as e:
        bot.rpc.send_msg(
            accid,
            msg.chat_id,
            MsgData(text=f"Ha ocurrido un error: {e}")
        )
@cli.on(events.NewMessage(command="/search3h"))
def scan_web(bot, accid, event):
    msg = event.msg
    payload = event.payload.strip()  
    payload = payload.replace(" ", "+")  
    print(f"Escaneando página")
    base = "es.3hentai.net"
    try:
        if "," in payload:
            tag, page_range = payload.split(",")
            tag = tag.strip()  
            page_range = page_range.strip()  
            if "-" in page_range:
                start_page, end_page = map(int, page_range.split("-"))
            else:
                start_page, end_page = int(page_range), int(page_range)  
        else:
            tag = payload.strip()  
            start_page, end_page = 1, 1  
        results = []
        for page in range(start_page, end_page + 1):  
            url = f"https://{base}/search?q={tag}&page={page}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if "/d/" in href:
                    gallery_id = href.split("/d/")[1].split("/")[0]  
                    detail_url = f"https://{base}/d/{gallery_id}"
                    detail_response = requests.get(detail_url)
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    title = detail_soup.title.string if detail_soup.title else "Sin título"
                    addr = cli.get_address(bot.rpc, accid)
                    results.append(f"{title} = [{gallery_id}](mailto:{addr}?body=%2Finfo3h%20{gallery_id})\n\n")
        for i in range(0, len(results), 10):
            chunk = results[i:i + 10]  
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="\n".join(chunk))
            )
        if not results:
            bot.rpc.send_msg(
                accid,
                msg.chat_id,
                MsgData(text="No se encontraron resultados.")
            )
    except Exception as e:
        bot.rpc.send_msg(
            accid,
            msg.chat_id,
            MsgData(text=f"Ha ocurrido un error: {e}")
        )
@cli.on(events.NewMessage(command="/help"))
def helptext(bot, accid, event):
    msg = event.msg
    text_help = """
**Bienvenido a Neko HDL versión Delta Chat**
Este es un bot para descargar contenido de las paginas web: https://nhentai.net y https://es.3hentai.net.
Los comandos hacen lo mismo y solo se diferencian en su terminación en dependencia se la página.
*Descargar:* Descargará las imágenes del código introducido y se las enviará al usuario en un archivo CBZ, si es superior a 15 MB, será comprimido. 
/nh code 
/3h code
*Buscar información:* muestra la primera imagen del código, e información útil como: título, autor, etiquetas, páginas y más.
/infonh code
/info3h code
*Buscar etiquetas:* busca códigos asociados a una etiqueta, se puede usar por rango.
/tagnh nakadashi (Obtiene una página de códigos de los últimos nakadashi)
/tag3h catgirl,1-3 (Obtiene las últimas 3 página de códigos catgirl)
*Buscar:* permite buscar un código introduciendo cualquier texto como palabra clave. 
/searchnh Titulo/Tag (Buscará códigos que coincidan con título o etiqueta)
/search3h Titulo/Tag + Spanish(Buscará códigos que coincidan con título o etiqueta y que estén en idioma español)

Neko es un proyecto iniciado en telegram por [@nakigeplayer](https://t.me/nakigeplayer)(en Delta [ERNP](mailto:ernp@nauta.cu))

Código en [Github](https://github.com/nakigeplayer/neko-hdl-delta)
""".strip()
    url = "https://cdn.imgchest.com/files/739cxnloag7.png"
    response = requests.get(url)
    if response.status_code == 200:
        with open("logo.png", "wb") as f:
            f.write(response.content)
    else:
        print(f"Error al descargar la imagen: {response.status_code}")
    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=text_help, file="logo.png"))
    os.remove("logo.png")
cli.start()
