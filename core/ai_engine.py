import json
import os
import re
from typing import Any, Dict, List

import requests
import streamlit as st

from core.playbooks import DOCUMENT_PLAYBOOKS

SYSTEM_PROMPT = """
Você é o DECIFRAM, um motor premium de leitura documental em português do Brasil.
Sua função é transformar documento confuso em plano claro, acionável, honesto e comercialmente bem organizado.
Você não presta aconselhamento definitivo. Você resume, prioriza, sinaliza riscos, prazos, valores, obrigações, partes, próximos passos, respostas iniciais e visão executiva.

Responda APENAS em JSON válido, sem markdown e sem texto fora do JSON.
Estrutura obrigatória:
{
  "detected_document_type": "...",
  "urgency_level": "Baixa|Média|Alta",
  "confidence_label": "Baixa|Moderada|Alta",
  "executive_score": 0,
  "risk_score": 0,
  "summary_bullets": ["...", "...", "..."],
  "key_points": ["...", "...", "..."],
  "risks": [{"title": "...", "details": "..."}],
  "deadlines": [{"date_or_window": "...", "what": "..."}],
  "values_found": ["..."],
  "obligations": ["..."],
  "entities": ["..."],
  "action_checklist": ["...", "...", "..."],
  "best_next_action": "...",
  "ready_reply": "...",
  "reply_variants": {"neutra": "...", "firme": "...", "estrategica": "..."},
  "plain_language_explanation": "...",
  "commercial_view": ["...", "...", "..."],
  "decision_matrix": [{"axis": "...", "status": "...", "note": "..."}],
  "important_notes": "..."
}

Regras:
- Use português do Brasil.
- Não invente datas, leis, números, cláusulas ou valores.
- Se algo não estiver claro, reconheça a limitação.
- Seja objetivo, útil e organizado.
- A resposta pronta deve soar humana, profissional e editável.
- executive_score e risk_score devem ser de 0 a 100.
""".strip()


@st.cache_resource(show_spinner=False)
def _http_session():
    session = requests.Session()
    session.headers.update({"User-Agent": "DECIFRAM-V6/1.0"})
    return session


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _truncate_text(text: str, max_chars: int) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars]


def _extract_values(text: str) -> List[str]:
    money = re.findall(r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?", text)
    perc = re.findall(r"\d{1,3}(?:,\d+)?%", text)
    out: List[str] = []
    for item in money + perc:
        if item not in out:
            out.append(item)
    return out[:12]


def _extract_dates(text: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for p in re.findall(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text)[:10]:
        out.append({"date_or_window": p, "what": "Data mencionada no documento"})
    time_keywords = ["30 dias", "15 dias", "10 dias", "5 dias", "48 horas", "72 horas", "24 horas", "imediato", "vencimento", "prazo"]
    for keyword in time_keywords:
        if keyword.lower() in text.lower() and not any(keyword in x["date_or_window"] for x in out):
            out.append({"date_or_window": keyword, "what": "Janela temporal mencionada no documento"})
    return out[:10]


def _extract_entities(text: str) -> List[str]:
    entities: List[str] = []
    for match in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú]+){0,3}", text):
        if len(match) > 2 and match not in entities:
            entities.append(match)
    return entities[:12]


def _infer_doc_type(text: str, context: str) -> str:
    t = text.lower()
    if context != "Auto detectar":
        return context
    rules = [
        ("Contrato", ["contrato", "cláusula", "vigência", "locador", "locatário", "rescis"]),
        ("Cobrança/Fatura/Boleto", ["boleto", "fatura", "cobrança", "negativação", "juros", "multa"]),
        ("Edital/Formulário", ["edital", "licitante", "pregão", "inabilitação", "certidão", "proposta"]),
        ("Laudo/Relatório", ["laudo", "relatório", "conclusão", "parecer"]),
        ("Plano de saúde/Seguro", ["plano de saúde", "carência", "cobertura", "seguradora"]),
        ("Comunicado bancário", ["banco", "conta", "tarifa", "cartão", "extrato"]),
        ("Notificação/Aviso", ["notific", "aviso", "intima", "desocupar", "comunicamos"]),
    ]
    for label, terms in rules:
        if any(k in t for k in terms):
            return label
    return "Outro"


