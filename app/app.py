"""
Padrão Equilibrium de Excelência — Sistema de Gestão
Grupo Equilibrium · Equilibrium Med Center LTDA

Executar:
    pip install -r requirements.txt
    python app.py
    http://127.0.0.1:8000
"""
import os, re, sqlite3, datetime, pathlib
from contextlib import closing

import markdown as md
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE = pathlib.Path(__file__).resolve().parent
DOCS = BASE.parent / "docs"
DB = BASE / "pee.db"

PESO = {"PADRAO": 3, "DIRETRIZ": 1, "RECOMENDACAO": 0}
ROTULO = {"PADRAO": "Padrão", "DIRETRIZ": "Diretriz", "RECOMENDACAO": "Recomendação"}

app = FastAPI(title="Padrão Equilibrium de Excelência")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
tpl = Jinja2Templates(directory=str(BASE / "templates"))


# ---------------------------------------------------------------- banco
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


SCHEMA = """
CREATE TABLE IF NOT EXISTS unidades (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, cidade TEXT, uf TEXT,
  cnpj TEXT, tipo TEXT DEFAULT 'propria', status TEXT DEFAULT 'implantacao',
  abertura TEXT);

CREATE TABLE IF NOT EXISTS documentos (
  codigo TEXT PRIMARY KEY, titulo TEXT, caderno TEXT, nivel TEXT,
  versao TEXT, arquivo TEXT);

CREATE TABLE IF NOT EXISTS vencimentos (
  id INTEGER PRIMARY KEY, unidade_id INTEGER REFERENCES unidades(id),
  item TEXT NOT NULL, orgao TEXT, validade TEXT, obs TEXT);

CREATE TABLE IF NOT EXISTS colaboradores (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, cargo TEXT,
  unidade_id INTEGER REFERENCES unidades(id), conselho TEXT, registro TEXT);

CREATE TABLE IF NOT EXISTS ciencia (
  id INTEGER PRIMARY KEY, colaborador_id INTEGER REFERENCES colaboradores(id),
  codigo TEXT, data TEXT, UNIQUE(colaborador_id, codigo));

CREATE TABLE IF NOT EXISTS checklist (
  id INTEGER PRIMARY KEY, caderno TEXT, nivel TEXT, inegociavel INTEGER DEFAULT 0,
  descricao TEXT NOT NULL, referencia TEXT);

CREATE TABLE IF NOT EXISTS auditorias (
  id INTEGER PRIMARY KEY, unidade_id INTEGER REFERENCES unidades(id),
  data TEXT, auditor TEXT, status TEXT DEFAULT 'aberta');

CREATE TABLE IF NOT EXISTS auditoria_itens (
  id INTEGER PRIMARY KEY,
  auditoria_id INTEGER REFERENCES auditorias(id) ON DELETE CASCADE,
  checklist_id INTEGER REFERENCES checklist(id),
  resultado TEXT, nota TEXT, UNIQUE(auditoria_id, checklist_id));

CREATE TABLE IF NOT EXISTS indicadores (
  id INTEGER PRIMARY KEY, unidade_id INTEGER REFERENCES unidades(id),
  competencia TEXT, nome TEXT, valor REAL, meta REAL);
"""


def init_db():
    novo = not DB.exists()
    with closing(db()) as c:
        c.executescript(SCHEMA)
        c.commit()
        if novo or not c.execute("SELECT 1 FROM checklist LIMIT 1").fetchone():
            seed(c)
    sync_documentos()


