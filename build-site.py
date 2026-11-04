#!/usr/bin/env python3
"""Genera il sito statico della documentazione nella cartella `site/`
organizzando i file in sottocartelle (html/, css/, js/) senza duplicare
file nella root di site/.
"""

import html
import json
import os
import re
import shutil
import urllib.request
from datetime import date
from functools import lru_cache
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import quote

# ---------- Configurazione ----------
GRUPPO = "0x06tudio"
SOTTOTITOLO = "Progetto didattico di Ingegneria del Software a.a. 2026/2027"
ISTITUTO = "Università degli Studi di Padova"
EMAIL = "0x06tudio@gmail.com"
REPO_SLUG = "0x06tudio/docs"
REPO_URL = f"https://github.com/{REPO_SLUG}"
REPO_BRANCH = "main"
CAPITOLATO_NOME = "Capitolato C9 - SpecCheck"
CAPITOLATO_URL = "https://www.math.unipd.it/~tullio/IS-1/2026/Progetto/C9.pdf"
LOGO = Path(__file__).resolve().parent / "src" / "media" / "logo_edited.png"
MEDIA_URL = "../../docs/src/media"

SRC = Path("src")
OUT = Path("out")
SITE = Path("site")

MESI = [
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
]

# ---------- Dati del gruppo e Timeline dei Ruoli ----------
MEMBRI = [
    ("Davide", "Colabove"),
    ("Catalin", "Chirilov"),
    ("Andrea", "Maggio"),
    ("Pietro", "Brocadello"),
    ("Alberto", "Cavalletto"),
    ("Nicolò", "Beltrame"),
]

# TIMELINE DEGLI SPRINT, dal più vecchio al più recente:
# L'ultimo sprint inserito in fondo alla lista rimarrà attivo/aperto di default.
TIMELINE_RUOLI = [
    {
        "sprint": "S01",
        "periodo": "Inizio Progetto - Ottobre 2026",
        "ruoli": {
            "Responsabile": "Davide Colabove",
            "Amministratore": "Catalin Chirilov",
            "Analista": "Andrea Maggio",
            "Progettista": "Pietro Brocadello",
            "Programmatore": "Alberto Cavalletto",
            "Verificatore": "Nicolò Beltrame",
        },
    },
]
SPRINT_CORRENTE = TIMELINE_RUOLI[-1]["sprint"]

RUOLI = {
    "Responsabile": (
        "Coordina i lavori, gestisce scadenze e riunioni, cura i rapporti con "
        "committente e proponente e approva i verbali.",
        48,
    ),
    "Amministratore": (
        "Gestisce l'infrastruttura: repository Git, pipeline CI/CD, ambienti "
        "di lavoro e strumenti a supporto della qualità della documentazione.",
        48,
    ),
    "Analista": (
        "Redige l'Analisi dei Requisiti, trasformando i bisogni del capitolato in "
        "casi d'uso e requisiti, e modella la tracciabilità.",
        105,
    ),
    "Progettista": (
        "Definisce l'architettura del software: skill OpenCode, interfacce dei "
        "tool deterministici e dashboard di sintesi.",
        125,
    ),
    "Programmatore": (
        "Implementa il software secondo la progettazione: skill, tool "
        "deterministici in Node.js e dashboard.",
        136,
    ),
    "Verificatore": (
        "Controlla la qualità di documenti e codice, ed esegue le suite di "
        "test (unitari, di integrazione e di sistema).",
        90,
    ),
}

PROGETTO = [
    ("Capitolato", "C9 - SpecCheck"),
    ("Proponente", "Zucchetti S.p.A."),
    (
        "Obiettivo",
        "Skill per OpenCode che verificano la tracciabilità end-to-end tra "
        "casi d'uso, requisiti e codice sorgente.",
    ),
    ("Monte ore", "552 ore complessive (circa 92 a componente)"),
    ("Costo preventivato", "11.540,00 €"),
    ("Consegna prevista", "24 marzo 2027"),
]

