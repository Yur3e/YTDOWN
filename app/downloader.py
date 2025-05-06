def build_download_command(url, format_code, file_type, is_combined, output_path, ytdlp_path):
    cmd = [ytdlp_path, '-o', output_path]

    if file_type == 'mp3':
        cmd += ['--extract-audio', '--audio-format', 'mp3']
    else:
        if not is_combined:
            cmd += ['-f', f'{format_code}+bestaudio[ext=m4a]', '--merge-output-format', 'mp4', '--no-part']
        else:
            cmd += ['-f', format_code]

    cmd.append(url)
    return cmd
