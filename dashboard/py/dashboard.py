#!/usr/bin/env python3
"""Gera o dashboard HTML a partir dos conteudo.md do repositório."""

import re
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent.parent
DASHBOARD_DIR = SCRIPT_DIR.parent
CSS_PATH = DASHBOARD_DIR / "css" / "style.css"
HTML_PATH = DASHBOARD_DIR / "html" / "index.html"

AREAS = {
    "01-LINGUAGENS": {
        "nome": "Linguagens e Códigos",
        "cor": "#e74c3c",
        "disciplinas": [
            ("portugues", "Português"),
            ("literatura", "Literatura"),
            ("ingles", "Inglês"),
            ("redacao", "Redação"),
            ("arte", "Arte"),
            ("educacao-fisica", "Educação Física"),
        ],
    },
    "02-MATEMATICA": {
        "nome": "Matemática",
        "cor": "#3498db",
        "disciplinas": [
            ("algebra", "Álgebra"),
            ("funcoes", "Funções"),
            ("geometria", "Geometria"),
            ("estatistica", "Estatística e Probabilidade"),
        ],
    },
    "03-CIENCIAS-NATUREZA": {
        "nome": "Ciências da Natureza",
        "cor": "#2ecc71",
        "disciplinas": [
            ("biologia", "Biologia"),
            ("fisica", "Física"),
            ("quimica", "Química"),
        ],
    },
    "04-CIENCIAS-HUMANAS": {
        "nome": "Ciências Humanas e Sociais",
        "cor": "#f39c12",
        "disciplinas": [
            ("historia", "História"),
            ("geografia", "Geografia"),
            ("filosofia", "Filosofia"),
            ("sociologia", "Sociologia"),
        ],
    },
}


def count_checkboxes(content):
    done = len(re.findall(r"^- \[x\]", content, re.MULTILINE))
    total = len(re.findall(r"^- \[[ x]\]", content, re.MULTILINE))
    return done, total


def read_conteudo(area, disciplina):
    path = ROOT / area / disciplina / "conteudo.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def build_data():
    areas_data = {}
    for area_id, area_info in AREAS.items():
        disc_data = {}
        for disc_id, disc_nome in area_info["disciplinas"]:
            content = read_conteudo(area_id, disc_id)
            done, total = count_checkboxes(content)
            disc_data[disc_id] = {
                "nome": disc_nome,
                "done": done,
                "total": total,
                "content": content,
            }
        areas_data[area_id] = {
            "nome": area_info["nome"],
            "cor": area_info["cor"],
            "disciplinas": disc_data,
        }
    return areas_data


