#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vault_builder_v5.py — graph-first Obsidian builder.

Yapı (Vault of an Ambition altında):
    00 - MOCs/Master MOC.md
    01 - Notes/                  → atomic notlar (düz)
    02 - People/@username.md     → kişi hub'ları (auto)
    03 - Topics/<Topic>.md       → sabit topic MOC'ları
    04 - Concepts/<concept>.md   → AI ürettiği serbest concept stub'ları

Her not 4-6 link verir ([[@author]], [[Topic]], [[concept-1]]…) → yoğun graph.

Mod:
    python3 vault_builder_v5.py fetch     → Twitter syndication + meta + AI batch + yaz
    python3 vault_builder_v5.py quick     → İçerik çekme yok, sadece username→topic + yaz
    python3 vault_builder_v5.py rebuild   → Sadece MOC + hub'ları yeniden üret
"""

import sys, os, re, json, math, time, asyncio, subprocess
from datetime import datetime
from pathlib import Path
from urllib import request, parse, error
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor

# ══════════════════════════════════════════════════════════════════════
#  AYARLAR
# ══════════════════════════════════════════════════════════════════════

VAULT = Path("/Users/serhateralp01/Documents/The Vault of an Ambition")
VAULT = Path(VAULT)  # string olarak girilse de Path'e çevirir

OPENROUTER_KEY   = "sk-or-..."
OPENROUTER_MODEL = "anthropic/claude-haiku-4-5"
# Alternatifler:
#   openai/gpt-4o-mini
#   google/gemini-flash-1.5
#   meta-llama/llama-3.1-8b-instruct:free   (ücretsiz)

BATCH_SIZE        = 15        # AI'a tek seferde gönderilecek URL sayısı
FETCH_CONCURRENCY = 10        # paralel HTTP çekme limiti
CHECKPOINT        = Path.home() / ".vault_builder_v5_checkpoint.json"

INSTAGRAM_USER = ""           # boşsa Instagram atlanır
INSTAGRAM_PASS = ""

# ══════════════════════════════════════════════════════════════════════
#  TOPICS (sabit hub seti — ~20 hub, AI bunlardan birini seçer)
# ══════════════════════════════════════════════════════════════════════

TOPICS = [
    "AI Tools & Products",
    "Prompt Engineering",
    "Agents & MCP",
    "Dev & Open Source",
    "Visual Design & Figma",
    "Fashion & Style",
    "Typography & Fonts",
    "BIST & Turkish Markets",
    "US & Global Markets",
    "Crypto & Web3",
    "Mindset & Psychology",
    "Productivity & Systems",
    "Health & Fitness",
    "Philosophy & Classics",
    "Startups & Entrepreneurship",
    "Strategy & Management",
    "Content & Marketing",
    "Sociology & Society",
    "Politics & Current Affairs",
    "Food & Drink",
    "Entertainment",
    "Uncategorized",
]

# ══════════════════════════════════════════════════════════════════════
#  URL LİSTELERİ  (apple notes + iphone tabs — v4'ten taşındı)
# ══════════════════════════════════════════════════════════════════════

APPLE_NOTES_LINKS = [
    "https://x.com/gregisenberg/status/2052110589682749869",
    "https://x.com/furkandumande/status/2052313883025551491",
    "https://x.com/browomo/status/2052333456416186585",
    "https://x.com/sefauygunn/status/2045908630449320386",
    "https://x.com/cartunmafia/status/2043641041387946465",
    "https://x.com/aakashgupta/status/2022548602053366079",
    "https://x.com/atarikguney/status/2022350898459279817",
    "https://x.com/thedankoe/status/2010042119121957316",
    "https://x.com/ArjunPatel_AI/status/2009867052623044806",
    "https://x.com/TheShiftJournal/status/2010009593276190732",
    "https://x.com/thedankoe/status/2010751592346030461",
    "https://x.com/Speculator_io/status/2011535488709247139",
    "https://x.com/sefauygunn/status/2012460043573023190",
    "https://www.instagram.com/p/DScv4yyjbVa/",
    "https://x.com/seth666king/status/2014617738195464323",
    "https://x.com/sefauygunn/status/2005911308793749635",
    "https://x.com/arrtnem/status/2005478032736215522",
    "https://x.com/Helios_Movement/status/2005325658831106146",
    "https://x.com/vbozkurt55/status/2005543532845568148",
    "https://x.com/girisimcihisler/status/2004201717672636907",
    "https://x.com/arrtnem/status/2004884856463872021",
    "https://x.com/__BigJo/status/2004911060537541096",
    "https://instagram.com/p/DM4zOxcNGtq/",
    "https://instagram.com/p/DNN_hZwAL9s/",
    "https://www.instagram.com/p/DNtB3A3Ysa_/",
    "https://x.com/aiwithghotai/status/1961506325000851483",
    "https://usgraphics.com/products/berkeley-mono",
    "https://x.com/exm7777/status/1961436484395008322",
    "https://x.com/alex_prompter/status/1961818044562284635",
    "https://x.com/aaditsh/status/1961307088090763588",
    "https://x.com/intuitmachine/status/1961399091184722100",
    "https://x.com/aaditsh/status/1961865770281078799",
    "https://x.com/quantscience_/status/1961821579089703184",
    "https://x.com/quantscience_/status/1961459923977441363",
    "https://x.com/robin_buildup/status/1961733636027482450",
    "https://x.com/alex_prompter/status/1962144098816553292",
    "https://x.com/thealexbanks/status/1961415269332443456",
    "https://youtu.be/hMarCPjGEuw",
    "https://x.com/ror_fly/status/1961424548835869078",
    "https://x.com/renckorzay/status/1961480239839940861",
    "https://www.instagram.com/reel/DN0jdZe0OCA/",
    "https://www.instagram.com/p/DN6CYzjgEI7/",
    "https://x.com/umutcakirai/status/1965009392245653940",
    "https://x.com/kinopee_ai/status/1964970439459111042",
    "https://www.instagram.com/p/DK2yizKA_DB/",
    "https://www.instagram.com/p/DOCsi8-gqLt/",
    "https://www.instagram.com/reel/DNdrw2asEFU/",
    "https://www.instagram.com/reel/DOWKo1MAFoS/",
    "https://www.instagram.com/p/DOTwsxQkRJI/",
    "https://x.com/questmoosa/status/1974766315253485698",
    "https://www.youtube.com/watch?v=VaUdnpSCK8k",
    "https://youtube.com/shorts/5cXwOdWWJnM",
    "https://www.instagram.com/reel/DJ6xWLHN7Fj/",
    "https://www.instagram.com/reel/DNDZbSkzPeI/",
    "https://x.com/philbak1/status/1973030126402351411",
    "https://x.com/altudev/status/1973293438809563646",
    "https://x.com/dogalyasalar/status/1976706293374001318",
    "https://x.com/thePerdesiz/status/1976672513779286274",
    "https://x.com/Bolsevik_D/status/1974165988711989386",
    "https://www.instagram.com/p/DPClGBIDNFg/",
    "https://x.com/schwarzstrife/status/1977759452590731610",
    "https://x.com/thebeautyofsaas/status/1977636766594261339",
    "https://x.com/sam_allsopp_/status/1979190622167646446",
    "https://x.com/TylerAlterman/status/1977841263559979276",
    "https://x.com/benfurkankilic/status/1987487184711254217",
    "https://x.com/Awakenthyself33/status/2028258988916461743",
    "https://x.com/coreyganim/status/2027871560762077610",
    "https://x.com/YourPrimePath/status/2028009845249740883",
    "https://x.com/ghumare64/status/2025221175719387515",
    "https://x.com/sefauygunn/status/2021294710665490888",
    "https://x.com/aaditsh/status/1907414534039470342",
    "https://x.com/gryhkn/status/1904176809186574673",
    "https://x.com/reha37/status/1906751947689865444",
    "https://youtu.be/hCSHuvDejGA",
    "https://x.com/yasinolmez/status/1894425923325497631",
    "https://x.com/Hesamation/status/1907809327282299211",
    "https://www.youtube.com/watch?v=YLr63nBFKg0",
    "https://x.com/Psikobilim_/status/1910824041650302987",
    "https://drive.google.com/file/d/1AbaBYbEa_EbPelsT40-vj64L-2IwUJHy/view",
    "https://www.instagram.com/p/DHBpR2fquDS/",
    "https://x.com/apollonator3000/status/1911514248339181586",
    "https://x.com/realEstateTrent/status/1911220818014536123",
    "https://docs.google.com/document/d/1vP_dXwd_kDd-f8Sh-SNEZ_6gTTUxl08jqVXb4JAheIs/edit",
    "https://fularsizentellik.com/journal/2017/2/6/aristo",
    "https://fularsizentellik.com/journal/2017/6/5/aristoteles-2-tanri",
    "https://www.youtube.com/watch?v=UmHMVU6dceA",
    "https://www.youtube.com/watch?v=AXpxZMRM1EY",
    "https://coolors.co/b8c480-d4e79e-922d50-501537-3c1b43",
    "https://www.behance.net/",
    "https://www.youtube.com/watch?v=jQ1sfKIl50E",
    "https://x.com/kisaca_bade/status/1911338842956640546",
]

IPHONE_TABS = [
    "https://x.com/cemoyvat/status/2046499292974600304",
    "https://x.com/jaynitx/status/2047591841219203336",
    "https://x.com/gryhkn/status/1980736696804119007",
    "https://x.com/BeatstoBytes/status/1980719207642751310",
    "https://x.com/davepl1968/status/1981211352267182112",
    "https://x.com/talesamurai44/status/1981825807942382046",
    "https://x.com/tom_doerr/status/1982036255236861959",
    "https://putthison.com/how-to-understand-silhouette-pt-one/",
    "https://x.com/reha37/status/1985358925131051245",
    "https://x.com/reha37/status/1986081062439600451",
    "https://x.com/yugenmarkos/status/1988900477254164624",
    "https://x.com/justinskycak/status/1989007599942136125",
    "https://x.com/neatprompts/status/1989740696241410418",
    "https://x.com/Kpaxs/status/1989911806945759662",
    "https://qwen-web.sdan.io/",
    "https://downmagaz.net/tags/the%20economist/",
    "https://github.com/Monkfishare/The_Economist/tree/main/TE/2025",
    "https://x.com/barissanli/status/1995437798149837001",
    "https://x.com/barissanli/status/1995436807207715032",
    "https://vert.sh/",
    "https://x.com/XCodeWraith/status/1996982601777660318",
    "https://academy.openai.com/public/tags/prompt-packs-6849a0f98c613939acef841c",
    "https://x.com/enkijust/status/2004606208141918356",
    "https://x.com/canleventozgun/status/2005322890460168360",
    "https://prompts.chat/",
    "https://x.com/thebeautyofsaas/status/2006104228381721052",
    "https://x.com/sonkezchpai/status/2006672555634249804",
    "https://x.com/CagriKent/status/2009049325473845363",
    "https://x.com/yatirim/status/2009311946718273666",
    "https://x.com/airistarvz/status/2009156629091250369",
    "https://x.com/BurkanYilmaz/status/2009343598551289971",
    "https://x.com/Kismetse0nur/status/2010761200657907925",
    "https://x.com/kemalalimoglu/status/2010781366753828902",
    "https://x.com/kesfsever/status/2013900550446723313",
    "https://x.com/Psikobilim_/status/2014003364665663604",
    "https://x.com/unutmanehri/status/2013963369930170457",
    "https://x.com/canitti/status/2013684550535176351",
    "https://x.com/onlineinsane/status/2016622586369581067",
    "https://x.com/sefauygunn/status/2022354535151174085",
    "https://x.com/Omercanozmen10/status/2022675949490442533",
    "https://x.com/eagleseyeinc/status/2022881834925781243",
    "https://colonist.io/",
    "https://x.com/AlpacaAurelius/status/2026822262436122650",
    "https://x.com/dengeplus/status/2027110056580259902",
    "https://x.com/taylanbaranr/status/2027825761156272620",
    "https://x.com/frank_ikemefune/status/2028798350439424019",
    "https://x.com/esattimben/status/2028938608594567538",
    "https://x.com/sefauygunn/status/2029134034744295843",
    "https://x.com/Timmysofine/status/2029210097243631630",
    "https://x.com/kendinefsime/status/2029537928947331186",
    "https://size.name/en",
    "https://x.com/AnishA_Moonka/status/2032508311354921357",
    "https://x.com/krlgcglgs/status/2035051929135358194",
    "https://x.com/ihtesham2005/status/2035325595048083663",
    "https://terraink.app/",
    "https://x.com/MhsnBeyy/status/2035424232935395832",
    "https://github.com/mvanhorn/last30days-skill",
    "https://x.com/axepreneur/status/2036888491884220578",
    "http://siir.me/ben-orhan-veli",
    "https://x.com/esattimben/status/2037270295770472917",
    "https://x.com/luckylamb420/status/2037986472285094008",
    "https://x.com/wavruby/status/2038120602163093594",
    "https://x.com/GraceGym_/status/2038187235422441765",
    "https://x.com/found_it_funny/status/2038300316618145871",
    "https://x.com/Kpaxs/status/2038462401083838886",
    "https://x.com/canitti/status/2038595635138498793",
    "https://x.com/alperen00s/status/2038691484350779570",
    "https://x.com/alecttrona/status/2039541797735764088",
    "https://x.com/samvonarx/status/2039249478314541129",
    "https://x.com/meva_la_vida/status/2040448534751715602",
    "https://x.com/emirbalbay/status/2040717886994432487",
    "https://x.com/buharlasan/status/2040535636394803599",
    "https://x.com/lorderaslan/status/2041223248730280026",
    "https://subscribenow.economist.com/student",
    "https://x.com/tatvermiyor/status/2041503379675877715",
    "https://x.com/sedatesnail/status/2041535734457213172",
    "https://closeness-to-things.netlify.app/",
    "https://x.com/regalstreak/status/2041778597028122828",
    "https://x.com/gymmaxxfit/status/2042201572550062303",
    "https://x.com/mrledtasso/status/2042483263239856247",
    "https://m.imdb.com/title/tt0118884/",
    "https://www.undermind.ai/",
    "https://www.brvds.com/en/",
    "https://x.com/gencfonlari/status/2042892464789299223",
    "https://x.com/dogalyasalar/status/2043625142148870165",
    "https://x.com/sefauygunn/status/2043617021833711617",
    "https://x.com/MrCeylan1907_/status/2043785120964874551",
    "https://x.com/ufuk24/status/2044126015341908053",
    "https://www.transfermarkt.com/nico-gonzalez/profil/spieler/486031",
    "https://x.com/nisamisa777/status/2044011962023989494",
    "https://x.com/midnight_animal/status/2044388345845895600",
    "https://x.com/AvBirant/status/2044111575523500420",
    "https://x.com/kirillk_web3/status/2044001467833426003",
    "https://x.com/BoringBiz_/status/2044387496864137483",
    "https://x.com/Dexerto/status/2044727461397549125",
    "https://x.com/jwegener/status/2044891266618659051",
    "https://x.com/redhairshanks86/status/2045170794209103984",
    "https://x.com/sefauygunn/status/2045184360991621176",
    "https://x.com/soigomaa/status/2045066043820052956",
    "https://x.com/CagriKent/status/2045927366858244569",
    "https://x.com/mrledtasso/status/2045887684468412597",
    "https://x.com/heynavtoor/status/2045826159636824423",
    "https://x.com/AlphaCartell/status/2046294992713646576",
    "https://x.com/themakinaci/status/2046619244272497025",
    "https://x.com/0xBriann/status/2046731206704922654",
    "https://x.com/girisimcihisler/status/2047417224894251135",
    "https://www.instagram.com/reel/DVJm6gGjaGr/",
    "https://x.com/kevin2kelly/status/2047405219751895549",
    "https://x.com/dogalmaxx/status/2047267586044207339",
    "https://x.com/HonitelHQ/status/2047330160903389541",
    "https://x.com/0xleegenz/status/2047624090538873156",
    "https://x.com/mogulinfluence/status/2048841260002140203",
    "https://x.com/SIGMAPROFESSOR/status/2049377138038731068",
    "https://x.com/signulll/status/2049548233832042781",
    "https://x.com/_PALEBLUEEARTH/status/2049458842585686340",
    "https://x.com/AydnPamuk6/status/2049732218344333813",
    "https://x.com/noisyb0y1/status/2049584756359115099",
    "https://x.com/anishmoonka/status/2050960825251475478",
    "https://x.com/deadshotXBT/status/2050808727930831076",
    "https://x.com/matthewwmullin/status/2050945938999431592",
    "https://x.com/itsolelehmann/status/2050548948419645488",
    "https://t24.com.tr/yazarlar/cemal-tuncdemir/kitaplarda-okuduklarimizi-unutuyorsak-hala-neden-okumaliyiz,21516",
    "https://x.com/yapayzekahocasi/status/2051578855136084262",
    "https://x.com/steipete/status/2051900143339704730",
    "https://memory.cobanov.dev/",
]

# ══════════════════════════════════════════════════════════════════════
#  YARDIMCI
# ══════════════════════════════════════════════════════════════════════

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
HDR = {"User-Agent": UA, "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5"}

def slugify(t: str, maxlen: int = 75) -> str:
    t = re.sub(r"[^\w\s-]", "", t.lower())
    return re.sub(r"[\s_-]+", "-", t).strip("-")[:maxlen] or "untitled"

def tw_username(url: str) -> str:
    m = re.search(r"(?:x|twitter)\.com/([^/?\s]+)", url, re.I)
    return m.group(1).lower() if m else ""

def tweet_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", url)
    return m.group(1) if m else ""

def ig_shortcode(url: str) -> str:
    m = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else ""

def url_kind(url: str) -> str:
    if tweet_id(url): return "twitter"
    if ig_shortcode(url): return "instagram"
    if "youtube.com" in url or "youtu.be" in url: return "youtube"
    return "web"

def dedup(urls):
    seen, out = set(), []
    for u in urls:
        base = re.sub(r"\?.*", "", u).rstrip("/")
        if base and base not in seen:
            seen.add(base); out.append(u)
    return out

# ══════════════════════════════════════════════════════════════════════
#  TWITTER SYNDICATION (login-free)
# ══════════════════════════════════════════════════════════════════════

_B36 = "0123456789abcdefghijklmnopqrstuvwxyz"

def _b36_int(n: int) -> str:
    if n == 0: return "0"
    s = ""
    while n: s = _B36[n % 36] + s; n //= 36
    return s

def syndication_token(tid: str) -> str:
    """Twitter'ın public syndication endpoint'i için tweet ID'den token üretir."""
    x = (int(tid) / 1e15) * math.pi
    i, f = divmod(x, 1)
    s_int = _b36_int(int(i))
    s_frac = ""
    for _ in range(15):
        f *= 36
        d = int(f)
        s_frac += _B36[d]
        f -= d
    return re.sub(r"0+|\.", "", s_int + "." + s_frac)

