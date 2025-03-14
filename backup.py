from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

# 📂 Carpeta del proyecto donde se guardarán los archivos
PROJECT_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(PROJECT_FOLDER, exist_ok=True)

def clean_filename(filename):
    """Limpia caracteres no válidos en nombres de archivos en Windows."""
    return re.sub(r'[<>:"/\\|?*]', "", filename)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    if not url:
        return "No ingresaste una URL", 400

    try:
        # Obtener información del video sin descargar
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info['title']
            clean_title = clean_filename(raw_title)
            final_file_path = os.path.join(PROJECT_FOLDER, f"{clean_title}.mp3")

        # Configurar opciones para descargar y convertir solo en la carpeta del proyecto
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(PROJECT_FOLDER, f"{clean_title}.webm"),
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            ],
        }

        # Descargar y convertir a MP3
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # 📥 Enviar el MP3 desde la carpeta del proyecto directamente al usuario
        return send_file(final_file_path, as_attachment=True)

    except Exception as e:
        return f"Error al descargar: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