GLOSSARIO = [
    (
        "AdR",
        "Analisi dei Requisiti: documento che traduce i bisogni del capitolato in casi d'uso e requisiti.",
    ),
    (
        "Agentic Coding",
        "Modo di sviluppare in cui un agente basato su LLM pianifica, scrive e modifica il codice con un certo grado di autonomia.",
    ),
    (
        "Amministratore",
        "Ruolo di progetto responsabile di repository, pipeline CI/CD, ambienti di lavoro e strumenti di supporto.",
    ),
    ("Analista", "Ruolo di progetto che redige l'Analisi dei Requisiti."),
    (
        "Capitolato",
        "Documento con cui un'azienda proponente descrive il progetto da realizzare. Il nostro è il C9 - SpecCheck.",
    ),
    (
        "Caso d'uso",
        "Descrizione di come un utente interagisce con il sistema per raggiungere un obiettivo; da esso discendono i requisiti.",
    ),
    (
        "CI/CD",
        "Integrazione e consegna continue: automazioni che costruiscono, verificano e pubblicano il lavoro a ogni modifica.",
    ),
    (
        "Committente",
        "Soggetto che commissiona e valuta il progetto didattico; nel corso sono i docenti.",
    ),
    (
        "Context window",
        "Quantità massima di testo (token) che un LLM riesce a considerare in una sola richiesta.",
    ),
    (
        "Diario di bordo",
        "Presentazione settimanale ai docenti sullo stato di avanzamento, le difficoltà e gli obiettivi a breve termine (DdB).",
    ),
    (
        "Harness",
        "Ambiente che fa funzionare un agente LLM e gli mette a disposizione strumenti e skill, ad esempio OpenCode o Claude Code.",
    ),
    (
        "LLM",
        "Large Language Model: modello di linguaggio di grandi dimensioni, base degli strumenti di agentic coding.",
    ),
    (
        "Mermaid",
        "Linguaggio testuale per descrivere diagrammi; formato privilegiato per i diagrammi in input a SpecCheck.",
    ),
    (
        "MVP",
        "Minimum Viable Product: prima versione del prodotto con le sole funzionalità essenziali.",
    ),
    (
        "NdP",
        "Norme di Progetto: regole di lavoro e di scrittura che il gruppo si impegna a rispettare.",
    ),
    (
        "Node.js",
        "Ambiente di esecuzione JavaScript usato per i tool deterministici del progetto.",
    ),
    (
        "Non-determinismo",
        "Proprietà per cui un LLM può dare risposte diverse a parità di input, che complica i test automatici.",
    ),
    (
        "OpenCode",
        "Agente di coding open source a riga di comando, per cui SpecCheck sviluppa le skill.",
    ),
    (
        "OpenSpec",
        "Strumento di sviluppo guidato dalle specifiche, mostrato dal proponente come esempio di plugin orchestratore.",
    ),
    (
        "Plugin orchestratore",
        "Componente deterministico che gestisce stato e dashboard e delega all'LLM solo le valutazioni semantiche.",
    ),
    (
        "PoC",
        "Proof of Concept: realizzazione minima per dimostrare la fattibilità di un'idea.",
    ),
    ("Programmatore", "Ruolo di progetto che implementa il software."),
    ("Progettista", "Ruolo di progetto che definisce l'architettura del software."),
    (
        "Proponente",
        "Azienda che propone il capitolato e affianca il gruppo; per il C9 è Zucchetti.",
    ),
    (
        "Requisito",
        "Capacità o vincolo che il sistema deve soddisfare; può essere funzionale, prestazionale o di vincolo.",
    ),
    ("Responsabile", "Ruolo di progetto che coordina il gruppo e approva i verbali."),
    (
        "Rotazione dei ruoli",
        "Passaggio dei ruoli tra i componenti al termine di ogni sprint, con meccanismo di shift +1.",
    ),
    (
        "Skill",
        "Insieme di istruzioni e strumenti che estende le capacità di un agente come OpenCode per un compito specifico.",
    ),
    (
        "SpecCheck",
        "Nome del capitolato C9: verifica della tracciabilità tra casi d'uso, requisiti e codice.",
    ),
    (
        "Sprint",
        "Periodo di lavoro di circa due settimane, al termine del quale avviene la rotazione dei ruoli.",
    ),
    (
        "Studio di fattibilità",
        "Documento che analizza i capitolati della shortlist e motiva la scelta finale.",
    ),
    (
        "Tracciabilità",
        "Possibilità di seguire il legame tra casi d'uso, requisiti e codice che li realizza.",
    ),
    (
        "Verbale",
        "Resoconto di una riunione. Gli interni riguardano il gruppo; gli esterni gli incontri con le aziende e riportano l'approvazione del proponente.",
    ),
    (
        "Verificatore",
        "Ruolo di progetto che controlla qualità e correttezza di documenti, codice e test.",
    ),
    (
        "Vibe Coding",
        "Scrittura di codice affidata a un LLM tramite richieste informali, spesso senza verificare che rispetti i requisiti.",
    ),
    (
        "Way of working",
        "Insieme di strumenti e pratiche di lavoro del gruppo: LaTeX, GitHub, git e allineamenti settimanali.",
    ),
    (
        "XMI",
        "Formato XML per scambiare modelli UML; tra i formati testuali di diagramma supportati da SpecCheck.",
    ),
]

PAGINE = [
    ("index.html", "Documenti"),
    ("issues.html", "Issues"),
    ("gruppo.html", "Gruppo"),
    ("cruscotto.html", "Cruscotto"),
    ("glossario.html", "Glossario"),
]


def data_estesa(iso: str) -> str:
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return f"{d} {MESI[m - 1]} {y}"


TITOLI = {
    "lettera_presentazione": "Lettera di presentazione",
    "preventivo_costi_e_impegni_orari": "Preventivo dei costi e degli impegni orari",
    "resoconto_capitolati": "Resoconto dei capitolati",
    "studio_di_fattibilita": "Studio di fattibilità",
}


def titolo_da_nome(stem: str) -> str:
    if stem in TITOLI:
        return TITOLI[stem]
    m = re.fullmatch(r"DiarioDiBordo(\d+)", stem)
    if m:
        return f"Diario di bordo {m.group(1)}"
    t = stem.replace("_", " ").strip()
    return t[:1].upper() + t[1:]