JS = """
const AREAS_DATA = AREAS_PLACEHOLDER;
const STORAGE_KEY = 'fuvest2027_progress';

function loadProgress() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; } catch { return {}; }
}

function saveProgress(p) { localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); }

function updateStats() {
    const p = loadProgress();
    let total = 0, done = 0;
    for (const [areaId, area] of Object.entries(AREAS_DATA)) {
        let areaTotal = 0, areaDone = 0;
        for (const [discId, disc] of Object.entries(area.disciplinas)) {
            let discDone = 0;
            for (let i = 0; i < disc.total; i++) {
                total++;
                areaTotal++;
                const key = discId + '_' + i;
                if (p[key]) { done++; areaDone++; discDone++; }
            }
            const uid = areaId + '-' + discId;
            const discPct = disc.total > 0 ? (discDone / disc.total * 100).toFixed(1) : '0.0';
            const fill = document.getElementById('disc-fill-' + uid);
            const count = document.getElementById('disc-count-' + uid);
            const pctEl = document.getElementById('disc-pct-' + uid);
            if (fill) {
                let barColor = area.cor;
                if (discPct >= 80) barColor = '#27ae60';
                else if (discPct >= 50) barColor = '#f39c12';
                fill.style.width = discPct + '%';
                fill.style.background = barColor;
            }
            if (count) count.textContent = discDone + '/' + disc.total;
            if (pctEl) pctEl.textContent = discPct + '%';
        }
        const areaPct = areaTotal > 0 ? (areaDone / areaTotal * 100).toFixed(1) : '0.0';
        const aPct = document.getElementById('area-pct-' + areaId);
        const aCount = document.getElementById('area-count-' + areaId);
        if (aPct) aPct.textContent = areaPct + '%';
        if (aCount) aCount.textContent = areaDone + '/' + areaTotal;
    }
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-done').textContent = done;
    document.getElementById('stat-pending').textContent = total - done;
    const pct = total > 0 ? (done / total * 100).toFixed(1) : '0.0';
    const bar = document.getElementById('overall-bar');
    bar.style.width = pct + '%';
    bar.textContent = pct + '%';
}

function toggleArea(id) {
    const body = document.getElementById('area-' + id);
    const chevron = document.getElementById('chevron-' + id);
    body.classList.toggle('open');
    chevron.classList.toggle('open');
}

function parseTopics(content) {
    const lines = content.split('\\n');
    const groups = [];
    let currentGroup = null;
    let inCodeBlock = false;
    for (const line of lines) {
        if (line.startsWith('```')) { inCodeBlock = !inCodeBlock; continue; }
        if (inCodeBlock) continue;
        if (line.startsWith('### ') || line.startsWith('## ')) {
            const name = line.replace(/^#+\\s*/, '');
            currentGroup = { name: name, items: [] };
            groups.push(currentGroup);
        } else if (currentGroup && line.match(/^- \\[([ x])\\]/)) {
            const text = line.replace(/^- \\[[ x]\\]\\s*/, '');
            currentGroup.items.push(text);
        }
    }
    return groups.filter(function(g) { return g.items.length > 0; });
}

function buildChecklist() {
    const tabsEl = document.getElementById('checklist-tabs');
    const contentsEl = document.getElementById('checklist-contents');
    const progress = loadProgress();
    let firstTab = null;
    for (const [areaId, area] of Object.entries(AREAS_DATA)) {
        for (const [discId, disc] of Object.entries(area.disciplinas)) {
            const groups = parseTopics(disc.content);
            if (groups.length === 0) continue;
            const tabId = 'tab-' + discId;

            const btn = document.createElement('button');
            btn.className = 'tab-btn';
            btn.dataset.tab = tabId;
            btn.textContent = disc.nome;
            btn.onclick = (function(tid) { return function() { switchTab(tid); }; })(tabId);
            tabsEl.appendChild(btn);

            const div = document.createElement('div');
            div.className = 'tab-content';
            div.id = tabId;

            let html = '';
            let itemIdx = 0;
            for (const group of groups) {
                html += '<div class="topic-group"><h3>' + group.name + '</h3>';
                for (const item of group.items) {
                    const key = discId + '_' + itemIdx;
                    const isChecked = progress[key] || false;
                    const cls = isChecked ? ' done' : '';
                    const chk = isChecked ? ' checked' : '';
                    html += '<label class="topic-item' + cls + '">';
                    html += '<input type="checkbox" data-key="' + key + '"' + chk + ' onchange="toggleTopic(this)">';
                    html += '<span class="topic-text">' + item + '</span>';
                    html += '</label>';
                    itemIdx++;
                }
                html += '</div>';
            }
            div.innerHTML = html;
            contentsEl.appendChild(div);

            if (!firstTab) firstTab = tabId;
        }
    }
    if (firstTab) switchTab(firstTab);
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab-content').forEach(function(d) { d.classList.remove('active'); });
    const btn = document.querySelector('.tab-btn[data-tab="' + tabId + '"]');
    const content = document.getElementById(tabId);
    if (btn) btn.classList.add('active');
    if (content) content.classList.add('active');
}

function toggleTopic(el) {
    const key = el.dataset.key;
    const progress = loadProgress();
    if (el.checked) {
        progress[key] = true;
    } else {
        delete progress[key];
    }
    saveProgress(progress);
    el.closest('.topic-item').classList.toggle('done', el.checked);
    updateStats();
}

function resetChecklist() {
    if (confirm('Tem certeza? Isso vai apagar todo o progresso salvo.')) {
        localStorage.removeItem(STORAGE_KEY);
        document.getElementById('checklist-tabs').innerHTML = '';
        document.getElementById('checklist-contents').innerHTML = '';
        buildChecklist();
        updateStats();
    }
}

function initCountdown() {
    const events = [
        { name: 'Inscrições', date: '2026-08-17' },
        { name: 'Inscrições (fim)', date: '2026-10-09' },
        { name: '1ª Fase', date: '2026-11-01' },
        { name: '2ª Fase', date: '2026-12-06' },
    ];
    const container = document.getElementById('countdown');
    const today = new Date();
    today.setHours(0,0,0,0);
    for (const ev of events) {
        const target = new Date(ev.date + 'T00:00:00');
        const diff = Math.ceil((target - today) / (1000 * 60 * 60 * 24));
        let cls, text;
        if (diff < 0) {
            text = 'Encerrado';
            cls = '';
        } else if (diff <= 30) {
            text = diff + ' dias';
            cls = 'urgent';
        } else if (diff <= 90) {
            text = diff + ' dias';
            cls = 'warning';
        } else {
            text = diff + ' dias';
            cls = 'safe';
        }
        const div = document.createElement('div');
        div.className = 'countdown-item';
        div.innerHTML = '<div class="label">' + ev.name + '</div>'
            + '<div class="value ' + cls + '">' + text + '</div>'
            + '<div class="date-label">' + ev.date + '</div>';
        container.appendChild(div);
    }
}

initCountdown();
buildChecklist();
updateStats();
"""


