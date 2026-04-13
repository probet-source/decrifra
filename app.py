
import json
import re
import zipfile
from io import BytesIO

import streamlit as st

from core.ai_engine import analyze_document, compare_documents
from core.extractors import extract_text_from_uploaded_file
from core.exporters import build_json_report, build_markdown_report, build_pdf_report, build_txt_report
from core.playbooks import DOCUMENT_PLAYBOOKS, OBJECTIVES, REPLY_STYLES, quick_examples
from core.ui import (
    inject_css,
    render_badges,
    render_callout,
    render_empty_state,
    render_feature_card,
    render_footer,
    render_hero,
    render_kpi,
    render_pricing_card,
    render_section_header,
    render_step_card,
    render_toolbar,
)

APP_NAME = "DECIFRAM"
APP_VERSION = "V7 Lançamento Comercial"
APP_TAGLINE = "Cole o documento. Entenda em minutos. Resolva hoje."
APP_SUBTITLE = (
    "Produto de leitura documental com cara de lançamento real: onboarding claro, cockpit executivo, "
    "comparação entre documentos, respostas por postura, playbook operacional e exportação pronta para uso."
)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9áàâãéèêíïóôõöúçñ_-]+", "-", value, flags=re.IGNORECASE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "documento"


def build_bundle_zip(document_name: str, result: dict, comparison: dict | None = None):
    md_content = build_markdown_report(result, document_name)
    txt_content = build_txt_report(result, document_name)
    json_content = build_json_report(result, document_name)
    pdf_bytes = build_pdf_report(result, document_name)
    mem = BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        safe_name = slugify(document_name)
        zf.writestr(f"{safe_name}_decifram_v7.md", md_content)
        zf.writestr(f"{safe_name}_decifram_v7.txt", txt_content)
        zf.writestr(f"{safe_name}_decifram_v7.json", json_content)
        zf.writestr(f"{safe_name}_decifram_v7.pdf", pdf_bytes)
        if comparison:
            zf.writestr(f"{safe_name}_comparacao_decifram_v7.json", json.dumps(comparison, ensure_ascii=False, indent=2))
    mem.seek(0)
    return md_content, txt_content, json_content, pdf_bytes, mem.getvalue()


def _copy_button(label: str, content: str | bytes, filename: str, mime: str = "text/plain"):
    st.download_button(label, data=content, file_name=filename, mime=mime, use_container_width=True)


def _render_bullets(items):
    if not items:
        st.caption("Sem itens extraídos nesta seção.")
        return
    for item in items:
        st.markdown(f"- {item}")


def _render_risks(risks):
    if not risks:
        st.caption("Sem alertas extraídos.")
        return
    for risk in risks:
        st.warning(f"**{risk.get('title', 'Alerta')}** — {risk.get('details', '')}")


def _render_deadlines(deadlines):
    if not deadlines:
        st.caption("Nenhum prazo explícito encontrado.")
        return
    for item in deadlines:
        st.info(f"**{item.get('date_or_window', '')}** — {item.get('what', '')}")


def _score_label(score: int) -> str:
    if score >= 80:
        return "Muito forte"
    if score >= 60:
        return "Bom"
    if score >= 40:
        return "Atenção"
    return "Crítico"


st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📄", layout="wide", initial_sidebar_state="expanded")
inject_css()