def fetch_tweet_sync(tid: str) -> dict:
    """Login'siz tweet metni + author + likes + media."""
    tok = syndication_token(tid)
    url = (f"https://cdn.syndication.twimg.com/tweet-result"
           f"?id={tid}&token={tok}&lang=en")
    try:
        req = request.Request(url, headers={**HDR, "Accept": "application/json"})
        with request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        if not d or "text" not in d: return {}
        return {
            "text":   d.get("text", ""),
            "author": d.get("user", {}).get("screen_name", ""),
            "name":   d.get("user", {}).get("name", ""),
            "likes":  d.get("favorite_count", 0),
            "date":   d.get("created_at", ""),
            "quoted": (d.get("quoted_tweet") or {}).get("text", ""),
        }
    except (error.HTTPError, error.URLError, json.JSONDecodeError, TimeoutError):
        return {}

# ══════════════════════════════════════════════════════════════════════
#  GENEL WEB META
# ══════════════════════════════════════════════════════════════════════

class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.title=""; self.desc=""; self._t=False
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title": self._t = True
        if tag == "meta":
            p = d.get("property","") or d.get("name","")
            v = d.get("content","")
            if p in ("og:title","twitter:title") and not self.title: self.title = v
            if p in ("og:description","description","twitter:description") and not self.desc:
                self.desc = v[:600]
    def handle_data(self, s):
        if self._t and not self.title: self.title = s.strip()
    def handle_endtag(self, tag):
        if tag == "title": self._t = False