def seed(c):
    """Popula checklist a partir da Carta de Inegociáveis e demais cadernos."""
    inegociaveis = [
        "Nenhum atendimento começa sem consentimento formal registrado",
        "Nenhum documento técnico sai sem assinatura individual identificada",
        "Ninguém atua fora da sua habilitação de conselho",
        "Nenhum diagnóstico é antecipado e nenhum resultado é prometido",
        "Dado de paciente não trafega por canal pessoal",
        "Credencial de acesso não se compartilha e não se documenta",
        "Prontuário não se altera retroativamente sem registro",
        "Ninguém permanece em tratamento sem indicação técnica vigente",
        "Toda avaliação termina em devolutiva",
        "Criança e adolescente têm consentimento do responsável e assentimento próprio",
        "Nenhuma unidade opera com licença, programa ou RT vencidos",
        "Erro se comunica no mesmo dia",
    ]
    for d in inegociaveis:
        c.execute(
            "INSERT INTO checklist (caderno,nivel,inegociavel,descricao,referencia)"
            " VALUES ('0','PADRAO',1,?,'PEE-0-002')", (d,))

    outros = [
        ("2", "PADRAO", "Guia validada no check-in antes do início da sessão", "PEE-2"),
        ("2", "PADRAO", "Evolução registrada no prontuário no mesmo dia do atendimento", "PEE-2"),
        ("2", "DIRETRIZ", "Primeiro contato respondido em até 30 minutos no horário comercial", "PEE-2"),
        ("2", "DIRETRIZ", "Confirmação de agendamento enviada na véspera", "PEE-2"),
        ("2", "RECOMENDACAO", "Acompanhamento entre 24h e 48h após a primeira consulta", "PEE-2"),
        ("3", "PADRAO", "Fechamento de faturamento conciliado por operadora no prazo", "PEE-3"),
        ("3", "DIRETRIZ", "Glosas recorridas em até 30 dias do demonstrativo", "PEE-3"),
        ("3", "DIRETRIZ", "Indicadores do mês lançados até o dia 10", "PEE-3"),
        ("4", "PADRAO", "Nenhum documento em uso com revisão vencida", "PEE-4-001"),
        ("4", "PADRAO", "Lista Mestra atualizada e conferida no trimestre", "PEE-4-001"),
        ("5", "PADRAO", "Toda a equipe com ciência assinada da Carta de Inegociáveis", "PEE-0-002"),
        ("5", "DIRETRIZ", "Trilha de integração concluída em até 30 dias da admissão", "PEE-5"),
    ]
    c.executemany(
        "INSERT INTO checklist (caderno,nivel,inegociavel,descricao,referencia)"
        " VALUES (?,?,0,?,?)", outros)

    c.execute("INSERT INTO unidades (nome,cidade,uf,cnpj,tipo,status,abertura)"
              " VALUES (?,?,?,?,?,?,?)",
              ("Equilibrium Uberlândia", "Uberlândia", "MG",
               "34.032.586/0001-98", "propria", "operacao", "2019-01-01"))
    uid = c.execute("SELECT id FROM unidades LIMIT 1").fetchone()["id"]

    venc = [
        (uid, "AVCB — Corpo de Bombeiros", "CBMMG", "2025-06-26", ""),
        (uid, "Alvará de Funcionamento", "Prefeitura de Uberlândia", "2026-01-26", ""),
        (uid, "PCMSO", "Medicina do Trabalho", "2025-02-18", ""),
        (uid, "PGR", "Segurança do Trabalho", "2026-02-18", ""),
        (uid, "PGRSS", "VISA Municipal", "2025-07-31", "Revisão anual"),
        (uid, "Alvará Sanitário", "VISA Municipal", "2028-06-01", ""),
    ]
    c.executemany("INSERT INTO vencimentos (unidade_id,item,orgao,validade,obs)"
                  " VALUES (?,?,?,?,?)", venc)
    c.commit()


# ------------------------------------------------- leitura dos documentos
CAB = re.compile(r"\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|")


def parse_doc(path: pathlib.Path):
    txt = path.read_text(encoding="utf-8")
    campos = {k.strip(): v.strip() for k, v in CAB.findall(txt[:2500])}
    titulo = ""
    for linha in txt.splitlines():
        if linha.startswith("# "):
            titulo = linha[2:].strip()
            break
    codigo = campos.get("Código", "")
    if not codigo and titulo:
        codigo = titulo.split("—")[0].strip()
    nivel = ""
    bruto = campos.get("Nível de exigência", "")
    for chave, alvo in (("PADRÃO", "PADRAO"), ("DIRETRIZ", "DIRETRIZ"),
                        ("RECOMENDA", "RECOMENDACAO")):
        if chave in bruto.upper():
            nivel = alvo
            break
    return {
        "codigo": codigo or path.stem,
        "titulo": titulo.split("—", 1)[-1].strip() if "—" in titulo else titulo,
        "caderno": campos.get("Caderno", path.parent.name),
        "nivel": nivel,
        "versao": campos.get("Versão", ""),
        "arquivo": str(path.relative_to(DOCS)),
    }


