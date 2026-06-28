# -*- coding: utf-8 -*-
"""BUBE V1 매매법 — 상세 흐름도 SVG 생성기.
한 거래 사이클(장 시작 전 레짐 판정 → 엔진 선택 → 진입 → 갭필터 → VIX 사이징 → 청산)을
위에서 아래로 따라가는 플로우차트. 결과물: assets/v1_method.svg
"""
import os

W = 1300
S = []
def A(s): S.append(s)
def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text_w(s, fs):
    """대략적 텍스트 폭(px) 추정 — 한글/CJK는 ~1.0em, ASCII는 ~0.55em, 공백 ~0.3em."""
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.30
        elif ord(ch) > 0x2000:   # CJK·전각·특수기호
            w += 1.0
        else:
            w += 0.55
    return w * fs

# ---- palette (v1_journey와 동일 계열)
BG0, BG1 = "#0d1117", "#161d29"
CARD, CARD_STK = "#1b2533", "#2c3a4e"
GOLD, CYAN, AMBER, GREEN, RED = "#f5c84b", "#4cc9f0", "#ff9242", "#5fd38b", "#ef5a6f"
BLUE = "#5b8def"
TXT, MUT = "#e8eef6", "#9fb0c3"
FONT = "'Malgun Gothic','Segoe UI',sans-serif"