def fetch_meta_sync(url: str) -> dict:
    if "youtube.com" in url or "youtu.be" in url:
        try:
            oe = f"https://www.youtube.com/oembed?url={parse.quote(url)}&format=json"
            with request.urlopen(request.Request(oe, headers=HDR), timeout=8) as r:
                d = json.loads(r.read())
            return {"title": d.get("title",""), "desc": f"YouTube · {d.get('author_name','')}"}
        except Exception:
            return {"title":"", "desc":""}
    try:
        with request.urlopen(request.Request(url, headers=HDR), timeout=8) as r:
            if "text/html" not in r.headers.get("Content-Type",""):
                return {"title":"", "desc":""}
            html = r.read(80000).decode("utf-8", errors="ignore")
        p = _MetaParser(); p.feed(html)
        return {"title": p.title, "desc": p.desc}
    except Exception:
        return {"title":"", "desc":""}

# ══════════════════════════════════════════════════════════════════════
#  INSTAGRAM (opsiyonel)
# ══════════════════════════════════════════════════════════════════════

_IL = None
def _ig_loader():
    global _IL
    if _IL is not None: return _IL
    if not INSTAGRAM_USER:
        _IL = False; return False
    try:
        import instaloader
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "instaloader", "-q"])
        import instaloader
    L = instaloader.Instaloader(quiet=True, download_pictures=False,
        download_videos=False, save_metadata=False, download_comments=False,
        download_geotags=False, download_video_thumbnails=False)
    try:
        L.login(INSTAGRAM_USER, INSTAGRAM_PASS)
    except Exception as e:
        print(f"  [ig] login failed: {e}"); _IL = False; return False
    _IL = L; return L

