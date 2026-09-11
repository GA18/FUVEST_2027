# FUVEST 2027 — Biblioteca de Estudo

## Como usar

1. Abra `dashboard/html/index.html` no navegador — dashboard de progresso interativo
2. Escolha uma matéria em `01-LINGUAGENS/`, `02-MATEMATICA/`, `03-CIENCIAS-NATUREZA/` ou `04-CIENCIAS-HUMANAS/`
3. Abra `conteudo.md` — checklist de tópicos
4. Estude e marque o item como `[x]` em `conteudo.md`
5. Para atualizar o dashboard: `python3 dashboard/py/dashboard.py` e recarregue o `index.html`

### Dashboard
- `dashboard/html/` — HTML gerado
- `dashboard/css/` — estilos
- `dashboard/py/` — script gerador
- Para regenerar: `python3 dashboard/py/dashboard.py`

## Estrutura

```
FUVEST_2027/
├── 01-LINGUAGENS/          → Português, Inglês, Arte e Educação Física; literatura e redação são apoio da 2ª fase
│   ├── portugues/
│   ├── literatura/
│   ├── ingles/
│   ├── redacao/
│   ├── arte/
│   └── educacao-fisica/
├── 02-MATEMATICA/           → álgebra, funções, geometria, estatística
│   ├── algebra/
│   ├── funcoes/
│   ├── geometria/            → checklist principal de Geometria
│   │   ├── geometria-analitica/
│   │   ├── geometria-plana/
│   │   └── geometria-espacial/
│   └── estatistica/
├── 03-CIENCIAS-NATUREZA/    → biologia, física, química
│   ├── biologia/
│   ├── fisica/
│   └── quimica/
├── 04-CIENCIAS-HUMANAS/     → história, geografia, filosofia, sociologia
│   ├── historia/
│   ├── geografia/
│   ├── filosofia/
│   └── sociologia/
├── dashboard/               → dashboard de progresso
│   ├── html/index.html
│   ├── css/style.css
│   └── py/dashboard.py
├── cronograma.md            → plano de estudo (3 meses)
├── fuvest2027_programa.txt  → programa oficial (DOWNLOAD)
├── guia_provas_2027.txt     → guia oficial da prova
└── *.pdf                    → provas anteriores e gabaritos (DOWNLOAD)
```

## Cada matéria tem

- `conteudo.md` — checklist detalhado de tópicos (marque com [x] ao concluir)
- `materials.md` — recursos reais verificados (YouTube, livros, sites)
- `resumo.txt` — suas anotações, fichamentos e revisão rápida

As subpastas `geometria/geometria-analitica/`, `geometria/geometria-plana/` e
`geometria/geometria-espacial/` são temas de apoio. O checklist interativo usa
`geometria/conteudo.md` como fonte única para evitar a duplicação dos itens.

## Referências oficiais

| Documento | Descrição |
|-----------|-----------|
| [fuvest2027_programa.txt](fuvest2027_programa.txt) | Programa oficial da FUVEST 2027 |
| [guia_provas_2027.txt](guia_provas_2027.txt) | Guia de Provas da FUVEST 2027 |
| [fuvest2027-programa-vestibular.pdf](fuvest2027-programa-vestibular.pdf) | Programa oficial em PDF |
| [guia_provas_2027.pdf](guia_provas_2027.pdf) | Guia de Provas em PDF |

## Obras obrigatórias (9 obras)

1. **Opúsculo Humanitário** — Nísia Floresta
2. **Nebulosas** — Narcisa Amália
3. **Memórias de Martha** — Julia Lopes de Almeida
4. **Caminho de Pedras** — Rachel de Queiroz
5. **A Paixão Segundo G.H.** — Clarice Lispector
6. **Geografia** — Sophia de Mello Breyner Andresen
7. **Balada de Amor ao Vento** — Paulina Chiziane
8. **Canção para Ninar Menino Grande** — Conceição Evaristo
9. **A Visão das Plantas** — Djaimilia Pereira de Almeida

## Datas importantes

- **Inscrições:** 17/08/2026 a 09/10/2026
- **1ª fase:** 01/11/2026 (80 questões de múltipla escolha, até 5 horas)
- **2ª fase:** 06 e 07/12/2026 (provas discursivas + redação)

## Escopo do checklist

Os checklists das disciplinas são uma decomposição prática dos objetos de conhecimento
do Programa do Vestibular 2027. O percentual do dashboard mede apenas os itens do
checklist interno; não é uma nota oficial nem garante, sozinho, o domínio integral do programa.
Literatura obrigatória e redação são mantidas no projeto como apoio específico da 2ª fase.
