# Como contribuir com o acervo

Este arquivo traduz o [PEE-4-001](docs/4-controle/pee-4-001.md) para o uso prático do GitHub.

## Se você só precisa consultar

Não use o GitHub. Abra o site publicado. É mais rápido, funciona no celular e a busca cobre todo o acervo.

## Se você precisa corrigir algo pequeno

1. Abra a página no site
2. Clique no ícone de lápis (canto superior direito)
3. Edite o texto
4. Em "Propose changes", descreva em uma frase o que mudou
5. Clique em "Create pull request"

Pronto. Você não precisa instalar nada nem saber Git. Um revisor recebe a proposta e decide.

## Se você vai criar um documento novo

1. Confira na [Lista Mestra](docs/4-controle/lista-mestra.md) se já existe algo cobrindo o tema
2. Reserve o código na Lista Mestra
3. Crie uma branch `doc/[codigo-em-minusculas]`
4. Parta de [`docs/4-controle/modelo-documento.md`](docs/4-controle/modelo-documento.md) — a estrutura de seções não pode ser alterada
5. Abra o pull request e preencha o checklist

## Fluxo de aprovação

```
Elabora          Revisa                Aprova
  autor    →    coordenação      →     Direção
   PR          comentários no PR      merge em main
```

- **O merge é a aprovação.** Não existe aprovação verbal, por WhatsApp ou por e-mail.
- Documento não mergeado **não está em vigor**, por mais pronto que pareça.
- Após o merge, o site atualiza sozinho em poucos minutos.

## Numeração de versão

| Mudou o quê | Versão |
|---|---|
| Digitação, formatação, link | não muda |
| Conteúdo, sem mudar a conduta | 1.0 → 1.1 |
| Conduta, fluxo, responsável ou base legal | 1.1 → 2.0 |

## Antes de abrir qualquer PR

Releia o que você escreveu procurando por: nome de paciente, CPF, número de carteirinha, senha, login. Se encontrar, **não comite** — a remoção posterior não apaga o histórico.
