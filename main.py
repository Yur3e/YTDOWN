import os
import subprocess
import re
from flask import Flask, render_template, request, send_file, jsonify
import glob

"""
Aplicação Flask para download de vídeos do YouTube utilizando yt-dlp.

Esta aplicação oferece uma interface web para que usuários possam:
- Informar a URL de um vídeo.
- Obter os formatos disponíveis para download (combinados ou separados).
- Realizar o download do vídeo ou do áudio no formato selecionado.

Funcionalidades:
---------------
- Página inicial renderizada com um formulário (index.html).
- Rota `/get_formats`: recebe uma URL e retorna os formatos disponíveis com base na saída do yt-dlp.
- Rota `/download`: baixa o vídeo ou o áudio no formato escolhido e retorna o arquivo para o usuário.
- Garante que os arquivos baixados sejam salvos com o título original do vídeo.
- Ordena os formatos por qualidade de resolução e evita duplicatas.

Dependências:
------------
- Flask
- yt-dlp (instalado no sistema e acessível via linha de comando)
- re (expressões regulares)
- subprocess (execução de comandos)
- glob, os (manipulação de arquivos e diretórios)

Pasta:
-----
- Os arquivos baixados são salvos na pasta `downloads`.

Execução:
---------
Execute este arquivo diretamente para iniciar o servidor Flask localmente com `debug=True`.

Exemplo:
--------
    $ python app.py
    Acesse: http://localhost:5000

Observações:
------------
- Para evitar problemas com nomes de arquivos inválidos, o nome do arquivo é baseado no título original do vídeo, limitado a 200 caracteres.
- Erros são tratados e mensagens amigáveis são retornadas via JSON.
"""

app = Flask(__name__, 
            template_folder='src', 
            static_folder='src')

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """
    Renderiza a página inicial da aplicação.

    Returns:
        str: HTML do template 'index.html'.
    """
    return render_template('index.html')

@app.route('/get_formats', methods=['POST'])
def get_formats():
    """
    Obtém os formatos disponíveis do vídeo informado via URL.

    A função utiliza o yt-dlp para listar os formatos disponíveis e filtra os resultados
    em busca de formatos combinados (vídeo+áudio) e de vídeo apenas. Em seguida, ordena 
    os formatos pela resolução definida na lista 'resolutions_order' e evita duplicatas.

    Returns:
        JSON: Uma lista de formatos disponíveis com os campos 'code', 'desc' e 'combined', 
              ou um JSON com chave 'error' em caso de falha.
    """
    url = request.json['url']
    try:
        # Executa o comando yt-dlp para listar os formatos
        cmd = ['yt-dlp', '--list-formats', url]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        output = result.stdout

        if not output:
            return jsonify({'error': 'Não foi possível obter formatos do vídeo'})

        resolutions_order = ['2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p']
        formats = []
        
        # Padrões para detectar formatos
        resolution_pattern = re.compile(r'(\d{3,4}p|\d{3,4}x\d{3,4})', re.IGNORECASE)
        combined_pattern = re.compile(r'(\d+)\s+\w+\s+mp4.*?(video|audio).*?(video|audio)', re.IGNORECASE)

        # Combina formatos de vídeo e áudio se possível
        for line in output.splitlines():
            match = combined_pattern.search(line)
            if match and 'video' in line.lower() and 'audio' in line.lower():
                format_id = match.group(1)
                res_match = resolution_pattern.search(line)
                if res_match:
                    resolution = res_match.group(1).lower()
                    if 'x' in resolution:
                        height = resolution.split('x')[1]
                        resolution = f"{height}p"
                    if resolution in resolutions_order:
                        formats.append({
                            'code': format_id,
                            'desc': resolution.upper(),
                            'combined': True
                        })

        # Procura formatos de vídeo apenas
        for line in output.splitlines():
            if 'video only' in line.lower():
                parts = line.split()
                if len(parts) < 2:
                    continue

                format_id = parts[0]
                res_match = resolution_pattern.search(line)
                if res_match:
                    resolution = res_match.group(1).lower()
                    if 'x' in resolution:
                        height = resolution.split('x')[1]
                        resolution = f"{height}p"
                    if resolution in resolutions_order:
                        formats.append({
                            'code': format_id,
                            'desc': resolution.upper(),
                            'combined': False
                        })

        # Ordena e remove duplicatas
        unique_formats = []
        seen_resolutions = set()
        
        for res in resolutions_order:
            for fmt in formats:
                if fmt['desc'].lower() == res.upper().lower() and res not in seen_resolutions:
                    unique_formats.append(fmt)
                    seen_resolutions.add(res)
                    break

        if not unique_formats:
            return jsonify({'error': 'Nenhum formato de vídeo encontrado'})

        return jsonify(unique_formats)

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Tempo esgotado ao buscar formatos'})
    except Exception as e:
        print(f"Erro ao buscar formatos: {str(e)}")
        return jsonify({'error': 'Erro ao processar os formatos do vídeo'})

@app.route('/download', methods=['POST'])
def download():
    """
    Realiza o download do conteúdo do vídeo ou áudio conforme os parâmetros informados.

    A função recebe os parâmetros via formulário e monta o comando do yt-dlp para baixar o arquivo.
    O arquivo é salvo na pasta 'downloads', com o título original do vídeo (limitado a 200 caracteres).
    Em caso de sucesso, o arquivo baixado é enviado como resposta; caso contrário, uma mensagem de erro é retornada.

    Returns:
        Response: O arquivo de mídia baixado (send_file) ou um JSON com mensagem de erro.
    """
    url = request.form['url']
    format_code = request.form['format_code']
    file_type = request.form['file_type']
    is_combined = request.form.get('combined', 'false').lower() == 'true'

    # A abordagem adotada mantém o título original do vídeo como nome do arquivo
    output_path = f"{DOWNLOAD_FOLDER}/%(title).200s.%(ext)s"

    cmd = ['yt-dlp', '-o', output_path]

    if file_type == 'mp3':
        cmd += ['--extract-audio', '--audio-format', 'mp3']
    else:
        if not is_combined:
            cmd += ['-f', f'{format_code}+bestaudio[ext=m4a]', '--merge-output-format', 'mp4', '--no-part']
        else:
            cmd += ['-f', format_code]

    cmd.append(url)

    try:
        subprocess.run(cmd, check=True)

        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.*"))
        files = sorted(files, key=os.path.getctime, reverse=True)

        if files:
            return send_file(files[0], as_attachment=True)

        return jsonify({"error": "Arquivo não encontrado, por favor tente novamente."}), 500
    except subprocess.CalledProcessError as e:
        print(f"Erro ao baixar: {str(e)}")
        return jsonify({"error": "Erro ao baixar o arquivo."}), 500
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return jsonify({"error": "Erro inesperado ao processar o arquivo."}), 500

if __name__ == '__main__':
    app.run(debug=True)