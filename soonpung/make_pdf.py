"""순풍 작업 요약 → PDF (fpdf2 + NanumGothic)."""
from pathlib import Path
from fpdf import FPDF

FONT = "/usr/share/fonts/truetype/nanum"
NAVY = (10, 26, 58)
BLUE = (30, 58, 138)
LBLUE = (238, 243, 251)
GREY = (90, 90, 90)
OK = (21, 128, 61)
WIP = (180, 83, 9)
TODO = (100, 116, 139)
AMBER_BG = (255, 247, 237)
BORDER = (196, 204, 216)

pdf = FPDF(format="A4")
pdf.set_margins(15, 15, 15)
pdf.set_auto_page_break(True, margin=15)
pdf.add_font("Nanum", "", f"{FONT}/NanumGothic.ttf")
pdf.add_font("Nanum", "B", f"{FONT}/NanumGothicBold.ttf")
pdf.add_font("Mono", "", f"{FONT}/NanumGothicCoding.ttf")
pdf.add_page()
W = pdf.epw  # effective page width


def h1_banner(title, sub):
    pdf.set_fill_color(*NAVY)
    y0 = pdf.get_y()
    pdf.rect(pdf.l_margin, y0, W, 20, "F")
    pdf.set_xy(pdf.l_margin + 4, y0 + 3.5)
    pdf.set_font("Nanum", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W - 8, 8, title)
    pdf.set_xy(pdf.l_margin + 4, y0 + 12)
    pdf.set_font("Nanum", "", 9)
    pdf.set_text_color(205, 217, 245)
    pdf.cell(W - 8, 5, sub)
    pdf.set_y(y0 + 24)
    pdf.set_text_color(0, 0, 0)


def quote(t):
    pdf.set_font("Nanum", "", 9.5)
    pdf.set_text_color(*BLUE)
    pdf.multi_cell(W, 5, t)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def h2(t):
    pdf.ln(2)
    pdf.set_font("Nanum", "B", 12.5)
    pdf.set_text_color(*BLUE)
    pdf.cell(W, 7, t)
    pdf.ln(7.5)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.4)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.l_margin + W, y)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def para(t):
    pdf.set_font("Nanum", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(W, 5.2, t)
    pdf.ln(1)


def bullets(items):
    pdf.set_font("Nanum", "", 9.8)
    pdf.set_text_color(0, 0, 0)
    for it in items:
        x = pdf.get_x()
        pdf.cell(5, 5, "-")
        pdf.multi_cell(W - 5, 5, it)
    pdf.ln(1)


def code(t):
    pdf.ln(1)
    pdf.set_font("Mono", "", 8.6)
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(232, 238, 252)
    pdf.multi_cell(W, 4.6, t, fill=True, padding=2)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1.5)


def note(t):
    pdf.ln(0.5)
    pdf.set_font("Nanum", "", 9.3)
    pdf.set_fill_color(*AMBER_BG)
    pdf.set_text_color(120, 53, 15)
    pdf.multi_cell(W, 5, t, fill=True, padding=2,
                   border=0)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1.5)


def table(headers, rows, widths, colors=None):
    pdf.set_draw_color(*BORDER)
    pdf.set_line_width(0.2)
    # header
    pdf.set_font("Nanum", "B", 8.8)
    pdf.set_fill_color(*LBLUE)
    pdf.set_text_color(*NAVY)
    line_h = 4.6
    for h, w in zip(headers, widths):
        pdf.cell(w, 6, h, border=1, fill=True, align="L")
    pdf.ln(6)
    pdf.set_font("Nanum", "", 8.6)
    pdf.set_text_color(0, 0, 0)
    for ri, row in enumerate(rows):
        # compute row height via split_only
        n_lines = 1
        cells_lines = []
        for txt, w in zip(row, widths):
            lines = pdf.multi_cell(w, line_h, txt, split_only=True)
            cells_lines.append(lines)
            n_lines = max(n_lines, len(lines))
        rh = n_lines * line_h + 1.5
        if pdf.get_y() + rh > pdf.page_break_trigger:
            pdf.add_page()
        x0, y0 = pdf.get_x(), pdf.get_y()
        for ci, (lines, w) in enumerate(zip(cells_lines, widths)):
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.rect(x, y, w, rh)
            # status color on last col
            if colors and ci == len(widths) - 1:
                pdf.set_text_color(*colors[ri])
                pdf.set_font("Nanum", "B", 8.6)
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Nanum", "", 8.6)
            pdf.set_xy(x, y + 0.6)
            pdf.multi_cell(w, line_h, "\n".join(lines), align="L")
            pdf.set_xy(x + w, y0)
        pdf.set_xy(x0, y0 + rh)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


# ── 본문 ───────────────────────────────────────────────────
h1_banner("순풍(順風) — SOXL 추세추종 신규 엔진",
          "작업 요약 리포트 · Phase 0~2 MVP 착수 · 2026-06-19")
quote('"상승은 끝까지 끌고, 하락은 돛을 미리 접는다." — 기존 평균회귀 계열과 상호보완되는 추세추종 축')

h2("1. 목적")
para("기존 평균회귀 엔진(BUBE·떨사오팔·그리드·동파법·양변기)의 두 가지 구조적 약점을 메우는 별도 추세추종 엔진.")
table(["약점", "순풍의 대응"],
      [["강한 상승장 조기 청산 (오르면 팔아 상단을 놓침)", "추세 확인 시 승자 끌고 가기 → 상단 최대 포획"],
       ["급락 시 물타기/그리드로 손실 확대", "레짐 이탈·변동성 급등 시 떨어지기 전에 선제 디레버리징"]],
      [W * 0.5, W * 0.5])
note("단독 운용이 목표가 아님. 기존 평균회귀 엔진과 국면 분산으로 묶어 전체 포트 변동성을 낮추는 것이 본질.")