def fetch_ig_sync(sc: str) -> dict:
    L = _ig_loader()
    if not L: return {}
    try:
        import instaloader
        post = instaloader.Post.from_shortcode(L.context, sc)
        return {
            "text":   (post.caption or "")[:500],
            "author": post.owner_username,
            "likes":  post.likes,
        }
    except Exception:
        return {}

# ══════════════════════════════════════════════════════════════════════
#  PARALEL FETCH
# ══════════════════════════════════════════════════════════════════════

async def fetch_all(urls: list) -> dict:
    """url → {text, author, likes, title, desc, kind}"""
    sem = asyncio.Semaphore(FETCH_CONCURRENCY)
    loop = asyncio.get_event_loop()
    pool = ThreadPoolExecutor(max_workers=FETCH_CONCURRENCY)

    async def one(url):
        async with sem:
            kind = url_kind(url)
            if kind == "twitter":
                d = await loop.run_in_executor(pool, fetch_tweet_sync, tweet_id(url))
                return url, {"kind": "twitter", **d}
            if kind == "instagram":
                d = await loop.run_in_executor(pool, fetch_ig_sync, ig_shortcode(url))
                return url, {"kind": "instagram", **d}
            m = await loop.run_in_executor(pool, fetch_meta_sync, url)
            return url, {"kind": kind, **m}

    print(f"[fetch] {len(urls)} URL paralel çekiliyor (max {FETCH_CONCURRENCY})...")
    results = {}
    done = 0
    for coro in asyncio.as_completed([one(u) for u in urls]):
        url, data = await coro
        results[url] = data
        done += 1
        if done % 20 == 0: print(f"  {done}/{len(urls)}")
    pool.shutdown(wait=False)
    return results