@lru_cache(maxsize=1)
def file_repository():
    url = (
        f"https://api.github.com/repos/{REPO_SLUG}/git/trees/"
        f"{REPO_BRANCH}?recursive=1"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "0x06tudio-docs-build",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        albero = json.load(response)
    if albero.get("truncated"):
        raise RuntimeError("L'albero GitHub è troncato: impossibile elencare i documenti.")
    return tuple(
        PurePosixPath(elemento["path"])
        for elemento in albero.get("tree", [])
        if elemento.get("type") == "blob"
    )


def raccogli(cartella: str, ext: str = "*.pdf"):
    trovati = []
    radici = (OUT,) if ext == "*.pdf" else (SRC,)
    for radice in radici:
        base = PurePosixPath(radice.as_posix()) / cartella
        for f in file_repository():
            if f.parent == base and f.match(ext):
                trovati.append(f)
    return sorted(trovati, key=lambda f: f.name)


def link_risorsa(f: PurePosixPath) -> str:
    percorso = quote(f.as_posix(), safe="/")
    return f"https://raw.githubusercontent.com/{REPO_SLUG}/{REPO_BRANCH}/{percorso}"


def link_logo() -> str:
    return f"{MEDIA_URL}/{quote(LOGO.name)}"


def voce(href: str, titolo: str, meta: str = "") -> str:
    ext = href.rsplit(".", 1)[-1].upper()
    meta_html = f'<span class="meta">{html.escape(meta)}</span>' if meta else ""
    return (
        f'<li><a href="{html.escape(href)}" target="_blank" rel="noopener noreferrer">'
        f'<span class="titolo">{html.escape(titolo)}</span>{meta_html}'
        f'<span class="tipo">{ext}</span></a></li>'
    )


def sezione(sid: str, titolo: str, descr: str, gruppi) -> str:
    gruppi = [(s, v) for s, v in gruppi if v]
    if not gruppi:
        return ""
    n = sum(len(v) for _, v in gruppi)
    out = [
        f'<section id="{sid}"><h2>{html.escape(titolo)}'
        f'<span class="conteggio">{n}</span></h2>'
        f'<p class="descr">{html.escape(descr)}</p>'
    ]
    for sub, voci in gruppi:
        if sub:
            out.append(f"<h3>{html.escape(sub)}</h3>")
        out.append("<ul>" + "".join(voci) + "</ul>")
    out.append("</section>")
    return "".join(out)


def voci_verbali(cartella: str, prefisso: str, etichetta: str):
    voci = []
    for f in sorted(raccogli(cartella), key=lambda f: f.name, reverse=True):
        m = re.search(r"(\d{4}_\d{2}_\d{2})", f.stem)
        if m:
            iso = m.group(1).replace("_", "-")
            voci.append(
                voce(link_risorsa(f), f"{etichetta} del {data_estesa(iso)}", iso)
            )
        else:
            voci.append(voce(link_risorsa(f), titolo_da_nome(f.stem)))
    return voci


def voci_diari():
    voci = []
    for f in raccogli("diari_di_bordo", "*.pptx"):
        voci.append(
            voce(
                link_risorsa(f), titolo_da_nome(re.sub(r"_ZeroSixStudio$", "", f.stem))
            )
        )
    return voci


def carica_issues():
    locale = os.environ.get("ISSUES_FILE")
    try:
        if locale:
            dati = json.loads(Path(locale).read_text(encoding="utf-8"))
        else:
            dati = []
            token = os.environ.get("GITHUB_TOKEN")
            for pagina in range(1, 11):
                url = (
                    f"https://api.github.com/repos/{REPO_SLUG}/issues"
                    f"?state=all&per_page=100&page={pagina}"
                )
                req = urllib.request.Request(
                    url,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "0x06tudio-docs-build",
                    },
                )
                if token:
                    req.add_header("Authorization", f"Bearer {token}")
                with urllib.request.urlopen(req, timeout=20) as r:
                    blocco = json.load(r)
                dati.extend(blocco)
                if len(blocco) < 100:
                    break
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    return [i for i in dati if "pull_request" not in i], None


def voce_issue(i: dict) -> str:
    chiusa = i.get("state") == "closed"
    url = str(i.get("html_url", ""))
    if not url.startswith("https://github.com/"):
        url = f"{REPO_URL}/issues/{int(i.get('number', 0))}"
    autore = (i.get("user") or {}).get("login", "")
    assegnati = [a.get("login", "") for a in (i.get("assignees") or [])]
    etichette = [
        l.get("name", "") for l in (i.get("labels") or []) if isinstance(l, dict)
    ]

    meta = [f"#{int(i.get('number', 0))}"]
    if chiusa and i.get("closed_at"):
        meta.append("chiusa il " + data_estesa(i["closed_at"]))
    elif i.get("created_at"):
        meta.append("aperta il " + data_estesa(i["created_at"]))
    if autore:
        meta.append("da " + autore)
    if assegnati:
        meta.append("assegnata a " + ", ".join(assegnati))

    chips = "".join(
        f'<span class="etichetta">{html.escape(e)}</span>' for e in etichette
    )
    stato = "Chiusa" if chiusa else "Aperta"
    return (
        f'<li><a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">'
        f'<span class="stato {"chiusa" if chiusa else "aperta"}">{stato}</span>'
        f'<span class="corpo"><span class="titolo">{html.escape(i.get("title", ""))}</span>'
        f'<span class="meta">{html.escape(" · ".join(meta))}</span>'
        f'{("<span class=etichette>" + chips + "</span>") if chips else ""}</span></a></li>'
    )


def sezioni_issues(issues):
    aperte = [i for i in issues if i.get("state") != "closed"]
    chiuse = [i for i in issues if i.get("state") == "closed"]
    aperte.sort(key=lambda i: i.get("created_at", ""), reverse=True)
    chiuse.sort(key=lambda i: i.get("closed_at") or "", reverse=True)

    out = []
    for sid, titolo, descr, lista in (
        ("aperte", "Aperte", "Dalla più recente.", aperte),
        ("chiuse", "Chiuse", "Dalla chiusa più di recente.", chiuse),
    ):
        voci = "".join(voce_issue(i) for i in lista)
        corpo = f"<ul>{voci}</ul>" if voci else '<p class="vuoto">Nessuna issue.</p>'
        out.append(
            f'<section id="{sid}" data-stato="{sid}"><h2>{titolo}'
            f'<span class="conteggio">{len(lista)}</span></h2>'
            f'<p class="descr">{descr}</p>{corpo}</section>'
        )
    return "".join(out)


def testata(attiva: str, logo_tag: str) -> str:
    def voce_menu(href: str, titolo: str) -> str:
        aria_corrente = ' aria-current="page"' if href == attiva else ""
        return f'<li><a href="{href}"{aria_corrente}>{titolo}</a></li>'

    voci = "".join(
        voce_menu(href, titolo) for href, titolo in PAGINE
    )
    return (
        f'<header class="top"><div class="in">'
        f'{logo_tag}<a class="nome" href="index.html">{html.escape(GRUPPO)}</a>'
        f'<span class="tag">Documentazione di progetto</span>'
        f'<nav class="menu" aria-label="Pagine del sito"><ul>{voci}</ul></nav>'
        f"</div></header>"
    )


