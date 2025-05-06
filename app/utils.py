import re

def extract_formats(output: str):
    resolutions_order = ['2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p']
    formats = []
    resolution_pattern = re.compile(r'(\d{3,4}p|\d{3,4}x\d{3,4})', re.IGNORECASE)
    combined_pattern = re.compile(r'(\d+)\s+\w+\s+mp4.*?(video|audio).*?(video|audio)', re.IGNORECASE)

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
                formats.append({'code': format_id, 'desc': resolution.upper(), 'combined': True})

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
                formats.append({'code': format_id, 'desc': resolution.upper(), 'combined': False})

    unique_formats = []
    seen_res = set()
    for res in resolutions_order:
        for fmt in formats:
            if fmt['desc'].lower() == res.lower() and res not in seen_res:
                unique_formats.append(fmt)
                seen_res.add(res)
                break

    return unique_formats