def sync_documentos():
    """Reimporta os metadados dos .md — o Git continua sendo a fonte da verdade."""
    if not DOCS.exists():
        return
    with closing(db()) as c:
        for p in sorted(DOCS.rglob("*.md")):
            if p.name == "index.md":
                continue
            d = parse_doc(p)
            c.execute(
                "INSERT INTO documentos (codigo,titulo,caderno,nivel,versao,arquivo)"
                " VALUES (:codigo,:titulo,:caderno,:nivel,:versao,:arquivo)"
                " ON CONFLICT(codigo) DO UPDATE SET titulo=:titulo,caderno=:caderno,"
                " nivel=:nivel,versao=:versao,arquivo=:arquivo", d)
        c.commit()


# ------------------------------------------------------------- utilidades
def hoje():
    return datetime.date.today()


def situacao(validade: str):
    """Retorna (rotulo, classe_css, dias_restantes)."""
    if not validade:
        return ("Sem data", "cinza", None)
    try:
        d = datetime.date.fromisoformat(validade)
    except ValueError:
        return ("Data inválida", "cinza", None)
    dias = (d - hoje()).days
    if dias < 0:
        return ("Vencido", "vermelho", dias)
    if dias <= 30:
        return ("Crítico", "vermelho", dias)
    if dias <= 90:
        return ("Atenção", "ambar", dias)
    return ("Regular", "verde", dias)


def pontuar(auditoria_id):
    """Índice de conformidade ponderado + reprovação por inegociável."""
    with closing(db()) as c:
        linhas = c.execute(
            "SELECT ai.resultado, ck.nivel, ck.inegociavel FROM auditoria_itens ai"
            " JOIN checklist ck ON ck.id = ai.checklist_id"
            " WHERE ai.auditoria_id = ?", (auditoria_id,)).fetchall()
    obtido = possivel = 0
    reprova = False
    respondidos = 0
    for l in linhas:
        if l["resultado"] in (None, "", "na"):
            continue
        respondidos += 1
        p = PESO.get(l["nivel"], 0)
        possivel += p
        if l["resultado"] == "conforme":
            obtido += p
        elif l["inegociavel"]:
            reprova = True
    score = round(obtido / possivel * 100, 1) if possivel else None
    return {"score": score, "reprova": reprova, "respondidos": respondidos,
            "total": len(linhas)}


def ctx(request, **kw):
    base = {"request": request, "hoje": hoje().strftime("%d/%m/%Y"),
            "rotulo": ROTULO, "situacao": situacao}
    base.update(kw)
    return base


# ------------------------------------------------------------------ rotas
@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with closing(db()) as c:
        unidades = c.execute("SELECT * FROM unidades ORDER BY nome").fetchall()
        vencs = c.execute(
            "SELECT v.*, u.nome AS unidade FROM vencimentos v"
            " LEFT JOIN unidades u ON u.id = v.unidade_id").fetchall()
        docs = c.execute("SELECT COUNT(*) n FROM documentos").fetchone()["n"]
        auds = c.execute(
            "SELECT a.*, u.nome AS unidade FROM auditorias a"
            " LEFT JOIN unidades u ON u.id = a.unidade_id"
            " ORDER BY a.data DESC LIMIT 5").fetchall()
        equipe = c.execute("SELECT COUNT(*) n FROM colaboradores").fetchone()["n"]
        cientes = c.execute(
            "SELECT COUNT(DISTINCT colaborador_id) n FROM ciencia"
            " WHERE codigo = 'PEE-0-002'").fetchone()["n"]

    alertas = []
    for v in vencs:
        rot, cls, dias = situacao(v["validade"])
        if cls in ("vermelho", "ambar"):
            alertas.append({**dict(v), "rotulo": rot, "classe": cls, "dias": dias})
    alertas.sort(key=lambda a: a["dias"] if a["dias"] is not None else 9999)

    scores = []
    for a in auds:
        p = pontuar(a["id"])
        scores.append({**dict(a), **p})

    return tpl.TemplateResponse(request, "dashboard.html", ctx(
        request, unidades=unidades, alertas=alertas, docs=docs,
        auditorias=scores, equipe=equipe, cientes=cientes))


