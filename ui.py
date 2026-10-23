"""Theme + small HTML helpers. Visual language: periwinkle sidebar, soft lavender canvas, white rounded cards,
outlined pill buttons, tinted rows with a coloured left edge."""
import html

import streamlit as st

INK, MUTED, BLUE, LINE = "#1b1f3b", "#8a94b8", "#2f8cf0", "#e3e8f6"
STATUS = {  # status -> (bg, fg)
    "New": ("#eceffa", "#5b6690"), "Screened": ("#fff4dc", "#b27a06"), "Shortlisted": ("#dff0ff", "#1f78d1"),
    "Selected": ("#d9f6ef", "#0f8f78"), "Rejected": ("#ffe3e8", "#d1304f"), "On Hold": ("#ece6ff", "#6b4fd8"),
    "sent": ("#d9f6ef", "#0f8f78"), "queued": ("#fff4dc", "#b27a06"), "failed": ("#ffe3e8", "#d1304f"),
}
STATUS_DOT = {"New": "#9aa5c8", "Screened": "#f5a524", "Shortlisted": "#2f8cf0", "Selected": "#12b79b",
              "Rejected": "#f0506e", "On Hold": "#8b6fe0"}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stApp, button, input, textarea, select {{ font-family: 'Outfit', sans-serif !important; }}