def generate_final_html():
    css_content = CSS_PATH.read_text(encoding="utf-8")

    areas_data = build_data()

    total_all = sum(
        d["total"]
        for area in areas_data.values()
        for d in area["disciplinas"].values()
    )
    done_all = sum(
        d["done"]
        for area in areas_data.values()
        for d in area["disciplinas"].values()
    )
    overall_pct = (done_all / total_all * 100) if total_all > 0 else 0

    # Build area sections
    areas_html = ""
    for area_id, area in areas_data.items():
        area_total = sum(d["total"] for d in area["disciplinas"].values())
        area_done = sum(d["done"] for d in area["disciplinas"].values())
        area_pct = (area_done / area_total * 100) if area_total > 0 else 0

        discs_html = ""
        for disc_id, disc in area["disciplinas"].items():
            pct = (disc["done"] / disc["total"] * 100) if disc["total"] > 0 else 0
            bar_color = area["cor"]
            if pct >= 80:
                bar_color = "#27ae60"
            elif pct >= 50:
                bar_color = "#f39c12"

            pct_str = "{:.1f}".format(pct)
            uid = area_id + "-" + disc_id
            discs_html += (
                '<div class="disc-card">'
                '<div class="disc-header">'
                '<span class="disc-name">' + disc["nome"] + "</span>"
                '<span class="disc-count" id="disc-count-' + uid + '">' + str(disc["done"]) + "/" + str(disc["total"]) + "</span>"
                "</div>"
                '<div class="progress-bar">'
                '<div class="progress-fill" id="disc-fill-' + uid + '" style="width:' + pct_str + "%;background:" + bar_color + '"></div>'
                "</div>"
                '<span class="disc-pct" id="disc-pct-' + uid + '">' + pct_str + "%</span>"
                "</div>"
            )

        area_pct_str = "{:.1f}".format(area_pct)
        areas_html += (
            '<div class="area-section">'
            '<div class="area-header" onclick="toggleArea(\'' + area_id + "')\">"
            '<div class="area-title">'
            '<span class="area-dot" style="background:' + area["cor"] + '"></span>'
            "<h2>" + area["nome"] + "</h2>"
            "</div>"
            '<div class="area-stats">'
            '<span class="area-pct" id="area-pct-' + area_id + '">' + area_pct_str + "%</span>"
            '<span class="area-count" id="area-count-' + area_id + '">' + str(area_done) + "/" + str(area_total) + "</span>"
            '<span class="chevron" id="chevron-' + area_id + '">▼</span>'
            "</div>"
            "</div>"
            '<div class="area-body" id="area-' + area_id + '">'
            '<div class="disc-grid">' + discs_html + "</div>"
            "</div>"
            "</div>"
        )

    overall_pct_str = "{:.1f}".format(overall_pct)
    pending = total_all - done_all

    areas_js = json.dumps(
        {
            aid: {
                "nome": a["nome"],
                "cor": a["cor"],
                "disciplinas": {
                    did: {
                        "nome": d["nome"],
                        "done": d["done"],
                        "total": d["total"],
                        "content": d["content"],
                    }
                    for did, d in a["disciplinas"].items()
                },
            }
            for aid, a in areas_data.items()
        },
        ensure_ascii=False,
        indent=2,
    )

    js = JS.replace("AREAS_PLACEHOLDER", areas_js)

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>FUVEST 2027 — Dashboard de Estudo</title>",
        '<link rel="stylesheet" href="../css/style.css">',
        "</head>",
        "<body>",
        '<div class="container">',
        # Header
        '<div class="header">',
        "<h1>FUVEST 2027</h1>",
        '<p class="subtitle">Dashboard de Estudo — Acompanhe seu progresso</p>',
        '<div class="countdown" id="countdown"></div>',
        "</div>",
        # Stats
        '<div class="stats-row">',
        '<div class="stat-card">',
        '<div class="stat-value" id="stat-total">' + str(total_all) + "</div>",
        '<div class="stat-label">Tópicos totais</div>',
        "</div>",
        '<div class="stat-card">',
        '<div class="stat-value" id="stat-done" style="color:var(--green)">' + str(done_all) + "</div>",
        '<div class="stat-label">Concluídos</div>',
        "</div>",
        '<div class="stat-card">',
        '<div class="stat-value" id="stat-pending" style="color:var(--yellow)">' + str(pending) + "</div>",
        '<div class="stat-label">Pendentes</div>',
        "</div>",
        "</div>",
        # Overall progress
        '<div class="overall-progress">',
        "<h3>Progresso Geral</h3>",
        '<div class="big-progress-bar">',
        '<div class="big-progress-fill" id="overall-bar" style="width:' + overall_pct_str + "%\">" + overall_pct_str + "%</div>",
        "</div>",
        "</div>",
        # Areas
        areas_html,
        # Checklist
        '<div class="checklist-section">',
        "<h2>Checklist Interativo</h2>",
        '<div class="checklist-tabs" id="checklist-tabs"></div>',
        '<div id="checklist-contents"></div>',
        '<button class="reset-btn" onclick="resetChecklist()">Resetar progresso</button>',
        "</div>",
        # Footer
        '<div class="footer">',
        'Gerado automaticamente por <code>dashboard.py</code> — FUVEST 2027',
        "</div>",
        "</div>",
        "<script>" + js + "</script>",
        "</body>",
        "</html>",
    ]

    return "\n".join(html_parts)


if __name__ == "__main__":
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    html = generate_final_html()
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard gerado: {HTML_PATH}")
    print("Abra dashboard/html/index.html no navegador para visualizar.")