DEFAULT_STATE = {
    "analysis": None,
    "analysis_compare": None,
    "comparison": None,
    "raw_text": "",
    "raw_text_compare": "",
    "document_name": "documento",
    "document_name_compare": "documento_comparado",
    "input_origin": "Nenhuma",
    "input_origin_compare": "Nenhuma",
    "session_runs": 0,
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.markdown(f"## {APP_NAME}")
    st.caption(f"{APP_VERSION} • GitHub + Streamlit • Stateless")
    st.markdown("### Configuração da leitura")
    model = st.selectbox(
        "Modelo via OpenRouter",
        [
            "openai/gpt-4.1-mini",
            "google/gemini-2.5-flash-preview",
            "deepseek/deepseek-chat-v3-0324",
            "meta-llama/llama-4-maverick",
        ],
        index=0,
    )
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.1, 0.01)
    max_chars = st.slider("Máx. de caracteres enviados", 4000, 50000, 24000, 1000)
    force_local = st.toggle("Forçar modo local", value=False)

    st.markdown("### Modo de lançamento")
    launch_mode = st.radio(
        "Experiência",
        ["Demonstração comercial", "Operação direta"],
        horizontal=False,
        index=0,
    )
    soft_cap = 3
    progress = min(st.session_state.session_runs / soft_cap, 1.0)
    st.progress(progress, text=f"Análises nesta sessão: {st.session_state.session_runs}/{soft_cap} no modo demonstração")
    st.info("Sem cadastro, sem banco e sem persistência. O app processa em memória e entrega saída acionável imediatamente.")
    if st.session_state.session_runs >= soft_cap:
        st.warning("Você já ultrapassou o volume sugerido de demonstração nesta sessão. O app continua funcionando, mas a barra já simula o argumento comercial de upgrade.")
    st.success("Pronto para apresentação, piloto, prova de valor e deploy rápido no Streamlit Cloud.")
    st.caption("Casos sensíveis ainda pedem validação humana antes do envio final.")

hero_left, hero_right = st.columns([1.55, 1], gap="large")
with hero_left:
    render_hero(APP_NAME, APP_VERSION, APP_TAGLINE, APP_SUBTITLE)
    render_badges([
        "Sem banco",
        "Sem cadastro",
        "Comparação premium",
        "Respostas por postura",
        "Cockpit executivo",
        "Exportação pronta",
    ])
    render_toolbar([
        "PDF • DOCX • TXT • MD",
        "Modo remoto ou local",
        "LGPD-friendly",
        "Pronto para GitHub",
        "White-label no futuro",
    ])
with hero_right:
    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi("Sessão", "Privada", "Processamento em memória")
    with c2:
        render_kpi("Saída", "Acionável", "Plano, risco e resposta")
    with c3:
        render_kpi("Status", "Launch-ready", "Produto apresentável")
    render_callout(
        "Posicionamento forte",
        "O DECIFRAM V7 foi lapidado para parecer um produto real de mercado: entrega rápida, leitura clara, prova de valor e narrativa comercial dentro do próprio app.",
    )

steps = st.columns(4)
step_items = [
    (1, "Inserir documento", "Envie arquivo ou cole texto do caso."),
    (2, "Escolher objetivo", "Selecione foco da leitura e tom da análise."),
    (3, "Receber cockpit", "Veja score, risco, prazos, resposta e playbook."),
    (4, "Exportar e agir", "Baixe os materiais e siga o plano hoje."),
]
for col, (idx, title, text) in zip(steps, step_items):
    with col:
        render_step_card(idx, title, text)

launch_cols = st.columns([1.3, 1.3, 1.3], gap="large")
with launch_cols[0]:
    render_feature_card("Dor resolvida rápido", "Transforma papelada confusa em entendimento operacional sem exigir estudo técnico prévio.")
with launch_cols[1]:
    render_feature_card("Valor percebido alto", "Não entrega só resumo: prioriza risco, plano de ação, resposta pronta e comparação entre versões.")
with launch_cols[2]:
    render_feature_card("Narrativa de venda", "A interface já ajuda a demonstrar o produto para cliente, parceiro ou potencial assinante.")

if launch_mode == "Demonstração comercial":
    p1, p2 = st.columns(2, gap="large")
    with p1:
        render_pricing_card("Demonstração", "R$ 0", ["Uso imediato", "Sem cadastro", "Leitura orientada", "Exportação completa"], accent=False)
    with p2:
        render_pricing_card("DECIFRAM PRO", "Sob ativação", ["Mais volume", "Mais contexto", "Fluxo white-label", "Escala comercial"], accent=True)

left_col, right_col = st.columns([1.04, 1.16], gap="large")