.stApp {{ background: #eef2fc; color: {INK}; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], header[data-testid="stHeader"] {{ display: none !important; }}
.block-container {{ padding: 1.6rem 2.2rem 3rem 2.2rem; max-width: 1280px; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: linear-gradient(180deg,#6b7fe8 0%,#6579e2 100%); width: 270px !important; border-right: 0; }}
section[data-testid="stSidebar"] > div {{ padding-top: 1.2rem; }}
section[data-testid="stSidebar"] * {{ color: #fff; }}
.brand {{ font-size: 1.9rem; font-weight: 300; letter-spacing: .18em; padding: .4rem .6rem 1.4rem .6rem; color:#fff; }}
section[data-testid="stSidebar"] .stButton > button {{
  width: 100%; justify-content: flex-start; background: transparent; border: 0; box-shadow: none; border-radius: 10px;
  padding: .55rem .8rem; font-size: .95rem; font-weight: 400; color: #e6ebff; }}
section[data-testid="stSidebar"] .stButton > button:hover {{ background: rgba(255,255,255,.12); color:#fff; }}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{ background: rgba(255,255,255,.28); color:#fff; font-weight:500; }}
section[data-testid="stSidebar"] .stButton > button p {{ color: inherit; }}
section[data-testid="stSidebar"] .stButton > button > div {{ justify-content: flex-start; gap: .6rem; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.35); margin: .8rem .5rem; }}
.promo {{ margin: 1.2rem .3rem 0 .3rem; padding: 1.1rem; border-radius: 18px; border: 1px solid rgba(255,255,255,.45);
  background: linear-gradient(160deg, rgba(255,255,255,.14), rgba(48,196,222,.55)); }}
.promo b {{ display:block; font-size: 1rem; margin-bottom:.35rem; }}
.promo small {{ display:block; font-size:.74rem; line-height:1.35; color:#eef1ff; margin-bottom:.8rem; }}
.promo .pill {{ display:block; text-align:center; border:1px solid #fff; border-radius:999px; padding:.55rem; font-size:.8rem; letter-spacing:.04em; }}

/* page header */
.topbar {{ display:flex; align-items:center; justify-content:space-between; padding-bottom:.9rem; border-bottom:1px solid {LINE}; margin-bottom: .9rem; }}
.topbar h1 {{ font-size: 2rem; font-weight: 600; margin: 0; color: {INK}; letter-spacing:-.01em; }}
.topbar .sub {{ color:{MUTED}; font-size:.9rem; margin-top:.15rem; }}
.who {{ display:flex; align-items:center; gap:.9rem; color:{MUTED}; font-size:.85rem; letter-spacing:.04em; }}
.who .dot {{ position:relative; }} .who .dot:after {{ content:''; position:absolute; top:-2px; right:-3px; width:8px; height:8px; background:#f0506e; border-radius:50%; }}

/* cards */
[class*="st-key-card"] {{ background:#fff; border-radius:16px; padding:1.1rem 1.3rem; box-shadow: 0 1px 2px rgba(60,80,160,.04); }}
.card-title {{ font-size:1.12rem; font-weight:600; color:{INK}; margin-bottom:.7rem; display:flex; align-items:center; gap:.5rem; }}
.card-title .edit {{ width:20px; height:20px; border-radius:50%; background:#e8efff; color:{BLUE}; font-size:.7rem; display:inline-flex; align-items:center; justify-content:center; }}
.kv {{ display:flex; gap:1rem; padding:.55rem 0; border-bottom:1px solid {LINE}; font-size:.84rem; }}
.kv:last-child {{ border-bottom:0; }} .kv .k {{ color:{MUTED}; min-width:36%; font-size:.76rem; }} .kv .v {{ color:{INK}; font-weight:500; }}
.profile {{ text-align:center; padding:.4rem 0; }}
.profile .name {{ font-size:1.3rem; font-weight:500; line-height:1.2; margin:.9rem 0 .5rem; }}
.profile .phone {{ color:{BLUE}; font-weight:500; font-size:.85rem; }} .profile .mail {{ color:{MUTED}; font-size:.78rem; margin-top:.15rem; }}
.avatar {{ display:inline-flex; align-items:center; justify-content:center; border-radius:50%; color:#fff; font-weight:600; flex-shrink:0; }}
.pill {{ display:inline-block; padding:.12rem .7rem; border-radius:999px; font-size:.74rem; font-weight:500; }}
.chip {{ display:inline-block; padding:.12rem .55rem; border-radius:7px; font-size:.74rem; margin:0 .25rem .25rem 0; font-weight:500; }}
.chip.g {{ background:#d9f6ef; color:#0f8f78; }} .chip.r {{ background:#ffe3e8; color:#d1304f; }} .chip.n {{ background:#eceffa; color:#5b6690; }} .chip.b {{ background:#dff0ff; color:#1f78d1; }}
.filerow {{ display:flex; align-items:center; gap:.7rem; padding:.55rem 0; font-size:.86rem; }}
.filerow .ic {{ color:#7c88c9; }} .filerow .sz {{ margin-left:auto; color:{MUTED}; font-size:.8rem; }}
.outline {{ display:inline-block; border:1px solid {BLUE}; color:{BLUE}; border-radius:999px; padding:.1rem .8rem; font-size:.72rem; letter-spacing:.04em; }}
.trow {{ display:flex; align-items:center; gap:1.2rem; border-radius:6px; padding:.85rem 1rem; margin-bottom:.7rem; border-left:4px solid; }}
.trow.p {{ background:#efecfc; border-color:#8b6fe0; }} .trow.t {{ background:#e4f6f4; border-color:#34c3b8; }}
.trow .col small {{ display:block; color:{MUTED}; font-size:.7rem; }} .trow .col b {{ font-size:.92rem; font-weight:500; }}
.trow .col.grow {{ flex:1; }} .trow .bar {{ height:7px; border-radius:6px; background:rgba(120,130,190,.2); overflow:hidden; margin-top:.35rem; }}
.trow .bar i {{ display:block; height:100%; background:{BLUE}; border-radius:6px; }}
.stat {{ display:flex; align-items:center; gap:.9rem; }} .stat .n {{ font-size:1.8rem; font-weight:600; line-height:1; }} .stat .l {{ color:{MUTED}; font-size:.8rem; }}
.stat .ico {{ width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; }}
.hbar {{ display:flex; align-items:center; gap:.7rem; margin:.45rem 0; font-size:.84rem; }} .hbar .lbl {{ width:96px; color:#5b6690; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.hbar .tr {{ flex:1; height:9px; border-radius:6px; background:#eceffa; }} .hbar .tr i {{ display:block; height:100%; border-radius:6px; }} .hbar .ct {{ width:28px; text-align:right; font-weight:500; }}
.crow {{ display:flex; align-items:center; gap:.9rem; }} .crow .nm {{ font-weight:500; line-height:1.2; }} .crow .em {{ color:{MUTED}; font-size:.76rem; }}
.empty {{ text-align:center; color:{MUTED}; padding:2.2rem 0; }}
.loginwrap {{ max-width: 1040px; margin: 5vh auto 0 auto; }}
[class*="st-key-card"] {{ border: 1px solid #e6ebf8; box-shadow: 0 1px 2px rgba(40,60,140,.04), 0 8px 24px -12px rgba(40,60,140,.12); transition: box-shadow .2s, transform .2s; }}
[class*="st-key-card_job_"]:hover, [class*="st-key-card_tpl"]:hover {{ box-shadow: 0 12px 28px -10px rgba(40,60,140,.25); transform: translateY(-1px); }}
.st-key-card_hero {{ background: linear-gradient(145deg,#1f2a6b 0%,#5469d8 55%,#2fc4de 130%) !important; color:#fff; border:0 !important; min-height: 520px; padding: 2.6rem 2.4rem !important; border-radius: 22px !important; }}
.st-key-card_hero h2 {{ font-size: 2.5rem; font-weight: 600; line-height: 1.12; margin: 2.2rem 0 1.2rem 0; color:#fff; letter-spacing:-.02em; }}
.st-key-card_hero li {{ color:#e5eaff; margin: .65rem 0; font-size: 1rem; list-style: none; }}
.st-key-card_hero li:before {{ content:'✓'; display:inline-block; width:22px; height:22px; margin-right:.7rem; border-radius:50%; background:rgba(255,255,255,.2); text-align:center; line-height:22px; font-size:.75rem; }}
.st-key-card_hero .tag {{ display:inline-block; padding:.2rem .8rem; border:1px solid rgba(255,255,255,.45); border-radius:999px; font-size:.75rem; letter-spacing:.06em; }}
.st-key-card_login {{ padding: 2.4rem 2.2rem !important; min-height: 520px; display:flex; justify-content:center; border-radius:22px !important; }}
.thead {{ display:flex; color:{MUTED}; font-size:.7rem; letter-spacing:.09em; text-transform:uppercase; padding:.2rem 0 .6rem 0; border-bottom:1px solid {LINE}; margin-bottom:.4rem; }}
.crumb {{ color:{MUTED}; font-size:.76rem; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.25rem; }}
.sitefoot {{ text-align:center; color:{MUTED}; font-size:.76rem; margin-top:2.4rem; padding-top:1rem; border-top:1px solid {LINE}; }}

/* buttons: outlined pill by default, filled for primary */
.main .stButton > button, .main .stDownloadButton > button, .main [data-testid="stFormSubmitButton"] > button {{
  border-radius:999px; border:1px solid {BLUE}; color:{BLUE}; background:transparent; padding:.3rem 1.3rem; font-size:.8rem; letter-spacing:.05em; text-transform:uppercase; font-weight:500; }}
.main .stButton > button:hover, .main .stDownloadButton > button:hover {{ background:#e8f2ff; border-color:{BLUE}; color:{BLUE}; }}
.main .stButton > button[kind="primary"], .main [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {{ background:{BLUE}; color:#fff; border-color:{BLUE}; }}
.main .stButton > button[kind="primary"]:hover {{ background:#1f7be0; color:#fff; }}
.main .stButton > button p {{ font-size:.8rem; }}
.btn-danger .stButton > button {{ border-color:#f0506e; color:#f0506e; }} .btn-danger .stButton > button:hover {{ background:#ffe9ed; color:#d1304f; }}
.btn-danger .stButton > button[kind="primary"] {{ background:#f0506e; color:#fff; }}

/* inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input, div[data-baseweb="select"] > div {{ border-radius:12px !important; background:#fff !important; border:1px solid {LINE} !important; }}
.stTextInput label, .stSelectbox label, .stTextArea label, .stNumberInput label, .stMultiSelect label, .stFileUploader label {{ color:{MUTED}; font-size:.76rem; }}
[data-testid="stFileUploaderDropzone"] {{ background:#f6f8ff; border:1.5px dashed #b9c5ef; border-radius:14px; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:1.8rem; border-bottom:1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ padding:.5rem 0; background:transparent; color:{MUTED}; font-size:.88rem; }}
.stTabs [aria-selected="true"] {{ color:{BLUE} !important; font-weight:500; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:{BLUE}; height:2px; }}
[data-testid="stAlert"] {{ border-radius:12px; }}
hr {{ border-color:{LINE}; }}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(s) -> str:
    return html.escape("" if s is None else str(s))


_AV = ["#6b7fe8", "#0ea5e9", "#12b79b", "#f5a524", "#ec4899", "#8b6fe0", "#14b8a6", "#f97316"]


def avatar(name: str, size: int = 38) -> str:
    initials = "".join(w[0] for w in (name or "?").split()[:2]).upper() or "?"
    bg = _AV[sum(ord(c) for c in (name or "?")) % len(_AV)]
    return (f'<span class="avatar" style="width:{size}px;height:{size}px;background:{bg};font-size:{size * .38:.0f}px">'
            f'{esc(initials)}</span>')


def pill(text: str) -> str:
    bg, fg = STATUS.get(text, ("#eceffa", "#5b6690"))
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(text)}</span>'


def ring(score, size: int = 46, stroke: int = 5) -> str:
    if score is None:
        return f'<span style="color:{MUTED};font-size:.78rem">pending</span>'
    r = (size - stroke) / 2
    c = 6.2832 * r
    col = "#12b79b" if score >= 75 else "#f5a524" if score >= 50 else "#f0506e"
    return (f'<span style="position:relative;display:inline-flex;width:{size}px;height:{size}px;align-items:center;justify-content:center">'
            f'<svg width="{size}" height="{size}" style="transform:rotate(-90deg)"><circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#e6eaf7" stroke-width="{stroke}"/>'
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{col}" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{c * (1 - score / 100):.1f}"/></svg>'
            f'<span style="position:absolute;font-weight:600;font-size:{size * .3:.0f}px">{round(score)}</span></span>')


def chips(items, tone="n", empty="—") -> str:
    return "".join(f'<span class="chip {tone}">{esc(i)}</span>' for i in items) or f'<span style="color:{MUTED}">{empty}</span>'


def kv(rows) -> str:
    return "".join(f'<div class="kv"><span class="k">{esc(k)}:</span><span class="v">{v}</span></div>' for k, v in rows)


def card_title(text: str, edit: bool = False) -> str:
    return f'<div class="card-title">{esc(text)}{"<span class=edit>✎</span>" if edit else ""}</div>'


def topbar(title: str, sub: str, user) -> None:
    st.markdown(
        f'<div class="topbar"><div><div class="crumb">CloudRiq · {esc(title)}</div><h1>{esc(title)}</h1><div class="sub">{esc(sub)}</div></div>'
        f'<div class="who"><span>{esc(user.role.replace("_", " ").upper())}</span><span class="dot">🔔</span>'
        f'{avatar(user.full_name, 40)}</div></div>', unsafe_allow_html=True)


def hbars(rows, color=BLUE, total=None) -> str:
    mx = max([v for _, v in rows] + [1])
    return "".join(
        f'<div class="hbar"><span class="lbl">{esc(k)}</span><span class="tr"><i style="width:{v / mx * 100:.0f}%;background:{color}"></i></span>'
        f'<span class="ct">{v}</span></div>' for k, v in rows)


def empty(msg: str) -> None:
    st.markdown(f'<div class="empty">{esc(msg)}</div>', unsafe_allow_html=True)