# ══════════════════════════════════════════════════════════════════════
#  AI BATCH CLASSIFY (OpenRouter)
# ══════════════════════════════════════════════════════════════════════

def _ai_request(payload: dict) -> str:
    body = json.dumps(payload).encode()
    hdrs = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vault-builder.local",
        "X-Title": "Vault Builder v5",
    }
    req = request.Request("https://openrouter.ai/api/v1/chat/completions",
                          data=body, headers=hdrs)
    with request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]

def ai_classify_batch(items: list) -> list:
    """
    items: [{idx, url, kind, author, title, content}]
    returns: [{idx, topic, concepts:[...], summary}]
    """
    topics_str = "\n".join(f"- {t}" for t in TOPICS)
    payload_items = [
        {
            "idx": it["idx"],
            "url": it["url"],
            "kind": it["kind"],
            "author": it.get("author",""),
            "title": (it.get("title","") or "")[:200],
            "content": (it.get("content","") or "")[:600],
        }
        for it in items
    ]
    prompt = f"""You are classifying bookmarks for a personal Obsidian knowledge graph.

For each item, output exactly:
- topic: ONE of the allowed topics (verbatim)
- concepts: 2-4 short kebab-case tags (lowercase, dashed). These become wiki-links and should be REUSABLE across notes (e.g. "prompt-engineering", "vector-db", "stoicism", "saas-pricing"). Avoid hyper-specific or proper-noun-only tags.
- summary: 1-2 sentence English summary. Inline-link concepts using [[double-brackets]] when they appear. If content is empty, infer from URL/author/title.

Allowed topics:
{topics_str}

Return a JSON array, one object per input item, no markdown, no commentary:
[{{"idx": 0, "topic": "...", "concepts": ["...","..."], "summary": "..."}}, ...]

Input items:
{json.dumps(payload_items, ensure_ascii=False)}
"""
    try:
        raw = _ai_request({
            "model": OPENROUTER_MODEL,
            "messages": [{"role":"user","content":prompt}],
            "max_tokens": 2000,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},  # bazı modeller saygı duyuyor
        })
    except Exception as e:
        print(f"  [ai] hata: {e}")
        return [{"idx": it["idx"], "topic":"Uncategorized","concepts":[],"summary":""} for it in items]

    raw = re.sub(r"```(?:json)?|```", "", raw).strip()
    # bazı modeller {array: [...]} döndürebiliyor
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", raw, re.S)
        parsed = json.loads(m.group(0)) if m else []
    if isinstance(parsed, dict):
        for k in ("results","items","data","array"):
            if k in parsed and isinstance(parsed[k], list):
                parsed = parsed[k]; break
        else:
            parsed = list(parsed.values())[0] if parsed else []

    out = []
    for r in parsed if isinstance(parsed, list) else []:
        topic = r.get("topic","Uncategorized")
        if topic not in TOPICS: topic = "Uncategorized"
        concepts = [slugify(c, 40) for c in (r.get("concepts") or [])][:4]
        concepts = [c for c in concepts if c and len(c) > 1]
        out.append({
            "idx": r.get("idx", -1),
            "topic": topic,
            "concepts": concepts,
            "summary": (r.get("summary") or "").strip(),
        })
    return out

