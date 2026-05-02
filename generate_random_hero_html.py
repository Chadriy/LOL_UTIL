import json
import re
import time
from functools import lru_cache
from pathlib import Path

import requests
from bs4 import BeautifulSoup


OUTPUT_HTML = "hero_random.html"

OPGG_CN_URLS = {
    "top": "https://opgg.cn/champions",
    "jungle": "https://opgg.cn/champions?pos=2",
    "mid": "https://opgg.cn/champions?pos=3",
    "adc": "https://opgg.cn/champions?pos=4",
    "support": "https://opgg.cn/champions?pos=5",
}

LANE_NAME = {
    "top": "上路",
    "jungle": "打野",
    "mid": "中路",
    "adc": "下路",
    "support": "辅助",
}

LANE_POS_ID = {
  "top": 1,
  "jungle": 2,
  "mid": 3,
  "adc": 4,
  "support": 5,
}

CHAMPION_TITLES = {
    "Aatrox": "暗裔剑魔",
    "Ahri": "九尾妖狐",
    "Akali": "离群之刺",
    "Akshan": "影哨",
    "Alistar": "牛头酋长",
    "Ambessa": "铁血狼母",
    "Amumu": "殇之木乃伊",
    "Anivia": "冰晶凤凰",
    "Annie": "黑暗之女",
    "Aphelios": "残月之肃",
    "Ashe": "寒冰射手",
    "AurelionSol": "铸星龙王",
    "Aurora": "双界灵兔",
    "Azir": "沙漠皇帝",
    "Bard": "星界游神",
    "Belveth": "虚空女皇",
    "Blitzcrank": "蒸汽机器人",
    "Brand": "复仇焰魂",
    "Braum": "弗雷尔卓德之心",
    "Briar": "狂厄蔷薇",
    "Caitlyn": "皮城女警",
    "Camille": "青钢影",
    "Cassiopeia": "魔蛇之拥",
    "Chogath": "虚空恐惧",
    "Corki": "英勇投弹手",
    "Darius": "诺克萨斯之手",
    "Diana": "皎月女神",
    "Draven": "荣耀行刑官",
    "DrMundo": "祖安狂人",
    "Ekko": "时间刺客",
    "Elise": "蜘蛛女皇",
    "Evelynn": "痛苦之拥",
    "Ezreal": "探险家",
    "Fiddlesticks": "远古恐惧",
    "Fiora": "无双剑姬",
    "Fizz": "潮汐海灵",
    "Galio": "正义巨像",
    "Gangplank": "海洋之灾",
    "Garen": "德玛西亚之力",
    "Gnar": "迷失之牙",
    "Gragas": "酒桶",
    "Graves": "法外狂徒",
    "Gwen": "灵罗娃娃",
    "Hecarim": "战争之影",
    "Heimerdinger": "大发明家",
    "Hwei": "异画师",
    "Illaoi": "海兽祭司",
    "Irelia": "刀锋舞者",
    "Ivern": "翠神",
    "Janna": "风暴之怒",
    "JarvanIV": "德玛西亚皇子",
    "Jax": "武器大师",
    "Jayce": "未来守护者",
    "Jhin": "戏命师",
    "Jinx": "暴走萝莉",
    "Kaisa": "虚空之女",
    "Kalista": "复仇之矛",
    "Karma": "天启者",
    "Karthus": "死亡颂唱者",
    "Kassadin": "虚空行者",
    "Katarina": "不祥之刃",
    "Kayle": "正义天使",
    "Kayn": "影流之镰",
    "Kennen": "狂暴之心",
    "Khazix": "虚空掠夺者",
    "Kindred": "永猎双子",
    "Kled": "暴怒骑士",
    "KogMaw": "深渊巨口",
    "KSante": "纳祖芒荣耀",
    "Leblanc": "诡术妖姬",
    "LeeSin": "盲僧",
    "Leona": "曙光女神",
    "Lillia": "含羞蓓蕾",
    "Lissandra": "冰霜女巫",
    "Lucian": "圣枪游侠",
    "Lulu": "仙灵女巫",
    "Lux": "光辉女郎",
    "Malphite": "熔岩巨兽",
    "Malzahar": "虚空先知",
    "Maokai": "扭曲树精",
    "MasterYi": "无极剑圣",
    "Milio": "明烛",
    "MissFortune": "赏金猎人",
    "MonkeyKing": "齐天大圣",
    "Mordekaiser": "铁铠冥魂",
    "Morgana": "堕落天使",
    "Naafiri": "百裂冥犬",
    "Nami": "唤潮鲛姬",
    "Nasus": "沙漠死神",
    "Nautilus": "深海泰坦",
    "Neeko": "万花通灵",
    "Nidalee": "狂野女猎手",
    "Nilah": "不羁之悦",
    "Nocturne": "永恒梦魇",
    "Nunu": "雪原双子",
    "Olaf": "狂战士",
    "Orianna": "发条魔灵",
    "Ornn": "山隐之焰",
    "Pantheon": "不屈之枪",
    "Poppy": "圣锤之毅",
    "Pyke": "血港鬼影",
    "Qiyana": "元素女皇",
    "Quinn": "德玛西亚之翼",
    "Rakan": "幻翎",
    "Rammus": "披甲龙龟",
    "RekSai": "虚空遁地兽",
    "Rell": "镕铁少女",
    "Renata": "炼金男爵",
    "Renekton": "荒漠屠夫",
    "Rengar": "傲之追猎者",
    "Riven": "放逐之刃",
    "Rumble": "机械公敌",
    "Ryze": "符文法师",
    "Samira": "沙漠玫瑰",
    "Sejuani": "北地之怒",
    "Senna": "涤魂圣枪",
    "Seraphine": "星籁歌姬",
    "Sett": "腕豪",
    "Shaco": "恶魔小丑",
    "Shen": "暮光之眼",
    "Shyvana": "龙血武姬",
    "Singed": "炼金术士",
    "Sion": "亡灵战神",
    "Sivir": "战争女神",
    "Skarner": "水晶先锋",
    "Smolder": "炽炎雏龙",
    "Sona": "琴瑟仙女",
    "Soraka": "众星之子",
    "Swain": "诺克萨斯统领",
    "Sylas": "解脱者",
    "Syndra": "暗黑元首",
    "TahmKench": "河流之王",
    "Taliyah": "岩雀",
    "Talon": "刀锋之影",
    "Taric": "瓦洛兰之盾",
    "Teemo": "迅捷斥候",
    "Thresh": "魂锁典狱长",
    "Tristana": "麦林炮手",
    "Trundle": "巨魔之王",
    "Tryndamere": "蛮族之王",
    "TwistedFate": "卡牌大师",
    "Twitch": "瘟疫之源",
    "Udyr": "兽灵行者",
    "Urgot": "无畏战车",
    "Varus": "惩戒之箭",
    "Vayne": "暗夜猎手",
    "Veigar": "邪恶小法师",
    "Velkoz": "虚空之眼",
    "Vex": "愁云使者",
    "Vi": "皮城执法官",
    "Viego": "破败之王",
    "Viktor": "机械先驱",
    "Vladimir": "猩红收割者",
    "Volibear": "不灭狂雷",
    "Warwick": "祖安怒兽",
    "Xayah": "逆羽",
    "Xerath": "远古巫灵",
    "XinZhao": "德邦总管",
    "Yasuo": "疾风剑豪",
    "Yone": "封魔剑魂",
    "Yorick": "牧魂人",
    "Yuumi": "魔法猫咪",
    "Zac": "生化魔人",
    "Zed": "影流之主",
    "Zeri": "祖安花火",
    "Ziggs": "爆破鬼才",
    "Zilean": "时光守护者",
    "Zoe": "暮光星灵",
    "Zyra": "荆棘之兴",
}