def _infer_risks(text: str, doc_type: str) -> List[Dict[str, str]]:
    t = text.lower()
    checks = [
        ("Prazo sensível", ["prazo", "vencimento", "até o dia", "48 horas", "72 horas", "30 dias", "15 dias"], "Há indicação de prazo. Perder esse marco pode gerar prejuízo prático."),
        ("Possível penalidade", ["multa", "penalidade", "negativação", "rescisão", "inabilitação", "suspensão"], "O texto menciona consequência desfavorável em caso de descumprimento."),
        ("Obrigação relevante", ["deverá", "obrigatório", "fica responsável", "sob pena", "dever de"], "Há obrigação expressa ou condição que exige ação."),
        ("Cobertura ou negativa", ["carência", "sem cobertura", "indeferido", "negado", "não autorizado"], "Existe sinal de recusa, limitação ou negativa que pede revisão humana."),
        ("Valor sensível", ["r$", "%", "reajuste", "juros", "correção monetária"], "Há valores, percentuais ou critérios financeiros que merecem conferência."),
    ]
    risks: List[Dict[str, str]] = []
    for title, terms, detail in checks:
        if any(term in t for term in terms):
            risks.append({"title": title, "details": detail})
    if not risks:
        risks.append({"title": "Atenção geral", "details": f"Documento classificado como {doc_type}. Recomenda-se validação do contexto completo antes de qualquer decisão."})
    return risks[:8]


def _infer_obligations(text: str) -> List[str]:
    obligations = []
    patterns = [r"deverá[^\n\.]{0,140}", r"fica responsável[^\n\.]{0,140}", r"obrigatóri[^\n\.]{0,140}", r"sob pena[^\n\.]{0,140}"]
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            cleaned = re.sub(r"\s+", " ", match).strip(" .;:-")
            if cleaned and cleaned not in obligations:
                obligations.append(cleaned)
    if not obligations:
        obligations = [
            "Revisar os trechos com obrigação, prazo, consequência ou condição de cumprimento.",
            "Conferir anexos, comprovantes, páginas e cláusulas complementares.",
            "Validar o documento integralmente antes de assinar, pagar, responder ou protocolar.",
        ]
    return obligations[:8]


def _infer_priority(deadlines: List[Dict[str, str]], risks: List[Dict[str, str]]) -> str:
    high_triggers = {"Prazo sensível", "Possível penalidade", "Cobertura ou negativa"}
    if deadlines or any(r["title"] in high_triggers for r in risks):
        return "Alta"
    if len(risks) >= 2:
        return "Média"
    return "Baixa"


def _build_reply_variants(doc_type: str) -> Dict[str, str]:
    base_subject = f"o documento classificado como {doc_type.lower()}"
    return {
        "neutra": (
            f"Prezados,\n\nApós leitura inicial de {base_subject}, identifiquei pontos que precisam de confirmação, especialmente quanto a prazos, obrigações e consequências. "
            "Solicito, por gentileza, esclarecimento formal dos itens sensíveis antes de qualquer providência definitiva.\n\nFico no aguardo."
        ),
        "firme": (
            f"Prezados,\n\nApós análise inicial de {base_subject}, verifiquei pontos sensíveis que exigem revisão e confirmação formal imediata. "
            "Até que esses itens sejam esclarecidos de forma objetiva, reservo-me o direito de não adotar providência definitiva que possa gerar prejuízo.\n\nAguardo retorno."
        ),
        "estrategica": (
            f"Prezados,\n\nEm análise preliminar de {base_subject}, notei aspectos que podem impactar prazo, obrigação e consequência prática. "
            "Para evitar ruído operacional e preservar segurança na próxima etapa, peço consolidação formal dos pontos críticos e indicação do procedimento correto a seguir.\n\nPermaneço à disposição."
        ),
    }


def _decision_matrix(risks: List[Dict[str, str]], deadlines: List[Dict[str, str]], values: List[str], entities: List[str]) -> List[Dict[str, str]]:
    return [
        {
            "axis": "Urgência operacional",
            "status": "Alta" if deadlines else "Média",
            "note": "Há prazo ou janela temporal a monitorar." if deadlines else "Sem prazo explícito muito claro no texto lido.",
        },
        {
            "axis": "Exposição a risco",
            "status": "Alta" if len(risks) >= 3 else "Média" if risks else "Baixa",
            "note": f"Foram sinalizados {len(risks)} alerta(s) relevantes.",
        },
        {
            "axis": "Impacto financeiro",
            "status": "Média" if values else "Baixa",
            "note": "Há valores ou percentuais que merecem conferência." if values else "Não apareceram valores claros no recorte lido.",
        },
        {
            "axis": "Mapeamento de partes",
            "status": "Bom" if entities else "Parcial",
            "note": "Partes ou entidades relevantes foram identificadas." if entities else "O documento não trouxe nomes claros no recorte analisado.",
        },
    ]