def pagina(
    nome: str, titolo: str, logo_tag: str, corpo: str, favicon_tag: str = "", css_extra: str = "", js: str = ""
) -> None:
    css = '<link rel="stylesheet" href="../css/style.css">'
    if css_extra:
        css += f'\n<link rel="stylesheet" href="../css/{css_extra}">'
    script = f'<script src="../js/{js}"></script>' if js else ""
    favicon_tag = favicon_tag or (
        f'<link rel="icon" href="../media/{LOGO.name}" type="image/png">'
        if LOGO.exists()
        else ""
    )

    testo = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{html.escape(titolo)} · {html.escape(GRUPPO)}</title>
{favicon_tag}
{css}
</head>
<body>
<a class="salta" href="#contenuto">Vai al contenuto</a>
{testata(nome, logo_tag)}
<main id="contenuto">
{corpo}
</main>
<footer>{html.escape(GRUPPO)} · {html.escape(ISTITUTO)}<br>Sito generato dai sorgenti del repository · <a href="{html.escape(REPO_URL)}" target="_blank" rel="noopener noreferrer">Sorgenti su GitHub</a></footer>
{script}
</body>
</html>
"""
    (SITE / "html" / nome).write_text(testo, encoding="utf-8")


def barra_ricerca(etichetta: str, segnaposto: str) -> str:
    return (
        f'<div class="cerca" role="search">'
        f'<label for="cerca">{html.escape(etichetta)}</label>'
        f'<input id="cerca" type="search" placeholder="{html.escape(segnaposto)}" autocomplete="off">'
        f'<p class="esito" id="esito" aria-live="polite"></p></div>'
    )


def info_progetto(aggiornato: str) -> str:
    def ext(href, testo):
        return (
            f'<a href="{html.escape(href)}" target="_blank" '
            f'rel="noopener noreferrer">{html.escape(testo)}</a>'
        )

    riga1 = f'<div class="info-riga">Aggiornato il {aggiornato}</div>'
    riga2 = (
        f'<div class="info-riga">'
        f"<span>{html.escape(CAPITOLATO_NOME)}</span>"
        f'<span class="sep-info">·</span>'
        f'{ext(REPO_URL, "Repository su GitHub")}'
        f'<span class="sep-info">·</span>'
        f'<a href="mailto:{html.escape(EMAIL)}">{html.escape(EMAIL)}</a>'
        f"</div>"
    )
    return f'<div class="info">{riga1}{riga2}</div>'


def pagina_documenti(logo_tag: str, favicon_tag: str = "") -> int:
    candidatura_voci = []
    for f in raccogli("candidatura"):
        candidatura_voci.append(voce(link_risorsa(f), titolo_da_nome(f.stem)))

    sezioni = [
        sezione(
            "candidatura",
            "Candidatura",
            "Documenti consegnati per la candidatura al capitolato.",
            [(None, candidatura_voci)],
        ),
        sezione(
            "verbali",
            "Verbali",
            "Dal più recente.",
            [
                ("Esterni", voci_verbali("verbali/esterni", "ve", "Verbale esterno")),
                ("Interni", voci_verbali("verbali/interni", "vi", "Verbale interno")),
            ],
        ),
        sezione(
            "diari",
            "Diari di bordo",
            "Le presentazioni settimanali ai docenti.",
            [(None, voci_diari())],
        ),
    ]
    sezioni = [s for s in sezioni if s]
    nav_ids = re.findall(r'<section id="([^"]+)"><h2>([^<]+)', "".join(sezioni))
    toc = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in nav_ids)

    corpo = f"""  <h1>{html.escape(GRUPPO)}</h1>
  <p class="intro">{html.escape(SOTTOTITOLO)}, {html.escape(ISTITUTO)}</p>
  {info_progetto(data_estesa(date.today().isoformat()))}

  <div class="layout-principale">
    <aside class="sidebar-toc">
      <nav class="toc" aria-label="In questa pagina"><p>In questa pagina</p><ol>{toc}</ol></nav>
    </aside>
    <div class="contenuto-principale">
      {barra_ricerca("Cerca un documento", "Es. Verbale interno del 22 ottobre")}
      {"".join(sezioni)}
    </div>
  </div>"""
    pagina("index.html", "Documentazione", logo_tag, corpo, favicon_tag=favicon_tag, js="script.js")
    return len(sezioni)


def pagina_issues(logo_tag: str, favicon_tag: str = "") -> None:
    issues, errore = carica_issues()
    if issues is None:
        ricerca = ""
        contenuto = (
            '<p class="avviso" role="status">Le issues non sono al momento disponibili '
            f"in questa versione del sito. Si possono consultare direttamente su "
            f'<a href="{html.escape(REPO_URL)}/issues" target="_blank" rel="noopener noreferrer">GitHub</a>.</p>'
        )
    else:
        ricerca = barra_ricerca(
            "Cerca un'issue", "Es. titolo, assegnatario o etichetta"
        )
        contenuto = sezioni_issues(issues)
    corpo = f"""  <h1>Issues</h1>
  <p class="intro">Attività e problemi tracciati su GitHub, aperti e chiusi.</p>
  {ricerca}
  {contenuto}"""
    pagina(
        "issues.html",
        "Issues",
        logo_tag,
        corpo,
        favicon_tag=favicon_tag,
        css_extra="issues.css",
        js="issues.js" if issues is not None else "",
    )


def pagina_gruppo(logo_tag: str, favicon_tag: str = "") -> None:
    ruoli_correnti = {
        persona: ruolo
        for ruolo, persona in TIMELINE_RUOLI[-1]["ruoli"].items()
    }
    schede = "".join(
        f'<li class="scheda"><span class="nome-membro">{html.escape(nome)}</span>'
        f'<span class="ruolo">{html.escape(ruoli_correnti[nome])}</span></li>'
        for nome in (f"{n} {c}" for n, c in MEMBRI)
    )
    ruoli = "".join(
        f'<div class="ruolo-def"><dt>{html.escape(r)}<span class="ore">{ore} ore previste</span></dt>'
        f"<dd>{html.escape(d)}</dd></div>"
        for r, (d, ore) in RUOLI.items()
    )
    progetto = "".join(
        f"<div><dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>"
        for k, v in PROGETTO
    )

    # Generazione automatica dei Tab e dei pannelli della timeline.
    # Solo l'ULTIMO sprint della lista risulterà attivo (aperto) di default.
    bottoni_tab = ""
    pannelli_tab = ""
    tot_sprint = len(TIMELINE_RUOLI)

    for i, item in enumerate(TIMELINE_RUOLI):
        sprint_id = item["sprint"].lower()
        is_ultimo = i == tot_sprint - 1
        attivo_attr = "true" if is_ultimo else "false"
        classe_attiva = " attivo" if is_ultimo else ""
        nascondi = "" if is_ultimo else " hidden"

        bottoni_tab += (
            f'<button type="button" id="tab-{sprint_id}" class="tab-btn{classe_attiva}" '
            f'data-target="{sprint_id}" role="tab" aria-selected="{attivo_attr}" '
            f'aria-controls="pane-{sprint_id}">Sprint {html.escape(item["sprint"])}'
            f'<span class="tab-periodo">{html.escape(item["periodo"])}</span></button>'
        )

        assegnazioni = "".join(
            f"<li><strong>{html.escape(ruolo)}:</strong> {html.escape(persona)}</li>"
            for ruolo, persona in item["ruoli"].items()
        )

        pannelli_tab += (
            f'<div id="pane-{sprint_id}" class="tab-pane{nascondi}" role="tabpanel" '
            f'aria-labelledby="tab-{sprint_id}">'
            f'<p class="meta-periodo">Periodo: {html.escape(item["periodo"])}</p>'
            f"<ul>{assegnazioni}</ul></div>"
        )

    corpo = f"""  <h1>Gruppo</h1>
  <p class="intro">I sei componenti di {html.escape(GRUPPO)} e i ruoli ricoperti.</p>

  <section id="componenti">
    <h2>Componenti<span class="conteggio">{len(MEMBRI)}</span></h2>
    <p class="descr">Ruoli dello sprint corrente ({html.escape(SPRINT_CORRENTE)}).</p>
    <ul class="membri">{schede}</ul>
  </section>

  <section id="timeline">
    <h2>Timeline dei Ruoli</h2>
    <p class="descr">Seleziona lo sprint per consultare l'assegnazione dei ruoli.</p>
    <div class="tabs-container" role="tablist">
      {bottoni_tab}
    </div>
    <div class="tabs-content">
      {pannelli_tab}
    </div>
  </section>

  <section id="ruoli">
    <h2>Ruoli</h2>
    <p class="descr">Compiti di ciascun ruolo e ore previste nel preventivo.</p>
    <dl class="ruoli">{ruoli}</dl>
  </section>

  <section id="progetto">
    <h2>Il progetto</h2>
    <dl class="progetto">{progetto}</dl>
    <p class="capitolato-testo"><strong>{html.escape(CAPITOLATO_NOME)}</strong></p>
  </section>

  <section id="contatti">
    <h2>Contatti</h2>
    <ul class="contatti">
      <li><a href="mailto:{html.escape(EMAIL)}">{html.escape(EMAIL)}</a></li>
      <li><a href="{html.escape(REPO_URL)}" target="_blank" rel="noopener noreferrer">Repository su GitHub</a></li>
    </ul>
  </section>"""

    pagina(
        "gruppo.html", "Gruppo", logo_tag, corpo, favicon_tag=favicon_tag, css_extra="gruppo.css", js="gruppo.js"
    )


def pagina_cruscotto(logo_tag: str) -> None:
    corpo = f"""  <h1>Cruscotto di Progetto</h1>
  <p class="intro">Panoramica dello stato di avanzamento, metriche e indicatori chiave del progetto.</p>
  <section id="stato-avanzamento">
    <h2>Stato Avanzamento Lavori</h2>
    <p class="descr">Cruscotto ispirato alle specifiche di monitoraggio e controllo della qualità.</p>
    <div class="cruscotto-grid">
      <div class="card">
        <h3>Sprint Attivo</h3>
        <p class="valore">{SPRINT_CORRENTE}</p>
      </div>
      <div class="card">
        <h3>Ore Totali Preventivate</h3>
        <p class="valore">552 h</p>
      </div>
      <div class="card">
        <h3>Stato Consegna</h3>
        <p class="valore">In corso</p>
      </div>
    </div>
  </section>"""
    pagina("cruscotto.html", "Cruscotto", logo_tag, corpo, css_extra="cruscotto.css")


def pagina_glossario(logo_tag: str) -> None:
    termini = sorted(GLOSSARIO, key=lambda t: t[0].casefold())
    lettere = sorted({t[0][0].upper() for t in termini})
    indice = "".join(f'<li><a href="#lett-{l}">{l}</a></li>' for l in lettere)
    blocchi = []
    for l in lettere:
        voci = "".join(
            f'<div class="termine"><dt id="t-{re.sub(r"[^a-z0-9]+", "-", t.casefold()).strip("-")}">{html.escape(t)}</dt>'
            f"<dd>{html.escape(d)}</dd></div>"
            for t, d in termini
            if t[0].upper() == l
        )
        blocchi.append(
            f'<section id="lett-{l}" class="lettera"><h2>{l}</h2><dl>{voci}</dl></section>'
        )
    corpo = f"""  <h1>Glossario</h1>
  <p class="intro">I termini che usiamo nei documenti e nel progetto.</p>
  {barra_ricerca("Cerca un termine", "Es. tracciabilità")}
  <nav class="indice" aria-label="Indice alfabetico"><ul>{indice}</ul></nav>
  {"".join(blocchi)}"""
    pagina(
        "glossario.html",
        "Glossario",
        logo_tag,
        corpo,
        css_extra="glossario.css",
        js="glossario.js",
    )


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()

    (SITE / "html").mkdir()
    (SITE / "css").mkdir()
    (SITE / "js").mkdir()
    (SITE / "media").mkdir()

    # Copia il logo nella directory media del sito generato
    logo_tag = ""
    favicon_tag = ""
    if LOGO.exists():
        shutil.copy(LOGO, SITE / "media" / LOGO.name)
        logo_tag = f'<img src="../media/{LOGO.name}" alt="" width="32" height="32">'
        favicon_tag = f'<link rel="icon" href="../media/{LOGO.name}" type="image/png">'

    n = pagina_documenti(logo_tag, favicon_tag)
    pagina_issues(logo_tag, favicon_tag)
    pagina_gruppo(logo_tag, favicon_tag)
    pagina_cruscotto(logo_tag)
    pagina_glossario(logo_tag)

    for nome, contenuto in (
        ("style.css", CSS),
        ("issues.css", CSS_ISSUES),
        ("gruppo.css", CSS_GRUPPO),
        ("cruscotto.css", CSS_CRUSCOTTO),
        ("glossario.css", CSS_GLOSSARIO),
        ("script.js", JS),
        ("issues.js", JS_ISSUES),
        ("glossario.js", JS_GLOSSARIO),
        ("gruppo.js", JS_GRUPPO),
    ):
        cartella_dest = "css" if nome.endswith(".css") else "js"
        (SITE / cartella_dest / nome).write_text(contenuto, encoding="utf-8")

    print(
        f"Sito generato in {SITE}/ con struttura pulita (html/, css/, js/) e gestione tab con persistenza localStorage."
    )


# ======================= CSS =======================
CSS = """:root{
  --sfondo:#faf9f6; --testo:#1f2328; --tenue:#5f6670; --linea:#e4e1d8;
  --accento:#1f4fa3; --hover:#f1efe8; --font:"Iowan Old Style","Charter","Georgia",serif;
  --ui:system-ui,-apple-system,"Segoe UI",sans-serif;
}
@media (prefers-color-scheme: dark){
  :root{--sfondo:#16181b; --testo:#e8e6e1; --tenue:#a0a5ad; --linea:#2c3036;
         --accento:#8ab4ff; --hover:#1f2226;}
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:6rem}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--sfondo);color:var(--testo);font:1.05rem/1.65 var(--font)}
a{color:inherit}
:focus-visible{outline:2px solid var(--accento);outline-offset:3px;border-radius:2px}
.salta{position:absolute;left:-999px}
.salta:focus{left:1rem;top:1rem;background:var(--sfondo);padding:.4rem .8rem;z-index:10}
header.top{position:sticky;top:0;z-index:5;background:var(--sfondo);border-bottom:1px solid var(--linea)}
header.top .in{max-width:64rem;margin:0 auto;padding:.7rem 1.25rem;display:flex;flex-wrap:wrap;align-items:center;gap:.4rem .7rem;font-family:var(--ui)}
header.top .nome{font-weight:650;text-decoration:none}
header.top .tag{color:var(--tenue);font-size:.92rem;margin-left:auto}
nav.menu{margin-left:auto}
nav.menu ul{display:flex;flex-wrap:wrap;gap:.2rem;border:0;margin:0;padding:0;list-style:none}
nav.menu li{border:0}
nav.menu a{display:block;padding:.25rem .65rem;border-radius:6px;font-size:.93rem;text-decoration:none;color:var(--tenue)}
nav.menu a:hover{background:var(--hover);color:var(--testo)}
nav.menu a[aria-current="page"]{color:var(--accento);font-weight:600;background:var(--hover)}
@media (max-width:640px){header.top .tag{display:none}nav.menu{margin-left:0;width:100%}}
main{max-width:64rem;margin:0 auto;padding:2.5rem 1.25rem 4rem}
h1{font-size:clamp(2rem,5vw,2.9rem);line-height:1.15;margin:.2rem 0 .6rem;letter-spacing:-.01em}
.intro{color:var(--tenue);margin:0 0 1.2rem}

