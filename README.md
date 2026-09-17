# WebCig — Archivio dei contratti pubblici italiani

Progetto universitario di elaborazione documentale che trasforma fonti CSV, JSON, HTML e PDF in documenti XML, integra un catalogo qualificato di fonti web istituzionali, valida il corpus mediante DTD, estrae un modello intermedio normalizzato e genera analisi territoriali, cronologiche ed economiche. La build produce un sito statico autonomo in `dist/`, pubblicato su GitHub Pages senza backend o database.

Sito: [https://massimilianoricchiuti.github.io/Elaborazione-di-testi-e-gestione-documentale/](https://massimilianoricchiuti.github.io/Elaborazione-di-testi-e-gestione-documentale/)

## Consultazione dell’archivio

La Home offre sei sezioni numerate con un indice persistente e collegamenti diretti: **Introduzione**, **Consultazione**, **Documenti**, **Progetto e metodo**, **Documentazione** e **Compilazione**. La sezione corrente viene evidenziata durante lo scorrimento; i collegamenti funzionano anche senza JavaScript. La navigazione principale porta a **Home**, **Archivio**, **Report dei dati** e **Qualità dei dati**. Il precedente URL `progetto.html` rimanda alla sezione `index.html#progetto-e-metodo`.

L’archivio espone i nomi dei file XML, ricerca per CIG/file/oggetto/ente, filtri territoriali e per tipologia, ordinamento e download. Ogni documento offre tre viste:

- **Scheda completa:** tutti i valori e gli attributi dell’XML, con sezioni navigabili e distinzione esplicita degli elementi vuoti;
- **Struttura XML:** albero espandibile, ricerca per tag/attributo/valore e collegamenti diretti ai nodi;
- **Codice XML:** sorgente integrale, copia e download del file.

`src/processing/xml_view.py` ricava queste viste direttamente dall’XML, preservando nodi ripetuti, attributi e ordine del testo misto. Il modello normalizzato in `ContractRecord` continua a servire alle analisi: i campi che non usa non vengono più esclusi dall’interfaccia. Schede, albero e sorgente sono generati nella pagina e restano consultabili senza JavaScript; quest’ultimo aggiunge schede a linguetta, ricerca e comandi dell’albero.

Il workflow esistente pubblica sia i push su `main` sia quelli su `development`: il sito pubblico riflette l’ultimo deployment completato.

## Requisiti

- Python 3.11 o successivo;
- `pip`;
- LaTeX facoltativo, necessario soltanto per ricompilare il report PDF;
- nessuna variabile segreta o API esterna.

## Struttura

```text
documenti_xml/       XML del dataset
fonti_originali/     CSV, JSON, HTML e PDF locali; catalogo web JSON
schema/              DTD
src/support/         configurazione, I/O, parsing, formattazione e controlli
src/processing/      preparazione, estrazione, analisi, sito e report
scripts/             entry point
site/templates/      template Jinja2
site/assets/         CSS e JavaScript
output_data/         risultati intermedi, incluso analysis.json
report/              report LaTeX, PDF e frammenti generati
tests/               test pytest
dist/                sito statico generato
```

## Installazione

### Linux e macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Preparazione del dataset

```bash
python scripts/prepare.py
```

La preparazione individua dinamicamente i CIG presenti nelle fonti JSON e integra le righe corrispondenti del CSV. Le altre fonti locali vengono associate cercando il CIG prima nel nome del file e, per i nomi descrittivi, nel contenuto testuale estraibile. Il criterio vale per l’intero dataset e non contiene eccezioni dedicate a singoli CIG.

Le risorse reperite sul web sono descritte in `fonti_originali/web/fonti_web.json`. Il caricatore pretende la corrispondenza esatta con l’insieme dei CIG, almeno una fonte per record, URL HTTP(S) validi e metadati completi. La data `verified_on` della singola voce, se presente, prevale su quella generale del catalogo, conservando le date delle verifiche precedenti. Quando si aggiungono JSON con nuovi CIG, occorre aggiungere anche le relative fonti prima di eseguire `build_all.py`. Ogni voce distingue il nesso probatorio (`cig-esatto`, lotto o accordo quadro, CUP e oggetto, procedura, fase antecedente, contesto o repertorio) affinché una fonte indiretta non venga presentata come atto della gara.

## Build del sito

Per validare gli XML esistenti, calcolare le analisi e generare `dist/`:

```bash
python scripts/build.py
```

Per rigenerare prima gli XML e, quando `pdflatex` è disponibile, compilare anche il report:

```bash
python scripts/build_all.py
```

Il controllo dei collegamenti viene eseguito automaticamente sulla sola directory `dist/`. La build fallisce se un riferimento locale non esiste o punta fuori dalla directory pubblicata.

## Relazione di progetto

La relazione unica contiene descrizione del progetto, riproducibilità, limiti e **Prompt documentati**. Gli otto prompt già registrati e la sintesi della revisione dell’interfaccia sono integrati in `report/report_progetto.tex`; non viene pubblicato un documento separato di prompt. Il PDF rimane entro tre pagine.

Dopo una build, i frammenti dinamici sono disponibili in `report/generated/`:

```bash
python scripts/build_report.py
```

Dopo aver ricompilato la relazione, eseguire `python scripts/build.py` per aggiornare anche il PDF scaricabile dal sito.

La build GitHub Pages non richiede LaTeX. Se `report/report_progetto.pdf` è già presente, viene copiato in `dist/downloads/report/`.

## Test

```bash
pytest
```

I test coprono parsing di importi e date, normalizzazione, estrazione XML, validazione dei due content model misti, copertura integrale del catalogo web, anomalie cronologiche, statistiche, pagine principali, collegamenti e file indispensabili al deploy.

## Contenuto di `dist/`

```text
dist/
├── index.html
├── archivio.html
├── report.html
├── progetto.html
├── qualita-dati.html
├── cig/
├── assets/
├── data/
├── downloads/
└── .nojekyll
```

Tutti i CSS, JavaScript, SVG, dati e download necessari sono locali. `assets/css/stile.css` è il foglio comune applicato a tutte le pagine e importa i moduli di base e delle fonti. Nessun collegamento relativo deve uscire da `dist/`.

## Pubblicazione su GitHub Pages

Il workflow `.github/workflows/static.yml` viene eseguito a ogni push su `main` o `development` e può essere avviato anche manualmente. La procedura:

1. installa Python e le dipendenze;
2. rigenera gli XML con `python scripts/prepare.py`, includendo gli eventuali nuovi documenti collegati;
3. genera il sito con `python scripts/build.py`;
4. esegue l'intera suite `pytest`;
5. carica esclusivamente `dist/` come artefatto GitHub Pages;
6. pubblica il sito nell'ambiente `github-pages`.

Nel repository, la sorgente di pubblicazione deve essere impostata una sola volta su **Settings → Pages → Source: GitHub Actions**. Il sito viene quindi aggiornato automaticamente all'indirizzo:

<https://massimilianoricchiuti.github.io/Elaborazione-di-testi-e-gestione-documentale/>

I riferimenti interni sono relativi e restano validi sotto il percorso di progetto `/Elaborazione-di-testi-e-gestione-documentale/`. La directory `dist/` è rigenerata dal workflow a partire dalle fonti; la copia nel repository viene aggiornata con la build locale. Il sito pubblico riflette l’ultimo deployment completato, anche quando proviene da `development`.

## Anteprima locale

Dopo la build, avviare un server HTTP dalla radice del progetto:

```bash
python -m http.server 8000 --directory dist
```

Il sito è disponibile su <http://localhost:8000/>.

## Provenienza e limiti dei dati

Il campione coincide con i documenti conservati nel progetto e non rappresenta l'intero sistema degli appalti pubblici. Le incongruenze cronologiche vengono segnalate senza correggere i dati e senza attribuirle automaticamente a errori della fonte. Le differenze tra importo di gara e aggiudicazione sono descrittive e non vengono denominate automaticamente ribassi. Le fonti web sono state verificate nella data dichiarata per ciascuna fonte, o in quella generale del manifesto se non specificata; disponibilità e contenuto delle pagine esterne possono mutare. Il tipo di nesso resta quindi sempre visibile nel sito e negli XML.