def _commercial_view(doc_type: str, urgency: str, risk_score: int) -> List[str]:
    return [
        f"Leitura comercial: o documento se comporta como {doc_type.lower()} e pede postura {urgency.lower()} no curto prazo.",
        f"O nível de atenção estimado ficou em {risk_score}/100, o que ajuda a priorizar resposta, revisão ou conferência interna.",
        "O valor do painel está em reduzir dúvida, encurtar leitura e acelerar uma decisão mais segura ainda hoje.",
    ]


def _local_fallback(raw_text: str, analysis_profile: str, document_context: str, tone: str) -> Dict[str, Any]:
    trimmed = _truncate_text(raw_text, 22000)
    doc_type = _infer_doc_type(trimmed, document_context)
    values = _extract_values(trimmed)
    deadlines = _extract_dates(trimmed)
    risks = _infer_risks(trimmed, doc_type)
    entities = _extract_entities(trimmed)
    obligations = _infer_obligations(trimmed)
    urgency = _infer_priority(deadlines, risks)
    confidence = "Alta" if len(trimmed) > 1200 else "Moderada"
    executive_score = 86 if len(trimmed) > 1200 else 76
    risk_score = min(95, 35 + len(risks) * 12 + len(deadlines) * 8 + (6 if values else 0))
    reply_variants = _build_reply_variants(doc_type)
    playbook = DOCUMENT_PLAYBOOKS.get(document_context, DOCUMENT_PLAYBOOKS["Outro"])

    objective_note = {
        "Diagnóstico Premium": "foco em leitura ampla e priorização",
        "Riscos e Cláusulas Sensíveis": "foco em riscos, lacunas e pontos delicados",
        "Checklist de Providências": "foco em execução prática e próximos passos",
        "Resposta Pronta": "foco em comunicação inicial editável",
        "Explicação em Linguagem Simples": "foco em compreensão acessível",
        "Visão Comercial/Executiva": "foco em síntese para decisão rápida",
        "Modo Contestação/Defesa": "foco em postura inicial de revisão e contestação",
    }.get(analysis_profile, "foco em organização prática")

    checklist = [
        "Ler o resumo e os alertas antes de tomar qualquer decisão.",
        "Conferir os prazos e as consequências mencionadas no documento original.",
        "Separar documentos de apoio, comprovantes e histórico relacionado ao caso.",
        "Escolher a variante de resposta mais adequada ao contexto real e revisar antes de enviar.",
    ]

    return {
        "detected_document_type": doc_type,
        "urgency_level": urgency,
        "confidence_label": confidence,
        "executive_score": executive_score,
        "risk_score": risk_score,
        "summary_bullets": [
            f"O documento foi lido como {doc_type} com {objective_note}.",
            f"Foram identificados {len(risks)} alerta(s), {len(deadlines)} prazo(s) e {len(values)} referência(s) de valor ou percentual.",
            "O objetivo do painel é transformar leitura confusa em plano de ação claro, sem armazenar dados da sessão.",
        ],
        "key_points": [
            f"Contexto predominante: {doc_type}.",
            "Há pontos que pedem revisão dos trechos críticos antes de decisão final.",
            "A leitura foi estruturada para facilitar entendimento, resposta e encaminhamento.",
        ],
        "risks": risks,
        "deadlines": deadlines,
        "values_found": values,
        "obligations": obligations,
        "entities": entities,
        "action_checklist": checklist,
        "best_next_action": "Conferir os trechos críticos e validar os prazos antes de assinar, responder, pagar ou protocolar qualquer medida.",
        "ready_reply": reply_variants["neutra"],
        "reply_variants": reply_variants,
        "plain_language_explanation": (
            "Em termos simples, este documento parece estabelecer informações que podem gerar obrigação, prazo, custo ou consequência. "
            "O ideal é verificar o que precisa ser feito agora, o que gera risco se for ignorado e qual resposta inicial é mais segura."
        ),
        "commercial_view": _commercial_view(doc_type, urgency, risk_score),
        "decision_matrix": _decision_matrix(risks, deadlines, values, entities),
        "important_notes": "Leitura feita em modo local heurístico. Use como organização inicial e confirme o documento completo antes de agir.",
        "playbook_guidance": playbook,
        "analysis_engine": "Modo local premium",
    }


def _openrouter_request(raw_text: str, model: str, temperature: float, max_chars: int, tone: str, document_context: str, analysis_profile: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", None)
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY não configurada.")

    trimmed = _truncate_text(raw_text, max_chars)
    playbook = DOCUMENT_PLAYBOOKS.get(document_context, DOCUMENT_PLAYBOOKS["Outro"])
    prompt = f"""
Tom solicitado: {tone}
Objetivo da análise: {analysis_profile}
Contexto selecionado: {document_context}
Playbook recomendado: {playbook}

Analise o documento abaixo e devolva o JSON pedido.

DOCUMENTO:
{trimmed}
""".strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "DECIFRAM V6 Premium Comercial",
    }
    response = _http_session().post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)
    parsed["analysis_engine"] = f"OpenRouter • {model}"
    parsed["playbook_guidance"] = playbook
    return parsed