with left_col:
    render_section_header("1) Entrada e configuração", "Fluxo comercialmente claro: carregue, enquadre o caso, escolha a postura e rode a análise.")
    analysis_profile = st.selectbox("Objetivo da análise", OBJECTIVES, index=0)
    document_context = st.selectbox("Contexto do documento", list(DOCUMENT_PLAYBOOKS.keys()), index=0)
    tone = st.select_slider("Tom da saída", options=["Mais humano", "Claro e objetivo", "Mais técnico", "Mais firme"], value="Claro e objetivo")
    response_style = st.radio("Resposta padrão a destacar", REPLY_STYLES, horizontal=True)
    compare_mode = st.toggle("Ativar comparação entre dois documentos", value=False)

    with st.expander("Exemplos rápidos para teste, venda e demonstração"):
        example_choice = st.selectbox("Carregar exemplo", ["Nenhum"] + list(quick_examples.keys()))
        if st.button("Usar exemplo no documento principal", use_container_width=True):
            if example_choice != "Nenhum":
                st.session_state.raw_text = quick_examples[example_choice]
                st.session_state.document_name = f"exemplo_{slugify(example_choice)}"
                st.session_state.input_origin = "Exemplo interno"
                st.rerun()

    uploaded = st.file_uploader("Documento principal", type=["pdf", "docx", "txt", "md"], accept_multiple_files=False, key="main_upload")
    pasted_text = st.text_area("Ou cole o conteúdo principal", height=220, placeholder="Cole aqui o conteúdo do documento principal...")

    if uploaded is not None:
        try:
            source_text, extraction_notice = extract_text_from_uploaded_file(uploaded)
            st.session_state.raw_text = source_text
            st.session_state.document_name = uploaded.name
            st.session_state.input_origin = "Arquivo enviado"
            if extraction_notice:
                st.warning(extraction_notice)
        except Exception as exc:
            st.error(f"Falha ao ler o documento principal: {exc}")
    elif pasted_text.strip():
        st.session_state.raw_text = pasted_text.strip()
        st.session_state.document_name = "texto_colado_principal"
        st.session_state.input_origin = "Texto colado"

    if compare_mode:
        st.markdown("---")
        uploaded_compare = st.file_uploader("Documento para comparar", type=["pdf", "docx", "txt", "md"], accept_multiple_files=False, key="compare_upload")
        pasted_text_compare = st.text_area("Ou cole o conteúdo do segundo documento", height=180, placeholder="Cole aqui o conteúdo do segundo documento...")
        if uploaded_compare is not None:
            try:
                source_text, extraction_notice = extract_text_from_uploaded_file(uploaded_compare)
                st.session_state.raw_text_compare = source_text
                st.session_state.document_name_compare = uploaded_compare.name
                st.session_state.input_origin_compare = "Arquivo enviado"
                if extraction_notice:
                    st.warning(extraction_notice)
            except Exception as exc:
                st.error(f"Falha ao ler o documento de comparação: {exc}")
        elif pasted_text_compare.strip():
            st.session_state.raw_text_compare = pasted_text_compare.strip()
            st.session_state.document_name_compare = "texto_colado_comparacao"
            st.session_state.input_origin_compare = "Texto colado"

    cta1, cta2 = st.columns(2)
    with cta1:
        analyze_clicked = st.button("Gerar cockpit premium", use_container_width=True, type="primary")
    with cta2:
        clear_clicked = st.button("Limpar sessão", use_container_width=True)

    if clear_clicked:
        for key, value in DEFAULT_STATE.items():
            st.session_state[key] = value
        st.rerun()

    if st.session_state.raw_text.strip():
        render_callout(
            "Documento principal pronto",
            f"Origem: {st.session_state.input_origin} • Nome: {st.session_state.document_name} • Tamanho lido: {len(st.session_state.raw_text):,} caracteres.",
        )
    else:
        render_empty_state("Nada carregado ainda.", "Envie um arquivo ou cole um texto. O DECIFRAM foi desenhado para transformar documento em plano de ação, não apenas em resumo.")

    if compare_mode:
        if st.session_state.raw_text_compare.strip():
            render_callout(
                "Documento de comparação pronto",
                f"Origem: {st.session_state.input_origin_compare} • Nome: {st.session_state.document_name_compare} • Tamanho lido: {len(st.session_state.raw_text_compare):,} caracteres.",
            )
        else:
            render_empty_state("Comparação aguardando segundo documento.", "Carregue um segundo arquivo para comparar cláusulas, prazos, valores, exigências e riscos.")

    if analyze_clicked:
        if not st.session_state.raw_text.strip():
            st.error("Envie ou cole o documento principal antes de analisar.")
        elif compare_mode and not st.session_state.raw_text_compare.strip():
            st.error("A comparação foi ativada, mas o segundo documento ainda não foi carregado.")
        else:
            with st.spinner("Lendo o documento e montando o cockpit executivo..."):
                main_result = analyze_document(
                    raw_text=st.session_state.raw_text,
                    model=model,
                    temperature=temperature,
                    max_chars=max_chars,
                    tone=tone,
                    document_context=document_context,
                    analysis_profile=analysis_profile,
                    force_local=force_local,
                )
                st.session_state.analysis = main_result
                st.session_state.session_runs += 1
                if compare_mode and st.session_state.raw_text_compare.strip():
                    compare_result = analyze_document(
                        raw_text=st.session_state.raw_text_compare,
                        model=model,
                        temperature=temperature,
                        max_chars=max_chars,
                        tone=tone,
                        document_context=document_context,
                        analysis_profile=analysis_profile,
                        force_local=force_local,
                    )
                    st.session_state.analysis_compare = compare_result
                    st.session_state.comparison = compare_documents(
                        main_result,
                        compare_result,
                        st.session_state.document_name,
                        st.session_state.document_name_compare,
                    )
                else:
                    st.session_state.analysis_compare = None
                    st.session_state.comparison = None