h2("2. 전략 컨셉")
code("순풍 = 레짐 필터(언제 탈지) × 변동성 타겟팅(얼마나 탈지) × 헤지 오버레이(어떻게 막을지)")

h2("3. 산출물 (전부 soonpung/ 패키지)")
table(["Phase", "파일", "내용", "상태"],
      [["0 리서치", "research_notes.md", "6개 논문+CPPI를 3열(메커니즘/수식/적용)로 정리", "완료"],
       ["0 리서치", "module_candidates.md", "6개 모듈 후보 비교표 → MVP 확정", "완료"],
       ["1 데이터", "data_pipeline.py", "시세 다운로드 + 합성 SOXL 역연장 + splice + 검증", "코드 완료"],
       ["2 모듈", "regime_filter.py", "Faber 200MA × MOP 12개월 TSM 부호 + dwell", "완료"],
       ["2 모듈", "vol_target.py", "Cooper 변동성 타겟(실현/EWMA) ★순풍의 심장", "완료"],
       ["3 백테", "backtest_mvp.py", "no-lookahead 통합 백테 + 국면별 성과 분해", "MVP"]],
      [W * 0.12, W * 0.22, W * 0.5, W * 0.16],
      colors=[OK, OK, OK, OK, OK, WIP])

h2("4. 리서치 핵심 근거 (웹 1차 출처 기반)")
table(["자료", "추출한 메커니즘", "채택"],
      [["Cooper (2010) ★", "변동성으로 레버리지 동적 조절 lev=σ_target/σ_hat → 변동성 감쇠(decay) 방어. 순풍의 심장", "핵심"],
       ["Cheng-Madhavan (2009)", "LETF 경로 의존성·변동성 드래그·비용모델 → 합성 SOXL 코어", "채택"],
       ["Moskowitz-Ooi-Pedersen (2012)", "12개월 시계열 모멘텀 부호 → ON/OFF 스위치", "채택"],
       ["Harvey et al. (2018)", "변동성 타겟팅의 샤프·꼬리위험 개선 실증(리스크 자산서 효과 큼)", "근거"],
       ["Faber (2007)", "200일 MA 타이밍 → 레짐 필터 베이스라인", "채택"],
       ["Antonacci Dual Momentum", "절대·상대 모멘텀 결합 (절대모멘텀만 MVP 흡수)", "부분"],
       ["CPPI (Black-Jones 1987)", "쿠션 비례 위험자산 배분 → 수익 플로어", "Phase3+"]],
      [W * 0.27, W * 0.59, W * 0.14],
      colors=[OK, OK, OK, OK, OK, WIP, TODO])

h2("5. MVP 사양 (1차 구현)")
code("position_t = regime_ON × clip(σ_target / σ_hat_60d, 0, lev_max)\n\n"
     "regime_ON  = (SOX > SMA200)  AND/OR  sign(R_252d) > 0   [dwell = 5]\n"
     "σ_hat          = SOXL 실현변동성(60일, 연율화)\n"
     "σ_target   = 0.35 (연)\n"
     "lev_max    = 1.0  (margin 미사용 — CHAMP_NOMARGIN 정책 정합)")
para("거래 대상: SOXL 1종. 보조 데이터: SOX/SOXX, VIX, VVIX, EWY, SOXS. "
     "헤지 오버레이·수익 플로어는 MVP 검증 통과 후 추가 (PBO 억제 — 최소 파라미터 원칙).")

h2("6. 합성 SOXL (하락 대비 검증용)")
bullets(["SOXL 상장 2010 → 2008 금융위기·2000 닷컴 미포함",
         "SOXX(2001~) 일일 3x 시뮬레이션 + 보수(0.89%)/금융비(Cheng-Madhavan 비용모델)로 역연장",
         "합성 + 실제 splice, 겹침 구간 일일수익률 상관 검증(목표 ≥ 0.99)"])
note("역연장 구간은 실제 SOXL이 아님 — 참고용, 과신 금지.")

h2("7. 검증 상태")
bullets(["원격 세션 환경은 Yahoo Finance 아웃바운드 차단 → 실데이터 생성 불가",
         "대신 합성 가격으로 end-to-end 자체검증 완료: splice / 상관검증 / no-lookahead(shift(1)) / 국면별 분해 모두 정상 동작",
         "네트워크 열린 로컬에서 파이프라인 실행 시 data/soonpung/에 산출물 생성",
         "이 저장소 CI 없음, 리뷰 코멘트 없음 → 현재 조치 필요 사항 없음"])

h2("8. 결과물 위치")
table(["항목", "위치"],
      [["Draft PR", "#1 — github.com/sunghakg/yb-mdd-or-dashboard/pull/1"],
       ["브랜치", "claude/soxl-trend-following-strategy-ae9kcf"]],
      [W * 0.25, W * 0.75])

h2("9. 남은 작업 (후속 PR)")
bullets(["정식 검증: Walk-forward · CSCV/PBO(과최적화 확률) · Deflated Sharpe(DSR)+PSR",
         "기존 평균회귀 엔진과 상관계수 · 합성 포트 효과 측정",
         "합격 기준: 하락 국면 MDD가 단순보유 대비 유의 개선 + 상승 포획률 충분 + PBO 낮음",
         "검증 통과 후 헤지 오버레이(조건부 SOXS/현금) · 수익 플로어(CPPI) 추가",
         "대시보드(app.py) 탭 편입 — data/soonpung/ 산출물 소비"])
note('참고: "순풍"은 가제 — 떨사오팔/양변기/동파법 라인업에 맞게 자유롭게 개명 가능.')

out = Path(__file__).parent / "순풍_요약.pdf"
pdf.output(str(out))
print("saved", out)
