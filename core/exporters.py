import json
from io import BytesIO
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

TITLE = "DECIFRAM V7 Lançamento Comercial"


def _risk_lines(result):
    return [f"{x.get('title', 'Alerta')}: {x.get('details', '')}" for x in result.get("risks", [])]


def _deadline_lines(result):
    return [f"{x.get('date_or_window', '')}: {x.get('what', '')}" for x in result.get("deadlines", [])]


def _matrix_lines(result):
    return [f"{x.get('axis', '')} — {x.get('status', '')}: {x.get('note', '')}" for x in result.get("decision_matrix", [])]


def build_markdown_report(result, document_name):
    md = [f"# {TITLE} — {document_name}", ""]
    md.append(f"**Tipo detectado:** {result.get('detected_document_type', 'Não definido')}")
    md.append(f"**Prioridade:** {result.get('urgency_level', 'Média')}")
    md.append(f"**Confiança:** {result.get('confidence_label', 'Moderada')}")
    md.append(f"**Score executivo:** {result.get('executive_score', 75)}")
    md.append(f"**Score de risco:** {result.get('risk_score', 55)}")
    md.append(f"**Motor:** {result.get('analysis_engine', 'Indefinido')}")
    md.append("")

    sections = [
        ("Resumo executivo", result.get("summary_bullets", []), True),
        ("Pontos centrais", result.get("key_points", []), True),
        ("Alertas e riscos", _risk_lines(result), True),
        ("Prazos e janelas", _deadline_lines(result), True),
        ("Valores encontrados", result.get("values_found", []), True),
        ("Obrigações e exigências", result.get("obligations", []), True),
        ("Entidades ou partes", result.get("entities", []), True),
        ("Checklist de providências", result.get("action_checklist", []), True),
        ("Visão comercial", result.get("commercial_view", []), True),
        ("Matriz de decisão", _matrix_lines(result), True),
        ("Próxima melhor ação", [result.get("best_next_action", "")], False),
        ("Resposta pronta", [result.get("ready_reply", "")], False),
        ("Resposta neutra", [result.get("reply_variants", {}).get("neutra", "")], False),
        ("Resposta firme", [result.get("reply_variants", {}).get("firme", "")], False),
        ("Resposta estratégica", [result.get("reply_variants", {}).get("estrategica", "")], False),
        ("Explicação simples", [result.get("plain_language_explanation", "")], False),
        ("Playbook sugerido", [result.get("playbook_guidance", "")], False),
        ("Observações", [result.get("important_notes", "")], False),
    ]

    for title, items, bullet in sections:
        md.append(f"## {title}")
        if items:
            for item in items:
                md.append(f"- {item}" if bullet else str(item))
        else:
            md.append("Sem conteúdo extraído.")
        md.append("")
    return "\n".join(md)


def build_txt_report(result, document_name):
    return build_markdown_report(result, document_name)


def build_json_report(result, document_name):
    payload = {"document_name": document_name, **result}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_pdf_report(result, document_name):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 40
    y = height - 40
    line_height = 16

    def ensure_page(font="Helvetica", size=10):
        nonlocal y
        if y < 60:
            pdf.showPage()
            y = height - 40
            pdf.setFont(font, size)

    def write_line(text, font="Helvetica", size=10, bullet=False):
        nonlocal y
        ensure_page(font, size)
        pdf.setFont(font, size)
        prefix = "• " if bullet else ""
        lines = wrap(prefix + str(text), 96)
        for line in lines:
            ensure_page(font, size)
            pdf.drawString(x, y, line)
            y -= line_height

    write_line(f"{TITLE} — {document_name}", font="Helvetica-Bold", size=14)
    y -= 2
    write_line(f"Tipo detectado: {result.get('detected_document_type', 'Não definido')}")
    write_line(f"Prioridade: {result.get('urgency_level', 'Média')}")
    write_line(f"Confiança: {result.get('confidence_label', 'Moderada')}")
    write_line(f"Score executivo: {result.get('executive_score', 75)}")
    write_line(f"Score de risco: {result.get('risk_score', 55)}")
    write_line(f"Motor: {result.get('analysis_engine', 'Indefinido')}")

    sections = [
        ("Resumo executivo", result.get("summary_bullets", []), True),
        ("Pontos centrais", result.get("key_points", []), True),
        ("Alertas e riscos", _risk_lines(result), True),
        ("Prazos e janelas", _deadline_lines(result), True),
        ("Valores encontrados", result.get("values_found", []), True),
        ("Obrigações e exigências", result.get("obligations", []), True),
        ("Entidades ou partes", result.get("entities", []), True),
        ("Checklist de providências", result.get("action_checklist", []), True),
        ("Visão comercial", result.get("commercial_view", []), True),
        ("Matriz de decisão", _matrix_lines(result), True),
        ("Próxima melhor ação", [result.get("best_next_action", "")], False),
        ("Resposta pronta", [result.get("ready_reply", "")], False),
        ("Resposta neutra", [result.get("reply_variants", {}).get("neutra", "")], False),
        ("Resposta firme", [result.get("reply_variants", {}).get("firme", "")], False),
        ("Resposta estratégica", [result.get("reply_variants", {}).get("estrategica", "")], False),
        ("Explicação simples", [result.get("plain_language_explanation", "")], False),
        ("Playbook sugerido", [result.get("playbook_guidance", "")], False),
        ("Observações", [result.get("important_notes", "")], False),
    ]

    for title, items, bullets in sections:
        y -= 2
        write_line(title, font="Helvetica-Bold", size=12)
        for item in items:
            if item:
                write_line(item, bullet=bullets)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
