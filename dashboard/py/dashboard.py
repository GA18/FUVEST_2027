#!/usr/bin/env python3
"""Gera o dashboard HTML a partir dos conteudo.md do repositório.

Uso:
    python3 dashboard/py/dashboard.py             # regenera dashboard/html/index.html
    python3 dashboard/py/dashboard.py --serve     # servidor local com write-back (md = fonte única)
"""

import re
import json
import sys
import threading
import argparse
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent.parent
DASHBOARD_DIR = SCRIPT_DIR.parent
CSS_PATH = DASHBOARD_DIR / "css" / "style.css"
HTML_PATH = DASHBOARD_DIR / "html" / "index.html"

AREAS = {
    "01-LINGUAGENS": {
        "nome": "Linguagens e suas Tecnologias",
        "cor": "#e74c3c",
        "disciplinas": [
            ("portugues", "Português"),
            ("ingles", "Inglês"),
            ("arte", "Arte"),
            ("educacao-fisica", "Educação Física"),
        ],
    },
    "02-MATEMATICA": {
        "nome": "Matemática e suas Tecnologias",
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
        "nome": "Ciências Humanas e Sociais Aplicadas",
        "cor": "#f39c12",
        "disciplinas": [
            ("historia", "História"),
            ("geografia", "Geografia"),
            ("filosofia", "Filosofia"),
            ("sociologia", "Sociologia"),
        ],
    },
    "05-SEGUNDA-FASE": {
        "nome": "Apoio da Segunda Fase",
        "cor": "#8e44ad",
        "disciplinas": [
            ("literatura", "Literatura obrigatória"),
            ("redacao", "Redação"),
        ],
    },
}

CONTENT_PATHS = {
    ("05-SEGUNDA-FASE", "literatura"): ("01-LINGUAGENS", "literatura"),
    ("05-SEGUNDA-FASE", "redacao"): ("01-LINGUAGENS", "redacao"),
}


def count_checkboxes(content):
    done = len(re.findall(r"^- \[x\]", content, re.MULTILINE))
    total = len(re.findall(r"^- \[[ x]\]", content, re.MULTILINE))
    return done, total


def done_indices(content):
    """Índices (ordem das linhas de checkbox) já marcados como [x]."""
    idxs = []
    i = 0
    for line in content.splitlines():
        if re.match(r"^- \[[ x]\]", line):
            if line.startswith("- [x]"):
                idxs.append(i)
            i += 1
    return idxs


def read_conteudo(area, disciplina):
    source_area, source_disc = CONTENT_PATHS.get((area, disciplina), (area, disciplina))
    path = ROOT / source_area / source_disc / "conteudo.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def read_resumo(area, disciplina):
    source_area, source_disc = CONTENT_PATHS.get((area, disciplina), (area, disciplina))
    root = ROOT / source_area / source_disc
    geral = (root / "resumo.txt").read_text(encoding="utf-8") if (root / "resumo.txt").exists() else ""
    temas = {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted((root / "resumos").glob("*.txt"))
    } if (root / "resumos").exists() else {}
    return {"geral": geral, "temas": temas}


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
                "resumo": read_resumo(area_id, disc_id),
                "doneFlags": done_indices(content),
            }
        areas_data[area_id] = {
            "nome": area_info["nome"],
            "cor": area_info["cor"],
            "disciplinas": disc_data,
        }
    return areas_data


def disc_path(area_id, disc_id):
    """Caminho do conteudo.md de uma disciplina."""
    source_area, source_disc = CONTENT_PATHS.get((area_id, disc_id), (area_id, disc_id))
    return ROOT / source_area / source_disc / "conteudo.md"


def resumo_path(area_id, disc_id, tema=None):
    source_area, source_disc = CONTENT_PATHS.get((area_id, disc_id), (area_id, disc_id))
    root = ROOT / source_area / source_disc
    return root / "resumo.txt" if tema in (None, "geral") else root / "resumos" / f"{tema}.txt"


def save_resumo(area_id, disc_id, content, tema=None):
    path = resumo_path(area_id, disc_id, tema)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def find_checkbox_lines(text):
    """Índices (linha) das linhas de checkbox '- [...]' fora de code blocks."""
    lines = text.splitlines()
    idxs = []
    in_code = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^- \[[ x]\]", line):
            idxs.append(i)
    return idxs


def set_checkbox(area_id, disc_id, index, checked):
    """Marca/desmarca o N-ésimo checkbox do conteudo.md e grava no disco.

    Retorna (done, total) atualizados da disciplina, ou None se inválido.
    """
    path = disc_path(area_id, disc_id)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    idxs = find_checkbox_lines(text)
    if index < 0 or index >= len(idxs):
        return None
    lines = text.splitlines()
    line_idx = idxs[index]
    marker = "- [x]" if checked else "- [ ]"
    lines[line_idx] = re.sub(r"^- \[[ x]\]", marker, lines[line_idx])
    path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    done, total = count_checkboxes(path.read_text(encoding="utf-8"))
    return done, total


