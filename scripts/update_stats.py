"""Gera assets/stats.png com os dados públicos de github.com/levyoliv."""
import json
import os
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

USERNAME = "levyoliv"
OUTPUT = Path("assets/stats.png")
NAVY = "#13213E"
BLUE = "#315DE6"
PALE = "#E8F0FF"
MUTED = "#B9CCEB"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def font(size, bold=False):
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT_DIR / filename), size)


def github_json(endpoint):
    token = os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "levy-profile-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{endpoint}", headers=headers)
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def gather():
    user = github_json(f"/users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = github_json(
            f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}"
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    own = [repo for repo in repos if not repo.get("fork")]
    language_counts = Counter(repo["language"] for repo in own if repo.get("language"))
    return {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(repo["stargazers_count"] for repo in own),
        "languages": language_counts.most_common(4),
    }


def render(data):
    width, height = 1600, 495
    image = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(image)

    # Faixa de marca, grid discreto e divisor.
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=27, fill=NAVY)
    for x in range(22, width, 32):
        for y in range(20, height, 32):
            draw.ellipse((x, y, x + 2, y + 2), fill="#243F73")
    draw.rectangle((0, 0, 11, height), fill=BLUE)
    draw.text((60, 38), "GITHUB  /  VISÃO GERAL", font=font(25, True), fill=PALE)
    draw.text((60, 82), "Dados públicos atualizados automaticamente", font=font(20), fill=MUTED)
    draw.line((60, 137, 1540, 137), fill="#385487", width=2)

    metrics = [
        ("REPOSITÓRIOS PÚBLICOS", data["repos"]),
        ("SEGUIDORES", data["followers"]),
        ("ESTRELAS RECEBIDAS", data["stars"]),
    ]
    for index, (label, value) in enumerate(metrics):
        left = 65 + index * 510
        draw.text((left, 171), f"{value:,}".replace(",", "."),
                  font=font(73, True), fill="#81A3FF")
        draw.text((left, 274), label, font=font(20, True), fill=PALE)
        if index < 2:
            border = left + 460
            draw.line((border, 166, border, 304), fill="#385487", width=2)
    draw.line((60, 323, 1540, 323), fill="#385487", width=2)

    draw.text((60, 355), "LINGUAGENS NOS REPOSITÓRIOS", font=font(22, True), fill=PALE)
    languages = data["languages"]
    if not languages:
        draw.text((60, 405), "Nenhuma linguagem identificada", font=font(20), fill=MUTED)
    else:
        max_count = max(count for _, count in languages)
        for index, (name, count) in enumerate(languages):
            x = 60 + (index % 2) * 760
            y = 399 + (index // 2) * 43
            label = f"{name}  ·  {count} repo" + ("s" if count != 1 else "")
            draw.text((x, y), label, font=font(17), fill=MUTED)
            draw.rounded_rectangle((x + 250, y + 5, x + 695, y + 17),
                                   radius=6, fill="#2B426F")
            fill_width = max(14, int(445 * count / max_count))
            draw.rounded_rectangle((x + 250, y + 5, x + 250 + fill_width, y + 17),
                                   radius=6, fill=BLUE)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", optimize=True)
    print(f"Criado: {OUTPUT}")


if __name__ == "__main__":
    render(gather())
