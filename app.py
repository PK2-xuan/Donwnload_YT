from flask import Flask, render_template, request
import yt_dlp
import os
import re
import subprocess

app = Flask(__name__)

# Obtener la ruta de la carpeta de descargas
user_profile = os.environ.get("USERPROFILE", "")  # "C:\Users\usuario"
downloads_folder = os.path.join(user_profile, "Downloads")
MUSIC_FOLDER = os.path.join(downloads_folder, "Musica - Youtube")
os.makedirs(MUSIC_FOLDER, exist_ok=True)

print(f"Descargas se almacenarán en: {MUSIC_FOLDER}")

def clean_filename(filename):
    """Limpia caracteres no válidos en nombres de archivos en Windows."""
    return re.sub(r'[<>:"/\\|?*]', "", filename)

def get_unique_filename(file_path):
    """
    Devuelve un nombre de archivo único si ya existe en la carpeta.
    """
    base, ext = os.path.splitext(file_path)
    counter = 1
    new_file_path = file_path

    while os.path.exists(new_file_path):
        new_file_path = f"{base} ({counter}){ext}"
        counter += 1

    return new_file_path

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    format_choice = request.form["format"]  # Obtener la opción seleccionada (audio o video)

    if not url:
        return render_template("index.html", message="No ingresaste una URL")

    try:
        # Obtener información del video sin descargar
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info['title']
            clean_title = clean_filename(raw_title)

            # Si es audio, generar solo archivo mp3
            if format_choice == "audio":
                file_path = os.path.join(MUSIC_FOLDER, f"{clean_title}")
                file_path = get_unique_filename(file_path)  # Asegura un nombre único
                ydl_opts = {
                    "format": "bestaudio/best",  # Seleccionar solo el mejor audio
                    "outtmpl": file_path,  # Guardar como archivo MP3
                    "postprocessors": [
                        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
                    ],
                    "concurrent_fragment_downloads": 8,  # Descargar 8 fragmentos simultáneamente
                }

            # Si es video, generar archivo mp4
            elif format_choice == "video":
                temp_file_path = os.path.join(MUSIC_FOLDER, f"{clean_title}.webm")  # Guardar como archivo temporal webm
                temp_file_path = get_unique_filename(temp_file_path)  # Asegura un nombre único
                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",  # Descargar el mejor video y audio
                    "outtmpl": temp_file_path,  # Guardar como archivo WebM
                    "concurrent_fragment_downloads": 8,  # Descargar 8 fragmentos simultáneamente
                }

            # Descargar el archivo en el formato original (webm)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Convertir el archivo descargado de webm a mp4 usando FFmpeg
            if format_choice == "video":
                mp4_file_path = temp_file_path.replace(".webm", ".mp4")  # Cambiar la extensión a mp4
                mp4_file_path = get_unique_filename(mp4_file_path)  # Asegura un nombre único para el archivo final

                # Usar FFmpeg para convertir el archivo WebM a MP4
                ffmpeg_path = os.path.join(os.getcwd(), 'bin', 'ffmpeg.exe')  # Ruta al ejecutable ffmpeg.exe dentro de la carpeta bin

                subprocess.run([ffmpeg_path, "-i", temp_file_path, "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", mp4_file_path])

                # Eliminar el archivo temporal webm después de la conversión
                os.remove(temp_file_path)

                # Mensaje de éxito
                return render_template("index.html", message=f"El archivo {mp4_file_path} ha sido descargado y convertido exitosamente.", url="")

        # Si el formato es audio, el archivo ya está descargado
        return render_template("index.html", message=f"El archivo {file_path} ha sido descargado exitosamente.", url="")

    except Exception as e:
        return render_template("index.html", message=f"Error al descargar: {str(e)}", url="")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
