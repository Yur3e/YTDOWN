import os
import subprocess
import glob
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from .utils import extract_formats
from .downloader import build_download_command

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/get_formats', methods=['POST'])
def get_formats():
    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL inválida.'}), 400
    try:
        result = subprocess.run(
            [current_app.config['YTDLP_PATH'], '--list-formats', url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        output = result.stdout
        if not output:
            return jsonify({'error': 'Não foi possível obter formatos do vídeo.'}), 500

        formats = extract_formats(output)
        return jsonify(formats)
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Tempo esgotado ao buscar formatos.'}), 408
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar formatos: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor.'}), 500

@main.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_code = request.form['format_code']
    file_type = request.form['file_type']
    is_combined = request.form.get('combined', 'false').lower() == 'true'

    output_path = os.path.join(current_app.config['DOWNLOAD_FOLDER'], "%(title).200s.%(ext)s")
    cmd = build_download_command(
        url=url,
        format_code=format_code,
        file_type=file_type,
        is_combined=is_combined,
        output_path=output_path,
        ytdlp_path=current_app.config['YTDLP_PATH']
    )

    try:
        subprocess.run(cmd, check=True)
        files = sorted(glob.glob(os.path.join(current_app.config['DOWNLOAD_FOLDER'], "*.*")),
                       key=os.path.getctime, reverse=True)
        if files:
            return send_file(files[0], as_attachment=True)
        return jsonify({"error": "Arquivo não encontrado."}), 500
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Erro ao baixar: {str(e)}")
        return jsonify({"error": "Erro ao baixar o arquivo."}), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {str(e)}")
        return jsonify({"error": "Erro inesperado ao processar o arquivo."}), 500