def reset_checkboxes(area_id=None):
    """Desmarca todos os checkboxes. area_id=None → todas as áreas."""
    reset_count = 0
    for aid, area_info in AREAS.items():
        if area_id and area_id != aid:
            continue
        for disc_id, _ in area_info["disciplinas"]:
            path = disc_path(aid, disc_id)
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            new_text = re.sub(r"(?m)^- \[x\]", "- [ ]", text)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                reset_count += 1
    return reset_count


class DashboardHandler(BaseHTTPRequestHandler):
    # Lock global compartilhado para escrita concorrente nos arquivos
    _write_lock = threading.Lock()

    def log_message(self, fmt, *args):
        sys.stderr.write("[dashboard] %s\n" % (fmt % args))

    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self._send(200, json.dumps({"ok": True}))
            return
        # Servir os arquivos públicos do dashboard.
        rel = urllib.parse.unquote(parsed.path.lstrip("/"))
        html_dir = DASHBOARD_DIR / "html"
        if rel in ("", "html"):
            self.send_response(302)
            self.send_header("Location", "/html/index.html")
            self.end_headers()
            return
        if ".." in rel:
            self._send(403, "forbidden", "text/plain")
            return
        if rel.startswith("html/"):
            f = html_dir / rel.removeprefix("html/")
        elif rel.startswith("css/"):
            f = DASHBOARD_DIR / rel
        else:
            self._send(404, json.dumps({"error": "not found"}))
            return
        if not f.is_file():
            self._send(404, json.dumps({"error": "not found"}))
            return
        ctype = "text/html" if f.suffix == ".html" else (
            "text/css" if f.suffix == ".css" else "application/octet-stream"
        )
        data = f.read_bytes()
        self._send(200, data, ctype)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/api/progress", "/api/reset", "/api/resumo"):
            self._send(404, json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            self._send(400, json.dumps({"error": "invalid json"}))
            return
        with self._write_lock:
            if parsed.path == "/api/reset":
                area = payload.get("area")
                if area is not None and area not in AREAS:
                    self._send(400, json.dumps({"error": "unknown area"}))
                    return
                n = reset_checkboxes(area)
                self._send(200, json.dumps({"reset_files": n}))
                return
            area_id = payload.get("area")
            disc_id = payload.get("disc")
            if parsed.path == "/api/resumo":
                content = payload.get("content")
                tema = payload.get("tema")
                if area_id not in AREAS or disc_id not in {
                    d for d, _ in AREAS[area_id]["disciplinas"]
                } or not isinstance(content, str) or (tema is not None and not isinstance(tema, str)):
                    self._send(400, json.dumps({"error": "invalid resumo payload"}))
                    return
                save_resumo(area_id, disc_id, content, tema)
                self._send(200, json.dumps({"area": area_id, "disc": disc_id, "tema": tema, "saved": True}))
                return
            index = payload.get("index")
            checked = payload.get("checked")
            if area_id not in AREAS or disc_id not in {
                d for d, _ in AREAS[area_id]["disciplinas"]
            }:
                self._send(404, json.dumps({"error": "unknown disciplina"}))
                return
            if not isinstance(index, int) or isinstance(index, bool) or not isinstance(checked, bool):
                self._send(400, json.dumps({"error": "invalid progress payload"}))
                return
            result = set_checkbox(area_id, disc_id, index, checked)
            if result is None:
                self._send(400, json.dumps({"error": "index out of range"}))
                return
            done, total = result
            self._send(200, json.dumps({"area": area_id, "disc": disc_id, "done": done, "total": total}))


JS = """
const AREAS_DATA = AREAS_PLACEHOLDER;
const STORAGE_KEY = 'fuvest2027_progress';
let SHOW_OFFLINE_WARNED = false;

function isServed() { return window.location.protocol.indexOf('http') === 0; }

function loadProgress() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; } catch { return {}; }
}

function saveProgress(p) { localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); }

function showOfflineNote() {
    if (SHOW_OFFLINE_WARNED) return;
    SHOW_OFFLINE_WARNED = true;
    const el = document.getElementById('offline-note');
    if (el) el.style.display = 'block';
}

function buildInitialState() {
    const state = {};
    const saved = loadProgress();
    let itemIdx = 0;
    for (const [areaId, area] of Object.entries(AREAS_DATA)) {
        for (const [discId, disc] of Object.entries(area.disciplinas)) {
            for (let i = 0; i < disc.total; i++) {
                const key = discId + '_' + i;
                const doneIdx = disc.doneFlags && disc.doneFlags.indexOf(i) >= 0;
                state[key] = doneIdx || saved[key] === true;
                itemIdx++;
            }
        }
    }
    return state;
}

const STATE = buildInitialState();
let SERVER_OK = isServed();

function updateStats() {
    let total = 0, done = 0;
    for (const [areaId, area] of Object.entries(AREAS_DATA)) {
        let areaTotal = 0, areaDone = 0;
        for (const [discId, disc] of Object.entries(area.disciplinas)) {
            let discDone = 0;
            for (let i = 0; i < disc.total; i++) {
                total++;
                areaTotal++;
                if (STATE[discId + '_' + i]) { done++; areaDone++; discDone++; }
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
    let itemIdx = 0;
        for (const line of lines) {
        if (line.startsWith('```')) { inCodeBlock = !inCodeBlock; continue; }
        if (inCodeBlock) continue;
        if (line.startsWith('### ') || line.startsWith('## ')) {
            const name = line.replace(/^#+\\s*/, '');
            currentGroup = { name: name, items: [] };
            groups.push(currentGroup);
        } else if (line.match(/^- \\[([ x])\\]/)) {
                if (!currentGroup) {
                    currentGroup = { name: 'Geral', items: [] };
                    groups.push(currentGroup);
                }
            const text = line.replace(/^- \\[[ x]\\]\\s*/, '');
            const checked = line.indexOf('- [x]') === 0;
            currentGroup.items.push({ text: text, idx: itemIdx, checked: checked });
            itemIdx++;
        }
    }
    return groups.filter(function(g) { return g.items.length > 0; });
}

function buildChecklist() {
    const tabsEl = document.getElementById('checklist-tabs');
    const contentsEl = document.getElementById('checklist-contents');
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
            html += '<div class="discipline-tools">';
            html += '<button class="view-btn active" type="button" onclick="showChecklist(&quot;' + tabId + '&quot;)">Checklist</button>';
            html += '<button class="view-btn" type="button" onclick="showSummary(&quot;' + tabId + '&quot;)">Resumo</button>';
            html += '</div>';
            html += '<div class="checklist-view" id="checklist-view-' + tabId + '">';
            for (const group of groups) {
                html += '<div class="topic-group"><h3>' + group.name + '</h3>';
                for (const item of group.items) {
                    const key = discId + '_' + item.idx;
                    const isChecked = STATE[key] || false;
                    const cls = isChecked ? ' done' : '';
                    const chk = isChecked ? ' checked' : '';
                    html += '<label class="topic-item' + cls + '">';
                    html += '<input type="checkbox" data-key="' + key + '" data-area="' + areaId + '" data-disc="' + discId + '" data-idx="' + item.idx + '"' + chk + ' onchange="toggleTopic(this)">';
                    html += '<span class="topic-text">' + item.text + '</span>';
                    html += '</label>';
                }
                html += '</div>';
            }
            html += '</div>';
            html += '<div class="summary-view" id="summary-view-' + tabId + '" hidden>';
            html += '<div class="summary-theme-list"><button class="summary-theme active" type="button" onclick="selectSummaryTheme(&quot;' + tabId + '&quot;,&quot;geral&quot;)">Resumo geral</button>';
            for (const tema of Object.keys(disc.resumo.temas || {})) {
                html += '<button class="summary-theme" type="button" onclick="selectSummaryTheme(&quot;' + tabId + '&quot;,&quot;' + tema + '&quot;)">' + tema.replace(/-/g, ' ') + '</button>';
            }
            html += '</div>';
            html += '<textarea class="summary-editor" id="summary-editor-' + tabId + '" spellcheck="true"></textarea>';
            html += '<div class="summary-actions"><span class="summary-status" id="summary-status-' + tabId + '"></span><button class="save-summary-btn" type="button" onclick="saveSummary(&quot;' + areaId + '&quot;,&quot;' + discId + '&quot;,&quot;' + tabId + '&quot;)">Salvar resumo</button></div>';
            html += '</div>';
            div.innerHTML = html;
            const editor = div.querySelector('.summary-editor');
            const savedSummaries = JSON.parse(localStorage.getItem('fuvest2027_summaries') || '{}');
            editor.value = savedSummaries[areaId + '_' + discId] || disc.resumo.geral || '';
            contentsEl.appendChild(div);

            if (!firstTab) firstTab = tabId;
        }
    }
    if (firstTab) switchTab(firstTab);
}

function showChecklist(tabId) {
    const tab = document.getElementById(tabId);
    tab.querySelector('.checklist-view').hidden = false;
    tab.querySelector('.summary-view').hidden = true;
    tab.querySelectorAll('.view-btn').forEach(function(btn, index) { btn.classList.toggle('active', index === 0); });
}

function showSummary(tabId) {
    const tab = document.getElementById(tabId);
    tab.querySelector('.checklist-view').hidden = true;
    tab.querySelector('.summary-view').hidden = false;
    tab.querySelectorAll('.view-btn').forEach(function(btn, index) { btn.classList.toggle('active', index === 1); });
}

function saveSummary(areaId, discId, tabId) {
    const editor = document.getElementById('summary-editor-' + tabId);
    const status = document.getElementById('summary-status-' + tabId);
    const content = editor.value;
    const key = areaId + '_' + discId;
    if (!isServed()) {
        const summaries = JSON.parse(localStorage.getItem('fuvest2027_summaries') || '{}');
        summaries[key] = content;
        localStorage.setItem('fuvest2027_summaries', JSON.stringify(summaries));
        status.textContent = 'Salvo neste navegador.';
        return;
    }
    fetch('/api/resumo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ area: areaId, disc: discId, content: content })
    }).then(function(response) {
        if (!response.ok) throw new Error('summary save failed');
        return response.json();
    }).then(function() {
        status.textContent = 'Resumo salvo em resumo.txt.';
    }).catch(function() {
        status.textContent = 'Não foi possível salvar no arquivo.';
    });
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
    const areaId = el.dataset.area;
    const discId = el.dataset.disc;
    const idx = parseInt(el.dataset.idx, 10);
    el.closest('.topic-item').classList.toggle('done', el.checked);

    if (isServed()) {
        fetch('/api/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ area: areaId, disc: discId, index: idx, checked: el.checked })
        }).then(function(r) {
            if (!r.ok) throw new Error('progress request failed');
            return r.json();
        }).then(function(res) {
            if (res && typeof res.done === 'number') {
                STATE[key] = el.checked;
                const disc = AREAS_DATA[res.area].disciplinas[res.disc];
                disc.done = res.done;
                disc.total = res.total;
                updateStats();
            }
        }).catch(function() {
            el.checked = !el.checked;
            el.closest('.topic-item').classList.toggle('done', el.checked);
            showOfflineNote();
        });
    } else {
        offlineFallback(el, key);
    }
}

function offlineFallback(el, key) {
    STATE[key] = el.checked;
    const progress = loadProgress();
    if (el.checked) progress[key] = true; else delete progress[key];
    saveProgress(progress);
    showOfflineNote();
    updateStats();
}

function resetChecklist() {
    if (!confirm('Tem certeza? Isso vai apagar todo o progresso salvo.')) return;
    if (isServed()) {
        fetch('/api/reset', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
            .catch(function() {});
    }
    localStorage.removeItem(STORAGE_KEY);
    for (const k in STATE) STATE[k] = false;
    document.getElementById('checklist-tabs').innerHTML = '';
    document.getElementById('checklist-contents').innerHTML = '';
    buildChecklist();
    updateStats();
}

function initCountdown() {
    const events = [
        { name: 'Inscrições', date: '2026-08-17' },
        { name: 'Inscrições (fim)', date: '2026-10-09' },
        { name: '1ª Fase', date: '2026-11-01' },
        { name: '2ª Fase (dia 1)', date: '2026-12-06' },
        { name: '2ª Fase (dia 2)', date: '2026-12-07' },
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
                        "resumo": d["resumo"],
                        "doneFlags": d["doneFlags"],
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
        '<div class="offline-note" id="offline-note">'
        "Você está abrindo o dashboard direto do arquivo. As alterações serão salvas só "
        "neste navegador. Para salvar nos <code>conteudo.md</code> do repositório, rode "
        "<code>python3 dashboard/py/dashboard.py --serve</code> e abra "
        "<code>http://localhost:8000/html/index.html</code>."
        "</div>",
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
    parser = argparse.ArgumentParser(description="Dashboard FUVEST 2027")
    parser.add_argument("--serve", action="store_true",
                        help="inicia servidor local com write-back nos conteudo.md")
    parser.add_argument("--port", type=int, default=8000, help="porta do servidor (padrão: 8000)")
    args = parser.parse_args()

    if args.serve:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), DashboardHandler)
        html_abs = (DASHBOARD_DIR / "html" / "index.html").resolve()
        print(f"Dashboard em http://localhost:{args.port}/html/index.html")
        print("Progresso marca/desmarca os checkboxes nos conteudo.md (fonte única).")
        if not html_abs.exists():
            print("ATENÇÃO: index.html ainda não foi gerado. Rode o script sem --serve primeiro.")
        try:
            print("Pressione Ctrl+C para encerrar.")
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")
            server.server_close()
        sys.exit(0)

    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    html = generate_final_html()
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard gerado: {HTML_PATH}")
    print("Abra dashboard/html/index.html no navegador para visualizar.")