def ai_classify_all(items: list) -> dict:
    """idx → result. Batch'lere böler."""
    by_idx = {}
    total = len(items)
    for i in range(0, total, BATCH_SIZE):
        chunk = items[i:i+BATCH_SIZE]
        print(f"[ai] batch {i//BATCH_SIZE + 1}/{(total + BATCH_SIZE - 1)//BATCH_SIZE} "
              f"({len(chunk)} item)...")
        res = ai_classify_batch(chunk)
        for r in res:
            by_idx[r["idx"]] = r
        time.sleep(0.5)
    # eksik idx'ler için fallback
    for it in items:
        if it["idx"] not in by_idx:
            by_idx[it["idx"]] = {"idx": it["idx"], "topic":"Uncategorized","concepts":[],"summary":""}
    return by_idx

# ══════════════════════════════════════════════════════════════════════
#  YAZMA — atomic notes + hub stubs + MOC
# ══════════════════════════════════════════════════════════════════════

DIR_NOTES    = "01 - Notes"
DIR_PEOPLE   = "02 - People"
DIR_TOPICS   = "03 - Topics"
DIR_CONCEPTS = "04 - Concepts"
DIR_MOC      = "00 - MOCs"

def ensure_dirs():
    for d in (DIR_NOTES, DIR_PEOPLE, DIR_TOPICS, DIR_CONCEPTS, DIR_MOC):
        (VAULT / d).mkdir(parents=True, exist_ok=True)

def ensure_topic_hub(topic: str):
    fp = VAULT / DIR_TOPICS / f"{topic}.md"
    if fp.exists(): return
    fp.write_text(
        f"---\ntype: topic\n---\n\n# {topic}\n\n"
        f"> Topic hub. Linked notes appear in backlinks.\n\n"
        f"```dataview\nLIST FROM \"{DIR_NOTES}\" WHERE topic = \"{topic}\" SORT date DESC\n```\n",
        encoding="utf-8",
    )

def ensure_concept_stub(concept: str):
    fp = VAULT / DIR_CONCEPTS / f"{concept}.md"
    if fp.exists(): return
    fp.write_text(
        f"---\ntype: concept\n---\n\n# {concept}\n\n"
        f"> *Auto-generated stub. Notes referencing this concept appear in backlinks.*\n",
        encoding="utf-8",
    )

