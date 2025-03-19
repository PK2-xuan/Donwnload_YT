from flask import Flask, render_template, request, redirect, url_for
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

def is_valid_youtube_url(url):
    """
    Verifica si la URL proporcionada es válida y pertenece a YouTube.
    """
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
    return re.match(youtube_regex, url) is not None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    format_choice = request.form["format"]

    if not url or not is_valid_youtube_url(url):
        # Enviar un mensaje de error a la plantilla si la URL no es válida
        return render_template("index.html", error_message="URL no válida. Asegúrate de que sea un enlace de YouTube.")
    
    try:
        # Obtener información del video sin descargar
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info['title']
            clean_title = clean_filename(raw_title)

            if format_choice == "audio":
                file_path = os.path.join(MUSIC_FOLDER, f"{clean_title}")
                file_path = get_unique_filename(file_path)
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": file_path,
                    "postprocessors": [
                        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
                    ], "concurrent_fragment_downloads": 8,  # Descargar 8 fragmentos simultáneamente
                }

            elif format_choice == "video":
                temp_file_path = os.path.join(MUSIC_FOLDER, f"{clean_title}.webm")
                temp_file_path = get_unique_filename(temp_file_path)
                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "outtmpl": temp_file_path,
                    "concurrent_fragment_downloads": 8, 
                }

            # Descargar el archivo
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if format_choice == "video":
                mp4_file_path = temp_file_path.replace(".webm", ".mp4")
                mp4_file_path = get_unique_filename(mp4_file_path)
                ffmpeg_path = os.path.join(os.getcwd(), 'bin', 'ffmpeg.exe')
                subprocess.run([ffmpeg_path, "-i", temp_file_path, "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", mp4_file_path])

                os.remove(temp_file_path)

            return render_template("index.html", download_complete=True)

    except Exception as e:
        # Si hay algún error durante el proceso de descarga
        return render_template("index.html", error_message=f"Error al intentar descargar: {str(e)}")

@app.route("/success")
def success():
    # Esta ruta solo se usa para mostrar el modal de éxito
    return render_template("index.html", download_complete=True)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