@app.get("/unidades", response_class=HTMLResponse)
def unidades(request: Request):
    with closing(db()) as c:
        us = c.execute("SELECT * FROM unidades ORDER BY nome").fetchall()
        dados = []
        for u in us:
            v = c.execute("SELECT validade FROM vencimentos WHERE unidade_id=?",
                          (u["id"],)).fetchall()
            venc = sum(1 for x in v if situacao(x["validade"])[1] == "vermelho")
            n = c.execute("SELECT COUNT(*) n FROM colaboradores WHERE unidade_id=?",
                          (u["id"],)).fetchone()["n"]
            dados.append({**dict(u), "pendencias": venc, "equipe": n})
    return tpl.TemplateResponse(request, "unidades.html", ctx(request, unidades=dados))


@app.post("/unidades")
def nova_unidade(nome: str = Form(...), cidade: str = Form(""), uf: str = Form(""),
                 cnpj: str = Form(""), tipo: str = Form("propria"),
                 status: str = Form("implantacao")):
    with closing(db()) as c:
        c.execute("INSERT INTO unidades (nome,cidade,uf,cnpj,tipo,status)"
                  " VALUES (?,?,?,?,?,?)", (nome, cidade, uf, cnpj, tipo, status))
        c.commit()
    return RedirectResponse("/unidades", status_code=303)


@app.get("/documentos", response_class=HTMLResponse)
def documentos(request: Request):
    sync_documentos()
    with closing(db()) as c:
        ds = c.execute("SELECT * FROM documentos ORDER BY codigo").fetchall()
    return tpl.TemplateResponse(request, "documentos.html", ctx(request, documentos=ds))


@app.get("/documentos/{codigo}", response_class=HTMLResponse)
def documento(request: Request, codigo: str):
    with closing(db()) as c:
        d = c.execute("SELECT * FROM documentos WHERE codigo=?", (codigo,)).fetchone()
    if not d:
        return HTMLResponse("Documento não encontrado", status_code=404)
    caminho = DOCS / d["arquivo"]
    corpo = md.markdown(caminho.read_text(encoding="utf-8"),
                        extensions=["tables", "fenced_code", "toc"])
    return tpl.TemplateResponse(request, "documento.html", ctx(request, doc=d, corpo=corpo))


@app.get("/vencimentos", response_class=HTMLResponse)
def vencimentos(request: Request):
    with closing(db()) as c:
        vs = c.execute(
            "SELECT v.*, u.nome AS unidade FROM vencimentos v"
            " LEFT JOIN unidades u ON u.id=v.unidade_id"
            " ORDER BY v.validade").fetchall()
        us = c.execute("SELECT * FROM unidades ORDER BY nome").fetchall()
    return tpl.TemplateResponse(request, "vencimentos.html",
                                ctx(request, vencimentos=vs, unidades=us))


@app.post("/vencimentos")
def novo_vencimento(unidade_id: int = Form(...), item: str = Form(...),
                    orgao: str = Form(""), validade: str = Form(""),
                    obs: str = Form("")):
    with closing(db()) as c:
        c.execute("INSERT INTO vencimentos (unidade_id,item,orgao,validade,obs)"
                  " VALUES (?,?,?,?,?)", (unidade_id, item, orgao, validade, obs))
        c.commit()
    return RedirectResponse("/vencimentos", status_code=303)


@app.post("/vencimentos/{vid}/renovar")
def renovar(vid: int, validade: str = Form(...)):
    with closing(db()) as c:
        c.execute("UPDATE vencimentos SET validade=? WHERE id=?", (validade, vid))
        c.commit()
    return RedirectResponse("/vencimentos", status_code=303)


@app.get("/auditorias", response_class=HTMLResponse)
def auditorias(request: Request):
    with closing(db()) as c:
        aus = c.execute(
            "SELECT a.*, u.nome AS unidade FROM auditorias a"
            " LEFT JOIN unidades u ON u.id=a.unidade_id ORDER BY a.data DESC").fetchall()
        us = c.execute("SELECT * FROM unidades ORDER BY nome").fetchall()
    dados = [{**dict(a), **pontuar(a["id"])} for a in aus]
    return tpl.TemplateResponse(request, "auditorias.html",
                                ctx(request, auditorias=dados, unidades=us))