def ensure_person_stub(username: str, display: str = ""):
    fp = VAULT / DIR_PEOPLE / f"@{username}.md"
    if fp.exists(): return
    name = display or username
    fp.write_text(
        f"---\ntype: person\nhandle: \"@{username}\"\n---\n\n"
        f"# @{username}{f' — {name}' if display and display != username else ''}\n\n"
        f"> *Auto-generated. Notes from this account appear in backlinks.*\n\n"
        f"https://x.com/{username}\n",
        encoding="utf-8",
    )

def write_note(url: str, kind: str, fetched: dict, ai: dict, idx: int) -> Path:
    author   = fetched.get("author", "") or fetched.get("name","")
    likes    = fetched.get("likes", 0)
    text     = fetched.get("text", "") or fetched.get("desc", "")
    title    = fetched.get("title", "") or (text[:70] + "..." if text else url)
    quoted   = fetched.get("quoted", "")
    topic    = ai.get("topic","Uncategorized")
    concepts = ai.get("concepts", [])
    summary  = ai.get("summary", "") or (text[:200] if text else "")

    # filename
    if kind == "twitter":
        base = f"tweet-{tweet_id(url)}-{slugify(author or 'x', 30)}"
    elif kind == "instagram":
        base = f"ig-{ig_shortcode(url)}"
    elif kind == "youtube":
        base = f"yt-{slugify(title, 60)}"
    else:
        base = slugify(title or url, 70)
    fp = VAULT / DIR_NOTES / f"{base}.md"
    if fp.exists() and fp.read_text(encoding="utf-8", errors="ignore").strip():
        return fp  # idempotent

    # frontmatter (Obsidian Properties uyumlu)
    fm_lines = ["---"]
    fm_lines.append(f'title: "{(title or url).replace(chr(34),chr(39))[:200]}"')
    fm_lines.append(f"url: {url}")
    fm_lines.append(f"source: {kind}")
    fm_lines.append(f"topic: \"{topic}\"")
    if author: fm_lines.append(f'author: "@{author}"')
    if likes:  fm_lines.append(f"likes: {likes}")
    fm_lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    fm_lines.append("tags:")
    fm_lines.append(f"  - source/{kind}")
    fm_lines.append(f"  - topic/{slugify(topic, 40)}")
    for c in concepts:
        fm_lines.append(f"  - concept/{c}")
    fm_lines.append("---")
    fm = "\n".join(fm_lines)

    # body — graph edges
    body = [f"\n# {title}\n"]
    if summary:
        body.append(f"> {summary}\n")
    if author:
        body.append(f"**Author:** [[@{author}]]")
    body.append(f"**Topic:** [[{topic}]]")
    if concepts:
        body.append("**Concepts:** " + " · ".join(f"[[{c}]]" for c in concepts))
    body.append("")
    if text and kind in ("twitter", "instagram"):
        body.append("---\n")
        body.append("```")
        body.append(text.strip())
        body.append("```\n")
        if quoted:
            body.append("**Quoted:**\n```\n" + quoted.strip() + "\n```\n")
    if likes:
        body.append(f"❤️ {likes:,}")
    body.append(f"\n**Source:** {url}\n")

    fp.write_text(fm + "\n".join(body), encoding="utf-8")

    # hub stubs
    for c in concepts: ensure_concept_stub(c)
    ensure_topic_hub(topic)
    if author: ensure_person_stub(author, fetched.get("name",""))
    return fp

# ══════════════════════════════════════════════════════════════════════
#  MASTER MOC
# ══════════════════════════════════════════════════════════════════════

def write_master_moc():
    fp = VAULT / DIR_MOC / "Master MOC.md"
    lines = [
        "---", "type: moc", "---", "",
        f"# Master MOC", "",
        f"> Generated {datetime.now():%Y-%m-%d %H:%M}", "",
        "## Topics", "",
        "```dataview",
        f'TABLE length(rows) AS "Notes" FROM "{DIR_NOTES}" GROUP BY topic SORT length(rows) DESC',
        "```", "",
        "## People (most-linked)", "",
        "```dataview",
        f'TABLE length(rows) AS "Notes" FROM "{DIR_NOTES}" '
        f'WHERE author GROUP BY author SORT length(rows) DESC LIMIT 30',
        "```", "",
        "## Concepts", "",
        f'See [[{DIR_CONCEPTS}]] folder. Most-referenced concepts:', "",
        "```dataview",
        f'TABLE length(rows) AS "Refs" FROM "{DIR_NOTES}" '
        f'FLATTEN file.tags AS t WHERE startswith(t, "#concept/") '
        f'GROUP BY t SORT length(rows) DESC LIMIT 25',
        "```", "",
        "## Recent", "",
        "```dataview",
        f'LIST FROM "{DIR_NOTES}" SORT date DESC LIMIT 30',
        "```", "",
    ]
    fp.write_text("\n".join(lines), encoding="utf-8")

