# DECIFRAM V7 Lançamento Comercial

Versão final de lançamento com foco em **produto pronto para apresentação, demonstração comercial e uso real** no GitHub + Streamlit.

## O que esta versão entrega

- interface mais **premium, profissional e intuitiva**
- narrativa de **lançamento comercial** dentro do próprio app
- fluxo com:
  - onboarding visual
  - cockpit executivo
  - comparação entre 2 documentos
  - respostas por postura
  - playbook operacional
  - exportação completa
- painel com:
  - tipo detectado
  - prioridade
  - score executivo
  - score de risco
  - resumo executivo
  - visão comercial
  - matriz de decisão
- leitura detalhada com:
  - alertas e riscos
  - prazos
  - valores encontrados
  - obrigações e exigências
  - entidades/partes
  - checklist de providências
- resposta pronta em 3 variações:
  - neutra
  - firme
  - estratégica
- exportação em:
  - PDF
  - Markdown
  - TXT
  - JSON
  - ZIP completo

## Estrutura

```bash
DECIFRAM-V7/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── assets/
└── core/
    ├── ai_engine.py
    ├── exporters.py
    ├── extractors.py
    ├── playbooks.py
    └── ui.py
```

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Configuração da API

Crie um arquivo `.env` com:

```env
OPENROUTER_API_KEY=sua_chave_aqui
```

Ou configure no Streamlit Cloud em **Secrets**.

## Observações importantes

- a aplicação segue **sem banco, sem cadastro e sem persistência**
- foi mantida a proposta **stateless** para facilitar deploy e reduzir complexidade
- o modo local continua funcional mesmo sem chave remota
- OCR nativo não foi incluído para preservar estabilidade no Streamlit Cloud
- PDFs escaneados em imagem podem exigir texto pesquisável ou colagem manual
- a seção de planos é **visual/comercial**, sem cobrança implementada nesta versão

## Próxima evolução sugerida

- limite free vs pro real
- white-label
- OCR opcional
- camada de monetização
- integração comercial futura