.info{margin:0 0 2.5rem;font-family:var(--ui);font-size:.95rem;color:var(--tenue);display:flex;flex-direction:column;gap:.3rem}
.info-riga{display:flex;flex-wrap:wrap;align-items:center;gap:.6rem}
.sep-info{color:var(--tenue)}
.info a{color:var(--accento)}

.layout-principale{display:grid;grid-template-columns:16rem 1fr;gap:2.5rem;align-items:start}
@media (max-width:850px){.layout-principale{grid-template-columns:1fr}}
.sidebar-toc{position:sticky;top:5rem}
nav.toc{font-family:var(--ui);border:1px solid var(--linea);border-radius:6px;padding:.9rem 1.1rem;background:var(--sfondo)}
nav.toc p{margin:0 0 .3rem;font-weight:600;font-size:.95rem}
nav.toc ol{margin:0;padding-left:1.2rem}
nav.toc a{color:var(--accento)}

section{margin:0 0 3rem}
h2{font-size:1.6rem;margin:0 0 .2rem;display:flex;align-items:baseline;gap:.6rem}
.conteggio{font:500 .85rem var(--ui);color:var(--tenue)}
h3{font:600 1.05rem var(--ui);margin:1.6rem 0 .3rem}
.descr{margin:0 0 .8rem;color:var(--tenue)}
ul{list-style:none;padding:0;margin:0;border-top:1px solid var(--linea)}
ul li{border-bottom:1px solid var(--linea)}
ul a{display:flex;align-items:baseline;gap:.8rem;padding:.7rem .5rem;text-decoration:none}
ul a:hover{background:var(--hover)}
ul a:hover .titolo{color:var(--accento);text-decoration:underline}
.titolo{flex:1}
.meta{font:.85rem var(--ui);color:var(--tenue);white-space:nowrap}
.tipo{font:600 .75rem var(--ui);color:var(--tenue);border:1px solid var(--linea);border-radius:4px;padding:.05rem .4rem}
footer{max-width:64rem;margin:0 auto;padding:1.5rem 1.25rem 3rem;border-top:1px solid var(--linea);font:.9rem var(--ui);color:var(--tenue)}
footer a{color:var(--accento)}
.cerca{margin:0 0 2.5rem;font-family:var(--ui)}
.cerca label{display:block;font-weight:600;font-size:.95rem;margin-bottom:.35rem}
.cerca input{width:100%;font:inherit;padding:.6rem .8rem;color:var(--testo);background:var(--sfondo);border:1px solid var(--linea);border-radius:6px}
.cerca input:focus-visible{border-color:var(--accento)}
.cerca .esito{margin:.4rem 0 0;font-size:.9rem;color:var(--tenue);min-height:1.3em}
[hidden]{display:none !important}
"""

CSS_ISSUES = """/* Pagina Issues */
.filtri{display:flex;gap:.4rem;margin:0 0 .6rem;font-family:var(--ui)}
.filtri button{font:inherit;font-size:.9rem;padding:.3rem .9rem;border:1px solid var(--linea);border-radius:999px;background:var(--sfondo);color:var(--tenue);cursor:pointer}
.filtri button:hover{background:var(--hover);color:var(--testo)}
.filtri button[aria-pressed="true"]{border-color:var(--accento);color:var(--accento);font-weight:600}
.riepilogo{font:.9rem var(--ui);color:var(--tenue);margin:0 0 2.5rem}
ul a{align-items:flex-start}
.corpo{flex:1;display:flex;flex-direction:column;gap:.15rem}
.corpo .titolo{flex:none}
.etichette{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.2rem}
.etichetta{font:.75rem var(--ui);color:var(--tenue);border:1px solid var(--linea);border-radius:999px;padding:.02rem .55rem}
.stato{font:600 .75rem var(--ui);border-radius:4px;padding:.1rem .5rem;margin-top:.2rem;border:1px solid var(--linea)}
.stato.aperta{color:#1a7f37;border-color:#1a7f37}
.stato.chiusa{color:var(--tenue)}
@media (prefers-color-scheme: dark){.stato.aperta{color:#56d364;border-color:#56d364}}
.vuoto{color:var(--tenue);font-family:var(--ui);border-top:1px solid var(--linea);padding-top:.8rem;margin:0}
.avviso{font-family:var(--ui);border:1px solid var(--linea);border-radius:6px;padding:.9rem 1.1rem}
.avviso a{color:var(--accento)}
"""

CSS_GRUPPO = """/* Pagina Gruppo e Tab Timeline */
.membri{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:.8rem;border:0}
.scheda{border:1px solid var(--linea);border-radius:8px;padding:.9rem 1rem;display:flex;flex-direction:column;gap:.2rem}
.nome-membro{font-weight:650}
.ruolo{font:.9rem var(--ui);color:var(--accento)}

/* Stili specifici per i Tab dei Ruoli */
.tabs-container { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid var(--linea); padding-bottom: 0.5rem; }
.tab-btn { font: inherit; font-size: 0.9rem; padding: 0.4rem 1rem; border: 1px solid var(--linea); border-radius: 6px; background: var(--sfondo); color: var(--tenue); cursor: pointer; }
.tab-btn:hover { background: var(--hover); color: var(--testo); }
.tab-btn.attivo { border-color: var(--accento); color: var(--accento); font-weight: 600; background: var(--hover); }
.tab-periodo { display: block; font-size: 0.75rem; font-weight: 400; color: var(--tenue); }
.tab-pane { border: 1px solid var(--linea); border-radius: 8px; padding: 1.2rem; background: var(--sfondo); }
.meta-periodo { margin: 0 0 0.8rem 0; font-size: 0.9rem; color: var(--tenue); font-family: var(--ui); font-weight: 600; }
.tab-pane ul { border-top: none; padding-left: 0; }
.tab-pane li { border-bottom: 1px solid var(--linea); padding: 0.4rem 0; font-family: var(--ui); font-size: 0.95rem; }

dl{margin:0}
.ruoli .ruolo-def,.progetto>div{border-top:1px solid var(--linea);padding:.8rem .5rem}
dt{font-weight:650}
.ore{font:.85rem var(--ui);color:var(--tenue);font-weight:400;margin-left:.7rem}
dd{margin:.15rem 0 0;color:var(--tenue)}
.progetto>div{display:grid;grid-template-columns:11rem 1fr;gap:.2rem 1rem}
.progetto dt{font:600 .95rem var(--ui)}
.progetto dd{margin:0;color:var(--testo)}
.capitolato-testo{margin-top:1rem;font-family:var(--ui)}
.contatti a{color:var(--accento)}
section p a{color:var(--accento)}
"""

CSS_CRUSCOTTO = """/* Pagina Cruscotto */
.cruscotto-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(15rem, 1fr));gap:1rem;margin-top:1.5rem}
.card{border:1px solid var(--linea);border-radius:8px;padding:1.2rem;background:var(--sfondo)}
.card h3{margin:0 0 .5rem;font-size:1rem;color:var(--tenue);font-family:var(--ui)}
.card .valore{font-size:1.8rem;font-weight:700;margin:0;color:var(--accento);font-family:var(--ui)}
"""

CSS_GLOSSARIO = """/* Pagina Glossario */
nav.indice{font-family:var(--ui);margin:0 0 2.5rem}
nav.indice ul{display:flex;flex-wrap:wrap;gap:.3rem;border:0}
nav.indice li{border:0}
nav.indice a{display:block;min-width:2rem;text-align:center;padding:.2rem .5rem;border:1px solid var(--linea);border-radius:6px;color:var(--accento);text-decoration:none}
nav.indice a:hover{background:var(--hover)}
.lettera{margin-bottom:2rem}
.lettera h2{border-bottom:1px solid var(--linea);padding-bottom:.3rem;color:var(--accento)}
dl{margin:0}
.termine{padding:.7rem .5rem;border-bottom:1px solid var(--linea)}
dt{font-weight:650}
dd{margin:.15rem 0 0;color:var(--tenue)}
"""

JS = r"""(function () {
  var input = document.getElementById("cerca");
  if (!input) return;
  var esito = document.getElementById("esito");
  var sezioni = Array.prototype.slice.call(document.querySelectorAll("main section"));

  function norm(t) {
    return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  var voci = Array.prototype.slice.call(document.querySelectorAll("main section li"));
  voci.forEach(function (li) {
    var a = li.querySelector("a");
    li._testo = norm(li.textContent + " " + (a ? decodeURIComponent(a.getAttribute("href")).replace(/[_\/.-]/g, " ") : ""));
  });

  function filtra() {
    var termini = norm(input.value).split(/\s+/).filter(Boolean);
    var totali = 0;

    sezioni.forEach(function (sez) {
      var visibiliSez = 0;
      var gruppi = sez.querySelectorAll("ul");
      Array.prototype.forEach.call(gruppi, function (ul) {
        var visibili = 0;
        Array.prototype.forEach.call(ul.children, function (li) {
          var ok = termini.every(function (t) { return li._testo.indexOf(t) !== -1; });
          li.hidden = !ok;
          if (ok) visibili++;
        });
        ul.hidden = visibili === 0;
        var titolo = ul.previousElementSibling;
        if (titolo && titolo.tagName === "H3") titolo.hidden = visibili === 0;
        visibiliSez += visibili;
      });
      sez.hidden = visibiliSez === 0;
      var cont = sez.querySelector(".conteggio");
      var tot = sez.querySelectorAll("li").length;
      if (cont) cont.textContent = termini.length ? visibiliSez + " di " + tot : tot;
      totali += visibiliSez;
    });

    var toc = document.querySelector("nav.toc");
    if (toc) toc.hidden = termini.length > 0;

    if (!termini.length) esito.textContent = "";
    else if (!totali) esito.textContent = "Nessun documento corrisponde alla ricerca.";
    else esito.textContent = totali + (totali === 1 ? " documento trovato" : " documenti trovati");
  }

  input.addEventListener("input", filtra);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { input.value = ""; filtra(); }
  });
})();
"""

JS_ISSUES = r"""(function () {
  var input = document.getElementById("cerca");
  if (!input) return;
  var esito = document.getElementById("esito");
  var sezioni = Array.prototype.slice.call(document.querySelectorAll("main section[data-stato]"));
  var bottoni = Array.prototype.slice.call(document.querySelectorAll(".filtri button"));
  var filtroStato = "tutte";

  function norm(t) {
    return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  sezioni.forEach(function (sez) {
    Array.prototype.forEach.call(sez.querySelectorAll("li"), function (li) {
      li._testo = norm(li.textContent);
    });
  });

  function filtra() {
    var termini = norm(input.value).split(/\s+/).filter(Boolean);
    var totali = 0;

    sezioni.forEach(function (sez) {
      var inclusa = filtroStato === "tutte" || sez.getAttribute("data-stato") === filtroStato;
      var tutte = sez.querySelectorAll("li");
      var visibili = 0;
      Array.prototype.forEach.call(tutte, function (li) {
        var ok = termini.every(function (t) { return li._testo.indexOf(t) !== -1; });
        li.hidden = !ok;
        if (ok) visibili++;
      });
      var cont = sez.querySelector(".conteggio");
      if (cont) cont.textContent = termini.length ? visibili + " di " + tutte.length : tutte.length;
      sez.hidden = !inclusa || (termini.length > 0 && visibili === 0);
      if (inclusa) totali += visibili;
    });

    if (!termini.length) esito.textContent = "";
    else if (!totali) esito.textContent = "Nessuna issue corrisponde alla ricerca.";
    else esito.textContent = totali + (totali === 1 ? " issue trovata" : " issue trovate");
  }

  bottoni.forEach(function (b) {
    b.addEventListener("click", function () {
      filtroStato = b.getAttribute("data-filtro");
      bottoni.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      filtra();
    });
  });

  input.addEventListener("input", filtra);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      input.value = "";
      filtra();
    }
  });
})();
"""

JS_GLOSSARIO = r"""(function () {
  var input = document.getElementById("cerca");
  if (!input) return;
  var esito = document.getElementById("esito");
  var lettere = Array.prototype.slice.call(document.querySelectorAll("section.lettera"));
  var indice = document.querySelector("nav.indice");

  function norm(t) {
    return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  lettere.forEach(function (sez) {
    Array.prototype.forEach.call(sez.querySelectorAll(".termine"), function (el) {
      el._testo = norm(el.textContent);
    });
  });

  function filtra() {
    var termini = norm(input.value).split(/\s+/).filter(Boolean);
    var totali = 0;
    lettere.forEach(function (sez) {
      var visibili = 0;
      Array.prototype.forEach.call(sez.querySelectorAll(".termine"), function (el) {
        var ok = termini.every(function (t) { return el._testo.indexOf(t) !== -1; });
        el.hidden = !ok;
        if (ok) visibili++;
      });
      sez.hidden = visibili === 0;
      totali += visibili;
    });
    if (indice) indice.hidden = termini.length > 0;
    if (!termini.length) esito.textContent = "";
    else if (!totali) esito.textContent = "Nessun termine corrisponde alla ricerca.";
    else esito.textContent = totali + (totali === 1 ? " termine trovato" : " termini trovati");
  }

  input.addEventListener("input", filtra);
})();
"""

JS_GRUPPO = r"""(function () {
  var bottoni = document.querySelectorAll(".tab-btn");
  if (!bottoni.length) return;
  
  var STORAGE_KEY = "0x06tudio_active_sprint";
  
  // Ripristina l'ultimo tab selezionato dalla memoria locale del browser (localStorage)
  var ultimoSprint = localStorage.getItem(STORAGE_KEY);
  if (ultimoSprint) {
    var btnTarget = document.querySelector('.tab-btn[data-target="' + ultimoSprint + '"]');
    var paneTarget = document.getElementById("pane-" + ultimoSprint);
    
    if (btnTarget && paneTarget) {
      bottoni.forEach(function (b) {
        b.classList.remove("attivo");
        b.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".tab-pane").forEach(function (pane) {
        pane.hidden = true;
      });
      
      btnTarget.classList.add("attivo");
      btnTarget.setAttribute("aria-selected", "true");
      paneTarget.hidden = false;
    }
  }
  
  // Gestisce il click sui tab e salva lo stato corrente
  bottoni.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = btn.getAttribute("data-target");
      var targetId = "pane-" + target;
      
      bottoni.forEach(function (b) {
        b.classList.remove("attivo");
        b.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".tab-pane").forEach(function (pane) {
        pane.hidden = true;
      });
      
      btn.classList.add("attivo");
      btn.setAttribute("aria-selected", "true");
      var pannelloTarget = document.getElementById(targetId);
      if (pannelloTarget) {
        pannelloTarget.hidden = false;
      }
      
      localStorage.setItem(STORAGE_KEY, target);
    });
  });
})();
"""

if __name__ == "__main__":
    main()
