#!/usr/bin/env python3
"""Rebuild dark_mode.svg and light_mode.svg from ascii.txt and the details below.

Run this only when the portrait or the text changes. The daily numbers (uptime, repos,
stars, commits, followers, lines of code) are then kept current by today.py, which edits
the elements with the ids used here. The markup follows Andrew6rant's card so his
today.py works unchanged apart from the widths.

    python3 build_svg.py && ACCESS_TOKEN=... USER_NAME=YSMsimon python3 today.py
"""
import datetime as dt
import html
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
USER = "YSMsimon"
W = 56                       # characters per line on the right, ". " included

HEADER = "simon@yang"
ABOUT = [
    ("OS", "macOS, iOS, Linux"),
    ("Uptime", None),        # filled by today.py (id age_data)
    ("Host", "University of Toronto"),
    ("Kernel", "BSc Computer Science"),
    ("IDE", "VS Code, Cursor, Xcode"),
    "dot",
    ("Languages.Code", "Python, TypeScript, Solidity, Swift"),
    ("Languages.Real", "English, Mandarin"),
    "dot",
    ("Research", "LLM agent safety"),
    ("Projects", "Warden, Speak and Edit, Deep-Copilot"),
    ("Interests", "SWE, AI agents, agent evals, DeFi"),
]
CONTACT = [
    ("Email", "simonyang6869@gmail.com"),
    ("LinkedIn", "simonyangprofile"),
    ("Site", "shimeng-dnx.pages.dev"),
]

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 cc="#616e7f", add="#3fb950", dele="#f85149", ascii="ascii.txt"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  cc="#c2cfde", add="#1a7f37", dele="#cf222e", ascii="ascii_light.txt"),
}
WIDTH, HEIGHT, ASCII_X, PANEL_X, LINE_H = 1000, 530, 15, 420, 20


def e(s):
    return html.escape(str(s), quote=False)


def dots(n):
    """Same rule as justify_format in today.py."""
    n = max(0, n)
    return {0: "", 1: " ", 2: ". "}[n] if n <= 2 else " " + "." * n + " "


def keys(name):
    return ".".join(f'<tspan class="key">{e(k)}</tspan>' for k in name.split("."))


def static_line(name, value):
    gap = W - 2 - len(name) - 1 - len(value) - 2
    return (f'<tspan class="cc">. </tspan>{keys(name)}:<tspan class="cc"> {"." * max(1, gap)} </tspan>'
            f'<tspan class="value">{e(value)}</tspan>')


def dyn(id_, value, length, cls="value"):
    value = f"{value:,}" if isinstance(value, int) else str(value)
    return (f'<tspan class="cc" id="{id_}_dots">{dots(length - len(value))}</tspan>'
            f'<tspan class="{cls}" id="{id_}">{e(value)}</tspan>')


def rule(title):
    return f"{e(title)} -" + "—" * (W - len(title) - 3) + "-"


def initial_numbers():
    """Public numbers so the card looks right before the first Actions run."""
    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "YSMsimon-profile"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    user = get(f"https://api.github.com/users/{USER}")
    repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100")
    created = dt.datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    return {
        "age": uptime(created),
        "repos": user["public_repos"],
        "contrib": user["public_repos"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "followers": user["followers"],
        "commits": 0, "add": 0, "del": 0,
    }


def uptime(start):
    now = dt.datetime.now()
    y, m, d = now.year - start.year, now.month - start.month, now.day - start.day
    if d < 0:
        m -= 1
        prev = (now.replace(day=1) - dt.timedelta(days=1))
        d += prev.day
    if m < 0:
        y -= 1
        m += 12
    pl = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{pl(y, 'year')}, {pl(m, 'month')}, {pl(d, 'day')}"


def panel(n):
    rows = [f'{e(HEADER)} -' + "—" * (W - len(HEADER) - 3) + "-"]
    for item in ABOUT:
        if item == "dot":
            rows.append('<tspan class="cc">. </tspan>')
        elif item[1] is None:
            rows.append(f'<tspan class="cc">. </tspan>{keys(item[0])}:{dyn("age_data", n["age"], 45)}')
        else:
            rows.append(static_line(*item))
    rows.append("")
    rows.append(rule("- Contact"))
    rows += [static_line(k, v) for k, v in CONTACT]
    rows.append("")
    rows.append(rule("- GitHub Stats"))
    rows.append(f'<tspan class="cc">. </tspan>{keys("Repos")}:{dyn("repo_data", n["repos"], 6)} '
                f'{{{keys("Contributed")}: <tspan class="value" id="contrib_data">{n["contrib"]}</tspan>}} | '
                f'{keys("Stars")}:{dyn("star_data", n["stars"], 11)}')
    rows.append(f'<tspan class="cc">. </tspan>{keys("Commits")}:{dyn("commit_data", n["commits"], 17)} | '
                f'{keys("Followers")}:{dyn("follower_data", n["followers"], 12)}')
    rows.append(f'<tspan class="cc">. </tspan>{keys("Lines of Code")}:{dyn("loc_data", n["add"] - n["del"], 13)} ( '
                f'<tspan class="addColor" id="loc_add">{n["add"]:,}</tspan><tspan class="addColor">++</tspan>, '
                f'{dyn("loc_del", n["del"], 7, "delColor")}<tspan class="delColor">--</tspan> )')
    return rows


def render(theme, n):
    t = THEMES[theme]
    with open(os.path.join(HERE, t["ascii"])) as f:
        art = f.read().rstrip("\n").split("\n")
    rows = panel(n)
    top = 30 + LINE_H * ((25 - len(rows)) // 2)   # centre the panel against the 25-line portrait
    out = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" '
        f'width="{WIDTH}px" height="{HEIGHT}px" font-size="16px">',
        "<style>",
        "@font-face {src: local('Consolas'), local('Consolas Bold'); font-family: 'ConsolasFallback';"
        " font-display: swap; -webkit-size-adjust: 109%; size-adjust: 109%;}",
        f".key {{fill: {t['key']};}} .value {{fill: {t['value']};}} .addColor {{fill: {t['add']};}}",
        f".delColor {{fill: {t['dele']};}} .cc {{fill: {t['cc']};}} text, tspan {{white-space: pre;}}",
        "</style>",
        f'<rect width="{WIDTH}px" height="{HEIGHT}px" fill="{t["bg"]}" rx="15"/>',
        f'<text x="{ASCII_X}" y="30" fill="{t["text"]}" class="ascii">',
    ]
    out += [f'<tspan x="{ASCII_X}" y="{30 + i * LINE_H}">{e(line)}</tspan>' for i, line in enumerate(art[:25])]
    out.append("</text>")
    out.append(f'<text x="{PANEL_X}" y="{top}" fill="{t["text"]}">')
    for i, row in enumerate(rows):
        out.append(f'<tspan x="{PANEL_X}" y="{top + i * LINE_H}">{row}</tspan>')
    out += ["</text>", "</svg>"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    numbers = initial_numbers()
    for theme in THEMES:
        with open(os.path.join(HERE, f"{theme}_mode.svg"), "w") as f:
            f.write(render(theme, numbers))
    print("built dark_mode.svg and light_mode.svg", numbers)
