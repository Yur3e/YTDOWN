import os
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='../src', static_folder='../src')

    # Diretórios e caminhos globais
    app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__ + '/../'))
    app.config['DOWNLOAD_FOLDER'] = os.path.join(app.config['BASE_DIR'], 'downloads')
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

    app.config['YTDLP_PATH'] = os.path.join(app.config['BASE_DIR'], 'bin', 'yt-dlp.exe')
    app.config['FFMPEG_PATH'] = os.path.join(app.config['BASE_DIR'], 'bin', 'ffmpeg.exe')

    # Blueprint de rotas
    from .routes import main
    app.register_blueprint(main)

    return app
