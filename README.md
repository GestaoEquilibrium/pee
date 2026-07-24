# Padrão Equilibrium de Excelência (PEE)

Sistema documental do Grupo Equilibrium — Equilibrium Med Center.
Acervo normativo único: manuais, POPs, formulários e listas de controle.

> **Repositório privado.** Este acervo não é público e não deve ser tornado público em nenhuma hipótese.

## Regra fundamental

**Nunca comite neste repositório:**

- dado identificável de paciente (nome, CPF, carteirinha, laudo, evolução, imagem)
- credencial de acesso (senha, token, login nominal)
- documento pessoal de colaborador

O histórico do Git é permanente. Arquivo comitado por engano permanece recuperável mesmo após remoção. A varredura automática bloqueia a publicação quando detecta violação, mas a prevenção é responsabilidade de quem escreve.

## Como rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

Site local em `http://127.0.0.1:8000`.

## Como propor uma mudança

Ver [CONTRIBUTING.md](CONTRIBUTING.md) e o [PEE-4-001](docs/4-controle/pee-4-001.md).

## Arquitetura

| Camada | Onde |
|---|---|
| Fonte da verdade | Markdown neste repositório, branch `main` |
| Publicação | Cloudflare Pages + Cloudflare Access (autenticado) |
| Versionamento | Histórico de commits e pull requests |
| Aprovação | Merge em `main`, restrito à Direção via CODEOWNERS |
| PDF para auditoria | Artefato gerado sob demanda pelo workflow `gerar-pdf` |

## Configuração inicial pendente

- [ ] Criar organização no GitHub sob titularidade da pessoa jurídica
- [ ] Criar times `@direcao-equilibrium` e `@qualidade-equilibrium`
- [ ] Ativar proteção da branch `main` com revisão obrigatória
- [ ] Configurar secrets `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID`
- [ ] Configurar Cloudflare Access com os e-mails da equipe
- [ ] Adicionar `docs/assets/logo.png`