with right_col:
    render_section_header("2) Cockpit executivo", "Painel de decisão mais claro: leitura rápida, risco, resposta, comparação e exportação em um só fluxo.")
    result = st.session_state.analysis
    compare_result = st.session_state.analysis_compare
    comparison = st.session_state.comparison

    if not result:
        render_empty_state("Seu painel executivo aparecerá aqui.", "A V7 combina prova de valor, clareza operacional, resposta editável, comparação e exportação em uma experiência de lançamento comercial.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        exec_score = int(result.get("executive_score", 75) or 75)
        risk_score = int(result.get("risk_score", 55) or 55)
        with k1:
            render_kpi("Tipo", result.get("detected_document_type", "Outro"), "Documento identificado")
        with k2:
            render_kpi("Prioridade", result.get("urgency_level", "Média"), "Urgência operacional")
        with k3:
            render_kpi("Score executivo", str(exec_score), _score_label(exec_score))
        with k4:
            render_kpi("Score de risco", str(risk_score), _score_label(100 - risk_score))

        st.progress(min(max(exec_score, 0), 100), text=f"Força executiva da leitura: {exec_score}/100")
        st.progress(min(max(risk_score, 0), 100), text=f"Risco operacional identificado: {risk_score}/100")

        tabs = st.tabs([
            "Visão executiva",
            "Riscos e prazos",
            "Resposta inteligente",
            "Comparação",
            "Exportação",
        ])

        with tabs[0]:
            top_a, top_b = st.columns([1.08, 0.92], gap="large")
            with top_a:
                st.subheader("Resumo executivo")
                _render_bullets(result.get("summary_bullets", []))
                st.subheader("Pontos centrais")
                _render_bullets(result.get("key_points", []))
                st.subheader("Próxima melhor ação")
                st.success(result.get("best_next_action", ""))
            with top_b:
                st.subheader("Visão comercial")
                _render_bullets(result.get("commercial_view", []))
                st.subheader("Playbook sugerido")
                st.info(result.get("playbook_guidance", ""))
            st.subheader("Explicação simples")
            st.write(result.get("plain_language_explanation", ""))
            st.subheader("Matriz de decisão")
            matrix = result.get("decision_matrix", [])
            if matrix:
                for row in matrix:
                    st.write(f"**{row.get('axis', '')}** — {row.get('status', '')}")
                    st.caption(row.get("note", ""))
            else:
                st.caption("Sem matriz disponível.")

        with tabs[1]:
            top_a, top_b = st.columns(2, gap="large")
            with top_a:
                st.subheader("Alertas e riscos")
                _render_risks(result.get("risks", []))
                st.subheader("Prazos e janelas")
                _render_deadlines(result.get("deadlines", []))
            with top_b:
                st.subheader("Valores encontrados")
                _render_bullets(result.get("values_found", []))
                st.subheader("Partes e entidades")
                _render_bullets(result.get("entities", []))
            st.subheader("Obrigações e exigências")
            _render_bullets(result.get("obligations", []))
            st.subheader("Checklist de providências")
            _render_bullets(result.get("action_checklist", []))
            st.subheader("Observações")
            st.caption(result.get("important_notes", ""))

        with tabs[2]:
            st.subheader("Resposta padrão")
            variant_key = {
                "Neutra": "neutra",
                "Firme": "firme",
                "Estratégica": "estrategica",
            }[response_style]
            selected_reply = result.get("reply_variants", {}).get(variant_key) or result.get("ready_reply", "")
            st.text_area("Texto sugerido", selected_reply, height=220)
            _copy_button("Baixar resposta em TXT", selected_reply, f"{slugify(st.session_state.document_name)}_resposta_{variant_key}.txt")
            cols = st.columns(3)
            variants = result.get("reply_variants", {})
            with cols[0]:
                st.markdown("**Neutra**")
                st.text_area("Variante neutra", variants.get("neutra", ""), height=180, key="reply_neutra")
            with cols[1]:
                st.markdown("**Firme**")
                st.text_area("Variante firme", variants.get("firme", ""), height=180, key="reply_firme")
            with cols[2]:
                st.markdown("**Estratégica**")
                st.text_area("Variante estratégica", variants.get("estrategica", ""), height=180, key="reply_estrategica")

        with tabs[3]:
            if comparison and compare_result:
                st.subheader("Resumo da comparação")
                _render_bullets(comparison.get("summary", []))
                cc1, cc2 = st.columns(2, gap="large")
                with cc1:
                    st.markdown(f"**Só em {st.session_state.document_name}**")
                    _render_bullets(comparison.get("only_primary", []))
                with cc2:
                    st.markdown(f"**Só em {st.session_state.document_name_compare}**")
                    _render_bullets(comparison.get("only_secondary", []))
                st.success(comparison.get("recommendation", ""))
                st.markdown("---")
                tc1, tc2 = st.columns(2, gap="large")
                with tc1:
                    st.markdown(f"### {st.session_state.document_name}")
                    st.caption(f"Tipo: {result.get('detected_document_type')} • Prioridade: {result.get('urgency_level')} • Risco: {result.get('risk_score')}")
                    _render_bullets(result.get("summary_bullets", []))
                with tc2:
                    st.markdown(f"### {st.session_state.document_name_compare}")
                    st.caption(f"Tipo: {compare_result.get('detected_document_type')} • Prioridade: {compare_result.get('urgency_level')} • Risco: {compare_result.get('risk_score')}")
                    _render_bullets(compare_result.get("summary_bullets", []))
            else:
                render_empty_state("Comparação não ativa nesta sessão.", "Ative a comparação e carregue um segundo documento para localizar divergências de risco, prazo, valor, exigências e posição do documento.")

        with tabs[4]:
            md_content, txt_content, json_content, pdf_bytes, zip_bytes = build_bundle_zip(
                st.session_state.document_name,
                result,
                comparison=comparison,
            )
            safe_name = slugify(st.session_state.document_name)
            c1, c2 = st.columns(2)
            with c1:
                _copy_button("Baixar PDF", pdf_bytes, f"{safe_name}_decifram_v7.pdf", mime="application/pdf")
                _copy_button("Baixar Markdown", md_content, f"{safe_name}_decifram_v7.md", mime="text/markdown")
                _copy_button("Baixar TXT", txt_content, f"{safe_name}_decifram_v7.txt")
            with c2:
                _copy_button("Baixar JSON", json_content, f"{safe_name}_decifram_v7.json", mime="application/json")
                _copy_button("Baixar ZIP completo", zip_bytes, f"{safe_name}_decifram_v7_bundle.zip", mime="application/zip")
            st.caption("O ZIP inclui a análise principal e a comparação em JSON quando a comparação estiver ativa.")

st.markdown("---")
launch_cta_left, launch_cta_right = st.columns([1.4, 1], gap="large")
with launch_cta_left:
    render_callout(
        "Pronto para apresentar e vender",
        "A V7 já traz a narrativa comercial no próprio produto: o usuário entende o valor, enxerga a dor resolvida e sai com material útil para agir.",
    )
with launch_cta_right:
    render_callout(
        "Estrutura preparada para próximos passos",
        "Sem alterar a arquitetura stateless, você pode evoluir para limites por plano, white-label, integrações e camada comercial futura.",
    )

render_footer("DECIFRAM V7 Lançamento Comercial • premium • técnico • intuitivo • sem banco • sem cadastro • pronto para GitHub + Streamlit")