# ---- helpers --------------------------------------------------------------
def card(x, y, w, h, c, fill=CARD, op=1.0):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" fill-opacity="{op}" stroke="{c}" stroke-opacity="0.85" stroke-width="1.4"/>')
    A(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{c}"/>')

def title_line(x, y, c, t, fs=18, w="700"):
    A(f'<text x="{x}" y="{y}" font-size="{fs}" font-weight="{w}" fill="{c}">{esc(t)}</text>')

def body_line(x, y, t, c=TXT, fs=13.5):
    A(f'<text x="{x}" y="{y}" font-size="{fs}" fill="{c}">{esc(t)}</text>')

def arrow(x, y1, y2, c=MUT, label=None, lc=None):
    A(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2-9}" stroke="{c}" stroke-width="2.4" marker-end="url(#arw)"/>')
    if label:
        lw = 16 + len(label) * 7.4
        A(f'<rect x="{x+10}" y="{(y1+y2)/2-13}" width="{lw:.0f}" height="24" rx="12" fill="{(lc or c)}" fill-opacity="0.15" stroke="{(lc or c)}" stroke-opacity="0.7"/>')
        A(f'<text x="{x+10+lw/2:.0f}" y="{(y1+y2)/2+4}" font-size="12.5" font-weight="700" fill="{(lc or c)}" text-anchor="middle">{esc(label)}</text>')

def stage_header(y, num, title, desc, c):
    A(f'<circle cx="76" cy="{y-6}" r="15" fill="{c}" fill-opacity="0.18" stroke="{c}" stroke-width="2"/>')
    A(f'<text x="76" y="{y-1}" font-size="15" font-weight="800" fill="{c}" text-anchor="middle">{num}</text>')
    title_line(102, y, TXT, title, fs=19, w="800")
    if desc:
        dx = 102 + text_w(title, 19) + 20
        A(f'<text x="{dx:.0f}" y="{y}" font-size="13.5" fill="{MUT}">{esc(desc)}</text>')

# ---- canvas height is computed as we go; build body then wrap -------------
B = []  # body elements (so we can compute H before header rect)
def AB(s): B.append(s)

cx = W / 2     # center spine x for arrows

# ===== HEADER =====
A('<DEFS_PLACEHOLDER>')
A(f'<rect width="{W}" height="HEIGHT_PLACEHOLDER" fill="url(#bg)"/>')
A(f'<text x="60" y="76" font-size="38" font-weight="800" fill="{TXT}">BUBE V1 매매법 — 상세 흐름도</text>')
A(f'<text x="62" y="108" font-size="18" fill="{GOLD}" font-weight="600">SOXL 3× 레버리지 · 매일 한 사이클: 레짐 판정 → 엔진 선택 → 돌파 진입 → 갭필터 → VIX 사이징 → 청산</text>')
# legend
leg = [("BULL/NEUTRAL", GREEN), ("BEAR", RED), ("롱변기", CYAN), ("양변기", GOLD), ("황금변기", AMBER)]
lx = 62
for name, c in leg:
    w = 38 + text_w(name, 13)
    A(f'<rect x="{lx}" y="126" width="{w:.0f}" height="26" rx="13" fill="{c}" fill-opacity="0.16" stroke="{c}" stroke-opacity="0.6"/>')
    A(f'<circle cx="{lx+15}" cy="139" r="4.5" fill="{c}"/>')
    A(f'<text x="{lx+27}" y="144" font-size="13" fill="{c}" font-weight="600">{esc(name)}</text>')
    lx += w + 12

y = 196  # running cursor

# ===== STAGE 0: 레짐 판정 =====
stage_header(y, "0", "장 시작 전 — 매일 레짐(시장 국면) 판정", "전부 전일(T−1) 데이터 사용 · 미래 정보 누설 0", BLUE)
y += 20
# three input cards feeding the regime
inp = [
    ("📈 추세 합의", BLUE, ["QQQ · SPY · SMH 의", "200일선 ±2% 밴드", "3개 중 2개 이상 합의"]),
    ("⚡ 빠른 곰장 신호", RED, ["VIX9D / VIX > 1.05", "  또는", "SOXL 5일 모멘텀 < −10%"]),
    ("🛡 안정 장치", MUT, ["dwell 5일 = 전환 최소 유지", "(레짐 깜빡임 방지)", "max_bear 90일 → 황금변기"]),
]
iw, ig = 393, 30
ix0 = 60
ih = 116
for i, (t, c, lines) in enumerate(inp):
    x = ix0 + i * (iw + ig)
    card(x, y, iw, ih, c)
    title_line(x + 22, y + 32, c, t, fs=16, w="700")
    A(f'<line x1="{x+22}" y1="{y+44}" x2="{x+iw-22}" y2="{y+44}" stroke="{CARD_STK}"/>')
    yy = y + 68
    for ln in lines:
        body_line(x + 22, yy, ln, c=TXT, fs=13.5); yy += 22
y += ih + 22
arrow(cx, y - 14, y + 18, c=MUT, label="종합 판정", lc=BLUE)
y += 30

# regime result row: BULL / NEUTRAL / BEAR
reg = [("🟢 BULL", GREEN, "상승장"), ("🟡 NEUTRAL", GOLD, "중립장"), ("🔴 BEAR", RED, "하락장")]
rw, rg = 393, 30
rh = 56
for i, (t, c, sub) in enumerate(reg):
    x = ix0 + i * (rw + rg)
    card(x, y, rw, rh, c, fill=c, op=0.12)
    title_line(x + 22, y + 36, c, t, fs=20, w="800")
    A(f'<text x="{x+rw-22}" y="{y+36}" font-size="14" fill="{MUT}" text-anchor="end">{esc(sub)}</text>')
y += rh + 18

# ===== STAGE 1: 엔진 선택 =====
stage_header(y + 8, "1", "엔진 선택 — 레짐이 매매 엔진을 결정", "", GOLD)
y += 24
# arrows from each regime to engine (simple vertical)
eng = [
    ("롱변기 (Long-byungi)", CYAN, "BULL · NEUTRAL", "SOXL 단방향 매수", "추세 추종"),
    ("양변기 v5 (Yang-byungi)", GOLD, "BEAR", "SOXL 롱 + SOXS 숏 페어", "평균회귀 보유"),
    ("황금변기 (Golden-byungi)", AMBER, "BEAR 90일↑", "SOXL 변동성 돌파", "tail 보험 (실데이터 0회)"),
]
y += 12
for i in range(3):
    x = ix0 + i * (rw + rg) + rw / 2
    arrow(x, y - 18, y + 16, c=reg[i][1])
y += 28
eh = 102
for i, (t, c, frm, what, kind) in enumerate(eng):
    x = ix0 + i * (rw + rg)
    card(x, y, rw, eh, c)
    title_line(x + 22, y + 32, c, t, fs=17, w="700")
    pw = 24 + text_w(frm, 12.5)
    A(f'<rect x="{x+rw-22-pw:.0f}" y="{y+14}" width="{pw:.0f}" height="24" rx="12" fill="{c}" fill-opacity="0.18" stroke="{c}" stroke-opacity="0.6"/>')
    A(f'<text x="{x+rw-22-pw/2:.0f}" y="{y+31}" font-size="12.5" font-weight="700" fill="{c}" text-anchor="middle">{esc(frm)}</text>')
    A(f'<line x1="{x+22}" y1="{y+44}" x2="{x+rw-22}" y2="{y+44}" stroke="{CARD_STK}"/>')
    body_line(x + 22, y + 68, what, c=TXT, fs=14.5)
    body_line(x + 22, y + 90, "성격: " + kind, c=MUT, fs=13)
y += eh + 18

# ===== STAGE 2: 진입 규칙 =====
stage_header(y + 8, "2", "진입 — 09:35 ET · 전부 stop-buy 변동성 돌파 (딥매수 아님)", "", GREEN)
y += 24
ent = [
    ("롱변기 진입", CYAN, ["시가 대비 +1.5% 돌파 시", "추격 매수 (buy-stop)", "→ 강갭업엔 marketable-limit"]),
    ("양변기 진입", GOLD, ["SOXL: 시가 +1.5% 돌파 매수", "SOXS: 시가 +6% 돌파 매수", "(인버스 매수 = 합성 숏)"]),
    ("황금변기 진입", AMBER, ["Keltner 상단 밴드 돌파 시", "변동성 K-vol 돌파 매수", "장기 L자 곰장 방어용"]),
]
y += 12
for i in range(3):
    x = ix0 + i * (rw + rg) + rw / 2
    arrow(x, y - 18, y + 12, c=eng[i][1])
y += 24
e2h = 102
for i, (t, c, lines) in enumerate(ent):
    x = ix0 + i * (rw + rg)
    card(x, y, rw, e2h, c)
    title_line(x + 22, y + 30, c, t, fs=16, w="700")
    A(f'<line x1="{x+22}" y1="{y+40}" x2="{x+rw-22}" y2="{y+40}" stroke="{CARD_STK}"/>')
    yy = y + 62
    for ln in lines:
        body_line(x + 22, yy, ln, c=TXT, fs=13.5); yy += 21
y += e2h + 20

# ===== STAGE 2.5: 갭필터 =====
stage_header(y + 8, "3", "갭필터 — 비대칭 A안 (2026-06-03)", "나쁜 진입만 거르고 좋은 진입은 살린다", AMBER)
y += 22
gh = 74
# left: SOXL long side, right: SOXS short side
gx2 = ix0 + (rw + rg)  # split into two halves of full width
half = (rw * 3 + rg * 2 - rg) / 2
card(ix0, y, half, gh, GREEN)
title_line(ix0 + 22, y + 30, GREEN, "롱변기 · 양변기롱 (SOXL 매수)", fs=15, w="700")
body_line(ix0 + 22, y + 54, "갭다운 −5% 이하만 진입 차단 · 갭업은 허용 (정상보다 ~2배 좋은 진입)", c=TXT, fs=13.5)
card(ix0 + half + rg, y, half, gh, RED)
title_line(ix0 + half + rg + 22, y + 30, RED, "양변기숏 (SOXS 매수)", fs=15, w="700")
body_line(ix0 + half + rg + 22, y + 54, "대칭 차단 유지 · |갭| > 5% 면 진입 차단 (양방향)", c=TXT, fs=13.5)
y += gh + 18
arrow(cx, y - 14, y + 18, c=MUT, label="진입 확정분에 비중 적용", lc=GOLD)
y += 30

# ===== STAGE 3: VIX 사이징 =====
stage_header(y + 6, "4", "VIX 동적 비중 — 변동성이 노출을 정한다", "전일 VIX 기준 · 마진 미사용 (cap 1.0)", GOLD)
y += 20
sh = 168
# formula card (left, wide) + table (right)
fw = rw * 2 + rg
card(ix0, y, fw, sh, GOLD)
title_line(ix0 + 22, y + 34, GOLD, "비중 공식", fs=16, w="700")
A(f'<text x="{ix0+22}" y="{y+72}" font-size="17" font-family="monospace" fill="{TXT}">k = 0.60 × clip( 20 / VIX , 0.5 , 2.0 )</text>')
A(f'<text x="{ix0+22}" y="{y+102}" font-size="17" font-family="monospace" fill="{TXT}">alloc = min( k × 엔진비중 , 1.0 )</text>')
body_line(ix0 + 22, y + 134, "VIX↑ (공포) → 비중↓   ·   VIX↓ (안정) → 비중↑", c=CYAN, fs=14)
body_line(ix0 + 22, y + 156, "margin 0% — 최대 100% 현금 한도, broker 강제청산 원천 차단", c=MUT, fs=13)
# table (right card)
tx = ix0 + fw + rg
card(tx, y, rw, sh, CYAN)
title_line(tx + 22, y + 30, CYAN, "VIX → 비중 직관", fs=15, w="700")
rows = [("VIX 10", "scale 2.0", "풀로딩", GREEN),
        ("VIX 20", "scale 1.0", "중립", GOLD),
        ("VIX 40", "scale 0.5", "디리스킹", AMBER),
        ("VIX 80", "lo clip", "최소", RED)]
yy = y + 58
for a, b, cmt, c in rows:
    A(f'<text x="{tx+22}" y="{yy}" font-size="13.5" font-family="monospace" fill="{TXT}">{esc(a)}</text>')
    A(f'<text x="{tx+128}" y="{yy}" font-size="13" fill="{MUT}">{esc(b)}</text>')
    A(f'<text x="{tx+rw-22}" y="{yy}" font-size="13.5" font-weight="700" fill="{c}" text-anchor="end">{esc(cmt)}</text>')
    yy += 28
y += sh + 18
arrow(cx, y - 14, y + 18, c=MUT, label="당일 보유 → 청산", lc=GREEN)
y += 30

# ===== STAGE 4: 청산 =====
stage_header(y + 6, "5", "청산 / 보유 — 엔진별 출구", "", GREEN)
y += 20
ext = [
    ("롱변기 청산", CYAN, ["−8% 하드스톱 (장중 손절)", "익일 시가(MOO) 청산", "손절이 약 = 추세 추종형"]),
    ("양변기 청산", GOLD, ["종가(LOC) 청산", "손실분 overnight carry →", "익일 반등 평균회귀 알파"]),
    ("황금변기 청산", AMBER, ["변동성 밴드 이탈 시", "곰장 종료까지 보유", "tail 위험 흡수"]),
]
y += 12
for i in range(3):
    x = ix0 + i * (rw + rg) + rw / 2
    arrow(x, y - 18, y + 12, c=ext[i][1])
y += 24
x4h = 102
for i, (t, c, lines) in enumerate(ext):
    x = ix0 + i * (rw + rg)
    card(x, y, rw, x4h, c)
    title_line(x + 22, y + 30, c, t, fs=16, w="700")
    A(f'<line x1="{x+22}" y1="{y+40}" x2="{x+rw-22}" y2="{y+40}" stroke="{CARD_STK}"/>')
    yy = y + 62
    for ln in lines:
        body_line(x + 22, yy, ln, c=TXT, fs=13.5); yy += 21
y += x4h + 24

# ===== FOOTER =====
A(f'<rect x="60" y="{y}" width="{W-120}" height="86" rx="12" fill="{GOLD}" fill-opacity="0.08" stroke="{GOLD}" stroke-opacity="0.45"/>')
A(f'<text x="84" y="{y+32}" font-size="15.5" font-weight="700" fill="{GOLD}">핵심 — 3개 엔진 모두 stop-buy 모멘텀(변동성 돌파) 진입. 평균회귀 알파는 \'진입\'이 아니라 양변기 \'보유기\'에서 나온다.</text>')
A(f'<text x="84" y="{y+58}" font-size="13.5" fill="{MUT}">진짜 알파 = ① 레짐 전환 + ② VIX 동적 사이징.  절대수익기가 아니라 SOXL Buy&amp;Hold −90% 낙폭을 약 −34%로 \'길들이는\' 위험관리 도구.</text>')
A(f'<text x="84" y="{y+78}" font-size="12.5" fill="#62748a">SOXL 단일자산 · in-sample 추정 · 소자본 유효.  운영 기대 Calmar ~1.6–1.9.</text>')
y += 86 + 30

H = int(y)

# ---- assemble -------------------------------------------------------------
defs = (
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>'
    f'<marker id="arw" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{MUT}"/></marker>'
    '</defs>'
)
head = f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">'
out = "\n".join(S)
out = out.replace("<DEFS_PLACEHOLDER>", defs).replace("HEIGHT_PLACEHOLDER", str(H))
svg = head + "\n" + out + "\n</svg>"

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(out_dir, exist_ok=True)
svg_path = os.path.join(out_dir, "v1_method.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg)
print("SVG:", svg_path, len(svg), "bytes  H=", H)
