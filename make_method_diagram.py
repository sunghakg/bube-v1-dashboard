# -*- coding: utf-8 -*-
"""BUBE V1 매매법 — 상세 흐름도 SVG 생성기 (2026-07-12 캐논 정합 + 대시보드 팔레트 통일).

한 거래 사이클(레짐 판정 → 엔진 선택 → 진입 → 갭필터 → VIX 사이징 → 청산)을
위에서 아래로 따라가는 플로우차트. 결과물: assets/v1_method.svg

★ 내용의 단일 소스 = regime_canon.py (벤더 사본) + CHAMP_NOMARGIN 스펙.
  - 레짐: 5신호 투표(VIX·QQQ주간RSI14·SPY MA200·SOXL MA50·SOXL 5일모멘텀),
    soft 비대칭(곰 2표/소 3표), fast-BEAR(VIX9D/VIX>1.05), 무상태(평활·dwell 없음)
  - 롱변기 청산: S_wide VIX-적응 손절 −8%×clip(VIX/20,1,1.5) (PR#34)
  규칙이 바뀌면 이 파일도 함께 갱신할 것.
★ 팔레트 = app.py 대시보드(Nord 계열)와 동일 — 디자인 이질감 제거 (2026-07-12).
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

# ---- palette — app.py 대시보드와 동일한 Nord 계열 --------------------------
BG0, BG1 = "#2E3440", "#3B4252"          # 헤더 카드와 같은 gradient
CARD, CARD_STK = "#3B4252", "#4C566A"
CYAN  = "#34A5C5"   # 대시보드 accent = 롱변기
GOLD  = "#EBCB8B"   # NEUTRAL · 양변기
AMBER = "#D08770"   # 황금변기
GREEN = "#A3BE8C"   # BULL / 긍정
RED   = "#BF616A"   # BEAR / 부정
BLUE  = "#81A1C1"   # 정보
TXT, MUT = "#ECEFF4", "#B8C0CE"
FONT = "'Malgun Gothic','Segoe UI',sans-serif"

# ---- helpers --------------------------------------------------------------
def card(x, y, w, h, c, fill=CARD, op=1.0):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" fill-opacity="{op}" stroke="{c}" stroke-opacity="0.8" stroke-width="1.4"/>')
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

cx = W / 2     # center spine x for arrows

# ===== HEADER =====
A('<DEFS_PLACEHOLDER>')
A(f'<rect width="{W}" height="HEIGHT_PLACEHOLDER" fill="url(#bg)"/>')
A(f'<rect x="0" y="0" width="6" height="HEIGHT_PLACEHOLDER" fill="{CYAN}"/>')
A(f'<text x="60" y="76" font-size="38" font-weight="800" fill="{TXT}">BUBE V1 매매법 — 상세 흐름도</text>')
A(f'<text x="62" y="108" font-size="18" fill="{CYAN}" font-weight="600">SOXL 3× 레버리지 · 매일 한 사이클: 레짐 판정 → 엔진 선택 → 돌파 진입 → 갭필터 → VIX 사이징 → 청산</text>')
# legend
leg = [("BULL", GREEN), ("NEUTRAL", GOLD), ("BEAR", RED), ("롱변기", CYAN), ("양변기", GOLD), ("황금변기", AMBER)]
lx = 62
for name, c in leg:
    w = 38 + text_w(name, 13)
    A(f'<rect x="{lx}" y="126" width="{w:.0f}" height="26" rx="13" fill="{c}" fill-opacity="0.14" stroke="{c}" stroke-opacity="0.6"/>')
    A(f'<circle cx="{lx+15}" cy="139" r="4.5" fill="{c}"/>')
    A(f'<text x="{lx+27}" y="144" font-size="13" fill="{c}" font-weight="600">{esc(name)}</text>')
    lx += w + 12

y = 196  # running cursor

# ===== STAGE 0: 레짐 판정 (캐논 regime_canon.py — 5신호 투표 + soft + fast-BEAR) =====
stage_header(y, "0", "장 시작 전 — 매일 레짐(시장 국면) 판정", "캐논 감지기 · 전부 전일(T−1) 종가 · 봇=백테=대시보드 동일 코드", BLUE)
y += 20
inp = [
    ("🗳 5신호 투표 (전일 종가)", BLUE, [
        "① VIX: ≤18 강세 · >30 약세",
        "② QQQ 주간 RSI14: ≥60 강세 · <40 약세",
        "③ SPY vs 200일선: ±2% 밴드",
        "④ SOXL vs 50일선: ±5% 밴드",
        "⑤ SOXL 5일 모멘텀: ±5% 밴드",
    ]),
    ("⚖ soft 분류 — 위험회피 비대칭", GOLD, [
        "약세 ≥ 2표  →  🔴 BEAR",
        "강세 ≥ 3표  →  🟢 BULL",
        "그 외        →  🟡 NEUTRAL",
        "곰은 2표면 인정 · 소는 3표 필요",
        "= 하락 위험에 더 민감하게 반응",
    ]),
    ("⚡ fast-BEAR + 무상태", RED, [
        "VIX9D/VIX > 1.05 (단기공포 역전)",
        "→ 투표 무시하고 즉시 BEAR",
        "평활·dwell 없음 = 매일 새로 판정",
        "(어제 레짐 기억 안 함 · 무상태)",
        "BEAR 연속 >90일 → 황금변기",
    ]),
]
iw, ig = 393, 30
ix0 = 60
ih = 158
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

# regime result row: BULL / NEUTRAL / BEAR — 카드 안에 '어느 엔진으로 가는지' 직접 명시
#   (세로 정렬만 보면 NEUTRAL→양변기로 오독하기 쉬움 → 목적지를 카드에 쓰고 합류 화살표로 해소)
reg = [
    ("🟢 BULL", GREEN, "상승장", "→ 🚀 롱변기로", CYAN),
    ("🟡 NEUTRAL", GOLD, "중립장", "→ 🚀 롱변기로 (BULL과 동일 취급!)", CYAN),
    ("🔴 BEAR", RED, "하락장", "→ 🚽 양변기로 (91일째부턴 ✨황금변기)", GOLD),
]
rw, rg = 393, 30
rh = 84
for i, (t, c, sub, dest, dc) in enumerate(reg):
    x = ix0 + i * (rw + rg)
    card(x, y, rw, rh, c, fill=c, op=0.12)
    title_line(x + 22, y + 34, c, t, fs=20, w="800")
    A(f'<text x="{x+rw-22}" y="{y+34}" font-size="14" fill="{MUT}" text-anchor="end">{esc(sub)}</text>')
    A(f'<text x="{x+22}" y="{y+64}" font-size="15" font-weight="700" fill="{dc}">{esc(dest)}</text>')
y += rh + 12

# ===== STAGE 1: 엔진 선택 =====
stage_header(y + 12, "1", "엔진 선택 — 레짐이 매매 엔진을 결정",
             "★ BULL과 NEUTRAL은 둘 다 롱변기 · BEAR만 양변기 — 선 색을 따라가세요", GOLD)
y += 26
eng = [
    ("롱변기 (Long-byungi)", CYAN, "BULL · NEUTRAL", "SOXL 단방향 매수", "추세 추종"),
    ("양변기 v5 (Yang-byungi)", GOLD, "BEAR", "SOXL 롱 + SOXS 숏 페어", "평균회귀 보유"),
    ("황금변기 (Golden-byungi)", AMBER, "BEAR 90일↑", "SOXL 변동성 돌파", "tail 보험 (실데이터 0회)"),
]

# ── 합류 화살표 존: BULL↓ + NEUTRAL↙ → 롱변기 / BEAR↙ → 양변기 / (점선) 91일째 → 황금변기
def _flow_pill(px, py, text, c, fs=12.5):
    lw = 18 + text_w(text, fs)
    A(f'<rect x="{px-lw/2:.0f}" y="{py-13}" width="{lw:.0f}" height="26" rx="13" fill="{BG0}" stroke="{c}" stroke-opacity="0.9" stroke-width="1.3"/>')
    A(f'<text x="{px:.0f}" y="{py+4.5}" font-size="{fs}" font-weight="700" fill="{c}" text-anchor="middle">{esc(text)}</text>')

c1 = ix0 + rw / 2
c2 = ix0 + (rw + rg) + rw / 2
c3 = ix0 + 2 * (rw + rg) + rw / 2
zone_top = y
zone_bot = y + 100          # 엔진 카드 상단
mid1 = zone_top + 30        # NEUTRAL 가로 구간
mid2 = zone_top + 68        # BEAR 가로 구간

# BULL → 롱변기 (초록 직선, 롱변기 카드 왼쪽 절반에 착지)
A(f'<circle cx="{c1-80}" cy="{zone_top+4}" r="4.5" fill="{GREEN}"/>')
A(f'<line x1="{c1-80}" y1="{zone_top+4}" x2="{c1-80}" y2="{zone_bot-9}" stroke="{GREEN}" stroke-width="3" marker-end="url(#arwg)"/>')
# NEUTRAL → 롱변기 (노란 ㄱ자 합류선, 롱변기 카드 오른쪽 절반에 착지)
A(f'<circle cx="{c2}" cy="{zone_top+4}" r="4.5" fill="{GOLD}"/>')
A(f'<path d="M {c2} {zone_top+4} L {c2} {mid1} L {c1+80} {mid1} L {c1+80} {zone_bot-9}" fill="none" stroke="{GOLD}" stroke-width="3" marker-end="url(#arwy)"/>')
# BEAR → 양변기 (빨간 ㄱ자)
A(f'<circle cx="{c3}" cy="{zone_top+4}" r="4.5" fill="{RED}"/>')
A(f'<path d="M {c3} {zone_top+4} L {c3} {mid2} L {c2} {mid2} L {c2} {zone_bot-9}" fill="none" stroke="{RED}" stroke-width="3" marker-end="url(#arwr)"/>')
# BEAR 91일째부터 → 황금변기 (주황 점선 — 희귀한 예외 경로)
A(f'<circle cx="{c3+95}" cy="{zone_top+4}" r="4.5" fill="{AMBER}"/>')
A(f'<line x1="{c3+95}" y1="{zone_top+4}" x2="{c3+95}" y2="{zone_bot-9}" stroke="{AMBER}" stroke-width="2.4" stroke-dasharray="6 4" marker-end="url(#arwa)"/>')

# 선 위 라벨 (불투명 배경 pill)
_flow_pill(c1 - 80, mid2, "BULL → 롱변기", GREEN)
_flow_pill((c2 + c1 + 80) / 2, mid1, "NEUTRAL도 롱변기!", GOLD, fs=13)
_flow_pill((c3 + c2) / 2, mid2, "BEAR 첫 90일 → 양변기", RED)
_flow_pill(c3 + 95, mid1, "91일째부터 (16y 0회)", AMBER, fs=11.5)

y = zone_bot
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
e2h = 114
for i, (t, c, lines) in enumerate(ent):
    x = ix0 + i * (rw + rg)
    card(x, y, rw, e2h, c)
    title_line(x + 22, y + 30, c, t, fs=16, w="700")
    A(f'<line x1="{x+22}" y1="{y+40}" x2="{x+rw-22}" y2="{y+40}" stroke="{CARD_STK}"/>')
    yy = y + 62
    for ln in lines:
        body_line(x + 22, yy, ln, c=TXT, fs=13.5); yy += 21
y += e2h + 20

# ===== STAGE 3: 갭필터 =====
stage_header(y + 8, "3", "갭필터 — 비대칭 A안 (2026-06-03)", "나쁜 진입만 거르고 좋은 진입은 살린다", AMBER)
y += 22
gh = 74
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

# ===== STAGE 4: VIX 사이징 =====
stage_header(y + 6, "4", "VIX 동적 비중 — 변동성이 노출을 정한다", "전일 VIX 기준 · 마진 미사용 (cap 1.0)", GOLD)
y += 20
sh = 168
fw = rw * 2 + rg
card(ix0, y, fw, sh, GOLD)
title_line(ix0 + 22, y + 34, GOLD, "비중 공식", fs=16, w="700")
A(f'<text x="{ix0+22}" y="{y+72}" font-size="17" font-family="monospace" fill="{TXT}">k = 0.60 × clip( 20 / VIX , 0.5 , 2.0 )</text>')
A(f'<text x="{ix0+22}" y="{y+102}" font-size="17" font-family="monospace" fill="{TXT}">alloc = min( k × 엔진비중 , 1.0 )</text>')
body_line(ix0 + 22, y + 134, "VIX↑ (공포) → 비중↓   ·   VIX↓ (안정) → 비중↑", c=CYAN, fs=14)
body_line(ix0 + 22, y + 156, "margin 0% — 최대 100% 현금 한도, broker 강제청산 원천 차단", c=MUT, fs=13)
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

# ===== STAGE 5: 청산 =====
stage_header(y + 6, "5", "청산 / 보유 — 엔진별 출구", "롱변기 손절은 VIX-적응 S_wide (2026-06-22 배포)", GREEN)
y += 20
ext = [
    ("롱변기 청산", CYAN, ["장중: VIX-적응 손절 S_wide", "−8% × clip( VIX/20 , 1 , 1.5 )", "익일 시가(MOO) 전량 청산"]),
    ("양변기 청산", GOLD, ["종가(LOC) 청산 · 장중 손절 없음", "손실분 overnight carry →", "익일 반등 평균회귀 알파"]),
    ("황금변기 청산", AMBER, ["변동성 밴드 이탈 시 청산", "곰장 종료까지 보유", "tail 위험 흡수 (16y 발동 0회)"]),
]
y += 12
for i in range(3):
    x = ix0 + i * (rw + rg) + rw / 2
    arrow(x, y - 18, y + 12, c=ext[i][1])
y += 24
x4h = 114
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
A(f'<rect x="60" y="{y}" width="{W-120}" height="86" rx="12" fill="{CYAN}" fill-opacity="0.08" stroke="{CYAN}" stroke-opacity="0.45"/>')
A(f'<text x="84" y="{y+32}" font-size="15.5" font-weight="700" fill="{CYAN}">핵심 — 3개 엔진 모두 stop-buy 모멘텀(변동성 돌파) 진입. 평균회귀 알파는 \'진입\'이 아니라 양변기 \'보유기\'에서 나온다.</text>')
A(f'<text x="84" y="{y+58}" font-size="13.5" fill="{MUT}">진짜 알파 = ① 레짐 전환 + ② VIX 동적 사이징.  SOXL Buy&amp;Hold −90% 낙폭을 −23~−31%로 \'길들이는\' 위험관리 도구.</text>')
A(f'<text x="84" y="{y+78}" font-size="12.5" fill="#7B8598">16y 캐논 Calmar ~2.5 · bootstrap 중앙값 ~1.9 = 운영 기대치 · SOXL 단일자산 · 소자본 유효.</text>')
y += 86 + 30

H = int(y)

# ---- assemble -------------------------------------------------------------
defs = (
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>'
    + "".join(
        f'<marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
        for mid, col in [("arw", MUT), ("arwg", GREEN), ("arwy", GOLD), ("arwr", RED), ("arwa", AMBER)]
    )
    + '</defs>'
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

# ============================================================
# 📱 모바일 버전 — 430px 단일 컬럼 스택 (assets/v1_method_mobile.svg)
#    데스크톱 1300px SVG는 폰에서 ~3.5배 축소되어 글자가 안 읽힘 →
#    같은 내용(inp/reg/eng/ent/ext/rows 재사용)을 세로로 쌓아 원본 크기 유지.
#    app.py가 CSS media query로 768px 이하에서 이 파일을 대신 표시 (2026-07-12).
#    WM=375: 폰 실측 컨테이너(~321px)에서 배율 0.86 → fs12.5가 ~10.7px로 읽힘.
# ============================================================
S.clear()
WM = 375
MX = 16
CW = WM - MX * 2
cxm = WM / 2


def m_stage(yy, num, title, c, desc=None):
    A(f'<circle cx="{MX+13}" cy="{yy-5}" r="12" fill="{c}" fill-opacity="0.18" stroke="{c}" stroke-width="1.8"/>')
    A(f'<text x="{MX+13}" y="{yy-1}" font-size="12.5" font-weight="800" fill="{c}" text-anchor="middle">{num}</text>')
    A(f'<text x="{MX+34}" y="{yy}" font-size="15.5" font-weight="800" fill="{TXT}">{esc(title)}</text>')
    if desc:
        A(f'<text x="{MX+34}" y="{yy+17}" font-size="11" fill="{MUT}">{esc(desc)}</text>')
        return 34
    return 18


def m_card_lines(yy, t, c, lines, fs=12.5, lh=19, title_fs=14):
    h = 66 + (len(lines) - 1) * lh
    card(MX, yy, CW, h, c)
    title_line(MX + 18, yy + 24, c, t, fs=title_fs, w="700")
    A(f'<line x1="{MX+18}" y1="{yy+34}" x2="{MX+CW-18}" y2="{yy+34}" stroke="{CARD_STK}"/>')
    ly = yy + 54
    for ln in lines:
        body_line(MX + 18, ly, ln, c=TXT, fs=fs); ly += lh
    return h


A('<DEFS_PLACEHOLDER>')
A(f'<rect width="{WM}" height="HEIGHT_PLACEHOLDER" fill="url(#bg)"/>')
A(f'<rect x="0" y="0" width="5" height="HEIGHT_PLACEHOLDER" fill="{CYAN}"/>')
A(f'<text x="{MX}" y="42" font-size="21" font-weight="800" fill="{TXT}">BUBE V1 매매법 — 상세 흐름도</text>')
A(f'<text x="{MX}" y="63" font-size="10.5" fill="{CYAN}" font-weight="600">레짐 판정 → 엔진 선택 → 돌파 진입 → 갭필터 → VIX 사이징 → 청산</text>')
y = 96

# ── 0. 레짐 판정
y += m_stage(y, "0", "매일 레짐(시장 국면) 판정", BLUE, "전부 전일(T−1) 종가 · 봇=백테=대시보드 동일 코드")
for t, c, lines in inp:
    y += m_card_lines(y, t, c, lines) + 10
arrow(cxm, y, y + 28, c=MUT, label="종합 판정", lc=BLUE)
y += 40

# ── 레짐 결과 카드 (목적지 명시)
for t, c, sub, dest, dc in reg:
    card(MX, y, CW, 62, c, fill=c, op=0.12)
    title_line(MX + 18, y + 26, c, t, fs=16, w="800")
    A(f'<text x="{MX+CW-18}" y="{y+26}" font-size="11.5" fill="{MUT}" text-anchor="end">{esc(sub)}</text>')
    A(f'<text x="{MX+18}" y="{y+48}" font-size="12.5" font-weight="700" fill="{dc}">{esc(dest)}</text>')
    y += 70
y += 10

# ── 1. 엔진 선택
y += m_stage(y, "1", "엔진 선택 — 레짐이 엔진을 결정", GOLD, "★ BULL·NEUTRAL 둘 다 롱변기 · BEAR만 양변기")
for t, c, frm, what, kind in eng:
    card(MX, y, CW, 86, c)
    title_line(MX + 18, y + 24, c, t, fs=14, w="700")
    pw = 20 + text_w(frm, 10.5)
    A(f'<rect x="{MX+CW-14-pw:.0f}" y="{y+10}" width="{pw:.0f}" height="20" rx="10" fill="{c}" fill-opacity="0.18" stroke="{c}" stroke-opacity="0.6"/>')
    A(f'<text x="{MX+CW-14-pw/2:.0f}" y="{y+24}" font-size="10.5" font-weight="700" fill="{c}" text-anchor="middle">{esc(frm)}</text>')
    A(f'<line x1="{MX+18}" y1="{y+34}" x2="{MX+CW-18}" y2="{y+34}" stroke="{CARD_STK}"/>')
    body_line(MX + 18, y + 55, what, c=TXT, fs=12.5)
    body_line(MX + 18, y + 74, "성격: " + kind, c=MUT, fs=11.5)
    y += 96
y += 10

# ── 2. 진입
y += m_stage(y, "2", "진입 — 09:35 ET · 전부 stop-buy 돌파", GREEN, "딥매수 아님 — 변동성 돌파 추격 매수")
for t, c, lines in ent:
    y += m_card_lines(y, t, c, lines) + 10
y += 8

# ── 3. 갭필터
y += m_stage(y, "3", "갭필터 — 비대칭 A안 (2026-06-03)", AMBER, "나쁜 진입만 거르고 좋은 진입은 살린다")
y += m_card_lines(y, "롱변기 · 양변기롱 (SOXL 매수)", GREEN,
                  ["갭다운 −5% 이하만 진입 차단 · 갭업은 허용", "(갭업 진입은 정상보다 ~2배 좋은 진입)"]) + 10
y += m_card_lines(y, "양변기숏 (SOXS 매수)", RED,
                  ["|갭| > 5% 면 진입 차단 (양방향 대칭 유지)"]) + 10
y += 8

# ── 4. VIX 동적 비중
y += m_stage(y, "4", "VIX 동적 비중", GOLD, "전일 VIX 기준 · 마진 미사용 (cap 1.0)")
card(MX, y, CW, 118, GOLD)
title_line(MX + 18, y + 24, GOLD, "비중 공식", fs=14, w="700")
A(f'<line x1="{MX+18}" y1="{y+34}" x2="{MX+CW-18}" y2="{y+34}" stroke="{CARD_STK}"/>')
A(f'<text x="{MX+18}" y="{y+56}" font-size="13" font-family="monospace" fill="{TXT}">k = 0.60 × clip( 20/VIX, 0.5, 2.0 )</text>')
A(f'<text x="{MX+18}" y="{y+78}" font-size="13" font-family="monospace" fill="{TXT}">alloc = min( k × 엔진비중, 1.0 )</text>')
body_line(MX + 18, y + 102, "VIX↑(공포)→비중↓ · VIX↓(안정)→비중↑", c=CYAN, fs=12)
y += 128
card(MX, y, CW, 130, CYAN)
title_line(MX + 18, y + 24, CYAN, "VIX → 비중 직관", fs=14, w="700")
A(f'<line x1="{MX+18}" y1="{y+34}" x2="{MX+CW-18}" y2="{y+34}" stroke="{CARD_STK}"/>')
yy = y + 54
for a, b, cmt, c in rows:
    A(f'<text x="{MX+18}" y="{yy}" font-size="12" font-family="monospace" fill="{TXT}">{esc(a)}</text>')
    A(f'<text x="{MX+112}" y="{yy}" font-size="11.5" fill="{MUT}">{esc(b)}</text>')
    A(f'<text x="{MX+CW-18}" y="{yy}" font-size="12" font-weight="700" fill="{c}" text-anchor="end">{esc(cmt)}</text>')
    yy += 22
y += 140
y += 8

# ── 5. 청산
y += m_stage(y, "5", "청산 / 보유 — 엔진별 출구", GREEN, "롱변기 손절 = VIX-적응 S_wide −8%×clip(VIX/20,1,1.5)")
for t, c, lines in ext:
    y += m_card_lines(y, t, c, lines) + 10
y += 8

# ── FOOTER
fh = 108
A(f'<rect x="{MX}" y="{y}" width="{CW}" height="{fh}" rx="10" fill="{CYAN}" fill-opacity="0.08" stroke="{CYAN}" stroke-opacity="0.45"/>')
A(f'<text x="{MX+16}" y="{y+26}" font-size="12.5" font-weight="700" fill="{CYAN}">핵심 — 3개 엔진 모두 stop-buy 변동성 돌파 진입.</text>')
A(f'<text x="{MX+16}" y="{y+46}" font-size="12" fill="{MUT}">평균회귀 알파는 \'진입\'이 아니라 양변기 \'보유기\'에서.</text>')
A(f'<text x="{MX+16}" y="{y+66}" font-size="12" fill="{MUT}">진짜 알파 = ① 레짐 전환 + ② VIX 동적 사이징.</text>')
A(f'<text x="{MX+16}" y="{y+90}" font-size="11" fill="#7B8598">16y Calmar ~2.5 · bootstrap 중앙값 ~1.9 = 운영 기대치</text>')
y += fh + 24

HM = int(y)
head_m = f'<svg viewBox="0 0 {WM} {HM}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">'
out_m = "\n".join(S).replace("<DEFS_PLACEHOLDER>", defs).replace("HEIGHT_PLACEHOLDER", str(HM))
svg_m = head_m + "\n" + out_m + "\n</svg>"
svg_path_m = os.path.join(out_dir, "v1_method_mobile.svg")
with open(svg_path_m, "w", encoding="utf-8") as f:
    f.write(svg_m)
print("SVG(mobile):", svg_path_m, len(svg_m), "bytes  H=", HM)