# ══════════════════════════════════════════════════════════════════════
#  SAFARI TABS (macOS)
# ══════════════════════════════════════════════════════════════════════

def get_safari_tabs() -> list:
    if sys.platform != "darwin": return []
    try:
        res = subprocess.run(["osascript", "-e", '''
set o to ""
tell application "Safari"
    repeat with w in windows
        repeat with t in tabs of w
            set o to o & (URL of t) & "\n"
        end repeat
    end repeat
end tell
return o'''], capture_output=True, text=True, timeout=10)
        return [u.strip() for u in res.stdout.strip().split("\n") if u.strip().startswith("http")]
    except Exception:
        return []

# ══════════════════════════════════════════════════════════════════════
#  CHECKPOINT
# ══════════════════════════════════════════════════════════════════════

def cp_load() -> set:
    if CHECKPOINT.exists():
        try: return set(json.loads(CHECKPOINT.read_text()))
        except Exception: return set()
    return set()

def cp_save(done: set):
    CHECKPOINT.write_text(json.dumps(sorted(done)))

# ══════════════════════════════════════════════════════════════════════
#  MOD: quick / fetch / rebuild
# ══════════════════════════════════════════════════════════════════════

def url_to_item(idx: int, url: str, fetched: dict) -> dict:
    return {
        "idx":     idx,
        "url":     url,
        "kind":    fetched.get("kind", url_kind(url)),
        "author":  fetched.get("author") or fetched.get("name") or tw_username(url),
        "title":   fetched.get("title", ""),
        "content": fetched.get("text") or fetched.get("desc", ""),
    }

def run_quick(urls: list):
    """Fetch yok, AI yok. Sadece username heuristic + topic=Uncategorized."""
    ensure_dirs()
    print(f"[quick] {len(urls)} URL → vault\n")
    for i, url in enumerate(urls):
        kind = url_kind(url)
        author = tw_username(url) if kind == "twitter" else ""
        write_note(url, kind, {"author": author}, {"topic":"Uncategorized","concepts":[],"summary":""}, i)
    write_master_moc()
    print(f"\n→ {VAULT}")

def run_fetch(urls: list):
    ensure_dirs()
    done = cp_load()
    remaining = [u for u in urls if u not in done]
    print(f"[fetch] toplam={len(urls)} done={len(done)} kalan={len(remaining)}\n")
    if not remaining:
        write_master_moc(); print("Hepsi tamam."); return

    fetched = asyncio.run(fetch_all(remaining))

    items = [url_to_item(i, u, fetched.get(u, {})) for i, u in enumerate(remaining)]

    use_ai = OPENROUTER_KEY and not OPENROUTER_KEY.startswith("sk-or-...")
    if use_ai:
        ai_results = ai_classify_all(items)
    else:
        print("[ai] OPENROUTER_KEY yok, AI atlandı, hepsi Uncategorized.")
        ai_results = {it["idx"]: {"topic":"Uncategorized","concepts":[],"summary":""} for it in items}

    print("\n[write] notlar yazılıyor...")
    for it in items:
        url = it["url"]
        write_note(url, it["kind"], fetched.get(url, {}), ai_results.get(it["idx"], {}), it["idx"])
        done.add(url); cp_save(done)

    write_master_moc()
    CHECKPOINT.unlink(missing_ok=True)
    print(f"\n→ {VAULT}")

def run_rebuild():
    """Mevcut notları okuyup MOC + hub stub'ları yeniden üretir."""
    ensure_dirs()
    notes_dir = VAULT / DIR_NOTES
    if not notes_dir.exists():
        print("Notes klasörü yok."); return
    n = 0
    for fp in notes_dir.glob("*.md"):
        try:
            txt = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        m = re.search(r"^topic:\s*\"?([^\"\n]+)\"?", txt, re.M)
        if m: ensure_topic_hub(m.group(1).strip())
        m = re.search(r"^author:\s*\"?@?([^\"\n]+)\"?", txt, re.M)
        if m: ensure_person_stub(m.group(1).strip())
        for c in re.findall(r"concept/([\w-]+)", txt):
            ensure_concept_stub(c)
        n += 1
    write_master_moc()
    print(f"[rebuild] {n} not tarandı, hub'lar tazelendi.")

# ══════════════════════════════════════════════════════════════════════

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "fetch"

    if mode == "rebuild":
        run_rebuild(); return

    print("[urls] toplanıyor...")
    safari = get_safari_tabs()
    print(f"  Mac Safari: {len(safari)} tab")
    urls = dedup(APPLE_NOTES_LINKS + IPHONE_TABS + safari)
    print(f"  Toplam (dedup): {len(urls)}\n")

    if mode == "quick":
        run_quick(urls)
    elif mode == "fetch":
        run_fetch(urls)
    else:
        print("Kullanım: python3 vault_builder_v5.py [fetch|quick|rebuild]")

if __name__ == "__main__":
    main()