@app.post("/auditorias")
def nova_auditoria(unidade_id: int = Form(...), auditor: str = Form(...)):
    with closing(db()) as c:
        cur = c.execute("INSERT INTO auditorias (unidade_id,data,auditor)"
                        " VALUES (?,?,?)",
                        (unidade_id, hoje().isoformat(), auditor))
        aid = cur.lastrowid
        itens = c.execute("SELECT id FROM checklist").fetchall()
        c.executemany("INSERT INTO auditoria_itens (auditoria_id,checklist_id)"
                      " VALUES (?,?)", [(aid, i["id"]) for i in itens])
        c.commit()
    return RedirectResponse(f"/auditorias/{aid}", status_code=303)


@app.get("/auditorias/{aid}", response_class=HTMLResponse)
def auditoria(request: Request, aid: int):
    with closing(db()) as c:
        a = c.execute(
            "SELECT a.*, u.nome AS unidade FROM auditorias a"
            " LEFT JOIN unidades u ON u.id=a.unidade_id WHERE a.id=?", (aid,)).fetchone()
        itens = c.execute(
            "SELECT ai.id, ai.resultado, ai.nota, ck.descricao, ck.nivel,"
            " ck.inegociavel, ck.caderno, ck.referencia"
            " FROM auditoria_itens ai JOIN checklist ck ON ck.id=ai.checklist_id"
            " WHERE ai.auditoria_id=? ORDER BY ck.caderno, ck.id", (aid,)).fetchall()
    if not a:
        return HTMLResponse("Auditoria não encontrada", status_code=404)
    return tpl.TemplateResponse(request, "auditoria.html",
                                ctx(request, a=a, itens=itens, **pontuar(aid)))


@app.post("/auditorias/{aid}/item/{item_id}")
def responder(aid: int, item_id: int, resultado: str = Form(...),
              nota: str = Form("")):
    with closing(db()) as c:
        c.execute("UPDATE auditoria_itens SET resultado=?, nota=? WHERE id=?",
                  (resultado, nota, item_id))
        c.commit()
    return RedirectResponse(f"/auditorias/{aid}", status_code=303)


@app.post("/auditorias/{aid}/encerrar")
def encerrar(aid: int):
    with closing(db()) as c:
        c.execute("UPDATE auditorias SET status='encerrada' WHERE id=?", (aid,))
        c.commit()
    return RedirectResponse(f"/auditorias/{aid}", status_code=303)


@app.get("/equipe", response_class=HTMLResponse)
def equipe(request: Request):
    with closing(db()) as c:
        cs = c.execute(
            "SELECT c.*, u.nome AS unidade FROM colaboradores c"
            " LEFT JOIN unidades u ON u.id=c.unidade_id ORDER BY c.nome").fetchall()
        us = c.execute("SELECT * FROM unidades ORDER BY nome").fetchall()
        docs = c.execute("SELECT codigo,titulo FROM documentos"
                         " WHERE nivel='PADRAO' ORDER BY codigo").fetchall()
        ci = c.execute("SELECT colaborador_id, codigo, data FROM ciencia").fetchall()
    mapa = {}
    for r in ci:
        mapa.setdefault(r["colaborador_id"], {})[r["codigo"]] = r["data"]
    return tpl.TemplateResponse(request, "equipe.html", ctx(
        request, equipe=cs, unidades=us, documentos=docs, ciencia=mapa))


@app.post("/equipe")
def novo_colaborador(nome: str = Form(...), cargo: str = Form(""),
                     unidade_id: int = Form(...), conselho: str = Form(""),
                     registro: str = Form("")):
    with closing(db()) as c:
        c.execute("INSERT INTO colaboradores (nome,cargo,unidade_id,conselho,registro)"
                  " VALUES (?,?,?,?,?)", (nome, cargo, unidade_id, conselho, registro))
        c.commit()
    return RedirectResponse("/equipe", status_code=303)


@app.post("/ciencia")
def registrar_ciencia(colaborador_id: int = Form(...), codigo: str = Form(...)):
    with closing(db()) as c:
        c.execute("INSERT OR IGNORE INTO ciencia (colaborador_id,codigo,data)"
                  " VALUES (?,?,?)", (colaborador_id, codigo, hoje().isoformat()))
        c.commit()
    return RedirectResponse("/equipe", status_code=303)


if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="127.0.0.1", port=8000)