def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    defaults = {
        "detected_document_type": "Outro",
        "urgency_level": "Média",
        "confidence_label": "Moderada",
        "executive_score": 75,
        "risk_score": 55,
        "summary_bullets": [],
        "key_points": [],
        "risks": [],
        "deadlines": [],
        "values_found": [],
        "obligations": [],
        "entities": [],
        "action_checklist": [],
        "best_next_action": "",
        "ready_reply": "",
        "reply_variants": {"neutra": "", "firme": "", "estrategica": ""},
        "plain_language_explanation": "",
        "commercial_view": [],
        "decision_matrix": [],
        "important_notes": "",
        "playbook_guidance": "",
        "analysis_engine": "Indefinido",
    }
    for key, value in defaults.items():
        result.setdefault(key, value)
    for key in ["executive_score", "risk_score"]:
        try:
            result[key] = int(result.get(key, defaults[key]))
        except Exception:
            result[key] = defaults[key]
        result[key] = max(0, min(100, result[key]))
    if not isinstance(result.get("reply_variants"), dict):
        result["reply_variants"] = defaults["reply_variants"].copy()
    return result


def analyze_document(raw_text: str, model: str, temperature: float, max_chars: int, tone: str, document_context: str, analysis_profile: str, force_local: bool = False) -> Dict[str, Any]:
    if force_local:
        return _normalize_result(_local_fallback(raw_text, analysis_profile, document_context, tone))
    try:
        return _normalize_result(_openrouter_request(raw_text, model, temperature, max_chars, tone, document_context, analysis_profile))
    except Exception as exc:
        fallback = _local_fallback(raw_text, analysis_profile, document_context, tone)
        fallback["important_notes"] += f" Falha no motor remoto: {exc}"
        return _normalize_result(fallback)


def compare_documents(primary_result: Dict[str, Any], secondary_result: Dict[str, Any], primary_name: str, secondary_name: str) -> Dict[str, Any]:
    p_values = set(primary_result.get("values_found", []))
    s_values = set(secondary_result.get("values_found", []))
    p_entities = set(primary_result.get("entities", []))
    s_entities = set(secondary_result.get("entities", []))
    p_deadlines = {x.get("date_or_window", "") for x in primary_result.get("deadlines", [])}
    s_deadlines = {x.get("date_or_window", "") for x in secondary_result.get("deadlines", [])}
    p_risks = {x.get("title", "") for x in primary_result.get("risks", [])}
    s_risks = {x.get("title", "") for x in secondary_result.get("risks", [])}

    differences = []
    if primary_result.get("detected_document_type") != secondary_result.get("detected_document_type"):
        differences.append(f"Tipo detectado diferente: {primary_name} foi lido como {primary_result.get('detected_document_type')} e {secondary_name} como {secondary_result.get('detected_document_type')}.")
    if p_values != s_values:
        differences.append("Os valores ou percentuais extraídos não coincidem integralmente entre os documentos.")
    if p_deadlines != s_deadlines:
        differences.append("Os prazos ou janelas temporais encontrados variam entre os dois arquivos.")
    if p_risks != s_risks:
        differences.append("O mapa de risco não é igual entre os documentos comparados.")
    if p_entities != s_entities:
        differences.append("As partes ou entidades identificadas não coincidem completamente.")
    if not differences:
        differences.append("Não foram percebidas divergências estruturais relevantes nos campos comparados desta leitura automatizada.")

    only_primary = []
    only_secondary = []
    for item in sorted(p_values - s_values):
        only_primary.append(f"Valor ou percentual só em {primary_name}: {item}")
    for item in sorted(s_values - p_values):
        only_secondary.append(f"Valor ou percentual só em {secondary_name}: {item}")
    for item in sorted(p_deadlines - s_deadlines):
        only_primary.append(f"Prazo só em {primary_name}: {item}")
    for item in sorted(s_deadlines - p_deadlines):
        only_secondary.append(f"Prazo só em {secondary_name}: {item}")

    recommendation = "Usar a comparação para revisar cláusulas, valores, prazos e partes antes de tomar decisão final ou reaproveitar texto entre versões."
    if differences and len(differences) >= 3:
        recommendation = "Há divergências suficientes para justificar revisão lado a lado do original antes de assinar, responder, protocolar ou cobrar."

    return {
        "summary": differences,
        "only_primary": only_primary[:10],
        "only_secondary": only_secondary[:10],
        "recommendation": recommendation,
    }
