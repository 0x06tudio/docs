<div align="center">
  <img alt="Logo 0x06tudio" src="src/media/0x06_Logo_Chiaro_trasparente.png" width="65%">
  <h1>Documentazione · 0x06tudio</h1>
  <p>Progetto didattico di Ingegneria del Software, a.a. 2026/2027<br>
  Università degli Studi di Padova · Corso di Laurea in Informatica</p>
</div>

## Struttura della repository

La repository contiene i sorgenti modificabili dei documenti in `src/` e i
relativi PDF pubblicati in `out/`.

```text
.
├── README.md
├── src/
│   ├── candidatura/       # Sorgenti LaTeX dei documenti di candidatura
│   ├── diari_di_bordo/    # Presentazioni dei diari di bordo
│   ├── media/             # Loghi e immagini usati nei documenti e nel sito
│   └── verbali/
│       ├── esterni/       # Verbali degli incontri con soggetti esterni
│       └── interni/       # Verbali delle riunioni del gruppo
└── out/
    ├── candidatura/       # PDF dei documenti di candidatura
    └── verbali/
        ├── esterni/       # PDF dei verbali esterni
        └── interni/       # PDF dei verbali interni
```

I file `.tex` sono le fonti da modificare; i PDF in `out/` sono le versioni
consultabili. Quando si aggiorna un documento, mantenere allineati il sorgente
e il PDF corrispondente. Le presentazioni `.pptx` dei diari di bordo si trovano
in `src/diari_di_bordo/`.

## Convenzioni per i documenti

### Verbali

- Separare i verbali interni e quelli esterni nelle rispettive cartelle,
  sia sotto `src/verbali/` sia sotto `out/verbali/`.
- Usare i prefissi `vi` per i verbali interni e `ve` per quelli esterni,
  seguiti dalla data nel formato `AAAA_MM_GG`: per esempio
  `vi_2026_11_03.tex` e `ve_2026_10_26.tex`.
- Scrivere la data all'interno del documento come `AAAA/MM/GG`, ad esempio
  `2026/11/03`.
- Mantenere nel verbale titolo, uso (interno/esterno), partecipanti,
  destinatari e le informazioni di riunione pertinenti. I verbali interni
  riportano anche luogo/modalità, orari e durata; quelli esterni includono le
  informazioni dell'incontro con il proponente.
- Tenere aggiornato il registro delle modifiche con versione, data,
  descrizione e autore. Nei verbali interni il registro riporta anche il
  verificatore.
- Salvare il PDF compilato con lo stesso nome e nella cartella omologa sotto
  `out/verbali/`.

Queste convenzioni sono ricavate dai verbali presenti nella repository; per
nuovi verbali fare riferimento ai sorgenti più recenti della stessa categoria.

### Altri nomi

- I documenti di candidatura usano nomi descrittivi in `snake_case`, ad
  esempio `lettera_presentazione.tex`.
- Le presentazioni seguono il nome `DiarioDiBordo<N>_ZeroSixStudio.pptx`,
  sostituendo `<N>` con il numero progressivo.

## Il sito

Il sito è una raccolta statica di pagine HTML, fogli CSS e script JavaScript.
La sua struttura generata è:

```text
site/
├── html/
│   ├── index.html       # Elenco e ricerca dei documenti
│   ├── gruppo.html      # Componenti, ruoli e informazioni sui componenti del gruppo
│   ├── cruscotto.html   # Riepilogo dello stato del progetto
│   └── glossario.html   # Glossario dei termini
├── css/                 # Stili condivisi e specifici delle pagine
└── js/                  # Ricerca dei documenti, glossario e interazioni
```

La pagina Documenti elenca i PDF di `out/candidatura/` e `out/verbali/` e le
presentazioni di `src/diari_di_bordo/`. I collegamenti ai file puntano alle
risorse della repository su GitHub; i documenti non vengono incorporati
nell'HTML. La navigazione tra pagine è condivisa e ogni pagina usa gli stili
comuni (`style.css`) più eventuali fogli e script specifici.

La cartella `site/` è un artefatto generato, non una fonte da modificare a
mano. La configurazione Git ignore la esclude dal versionamento; le modifiche
al sito vanno fatte nel generatore e poi rigenerate.

## Generazione e pubblicazione con GitHub Actions

Il generatore ricostruisce `site/` da zero, creando le sottocartelle `html/`,
`css/` e `js/`, le quattro pagine HTML e gli asset. Per popolare l'elenco dei
documenti consulta l'albero dei file della repository su GitHub, sul branch
configurato (`main`), e seleziona i PDF e le presentazioni secondo cartella ed
estensione. Per questo motivo i nuovi file devono essere presenti nel branch
pubblicato perché compaiano nell'elenco; il generatore non compila i `.tex` in
PDF.

La pipeline GitHub Pages descritta dalla configurazione disponibile prevede:

1. avvio dopo un push su `main`, su pianificazione giornaliera alle 05:00 UTC
   oppure manualmente;
2. checkout della repository e configurazione di Python 3.10;
3. esecuzione del generatore;
4. caricamento di `site/` come artifact GitHub Pages;
5. pubblicazione dell'artifact tramite il job di deploy.