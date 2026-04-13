
import streamlit as st


def inject_css():
    st.markdown(
        """
        <style>
            :root {
                --bg-1: #06101d;
                --bg-2: #0b1728;
                --panel: rgba(10, 20, 37, .74);
                --panel-2: rgba(10, 20, 37, .88);
                --border: rgba(255,255,255,.08);
                --text: #f8fbff;
                --muted: #b8cbe7;
                --accent: #8fd7ff;
                --accent-2: #8b5cf6;
                --success: #8cf3bf;
                --warning: #ffd58f;
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, .12), transparent 26%),
                    radial-gradient(circle at top right, rgba(139, 92, 246, .16), transparent 23%),
                    linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(7,17,31,.96) 0%, rgba(11,23,40,.94) 100%);
                border-right: 1px solid var(--border);
            }
            .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2rem;
                max-width: 1380px;
            }
            .hero-box, .panel-card, .soft-card, .kpi-card, .feature-card, .empty-card, .callout-card, .step-card, .pricing-card {
                background: var(--panel);
                backdrop-filter: blur(16px);
                border: 1px solid var(--border);
                box-shadow: 0 18px 45px rgba(0,0,0,.24);
                border-radius: 24px;
            }
            .hero-box { padding: 30px; margin-bottom: 14px; min-height: 240px; }
            .eyebrow { color: var(--accent); font-size: .84rem; font-weight: 800; text-transform: uppercase; letter-spacing: .12em; margin-bottom: 12px; }
            .hero-title { font-size: clamp(2rem, 3.4vw, 3.2rem); font-weight: 850; line-height: 1.02; color: var(--text); margin-bottom: 8px; }
            .hero-subtitle { font-size: 1rem; color: var(--muted); margin-top: 8px; line-height: 1.65; max-width: 830px; }
            .hero-note { margin-top: 16px; color: #edf6ff; font-weight: 700; font-size: 1rem; }
            .badge-row { display:flex; flex-wrap:wrap; gap:8px; margin: 10px 0 8px 0; }
            .soft-badge { padding: 8px 12px; border-radius: 999px; background: rgba(96,165,250,.12); color: #dcecff; border: 1px solid rgba(96,165,250,.22); font-size: .82rem; font-weight: 600; }
            .kpi-card { padding: 16px 14px; min-height: 106px; text-align:center; display:flex; flex-direction:column; justify-content:center; }
            .kpi-label { color: #9eb4d9; font-size: .82rem; text-transform: uppercase; letter-spacing: .05em; }
            .kpi-value { font-size: 1.22rem; font-weight: 850; margin-top: 8px; color: var(--text); line-height: 1.15; }
            .kpi-help { font-size: .8rem; color: #9eb4d9; margin-top: 6px; }
            .panel-card, .soft-card, .feature-card, .empty-card, .callout-card, .step-card, .pricing-card { padding: 18px; }
            .section-head { margin: 4px 0 12px 0; }
            .section-head h3 { margin-bottom: 4px; }
            .section-head p { color: #9eb4d9; margin: 0; line-height: 1.5; }
            .feature-title, .callout-title, .step-title, .pricing-title { color: #e7f0ff; font-weight: 800; margin-bottom: 6px; font-size: 1rem; }
            .feature-text, .callout-text, .step-text, .pricing-text { color: #bdd4f5; font-size: .95rem; line-height: 1.55; }
            .empty-card { border-style: dashed; padding: 24px; }
            .callout-card { background: linear-gradient(180deg, rgba(13,26,43,.92) 0%, rgba(10,20,37,.82) 100%); }
            .step-index { width: 34px; height: 34px; border-radius: 999px; display:flex; align-items:center; justify-content:center; font-weight: 800; background: rgba(96,165,250,.15); border: 1px solid rgba(96,165,250,.24); color: var(--text); margin-bottom: 10px; }
            .pricing-card.accent { background: linear-gradient(180deg, rgba(31, 74, 124, .52) 0%, rgba(20, 26, 54, .88) 100%); border-color: rgba(143, 215, 255, .24); }
            .pricing-price { font-size: 1.45rem; font-weight: 850; color: #ffffff; margin-bottom: 10px; }
            .pricing-list { margin: 0; padding-left: 18px; color: #dbeafe; }
            .pricing-list li { margin-bottom: 6px; }
            .app-toolbar { display:flex; gap:10px; flex-wrap:wrap; margin: 6px 0 0 0; }
            .toolbar-pill { padding: 10px 12px; border-radius: 14px; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.06); color: #dcecff; font-size: .84rem; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; flex-wrap: wrap; }
            .stTabs [data-baseweb="tab"] { background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.06); border-radius: 14px; padding: 10px 14px; height: auto; }
            .stTabs [aria-selected="true"] { background: rgba(96,165,250,.14) !important; border-color: rgba(96,165,250,.28) !important; }
            div[data-testid="stMetric"] { background: transparent; }
            .stTextArea textarea, .stTextInput input { border-radius: 16px !important; }
            @media (max-width: 1100px) {
                .block-container { padding-top: .8rem; padding-left: 1rem; padding-right: 1rem; }
                .hero-box { padding: 22px; min-height: auto; }
            }
            @media (max-width: 768px) {
                .kpi-card { min-height: 92px; }
                .hero-title { font-size: 1.9rem; }
                .hero-subtitle, .feature-text, .callout-text, .step-text, .pricing-text { font-size: .92rem; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(app_name: str, version: str, tagline: str, subtitle: str):
    st.markdown(
        f"""
        <div class='hero-box'>
            <div class='eyebrow'>{version}</div>
            <div class='hero-title'>{app_name}</div>
            <div class='hero-subtitle'>{subtitle}</div>
            <div class='hero-note'>{tagline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badges(items):
    tags = "".join([f"<span class='soft-badge'>{item}</span>" for item in items])
    st.markdown(f"<div class='badge-row'>{tags}</div>", unsafe_allow_html=True)


def render_kpi(label: str, value: str, help_text: str | None = None):
    help_html = f"<div class='kpi-help'>{help_text}</div>" if help_text else ""
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value'>{value}</div>
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str):
    st.markdown(f"<div class='section-head'><h3>{title}</h3><p>{subtitle}</p></div>", unsafe_allow_html=True)


def render_feature_card(title: str, text: str):
    st.markdown(f"<div class='feature-card'><div class='feature-title'>{title}</div><div class='feature-text'>{text}</div></div>", unsafe_allow_html=True)


def render_callout(title: str, text: str):
    st.markdown(f"<div class='callout-card'><div class='callout-title'>{title}</div><div class='callout-text'>{text}</div></div>", unsafe_allow_html=True)


def render_empty_state(title: str, text: str):
    st.markdown(f"<div class='empty-card'><div class='feature-title'>{title}</div><div class='feature-text'>{text}</div></div>", unsafe_allow_html=True)


def render_footer(text: str):
    st.markdown(f"<div style='margin-top:22px;color:#8ea7cd;font-size:.88rem;text-align:center'>{text}</div>", unsafe_allow_html=True)


def render_step_card(index: int, title: str, text: str):
    st.markdown(
        f"""
        <div class='step-card'>
            <div class='step-index'>{index}</div>
            <div class='step-title'>{title}</div>
            <div class='step-text'>{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_toolbar(items: list[str]):
    html = "".join([f"<span class='toolbar-pill'>{item}</span>" for item in items])
    st.markdown(f"<div class='app-toolbar'>{html}</div>", unsafe_allow_html=True)


def render_pricing_card(title: str, price: str, items: list[str], accent: bool = False):
    css_class = 'pricing-card accent' if accent else 'pricing-card'
    bullets = ''.join([f'<li>{item}</li>' for item in items])
    st.markdown(
        f"""
        <div class='{css_class}'>
            <div class='pricing-title'>{title}</div>
            <div class='pricing-price'>{price}</div>
            <div class='pricing-text'>Estrutura visual para apresentação comercial e percepção de valor.</div>
            <ul class='pricing-list'>{bullets}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