def normalize_champion_id(value: str) -> str:
    value = value.strip()
    value = value.replace("'", "")
    value = value.replace(".", "")
    value = value.replace(" ", "")
    value = value.replace("&", "")
    return value


def extract_json_array_text(raw_text: str, array_open_index: int) -> str:
    depth = 0
    end_index = -1

    for idx in range(array_open_index, len(raw_text)):
        ch = raw_text[idx]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end_index = idx
                break

    if end_index < 0:
        return ""

    return raw_text[array_open_index + 1 : end_index]


def extract_opgg_position_champion_numeric_ids(html: str, pos_id: int):
    position_marker = f'\\"position_id\\":{pos_id},'
    start = html.find(position_marker)
    if start < 0:
        return []

    champions_marker = '\\"champions\\":['
    marker_start = html.find(champions_marker, start)
    if marker_start < 0:
        return []

    array_open_index = marker_start + len(champions_marker) - 1
    champions_text = extract_json_array_text(html, array_open_index)
    if not champions_text:
        return []

    return re.findall(r'\\"champion_id\\":(\d+)', champions_text)


def extract_opgg_game_version(html: str) -> str:
    patterns = [
        r'\\"version\\":\\"(\d+\.\d+)\\"',
        r'"version":"(\d+\.\d+)"',
        r'\\"versions\\":\[\\"(\d+\.\d+)\\"',
        r'"versions":\["(\d+\.\d+)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return ""


@lru_cache(maxsize=1)
def get_ddragon_champion_key_map():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    fallback_versions = ["14.24.1", "14.23.1"]

    try:
        versions_resp = requests.get(versions_url, headers=headers, timeout=20)
        versions_resp.raise_for_status()
        versions = versions_resp.json()[:3]
    except Exception:
        versions = []

    for version in versions + fallback_versions:
        try:
            champion_url = (
                f"https://ddragon.leagueoflegends.com/cdn/{version}/"
                "data/zh_CN/champion.json"
            )
            resp = requests.get(champion_url, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            # ddragon: champion.key 是数字字符串，champion.id 是 Aatrox 这类 ID
            return {champion["key"]: champion["id"] for champion in data.values()}
        except Exception:
            continue

    return {}


def fetch_opgg_cn_lane_champions(lane_key: str):
    url = OPGG_CN_URLS[lane_key]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://opgg.cn/champions",
    }

    print(f"正在抓取 {LANE_NAME[lane_key]}：{url}")

    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    game_version = extract_opgg_game_version(html)

    valid_ids = set(CHAMPION_TITLES.keys())
    found = []

    # 优先使用页面内按分路返回的结构化数据，避免误扫到整页预加载资源。
    pos_id = LANE_POS_ID[lane_key]
    champion_numeric_ids = extract_opgg_position_champion_numeric_ids(html, pos_id)
    numeric_to_id = get_ddragon_champion_key_map()

    for champion_numeric_id in champion_numeric_ids:
        champion_id = numeric_to_id.get(champion_numeric_id)
        if champion_id in valid_ids and champion_id not in found:
            found.append(champion_id)

    # 结构化数据获取失败时，再退化到页面可见的 build 链接提取。
    if not found:
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href") or ""
            m = re.search(r"/champions/([A-Za-z0-9]+)/build", href)
            if not m:
                continue

            champion_id = m.group(1)
            if champion_id in valid_ids and champion_id not in found:
                found.append(champion_id)

    print(f"  获取到 {len(found)} 个英雄")

    return found, game_version


def fetch_all_opgg_cn_data():
    lane_to_champions = {}
    game_version = ""

    for lane_key in ["top", "jungle", "mid", "adc", "support"]:
        try:
            champions, lane_version = fetch_opgg_cn_lane_champions(lane_key)
            lane_to_champions[lane_key] = champions
            if not game_version and lane_version:
                game_version = lane_version
            time.sleep(1)
        except Exception as e:
            print(f"  抓取 {LANE_NAME[lane_key]} 失败：{e}")
            lane_to_champions[lane_key] = []

    return lane_to_champions, game_version


def build_hero_lane_config(lane_to_champions):
    hero_to_lanes = {}

    for lane_key, champion_ids in lane_to_champions.items():
        for champion_id in champion_ids:
            hero_to_lanes.setdefault(champion_id, [])
            hero_to_lanes[champion_id].append(LANE_NAME[lane_key])

    lines = []

    for champion_id, title in CHAMPION_TITLES.items():
        lane_names = hero_to_lanes.get(champion_id)
        if lane_names:
            lines.append(f"{title}：{'，'.join(lane_names)}")

    return "\n".join(lines)


def build_html(hero_lane_config, game_version):
    champion_titles_js = json.dumps(CHAMPION_TITLES, ensure_ascii=False, indent=6)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>英雄联盟5V5英雄随机器</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{
      background:
        radial-gradient(circle at 18% 8%, rgba(37, 99, 235, .35), transparent 32%),
        radial-gradient(circle at 82% 12%, rgba(220, 38, 38, .30), transparent 30%),
        radial-gradient(circle at 50% 110%, rgba(202, 138, 4, .16), transparent 38%),
        #020617;
    }}
    .glass {{ background: rgba(15, 23, 42, .72); backdrop-filter: blur(18px); box-shadow: 0 24px 80px rgba(0,0,0,.35); }}
    .hero-card {{ transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease, background .18s ease; }}
    .hero-card:hover {{ transform: translateY(-3px); border-color: rgba(234,179,8,.65); box-shadow: 0 12px 28px rgba(0,0,0,.35), 0 0 22px rgba(234,179,8,.10); background: rgba(15,23,42,.92); }}
    .gold-text {{ background: linear-gradient(90deg, #fde68a, #f59e0b, #fef3c7); -webkit-background-clip: text; background-clip: text; color: transparent; }}
    .lane-title::before {{ content: ""; width: 8px; height: 8px; border-radius: 999px; background: #facc15; box-shadow: 0 0 18px rgba(250,204,21,.8); }}
  </style>
</head>
<body class="min-h-screen text-slate-100 selection:bg-amber-400 selection:text-slate-950">
  <div class="max-w-7xl mx-auto px-4 py-8 md:py-10">
    <header class="mb-7 text-center relative">
      <div class="inline-flex items-center gap-2 rounded-full border border-amber-300/25 bg-amber-300/10 px-4 py-1.5 text-xs text-amber-100 shadow-lg shadow-amber-950/20">
        <span class="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,.9)]"></span>
        Python 生成 · OPGG.CN 数据 · 双方英雄不重复 · 使用英雄称号
      </div>
      <h1 class="mt-4 text-4xl md:text-6xl font-black tracking-tight gold-text">英雄联盟5V5英雄随机器</h1>
      <p class="mt-3 text-slate-300">按分路随机英雄，英雄池由 Python 脚本从 opgg.cn/champions 抓取生成。</p>
      <p class="mt-2 text-sm text-amber-200/90">当前游戏版本：<span id="gameVersion" class="font-bold">-</span></p>
    </header>

    <section class="mb-7 rounded-3xl border border-white/10 glass p-4 md:p-5">
      <div class="flex flex-col lg:flex-row lg:items-center gap-4 justify-between">
        <div class="flex flex-col sm:flex-row gap-4 sm:items-end">
          <div>
            <label for="count" class="block text-sm font-semibold text-slate-200 mb-2">每个分路随机数量 n</label>
            <div class="flex items-center rounded-2xl border border-white/10 bg-slate-950/70 p-1.5 focus-within:ring-2 focus-within:ring-amber-400/60">
              <button id="minusBtn" class="h-10 w-10 rounded-xl bg-slate-800 hover:bg-slate-700 font-black transition" type="button">−</button>
              <input id="count" type="number" min="1" max="5" value="3" class="w-20 bg-transparent px-3 py-2 text-center text-lg font-black text-white outline-none" />
              <button id="plusBtn" class="h-10 w-10 rounded-xl bg-slate-800 hover:bg-slate-700 font-black transition" type="button">+</button>
            </div>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3">
          <button id="randomBtn" class="rounded-2xl bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 hover:from-amber-200 hover:to-yellow-300 text-slate-950 font-black px-7 py-3 transition shadow-lg shadow-amber-950/30 active:scale-95">开始随机</button>
          <button id="clearBtn" class="rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 text-slate-100 font-bold px-6 py-3 transition active:scale-95">清空结果</button>
        </div>
      </div>
    </section>

    <main class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <section class="rounded-[2rem] border border-blue-300/25 bg-blue-950/25 overflow-hidden shadow-2xl shadow-blue-950/30">
        <div class="px-5 py-4 bg-gradient-to-r from-blue-600/45 via-blue-500/20 to-transparent border-b border-blue-300/20 flex items-center justify-between">
          <div><h2 class="text-2xl md:text-3xl font-black">蓝色方</h2><p class="text-xs text-blue-100/70 mt-1">Blue Side</p></div>
          <div class="h-11 w-11 rounded-2xl bg-blue-400/20 border border-blue-200/20 grid place-items-center text-blue-100 font-black">B</div>
        </div>
        <div id="blueTeam" class="p-4 space-y-4"></div>
      </section>

      <section class="rounded-[2rem] border border-red-300/25 bg-red-950/25 overflow-hidden shadow-2xl shadow-red-950/30">
        <div class="px-5 py-4 bg-gradient-to-r from-red-600/45 via-red-500/20 to-transparent border-b border-red-300/20 flex items-center justify-between">
          <div><h2 class="text-2xl md:text-3xl font-black">红色方</h2><p class="text-xs text-red-100/70 mt-1">Red Side</p></div>
          <div class="h-11 w-11 rounded-2xl bg-red-400/20 border border-red-200/20 grid place-items-center text-red-100 font-black">R</div>
        </div>
        <div id="redTeam" class="p-4 space-y-4"></div>
      </section>
    </main>

    <footer class="mt-7 text-center text-xs text-slate-500">
      英雄池由 Python 脚本从 opgg.cn/champions 生成；重新运行脚本即可更新。
    </footer>
  </div>

  <script type="text/plain" id="heroLaneConfig">
{hero_lane_config}
  </script>

  <script>
    const OPGG_GAME_VERSION = {json.dumps(game_version or "未知", ensure_ascii=False)};
    const VERSION = OPGG_GAME_VERSION === "未知" ? "14.24.1" : `${{OPGG_GAME_VERSION}}.1`;
    const FALLBACK_VERSION = "14.23.1";

    const lanes = [
      {{ key: "top", name: "上路", icon: "TOP" }},
      {{ key: "jungle", name: "打野", icon: "JUG" }},
      {{ key: "mid", name: "中路", icon: "MID" }},
      {{ key: "adc", name: "下路", icon: "ADC" }},
      {{ key: "support", name: "辅助", icon: "SUP" }}
    ];

    const laneNameToKey = {{ 上路: "top", 打野: "jungle", 中路: "mid", 下路: "adc", 辅助: "support" }};
    const championTitles = {champion_titles_js};

    const titleToId = Object.fromEntries(Object.entries(championTitles).map(([id, title]) => [title, id]));

    function buildPoolsFromList(listText) {{
      const result = Object.fromEntries(lanes.map(lane => [lane.key, []]));

      listText.split(/\\n+/).map(line => line.trim()).filter(Boolean).forEach(line => {{
        const parts = line.split(/[：:]/);
        if (parts.length < 2) return;

        const id = titleToId[parts[0].trim()];
        if (!id) return;

        parts.slice(1).join("：").split(/[，,、/\\s]+/).map(x => x.trim()).filter(Boolean).forEach(laneName => {{
          const key = laneNameToKey[laneName];
          if (key && !result[key].includes(id)) result[key].push(id);
        }});
      }});

      return result;
    }}

    const pools = buildPoolsFromList(document.getElementById("heroLaneConfig").textContent.trim());

    const $ = id => document.getElementById(id);
    const safeTitle = id => championTitles[id] || id;

    function iconUrl(id) {{ return `https://game.gtimg.cn/images/lol/act/img/champion/${{id}}.png`; }}
    function fallbackIconUrl(id) {{ return `https://ddragon.leagueoflegends.com/cdn/${{VERSION}}/img/champion/${{id}}.png`; }}
    function secondFallbackIconUrl(id) {{ return `https://ddragon.leagueoflegends.com/cdn/${{FALLBACK_VERSION}}/img/champion/${{id}}.png`; }}

    function shuffle(arr) {{
      const a = [...arr];
      for (let i = a.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }}
      return a;
    }}

    function pickUnique(pool, count, used) {{
      const available = shuffle(pool.filter(id => !used.has(id)));
      const picked = available.slice(0, count);
      picked.forEach(id => used.add(id));
      return picked;
    }}

    function card(id) {{
      const title = safeTitle(id);
      return `
        <div class="hero-card group flex items-center gap-3 rounded-2xl bg-slate-950/65 border border-white/10 p-2.5 overflow-hidden">
          <div class="relative shrink-0">
            <img src="${{iconUrl(id)}}" alt="${{title}}" class="w-14 h-14 rounded-2xl object-cover border border-amber-200/20 shadow-lg shadow-black/30" loading="lazy" onerror="if (!this.dataset.fallback) {{ this.dataset.fallback='1'; this.src='${{fallbackIconUrl(id)}}'; }} else {{ this.onerror=null; this.src='${{secondFallbackIconUrl(id)}}'; }}" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="font-black text-sm md:text-base truncate text-slate-50 group-hover:text-amber-100 transition">${{title}}</div>
            <div class="text-xs text-slate-500 truncate">${{id}}</div>
          </div>
        </div>`;
    }}

    function laneBlock(lane, picks) {{
      return `
        <div class="rounded-3xl border border-white/10 bg-slate-950/40 overflow-hidden">
          <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between bg-white/[0.03]">
            <h3 class="lane-title flex items-center gap-2 font-black text-lg">${{lane.name}}</h3>
            <span class="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs text-amber-100">${{lane.icon}} · ${{picks.length}} 个</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 p-3">${{picks.map(card).join("")}}</div>
        </div>`;
    }}

    function randomize() {{
      const n = Math.max(1, Math.min(5, Number($("count").value) || 3));
      $("count").value = n;

      const used = new Set();
      const blue = {{}};
      const red = {{}};

      for (const lane of lanes) blue[lane.key] = pickUnique(pools[lane.key], n, used);
      for (const lane of lanes) red[lane.key] = pickUnique(pools[lane.key], n, used);

      $("blueTeam").innerHTML = lanes.map(lane => laneBlock(lane, blue[lane.key])).join("");
      $("redTeam").innerHTML = lanes.map(lane => laneBlock(lane, red[lane.key])).join("");
    }}

    function clearResults() {{
      $("blueTeam").innerHTML = `<div class="rounded-3xl border border-dashed border-blue-200/20 bg-blue-950/20 text-blue-100/60 text-center py-16">点击“开始随机”生成蓝色方结果</div>`;
      $("redTeam").innerHTML = `<div class="rounded-3xl border border-dashed border-red-200/20 bg-red-950/20 text-red-100/60 text-center py-16">点击“开始随机”生成红色方结果</div>`;
    }}

    function clampCount(delta) {{
      const input = $("count");
      input.value = Math.max(1, Math.min(5, (Number(input.value) || 3) + delta));
    }}

    $("randomBtn").addEventListener("click", randomize);
    $("clearBtn").addEventListener("click", clearResults);
    $("minusBtn").addEventListener("click", () => clampCount(-1));
    $("plusBtn").addEventListener("click", () => clampCount(1));

    clearResults();

    // 页面显式展示当前版本，方便确认英雄池对应补丁。
    $("gameVersion").textContent = OPGG_GAME_VERSION;
  </script>
</body>
</html>
"""


def main():
    lane_to_champions, game_version = fetch_all_opgg_cn_data()
    hero_lane_config = build_hero_lane_config(lane_to_champions)

    if not hero_lane_config.strip():
        raise RuntimeError("没有抓取到任何英雄数据，请检查 opgg.cn 页面结构或网络访问。")

    Path(OUTPUT_HTML).write_text(
        build_html(hero_lane_config, game_version), encoding="utf-8"
    )

    print()
    print(f"已生成：{OUTPUT_HTML}")
    print(f"游戏版本：{game_version or '未知'}")
    print(f"英雄配置行数：{len(hero_lane_config.splitlines())}")

    print()
    print("生成的英雄分路配置预览：")
    print(hero_lane_config)


if __name__ == "__main__":
    main()
