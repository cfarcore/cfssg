import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import os

# Imposta la configurazione della pagina all'inizio
st.set_page_config(page_title="Fitness Gauge", layout="wide")

# Load CSVs
utenti_df = pd.read_csv("fitness_app/utenti.csv")
esercizi_df = pd.read_csv("fitness_app/esercizi.csv")
test_df = pd.read_csv("fitness_app/test.csv")
benchmark_df = pd.read_csv("fitness_app/benchmark.csv")
wod_df = pd.read_csv("fitness_app/wod.csv")  # Aggiunto caricamento del file wod.csv

# Carica il CSV dei WOD (Workout Of the Day)
wod_path = "fitness_app/wod.csv"
if not os.path.exists(wod_path):
    pd.DataFrame(columns=["data", "titolo", "descrizione"]).to_csv(wod_path, index=False)
wod_df = pd.read_csv(wod_path)

# Correggi automaticamente i formati di data non validi
def correggi_date(df, colonna_data):
    try:
        df[colonna_data] = pd.to_datetime(df[colonna_data], format="%Y-%m-%d", errors="coerce")
        if df[colonna_data].isnull().any():
            st.warning("Alcune date non valide sono state rilevate e rimosse.")
            df = df.dropna(subset=[colonna_data])
    except Exception as e:
        st.error(f"Errore durante la correzione delle date: {e}")
        st.stop()
    return df

wod_df = correggi_date(wod_df, "data")

st.title("🏋️ Fitness Gauge")

# Inizializza session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_pin = ""
    st.session_state.utente = None
    st.session_state.refresh = False  # Aggiunto per gestire il refresh

# Funzione per logout
def logout():
    st.session_state.logged_in = False
    st.session_state.user_pin = ""
    st.session_state.utente = None
    st.session_state.refresh = True  # Imposta il refresh

# Login
if not st.session_state.logged_in:
    ruolo = st.selectbox("Seleziona il tuo ruolo", ["atleta", "coach"])  # Aggiunto per scegliere il ruolo
    nome = st.text_input("Inserisci il tuo nome")
    pin = st.text_input("Inserisci il tuo PIN", type="password")
    if st.button("Accedi"):
        # Normalizza i dati per il confronto
        utenti_df["nome"] = utenti_df["nome"].astype(str).str.strip()
        utenti_df["pin"] = utenti_df["pin"].astype(str).str.strip()
        utenti_df["ruolo"] = utenti_df["ruolo"].astype(str).str.strip()
        nome_normalizzato = nome.strip()
        pin_normalizzato = pin.strip()

        # Filtra l'utente in base al ruolo selezionato
        utente_raw = utenti_df[
            (utenti_df["nome"] == nome_normalizzato) &
            (utenti_df["pin"] == pin_normalizzato) &
            (utenti_df["ruolo"] == ruolo)
        ]
        if not utente_raw.empty:
            st.session_state.logged_in = True
            st.session_state.user_pin = pin_normalizzato
            st.session_state.utente = utente_raw.squeeze()
            st.session_state.refresh = True  # Imposta il refresh
        else:
            st.error("Nome, PIN o ruolo non validi. Riprova.")
    st.stop()

# Tema chiaro/scuro
tema = st.sidebar.radio("🎨 Tema", ["Chiaro", "Scuro"])
st.markdown(
    f"""<style>
    body {{ background-color: {'#1e1e1e' if tema == 'Scuro' else '#ffffff'}; color: {'#f0f0f0' if tema == 'Scuro' else '#000000'}; }}
    </style>""",
    unsafe_allow_html=True
)

# Gestione del refresh della pagina
if st.session_state.refresh:
    st.session_state.refresh = False
    st.query_params = {"refresh": "true"}  # Simula un aggiornamento della pagina

# Utente loggato
utente = st.session_state.utente
st.success(f"Benvenuto, {utente['nome']} ({utente['ruolo']})")

# Barra laterale per navigazione con pulsanti
if utente['ruolo'] == 'coach':
    pagine_sidebar = [
        "🏠 Dashboard",  # Nuova home
        "📅 Calendario WOD",
        "➕ Inserisci nuovo test",
        "👤 Profilo Atleta",
        "⚙️ Gestione Esercizi",
        "📋 Storico Dati Utenti",
        "📊 Bilanciamento Atleti",
        "➕ Aggiungi Utente",
        "⚙️ Gestione Benchmark",
        "📊 Grafici",
        "📈 Storico Progressi",
        "📒 WOD",
        "🏆 Classifiche"
    ]
else:
    pagine_sidebar = [
        "🏠 Dashboard",  # Nuova home
        "📅 Calendario WOD",
        "➕ Inserisci nuovo test",
        "👤 Profilo Atleta",
        "📊 Grafici",
        "📜 Storico Test",
        "📈 Storico Progressi",
        "📒 WOD",
    ]

# Inizializza la pagina attiva se non esiste
if 'pagina_attiva' not in st.session_state:
    st.session_state.pagina_attiva = pagine_sidebar[0]

with st.sidebar:
    # CSS per rendere i pulsanti sidebar della stessa dimensione
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important;
            min-width: 120px;
            margin-bottom: 0.25rem;
        }
        </style>
    """, unsafe_allow_html=True)
    for pagina_nome in pagine_sidebar:
        if st.button(pagina_nome, key=f"btn_{pagina_nome}"):
            st.session_state.pagina_attiva = pagina_nome  # Aggiorna correttamente la pagina attiva

    # Pulsante per uscire
    if st.button("Esci", key="sidebar_logout_button"):
        logout()

# Assicurati che la pagina attiva venga caricata
pagina = st.session_state.get('pagina_attiva', pagine_sidebar[0])

# Debug: Mostra la pagina attiva per verificare
st.write(f"DEBUG: Pagina attiva: {pagina}")

# Definizione dei livelli di valutazione
livelli_val = {"base": 1, "principiante": 2, "intermedio": 3, "buono": 4, "elite": 5}

# Inizializza punteggi per le macro aree
punteggi = {"forza": [], "ginnastica": [], "metabolico": []}

# Pagina: Inserisci nuovo test
if pagina == "➕ Inserisci nuovo test":
    st.subheader("➕ Inserisci un nuovo test")
    # Selezione categoria prima di esercizio
    categorie_disponibili = esercizi_df["categoria"].unique()
    categoria_selezionata = st.selectbox("Seleziona categoria", categorie_disponibili)
    esercizi_filtrati = esercizi_df[esercizi_df["categoria"] == categoria_selezionata]["esercizio"].unique()
    nome_atleta = utente['nome'] if utente['ruolo'] == 'atleta' else st.selectbox("Seleziona atleta", utenti_df[utenti_df['ruolo'] == 'atleta']['nome'].unique())
    esercizio = st.selectbox("Esercizio", esercizi_filtrati)
    tipo_valore = esercizi_df[esercizi_df["esercizio"] == esercizio]["tipo_valore"].values[0]
    genere = st.selectbox("Genere", ["Maschio", "Femmina", "Altro"], key="genere_test")  # Aggiunto campo per il genere

    if tipo_valore == "tempo":
        minuti = st.number_input("Minuti", min_value=0, max_value=59, step=1)
        secondi = st.number_input("Secondi", min_value=0, max_value=59, step=1)
        valore = f"{int(minuti):02d}:{int(secondi):02d}"
    else:
        valore = st.number_input("Valore", step=1.0)

    data_test = st.date_input("Data", value=datetime.date.today())
    peso_corporeo = utente["peso"] if utente["ruolo"] == "atleta" else st.number_input("Peso corporeo (kg)", min_value=30.0, max_value=200.0, step=0.1)

    # 🔁 BLOCCO SOSTITUITO: if st.button("Salva test"):
    if st.button("Salva test"):
        relativo = None
        if tipo_valore == "kg_rel" and peso_corporeo > 0:
            relativo = round(float(valore) / float(peso_corporeo), 2)

        nuovo_test = {
            "nome": nome_atleta,
            "esercizio": esercizio,
            "valore": valore,
            "tipo_valore": tipo_valore,
            "peso_corporeo": peso_corporeo,
            "relativo": relativo,
            "data": data_test.strftime("%Y-%m-%d"),
            "genere": genere
        }
        test_df = pd.concat([test_df, pd.DataFrame([nuovo_test])], ignore_index=True)
        test_df.to_csv("fitness_app/test.csv", index=False)
        st.success("Test salvato correttamente!")

        # Feedback intelligente
        test_utente = test_df[(test_df["nome"] == nome_atleta) & (test_df["esercizio"] == esercizio)]
        test_utente["data"] = pd.to_datetime(test_utente["data"])
        test_utente = test_utente.sort_values("data")

        # Calcolo valore attuale
        if tipo_valore == "tempo":
            val_attuale = int(minuti) * 60 + int(secondi)
        elif tipo_valore == "kg_rel":
            val_attuale = relativo
        else:
            val_attuale = float(valore)

        # Recupera benchmark
        benchmark = benchmark_df[
            (benchmark_df["esercizio"] == esercizio) &
            (benchmarkDf["genere"] == genere)
        ]
        benchmark = benchmark.squeeze() if not benchmark.empty else None

        livello_raggiunto = "Non valutabile"
        livello_prossimo = None
        target_prossimo = None

        if benchmark is not None:
            soglie = ["base", "principiante", "intermedio", "buono", "elite"]
            valori = []
            for soglia in soglie:
                valore_raw = benchmark[soglia]
                if tipo_valore == "tempo" and ":" in str(valore_raw):
                    m, s = map(int, valore_raw.split(":"))
                    valori.append(m * 60 + s)
                else:
                    valori.append(float(valore_raw))

            # Determina il livello attuale
            for i, soglia in enumerate(reversed(soglie)):
                if (tipo_valore == "tempo" and val_attuale <= valori[-(i+1)]) or (tipo_valore != "tempo" and val_attuale >= valori[-(i+1)]):
                    livello_raggiunto = soglia.capitalize()
                    if i != 0:
                        livello_prossimo = soglie[-(i)]  # livello appena superiore
                        target_prossimo = valori[-(i)]
                    break

        st.info(f"🎯 Hai raggiunto il livello **{livello_raggiunto}** nel test di **{esercizio}**.")
        if livello_prossimo and target_prossimo:
            st.warning(f"➡️ Obiettivo consigliato: livello **{livello_prossimo.capitalize()}** ({target_prossimo}).")
        st.caption(f"📅 Ripeti il test tra circa **6 settimane** ({(data_test + datetime.timedelta(weeks=6)).strftime('%d/%m/%Y')}).")

        # Miglioramento percentuale rispetto al test precedente
        if len(test_utente) > 1:
            penultimo = test_utente.iloc[-2]
            if tipo_valore == "tempo":
                m, s = map(int, str(penultimo["valore"]).split(":"))
                val_prec = m * 60 + s
            elif tipo_valore == "kg_rel":
                val_prec = penultimo["relativo"]
            else:
                val_prec = float(penultimo["valore"])

            if val_prec and val_prec != 0:
                if tipo_valore == "tempo":
                    delta = val_prec - val_attuale
                    miglioramento = (delta / val_prec) * 100
                else:
                    delta = val_attuale - val_prec
                    miglioramento = (delta / val_prec) * 100
                st.success(f"📈 Miglioramento del **{miglioramento:.2f}%** rispetto al test precedente.")

                # Badge sbloccato
                if livello_raggiunto != "Non valutabile":
                    if livelli_val.get(livello_raggiunto.lower(), 0) > livelli_val.get(penultimo.get("livello", "").lower(), 0):
                        st.balloons()
                        st.success("🏅 Hai sbloccato un nuovo badge di livello!")

    # Mostra l'expander solo dopo il salvataggio
    if st.session_state.get('show_expander', False):
        with st.expander("📊 Analisi del test appena inserito", expanded=True):
            # 1. Calcola livello raggiunto
            benchmark = benchmark_df[
                (benchmarkDf['esercizio'].astype(str).str.strip() == str(esercizio).strip()) &
                (benchmarkDf['genere'].astype(str).str.strip() == str(genere).strip())
            ]
            benchmark = benchmark.squeeze() if not benchmark.empty else None
            livello_raggiunto = "Non valutabile"
            livello_num = 0
            prossimo_livello = None
            valore_target = None
            livelli_val = {"base": 1, "principiante": 2, "intermedio": 3, "buono": 4, "elite": 5}
            livelli_ordine = list(livelli_val.keys())
            val = None
            if benchmark is not None and isinstance(benchmark, pd.Series):
                tipo = benchmark['tipo_valore']
                try:
                    peso_corporeo = float(peso_corporeo)
                except Exception:
                    peso_corporeo = None
                if tipo == 'kg_rel' and peso_corporeo and peso_corporeo != 0:
                    try:
                        val = float(valore) / peso_corporeo
                    except Exception:
                        val = None
                elif tipo == 'reps' or tipo == 'valore':
                    try:
                        val = float(valore)
                    except Exception:
                        val = None
                elif tipo == 'tempo':
                    try:
                        m, s = map(int, str(valore).split(":"))
                        val = m * 60 + s
                        benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                            lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]) if ":" in str(x) else float(x)
                            if pd.notnull(x) else x
                        )
                    except Exception:
                        val = None
                else:
                    try:
                        val = float(valore)
                    except Exception:
                        val = None

                # Trova livello raggiunto
                livello_nome_trovato = None
                if tipo == 'tempo':
                    for livello_nome in reversed(livelli_ordine):
                        soglia = benchmark[livello_nome]
                        if isinstance(soglia, str) and ":" in soglia:
                            m, s = map(int, soglia.split(":"))
                            soglia = m * 60 + s
                        else:
                            soglia = float(soglia)
                        if val is not None and val <= soglia:
                            livello_nome_trovato = livello_nome.capitalize()
                            livello_num = livelli_val[livello_nome]
                            break
                else:
                    for livello_nome in reversed(livelli_ordine):
                        soglia = benchmark[livello_nome]
                        if isinstance(soglia, str):
                            soglia = float(soglia)
                        if val is not None and val >= soglia:
                            livello_nome_trovato = livello_nome.capitalize()
                            livello_num = livelli_val[livello_nome]
                            break
                livello_raggiunto = livello_nome_trovato if livello_nome_trovato else "Non valutabile"

                # 2. Consiglia prossimo livello e valore target
                if livello_nome_trovato and livello_nome_trovato.lower() != "elite":
                    idx = livelli_ordine.index(livello_nome_trovato.lower())
                    if idx < len(livelli_ordine) - 1:
                        prossimo_livello = livelli_ordine[idx + 1].capitalize()
                        valore_target = benchmark[livelli_ordine[idx + 1]]
                        if tipo == 'tempo' and isinstance(valore_target, (int, float)):
                            minuti = int(valore_target) // 60
                            secondi = int(valore_target) % 60
                            valore_target = f"{minuti:02d}:{secondi:02d}"
                elif livello_nome_trovato and livello_nome_trovato.lower() == "elite":
                    prossimo_livello = None
                    valore_target = None

            # Mostra risultati analisi post-salvataggio
            st.info(f"**Livello raggiunto:** {livello_raggiunto}")
            if prossimo_livello and valore_target is not None:
                st.info(f"🎯 Obiettivo prossimo livello: **{prossimo_livello}** (target: {valore_target})")
            elif livello_raggiunto == "Elite":
                st.success("🏆 Complimenti! Hai raggiunto il livello massimo (Elite).")

            # 3. Suggerisci quando ripetere il test (6 settimane)
            data_prossimo_test = data_test + datetime.timedelta(weeks=6)
            st.info(f"🔁 Ripeti questo test il: **{data_prossimo_test.strftime('%Y-%m-%d')}**")

            # 4. Calcola miglioramento percentuale rispetto al test precedente
            storico = test_df[
                (test_df['nome'] == nome_atleta) &
                (test_df['esercizio'] == esercizio) &
                (test_df['data'] < data_test.strftime("%Y-%m-%d"))
            ].sort_values("data", ascending=False)
            miglioramento = None
            badge = False
            if not storico.empty:
                row_prec = storico.iloc[0]
                # Calcola valore precedente
                val_prec = None
                if tipo_valore == 'kg_rel' and float(row_prec['peso_corporeo']) > 0:
                    val_prec = float(row_prec['valore']) / float(row_prec['peso_corporeo'])
                elif tipo_valore == 'reps' or tipo_valore == 'valore':
                    val_prec = float(row_prec['valore'])
                elif tipo_valore == 'tempo':
                    m, s = map(int, str(row_prec['valore']).split(":"))
                    val_prec = m * 60 + s
                else:
                    val_prec = float(row_prec['valore'])

                # Calcola miglioramento percentuale (attenzione: per il tempo, meno è meglio)
                if val is not None and val_prec is not None:
                    if tipo_valore == 'tempo':
                        miglioramento = (val_prec - val) / val_prec * 100 if val_prec > 0 else None
                    else:
                        miglioramento = (val - val_prec) / val_prec * 100 if val_prec > 0 else None
                    if miglioramento is not None:
                        st.info(f"📈 Miglioramento rispetto al test precedente: **{miglioramento:+.2f}%**")

                # 5. Badge se migliora di livello
                livello_prec = None
                if benchmark is not None and isinstance(benchmark, pd.Series):
                    # ...existing code for livello_prec_nome...
                    if livello_nome_trovato and livello_prec_nome:
                        if livelli_val[livello_nome_trovato.lower()] > livelli_val[livello_prec_nome]:
                            badge = True
                if badge:
                    st.success("🎉 **Complimenti! Hai sbloccato un nuovo livello!**")

            # Alla fine, resetta il flag per non mostrare l'expander al prossimo caricamento
            st.session_state['show_expander'] = False

# Pagina: Dashboard Atleta
elif pagina == "📈 Dashboard Atleta":
    st.subheader("📈 Dashboard Atleta")
    atleta_test = test_df[test_df['nome'] == utente['nome']]
    latest_tests = atleta_test.sort_values("data").groupby("esercizio").tail(1)

    for _, row in latest_tests.iterrows():
        benchmark = benchmark_df[benchmark_df['esercizio'] == row['esercizio']]
        benchmark = benchmark.squeeze() if not benchmark.empty else None
        livello = "Non valutabile"

        if benchmark is not None:
            tipo = benchmark['tipo_valore']
            if tipo == 'kg_rel' and pd.notnull(row['relativo']):
                val = float(row['relativo'])
            elif tipo == 'reps':
                val = float(row['valore'])
            elif tipo == 'tempo':
                # Converti il valore in secondi
                m, s = map(int, str(row['valore']).split(":"))
                val = m * 60 + s
                # Converti i valori del benchmark in secondi
                if isinstance(benchmark, pd.Series):
                    benchmark['base'] = float(benchmark['base']) if ":" not in str(benchmark['base']) else int(benchmark['base'].split(":")[0]) * 60 + int(benchmark['base'].split(":")[1])
                    benchmark['elite'] = float(benchmark['elite']) if ":" not in str(benchmark['elite']) else int(benchmark['elite'].split(":")[0]) * 60 + int(benchmark['elite'].split(":")[1])
            else:
                val = float(row['valore'])

            for livello_nome in reversed(list(livelli_val.keys())) if tipo == 'tempo' else livelli_val:
                soglia_min = float(benchmark['base']) if isinstance(benchmark, pd.Series) else float(benchmark['base'].iloc[0])
                soglia_max = float(benchmark['elite']) if isinstance(benchmark, pd.Series) else float(benchmark['elite'].iloc[0])
                if tipo == 'tempo':
                    if soglia_min <= val <= soglia_max:
                        livello = benchmark['tipo_valore'] if isinstance(benchmark, pd.Series) else benchmark['tipo_valore'].iloc[0]
                        break
                else:
                    if soglia_min <= val <= soglia_max:
                        livello = benchmark['tipo_valore'] if isinstance(benchmark, pd.Series) else benchmark['tipo_valore'].iloc[0]
                        break

        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric(f"{row['esercizio']}", row['valore'], help=f"Livello: {livello}")
        with col2:
            if row['tipo_valore'] == 'kg_rel':
                st.text(f"Forza relativa: {row['relativo']}")

# Pagina: Storico Dati
elif pagina == "📜 Storico Dati":
    st.subheader("📜 Storico Dati")
    atleta_test = test_df[test_df['nome'] == utente['nome']]

    if atleta_test.empty:
        st.info("Non ci sono test disponibili per questo utente.")
    else:
        # Calcola dinamicamente il livello per ogni esercizio
        livelli = []
        for _, row in atleta_test.iterrows():
            benchmark = benchmark_df[benchmark_df['esercizio'] == row['esercizio']]
            benchmark = benchmark.squeeze() if not benchmark.empty else None
            livello = "Non valutabile"

            if benchmark is not None:
                tipo = benchmark['tipo_valore']
                if tipo == 'kg_rel' and pd.notnull(row['peso_corporeo']):
                    val = float(row['valore']) / float(row['peso_corporeo'])
                elif tipo == 'reps' or tipo == 'valore':
                    val = float(row['valore'])
                elif tipo == 'tempo':
                    m, s = map(int, str(row['valore']).split(":"))
                    val = m * 60 + s
                    # Filtra solo le colonne pertinenti per il confronto
                    benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                        lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]) if ":" in str(x) else float(x)
                        if pd.notnull(x) else x
                    )
                else:
                    val = float(row['valore'])

                for livello_nome in reversed(list(livelli_val.keys())) if tipo == 'tempo' else livelli_val:
                    soglia = benchmark[livello_nome]
                    if isinstance(soglia, str):  # Converte soglia in float se è una stringa
                        soglia = float(soglia)
                    if tipo == 'tempo':
                        if val <= soglia:
                            livello = livello_nome.capitalize()
                            break
                    else:
                        if val >= soglia:
                            livello = livello_nome.capitalize()
                            break

            livelli.append(livello)

        # Aggiungi i livelli calcolati allo storico
        atleta_test['livello'] = livelli
        st.dataframe(atleta_test)

        # Pulsante per eliminare un test
        atleta_test['info'] = atleta_test.apply(
            lambda row: f"Esercizio: {row['esercizio']} | Data: {row['data']} | Valore: {row['valore']} | Tipo: {row['tipo_valore']}", axis=1
        )
        test_da_eliminare = st.selectbox("Seleziona un test da eliminare", atleta_test['info'])
        if st.button("Elimina test"):
            index_to_delete = atleta_test[atleta_test['info'] == test_da_eliminare].index[0]
            test_df = test_df.drop(index=index_to_delete)
            test_df.to_csv("fitness_app/test.csv", index=False)
            st.success("Test eliminato con successo!")
            st.query_params = {"refresh": "true"}  # Simula un aggiornamento della pagina

    # Genera un grafico radar per lo stato dell'atleta
    st.subheader("📊 Stato dell'Atleta")
    radar_labels = []
    radar_values = []
    for categoria in punteggi.keys():
        categoria_tests = atleta_test[atleta_test['esercizio'].isin(esercizi_df[esercizi_df['categoria'] == categoria]['esercizio'])]
        if not categoria_tests.empty:
            categoria_livelli = categoria_tests['livello'].map(lambda x: livelli_val.get(x.lower(), 0))
            radar_labels.append(categoria.capitalize())
            radar_values.append(round(categoria_livelli.mean(), 2) if not categoria_livelli.empty else 0)

    if radar_labels:
        fig = go.Figure(data=go.Scatterpolar(
            r=radar_values,
            theta=radar_labels,
            fill='toself'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# Pagina: Grafici (grafico a barre orizzontali per risultati esercizi)
elif pagina == "📊 Grafici":
    st.subheader("📊 Risultati esercizi (Grafico a barre orizzontali)")

    # Selezione categoria prima di esercizio
    categorie_disponibili = esercizi_df["categoria"].unique()
    categoria_selezionata = st.selectbox("Seleziona categoria", categorie_disponibili)
    esercizi_filtrati = esercizi_df[esercizi_df["categoria"] == categoria_selezionata]["esercizio"].unique()
    esercizio_selezionato = st.selectbox("Seleziona esercizio", esercizi_filtrati)

    atleta_test = test_df[(test_df['nome'] == utente['nome']) & (test_df['esercizio'] == esercizio_selezionato)]

    # Calcola i livelli se non presenti
    if not atleta_test.empty:
        livelli = []
        valori_barra = []
        etichette_barra = []
        for _, row in atleta_test.iterrows():
            genere_row = row['genere'] if 'genere' in row and pd.notnull(row['genere']) else utente['genere']
            benchmark = benchmark_df[
                (benchmark_df['esercizio'] == row['esercizio']) &
                (benchmark_df['genere'] == genere_row)
            ]
            benchmark = benchmark.squeeze() if not benchmark.empty else None
            livello = "Non valutabile"
            val = None
            max_val = None
            min_val = None
            if benchmark is not None and isinstance(benchmark, pd.Series):
                tipo = benchmark['tipo_valore']
                try:
                    peso_corporeo = float(row['peso_corporeo'])
                except Exception:
                    peso_corporeo = None
                # Calcolo valore per la barra
                if tipo == 'kg_rel' and peso_corporeo is not None and not pd.isna(peso_corporeo) and peso_corporeo != 0:
                    try:
                        val = float(row['valore']) / peso_corporeo
                    except Exception:
                        val = None
                elif tipo == 'reps' or tipo == 'valore':
                    try:
                        val = float(row['valore'])
                    except Exception:
                        val = None
                elif tipo == 'tempo':
                    try:
                        m, s = map(int, str(row['valore']).split(":"))
                        val = m * 60 + s
                        benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                            lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]) if ":" in str(x) else float(x)
                            if pd.notnull(x) else x
                        )
                    except Exception:
                        val = None
                else:
                    try:
                        val = float(row['valore'])
                    except Exception:
                        val = None

                # Trova livello e prepara valori per la barra
                livello_num = 0
                if tipo == 'tempo':
                    # Ordina i livelli dal più difficile (elite) al più facile (base)
                    livelli_ordine = list(reversed(list(livelli_val.keys())))
                    for livello_nome in livelli_ordine:
                        soglia = benchmark[livello_nome]
                        # Converte soglia in secondi se necessario
                        if isinstance(soglia, str) and ":" in soglia:
                            m, s = map(int, soglia.split(":"))
                            soglia = m * 60 + s
                        else:
                            soglia = float(soglia)
                        if val is not None and val <= soglia:
                            livello = livello_nome.capitalize()
                            livello_num = livelli_val[livello_nome]
                            break
                    try:
                        progresso = livello_num / max(livelli_val.values())
                    except Exception:
                        progresso = 0
                else:
                    for livello_nome in reversed(list(livelli_val.keys())):
                        soglia = benchmark[livello_nome]
                        if isinstance(soglia, str):
                            soglia = float(soglia)
                        if val is not None and val >= soglia:
                            livello = livello_nome.capitalize()
                            livello_num = livelli_val[livello_nome]
                            break
                    try:
                        progresso = livello_num / max(livelli_val.values())
                    except Exception:
                        progresso = 0
            else:
                progresso = 0

            livelli.append(livello)
            valori_barra.append(progresso)
            etichette_barra.append(f"{row['valore']} ({livello})")

        # Visualizzazione grafico a barra singola
        if valori_barra:
            st.write(f"**Livello raggiunto:** {livelli[-1]}")
            st.write(f"**Valore inserito:** {row['valore']}")
            st.progress(valori_barra[-1], text=f"Progresso verso Elite: {int(valori_barra[-1]*100)}%")
            # Barra orizzontale con Plotly per chiarezza
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=[valori_barra[-1]*100],
                y=[esercizio_selezionato],
                orientation='h',
                marker=dict(
                    color='rgba(0, 123, 255, 0.7)',
                    line=dict(color='rgba(0, 123, 255, 1.0)', width=8)
                ),
                text=[f"{row['valore']} ({livelli[-1]})"],
                textposition='outside'
            ))
            fig.update_layout(
                xaxis=dict(range=[0, 100], title="Progresso verso Elite (%)"),
                yaxis=dict(title="Esercizio"),
                title=f"Progresso su {esercizio_selezionato}",
                bargap=0.4,
                height=200
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Non ci sono dati sufficienti per mostrare il grafico.")

    # Grafico radar per atleta (tutte le macro-categorie)
    if utente['ruolo'] == 'atleta':
        st.subheader("📊 Profilo Radar: Tutte le Macro-Categorie")
        tutte_categorie = esercizi_df["categoria"].unique()
        radar_labels = []
        radar_values = []
        for categoria in tutte_categorie:
            esercizi_cat = esercizi_df[esercizi_df['categoria'] == categoria]['esercizio']
            test_cat = test_df[(test_df['nome'] == utente['nome']) & (test_df['esercizio'].isin(esercizi_cat))]
            livelli_cat = []
            for _, row in test_cat.iterrows():
                benchmark = benchmark_df[
                    (benchmark_df['esercizio'] == row['esercizio']) &
                    (benchmark_df['genere'] == row['genere'])
                ]
                benchmark = benchmark.squeeze() if not benchmark.empty else None
                livello_num = 0
                if benchmark is not None and isinstance(benchmark, pd.Series):
                    tipo = benchmark['tipo_valore']
                    try:
                        peso_corporeo = float(row['peso_corporeo'])
                    except Exception:
                        peso_corporeo = None
                    if tipo == 'kg_rel' and peso_corporeo is not None and not pd.isna(peso_corporeo) and peso_corporeo != 0:
                        try:
                            val = float(row['valore']) / peso_corporeo
                        except Exception:
                            val = None
                    elif tipo == 'reps' or tipo == 'valore':
                        try:
                            val = float(row['valore'])
                        except Exception:
                            val = None
                    elif tipo == 'tempo':
                        try:
                            m, s = map(int, str(row['valore']).split(":"))
                            val = m * 60 + s
                            benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                                lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]) if ":" in str(x) else float(x)
                                if pd.notnull(x) else x
                            )
                        except Exception:
                            val = None
                    else:
                        try:
                            val = float(row['valore'])
                        except Exception:
                            val = None

                    if tipo == 'tempo':
                        livelli_ordine = list(reversed(list(livelli_val.keys())))
                        for livello_nome in livelli_ordine:
                            soglia = benchmark[livello_nome]
                            if isinstance(soglia, str) and ":" in soglia:
                                m, s = map(int, soglia.split(":"))
                                soglia = m * 60 + s
                            else:
                                soglia = float(soglia)
                            if val is not None and val <= soglia:
                                livello_num = livelli_val[livello_nome]
                                break
                    else:
                        for livello_nome in reversed(list(livelli_val.keys())):
                            soglia = benchmark[livello_nome]
                            if isinstance(soglia, str):
                                soglia = float(soglia)
                            if val is not None and val >= soglia:
                                livello_num = livelli_val[livello_nome]
                                break
                livelli_cat.append(livello_num)
            if livelli_cat:
                radar_labels.append(categoria.capitalize())
                radar_values.append(round(sum(livelli_cat) / len(livelli_cat), 2))
        if radar_labels:
            fig = go.Figure(data=go.Scatterpolar(
                r=radar_values,
                theta=radar_labels,
                fill='toself',
                marker=dict(color='rgba(0,123,255,0.7)')
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=False,
                title="Profilo Radar per Macro-Categoria",
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            # Miglioria: mostra valori numerici accanto alle etichette
            for label, value in zip(radar_labels, radar_values):
                st.write(f"**{label}**: {value}/5")
        else:
            st.info("Non ci sono dati sufficienti per generare il grafico radar.")

# Pagina: Profilo Fitness per Area
elif pagina == "📊 Profilo Fitness per Area":
    st.subheader("📊 Profilo Fitness per Area")
    
    # Seleziona esercizi da visualizzare
    esercizi_selezionati = st.multiselect(
        "Seleziona esercizi",
        options=esercizi_df["esercizio"].unique(),
        default=esercizi_df["esercizio"].unique()
    )
    
    # Filtra i test dell'atleta per gli esercizi selezionati
    atleta_test = test_df[(test_df['nome'] == utente['nome']) & (test_df['esercizio'].isin(esercizi_selezionati))]
    
    # Calcola il livello per ogni esercizio
    livelli = []
    for _, row in atleta_test.iterrows():
        benchmark = benchmark_df[benchmark_df['esercizio'] == row['esercizio']]
        benchmark = benchmark.squeeze() if not benchmark.empty else None
        livello = "Non valutabile"

        if benchmark is not None:
            tipo = benchmark['tipo_valore']
            if tipo == 'kg_rel' and pd.notnull(row['peso_corporeo']):
                val = float(row['valore']) / float(row['peso_corporeo'])
            elif tipo == 'reps' or tipo == 'valore':
                val = float(row['valore'])
            elif tipo == 'tempo':
                m, s = map(int, str(row['valore']).split(":"))
                val = m * 60 + s
                benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                    lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]) if ":" in str(x) else float(x)
                    if pd.notnull(x) else x
                )
            else:
                val = float(row['valore'])

            for livello_nome in reversed(list(livelli_val.keys())):
                soglia = benchmark[livello_nome]
                if isinstance(soglia, str):
                    soglia = float(soglia)
                if tipo == 'tempo':
                    if val <= soglia:
                        livello = livello_nome.capitalize()
                        break
                else:
                    if val >= soglia:
                        livello = livello_nome.capitalize()
                        break

        livelli.append((row['esercizio'], livello))

    # Genera il grafico a barre orizzontali
    if livelli:
        df_livelli = pd.DataFrame(livelli, columns=["Esercizio", "Livello"])
        livello_mapping = {"Base": 1, "Principiante": 2, "Intermedio": 3, "Buono": 4, "Elite": 5}
        df_livelli["Livello Numerico"] = df_livelli["Livello"].map(livello_mapping)

        fig = go.Figure(go.Bar(
            x=df_livelli["Livello Numerico"],
            y=df_livelli["Esercizio"],
            orientation='h',
            text=df_livelli["Livello"],
            textposition='auto'
        ))
        fig.update_layout(
            xaxis=dict(
                tickvals=list(livello_mapping.values()),
                ticktext=list(livello_mapping.keys()),
                title="Livello"
            ),
            yaxis=dict(title="Esercizio"),
            title="Livello per Esercizio"
        )
        st.plotly_chart(fig, use_container_width=True)

# Pagina: Profilo Atleta
elif pagina == "👤 Profilo Atleta":

    # Carica i dati dell'atleta
    atleta = utenti_df[utenti_df['nome'] == utente['nome']].squeeze()

    # Mostra i dati attuali
    st.write("### Dati attuali:")
    st.write(f"**Nome:** {atleta['nome']}")
    st.write(f"**Ruolo:** {atleta['ruolo']}")
    st.write(f"**Data di nascita:** {atleta['data_nascita']}")
    st.write(f"**Peso corporeo:** {atleta['peso']} kg")
    st.write(f"**Genere:** {atleta['genere']}")

    # Modifica i dati
    st.write("### Modifica i tuoi dati:")
    data_nascita_default = pd.to_datetime(atleta['data_nascita']) if pd.notnull(atleta['data_nascita']) else datetime.date(2000, 1, 1)
    nuova_data_nascita = st.date_input(
        "Data di nascita",
        value=data_nascita_default,
        min_value=datetime.date(1960, 1, 1)
    )
    nuovo_peso = st.number_input("Peso corporeo (kg)", min_value=30.0, max_value=200.0, step=0.1, value=float(atleta['peso']) if pd.notnull(atleta['peso']) else 70.0)
    nuovo_genere = st.selectbox(
        "Genere",
        options=["Maschio", "Femmina", "Altro"],
        index=["Maschio", "Femmina", "Altro"].index(atleta['genere']) if atleta['genere'] in ["Maschio", "Femmina", "Altro"] else 0
    )

    if st.button("Salva modifiche"):
        # Aggiorna i dati nel DataFrame
        utenti_df.loc[utenti_df['nome'] == utente['nome'], 'data_nascita'] = nuova_data_nascita.strftime("%Y-%m-%d")
        utenti_df.loc[utenti_df['nome'] == utente['nome'], 'peso'] = nuovo_peso
        utenti_df.loc[utenti_df['nome'] == utente['nome'], 'genere'] = nuovo_genere

        # Salva i dati aggiornati nel file CSV
        utenti_df.to_csv("fitness_app/utenti.csv", index=False)
        st.success("Dati aggiornati con successo!")

# Pagina: Gestione Esercizi (solo per coach)
if pagina == "⚙️ Gestione Esercizi" and utente['ruolo'] == 'coach':
    st.subheader("⚙️ Gestione Esercizi")
    st.info("Sei nell'area riservata ai coach.")

    # Visualizza gli esercizi esistenti
    st.write("### Esercizi esistenti:")
    st.dataframe(esercizi_df)

    # Aggiungi un nuovo esercizio
    st.write("### Aggiungi un nuovo esercizio:")
    nuovo_esercizio = st.text_input("Nome esercizio")
    categoria = st.selectbox("Categoria", ["forza", "ginnastica", "metabolico"])
    tipo_valore = st.selectbox("Tipo di valore", ["kg", "kg_rel", "reps", "tempo", "valore"])

    if st.button("Aggiungi esercizio"):
        if nuovo_esercizio and categoria and tipo_valore:
            nuovo_record = {"esercizio": nuovo_esercizio, "categoria": categoria, "tipo_valore": tipo_valore}
            esercizi_df = pd.concat([esercizi_df, pd.DataFrame([nuovo_record])], ignore_index=True)
            esercizi_df.to_csv("fitness_app/esercizi.csv", index=False)
            st.success("Esercizio aggiunto con successo!")
        else:
            st.error("Compila tutti i campi per aggiungere un esercizio.")

    # Elimina un esercizio esistente
    st.write("### Elimina un esercizio:")
    esercizio_da_eliminare = st.selectbox("Seleziona un esercizio da eliminare", esercizi_df["esercizio"])

    if st.button("Elimina esercizio"):
        esercizi_df = esercizi_df[esercizi_df["esercizio"] != esercizio_da_eliminare]
        esercizi_df.to_csv("fitness_app/esercizi.csv", index=False)
        st.success("Esercizio eliminato con successo!")

    # Elimina i dati di tutti gli utenti
    st.write("### Elimina i dati di tutti gli utenti:")
    if st.button("Elimina tutti i dati utenti", key="elimina_tutti_utenti"):
        utenti_df = utenti_df.iloc[0:0]  # Rimuove tutti i dati mantenendo le colonne
        utenti_df.to_csv("fitness_app/utenti.csv", index=False)
        st.success("Tutti i dati degli utenti sono stati eliminati con successo!")

# Pagina: Gestione Benchmark (solo per coach)
if pagina == "⚙️ Gestione Benchmark" and utente['ruolo'] == 'coach':
    st.subheader("⚙️ Gestione Benchmark")
    st.info("Sei nell'area riservata ai coach per gestire i dati di benchmark.")

    # Visualizza i benchmark esistenti
    st.write("### Benchmark esistenti:")
    st.dataframe(benchmark_df)

    # Aggiungi un nuovo benchmark
    st.write("### Aggiungi un nuovo benchmark:")
    nuovo_esercizio = st.selectbox("Esercizio", esercizi_df["esercizio"].unique(), key="aggiungi_esercizio")
    genere = st.selectbox("Genere", ["Maschio", "Femmina", "Altro"], key="aggiungi_genere")
    base = st.text_input("Base", key="aggiungi_base")
    principiante = st.text_input("Principiante", key="aggiungi_principiante")
    intermedio = st.text_input("Intermedio", key="aggiungi_intermedio")
    buono = st.text_input("Buono", key="aggiungi_buono")
    elite = st.text_input("Elite", key="aggiungi_elite")

    if st.button("Aggiungi benchmark", key="aggiungi_benchmark_button"):
        if nuovo_esercizio and tipo_valore and genere and base and principiante and intermedio and buono and elite:
            nuovo_record = {
                "esercizio": nuovo_esercizio,
                "tipo_valore": tipo_valore,
                "genere": genere,
                "base": base,
                "principiante": principiante,
                "intermedio": intermedio,
                "buono": buono,
                "elite": elite
            }
            benchmark_df = pd.concat([benchmark_df, pd.DataFrame([nuovo_record])], ignore_index=True)
            benchmark_df.to_csv("fitness_app/benchmark.csv", index=False)
            st.success("Nuovo benchmark aggiunto con successo!")
        else:
            st.error("Compila tutti i campi per aggiungere un benchmark.")

    # Elimina un benchmark esistente
    st.write("### Elimina un benchmark:")
    benchmark_da_eliminare = st.selectbox("Seleziona un benchmark da eliminare", benchmark_df[["esercizio", "genere"]].apply(lambda x: f"{x['esercizio']} ({x['genere']})", axis=1), key="elimina_benchmark")

    if st.button("Elimina benchmark", key="elimina_benchmark_button"):
        esercizio, genere = benchmark_da_eliminare.rsplit(" (", 1)
        genere = genere.rstrip(")")
        benchmark_df = benchmark_df[~((benchmark_df["esercizio"] == esercizio) & (benchmark_df["genere"] == genere))]
        benchmark_df.to_csv("fitness_app/benchmark.csv", index=False)
        st.success("Benchmark eliminato con successo!")

    # Modifica un benchmark esistente
    st.write("### Modifica un benchmark esistente:")
    benchmark_da_modificare = st.selectbox("Seleziona un benchmark da modificare", benchmark_df[["esercizio", "genere"]].apply(lambda x: f"{x['esercizio']} ({x['genere']})", axis=1), key="modifica_benchmark")
    if benchmark_da_modificare:
        esercizio, genere = benchmark_da_modificare.rsplit(" (", 1)
        genere = genere.rstrip(")")
        benchmark_selezionato = benchmark_df[(benchmark_df["esercizio"] == esercizio) & (benchmark_df["genere"] == genere)].iloc[0]
        nuovo_tipo_valore = st.selectbox("Tipo di valore", ["kg", "kg_rel", "reps", "tempo", "valore"], index=["kg", "kg_rel", "reps", "tempo", "valore"].index(benchmark_selezionato["tipo_valore"]), key="modifica_tipo_valore")
        nuovo_genere = st.selectbox("Genere", ["Maschio", "Femmina", "Altro"], index=["Maschio", "Femmina", "Altro"].index(benchmark_selezionato["genere"]), key="modifica_genere")
        nuovo_base = st.text_input("Base", value=benchmark_selezionato["base"], key="modifica_base")
        nuovo_principiante = st.text_input("Principiante", value=benchmark_selezionato["principiante"], key="modifica_principiante")
        nuovo_intermedio = st.text_input("Intermedio", value=benchmark_selezionato["intermedio"], key="modifica_intermedio")
        nuovo_buono = st.text_input("Buono", value=benchmark_selezionato["buono"], key="modifica_buono")
        nuovo_elite = st.text_input("Elite", value=benchmark_selezionato["elite"], key="modifica_elite")

        if st.button("Salva modifiche", key="salva_modifiche_benchmark"):
            benchmark_df.loc[(benchmark_df["esercizio"] == esercizio) & (benchmark_df["genere"] == genere), ["tipo_valore", "genere", "base", "principiante", "intermedio", "buono", "elite"]] = [
                nuovo_tipo_valore, nuovo_genere, nuovo_base, nuovo_principiante, nuovo_intermedio, nuovo_buono, nuovo_elite
            ]
            benchmark_df.to_csv("fitness_app/benchmark.csv", index=False)
            st.success("Benchmark modificato con successo!")

# Pagina: Aggiungi Utente (solo per coach)
if pagina == "➕ Aggiungi Utente" and utente['ruolo'] == 'coach':
    st.subheader("➕ Aggiungi un nuovo utente")

    # Mostra tutti gli utenti esistenti
    st.write("### Utenti esistenti:")
    st.dataframe(utenti_df)

    # Mostra solo i coach esistenti
    st.write("### Coach esistenti:")
    coach_df = utenti_df[utenti_df["ruolo"] == "coach"]
    st.dataframe(coach_df)

    # Seleziona un utente da eliminare
    st.write("### Elimina un utente:")
    utente_da_eliminare = st.selectbox("Seleziona un utente da eliminare", utenti_df["nome"].unique(), key="elimina_utente")

    if st.button("Elimina utente", key="elimina_utente_button"):
        # Elimina l'utente dal DataFrame degli utenti
        utenti_df = utenti_df[utenti_df["nome"] != utente_da_eliminare]
        utenti_df.to_csv("fitness_app/utenti.csv", index=False)

        # Elimina i dati dell'utente dal DataFrame dei test
        test_df = test_df[test_df["nome"] != utente_da_eliminare]
        test_df.to_csv("fitness_app/test.csv", index=False)

        st.success(f"Utente '{utente_da_eliminare}' e i suoi dati sono stati eliminati con successo!")

    # Input per i dettagli del nuovo utente (coach o atleta)
    st.write("### Aggiungi un nuovo utente:")
    nuovo_nome = st.text_input("Nome utente")
    nuovo_pin = st.text_input("PIN utente", type="password")
    nuovo_ruolo = st.selectbox("Ruolo", ["atleta", "coach"], key="aggiungi_ruolo")
    nuovo_peso = st.number_input("Peso corporeo (kg)", min_value=30.0, max_value=200.0, step=0.1, key="aggiungi_peso")
    nuova_data_nascita = st.date_input(
        "Data di nascita",
        value=datetime.date(2000, 1, 1),
        min_value=datetime.date(1960, 1, 1),
        key="aggiungi_data_nascita"
    )
    nuovo_genere = st.selectbox("Genere", ["Maschio", "Femmina", "Altro"], key="aggiungi_genere_utente")

    if st.button("Aggiungi utente", key="aggiungi_utente_button"):
        if nuovo_nome and nuovo_pin:
            nuovo_utente = {
                "nome": nuovo_nome,
                "pin": nuovo_pin,
                "ruolo": nuovo_ruolo,
                "peso": nuovo_peso,
                "data_nascita": nuova_data_nascita.strftime("%Y-%m-%d"),
                "genere": nuovo_genere
            }
            utenti_df = pd.concat([utenti_df, pd.DataFrame([nuovo_utente])], ignore_index=True)
            utenti_df.to_csv("fitness_app/utenti.csv", index=False)
            st.success(f"Nuovo utente '{nuovo_nome}' aggiunto con successo come {nuovo_ruolo}!")
        else:
            st.error("Compila tutti i campi richiesti.")

# Pagina: Storico Dati Utenti (solo per coach)
if pagina == "📋 Storico Dati Utenti" and utente['ruolo'] == 'coach':
    st.subheader("📋 Storico Dati Utenti")
    st.write("### Risultati di tutti i test:")
    st.dataframe(test_df)

    # Opzione per filtrare i test per utente
    st.write("### Filtra per utente:")
    utente_selezionato = st.selectbox("Seleziona un utente", utenti_df["nome"].unique(), key="filtra_utente")
    test_filtrati = test_df[test_df["nome"] == utente_selezionato]

    if test_filtrati.empty:
        st.info(f"Non ci sono test disponibili per l'utente '{utente_selezionato}'.")
    else:
        st.write(f"### Test di {utente_selezionato}:")
        st.dataframe(test_filtrati)

# Pagina: Aree di Performance
if pagina == "📊 Bilanciamento Atleti" and utente['ruolo'] == 'coach':
    st.subheader("📊 Aree di Performance")

    # Calcola i punteggi medi per ogni categoria
    radar_labels = []
    radar_values = []
    for categoria in punteggi.keys():
        categoria_tests = test_df[test_df['esercizio'].isin(esercizi_df[esercizi_df['categoria'] == categoria]['esercizio'])]
        if not categoria_tests.empty:
            # Gestione dei valori di tipo tempo
            def convert_to_seconds(val):
                if isinstance(val, str) and ":" in val:
                    m, s = map(int, val.split(":"))
                    return m * 60 + s
                return float(val)

            categoria_tests['valore_converted'] = categoria_tests['valore'].apply(convert_to_seconds)
            radar_labels.append(categoria.capitalize())
            radar_values.append(round(categoria_tests['valore_converted'].mean(), 2) if not categoria_tests['valore_converted'].empty else 0)

    # Mostra il grafico radar
    if radar_labels:
        fig = go.Figure(data=go.Scatterpolar(
            r=radar_values,
            theta=radar_labels,
            fill='toself'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(radar_values) + 1])),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Non ci sono dati sufficienti per generare il grafico radar.")

    # Grafico a barre per il bilanciamento di genere
    st.subheader("📊 Distribuzione per Genere")
    genere_counts = utenti_df['genere'].value_counts()
    fig_genere = go.Figure(data=go.Bar(
        x=genere_counts.index,
        y=genere_counts.values,
        text=genere_counts.values,
        textposition='auto'
    ))
    fig_genere.update_layout(
        xaxis_title="Genere",
        yaxis_title="Numero di Utenti",
        title="Distribuzione degli Utenti per Genere"
    )
    st.plotly_chart(fig_genere, use_container_width=True)

# Pagina: Storico Test (solo atleta)
if pagina == "📜 Storico Test" and utente['ruolo'] == 'atleta':
    st.subheader("📜 Storico dei Test Inseriti")
    atleta_test = test_df[test_df['nome'] == utente['nome']]
    if atleta_test.empty:
        st.info("Non ci sono test disponibili per questo utente.")
    else:
        st.dataframe(atleta_test.sort_values("data", ascending=False))

# Pagina: Calendario WOD
if pagina == "📅 Calendario WOD":
    st.subheader("📅 Calendario WOD (Workout Of the Day)")

    # Seleziona una data
    data_selezionata = st.date_input("Seleziona una data", value=datetime.date.today(), key="wod_date")
    data_str = data_selezionata.strftime("%Y-%m-%d")
    wod_giorno = wod_df[wod_df["data"] == data_str]

    if not wod_giorno.empty:
        st.write(f"### WOD del {data_str}")
        st.write(f"**Nome:** {wod_giorno.iloc[0]['nome']}")  # Corrected column name
        st.write(f"**Descrizione:** {wod_giorno.iloc[0]['descrizione']}")
    else:
        st.info("Nessun WOD pubblicato per questa data.")

    # Solo i coach possono aggiungere/modificare/eliminare WOD
    if utente['ruolo'] == 'coach':
        st.write("---")
        st.write("### Pubblica o modifica WOD per questa data")
        titolo_wod = st.text_input("Titolo WOD", value=wod_giorno.iloc[0]['titolo'] if not wod_giorno.empty else "")
        descrizione_wod = st.text_area("Descrizione WOD", value=wod_giorno.iloc[0]['descrizione'] if not wod_giorno.empty else "")

        if st.button("Salva/Modifica WOD", key="salva_wod"):
            # Se esiste già, aggiorna; altrimenti aggiungi
            if not wod_giorno.empty:
                wod_df.loc[wod_df["data"] == data_str, ["titolo", "descrizione"]] = [titolo_wod, descrizione_wod]
            else:
                nuovo_wod = {"data": data_str, "titolo": titolo_wod, "descrizione": descrizione_wod}
                wod_df = pd.concat([wod_df, pd.DataFrame([nuovo_wod])], ignore_index=True)
            wod_df.to_csv(wod_path, index=False)
            st.success("WOD salvato/modificato con successo!")

        if not wod_giorno.empty:
            if st.button("Elimina WOD", key="elimina_wod"):
                wod_df = wod_df[wod_df["data"] != data_str]
                wod_df.to_csv(wod_path, index=False)
                st.success("WOD eliminato con successo!")

    st.write("---")
    st.write("### Storico WOD pubblicati")
    # Modifica per gestire formati di data non standard
    wod_df["data"] = pd.to_datetime(wod_df["data"], format="%Y-%m-%d", errors="coerce")
    if wod_df["data"].isnull().any():
        st.error("Errore nel formato delle date in 'wod.csv'. Assicurati che siano nel formato 'YYYY-MM-DD'.")
        st.stop()

    wod_df = wod_df.sort_values("data", ascending=False)

    for idx, row in wod_df.iterrows():
        # Verifica che la colonna 'nome' esista, altrimenti usa un valore predefinito
        nome_wod = row['nome'] if 'nome' in row else "WOD"
        with st.expander(f"{row['data'].date()} - {nome_wod}"):
            st.markdown(f"**Descrizione:** {row['descrizione']}")
            esercizi_collegati = row['esercizi'].split(";") if 'esercizi' in row and pd.notnull(row['esercizi']) else []
            if esercizi_collegati:
                st.markdown(f"**Esercizi collegati:** {', '.join(esercizi_collegati)}")

            # Mostra test dell’atleta legati al WOD
            test_collegati = test_df[
                (test_df["nome"] == utente["nome"]) &
                (test_df["esercizio"].isin(esercizi_collegati))
            ]
            if not test_collegati.empty:
                st.markdown("📊 **Test collegati a questo WOD:**")
                st.dataframe(test_collegati[["data", "esercizio", "valore", "tipo_valore"]])
            else:
                st.info("Nessun test collegato trovato per questo WOD.")

            # Aggiungi nota personale
            st.markdown("📝 **Nota personale**")
            note_key = f"nota_{idx}_{utente['nome']}"
            nota = st.text_area("Scrivi una nota (visibile solo a te)", key=note_key)
            if st.button("Salva nota", key=f"salva_{note_key}"):
                # Salva su CSV o mostra (puoi implementare salvataggio locale più avanti)
                st.success("Nota salvata! (implementare salvataggio permanente)")

# Pagina: Storico Progressi
if pagina == "📈 Storico Progressi":
    st.subheader("📈 Storico Progressi per Esercizio")

    # Selezione esercizio
    esercizi_disponibili = test_df[test_df['nome'] == utente['nome']]['esercizio'].unique()
    if len(esercizi_disponibili) == 0:
        st.info("Non ci sono test disponibili per questo utente.")
    else:
        esercizio_sel = st.selectbox("Seleziona esercizio", esercizi_disponibili)
        dati_esercizio = test_df[(test_df['nome'] == utente['nome']) & (test_df['esercizio'] == esercizio_sel)].copy()

        # Assicurati che i dati siano ordinati per data
        dati_esercizio["data"] = pd.to_datetime(dati_esercizio["data"], format="%Y-%m-%d", errors="coerce")
        dati_esercizio = dati_esercizio.sort_values("data")

        # Calcola livello per ogni test
        livelli_val = {"base": 1, "principiante": 2, "intermedio": 3, "buono": 4, "elite": 5}
        livelli = []
        for _, row in dati_esercizio.iterrows():
            benchmark = benchmark_df[
                (benchmark_df['esercizio'] == row['esercizio']) &
                (benchmark_df['genere'] == row.get('genere', utente.get('genere', 'Maschio')))
            ]
            benchmark = benchmark.squeeze() if not benchmark.empty else None
            livello = "Non valutabile"
            val = None
            if benchmark is not None and isinstance(benchmark, pd.Series):
                tipo = benchmark['tipo_valore']
                try:
                    peso_corporeo = float(row['peso_corporeo'])
                except Exception:
                    peso_corporeo = None
                if tipo == 'kg_rel' and peso_corporeo and peso_corporeo != 0:
                    try:
                        val = float(row['valore']) / peso_corporeo
                    except Exception:
                        val = None
                elif tipo == 'reps' or tipo_valore == 'valore':
                    try:
                        val = float(row['valore'])
                    except Exception:
                        val = None
                elif tipo == 'tempo':
                    try:
                        m, s = map(int, str(row['valore']).split(":"))
                        val = m * 60 + s
                        benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                            lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]) if ":" in str(x) else float(x)
                            if pd.notnull(x) else x
                        )
                    except Exception:
                        val = None
                else:
                    try:
                        val = float(row['valore'])
                    except Exception:
                        val = None

                livello_num = 0
                livello_nome_trovato = None
                if tipo == 'tempo':
                    livelli_ordine = list(reversed(list(livelli_val.keys())))
                    for livello_nome in livelli_ordine:
                        soglia = benchmark[livello_nome]
                        if isinstance(soglia, str) and ":" in soglia:
                            m, s = map(int, soglia.split(":"))
                            soglia = m * 60 + s
                        else:
                            soglia = float(soglia)
                        if val is not None and val <= soglia:
                            livello_nome_trovato = livello_nome.capitalize()
                            livello_num = livelli_val[livello_nome]
                            break
                else:
                    for livello_nome in reversed(list(livelli_val.keys())):
                        soglia = benchmark[livello_nome]
                        if isinstance(soglia, str):
                            soglia = float(soglia)
                        if val is not None and val >= soglia:
                            livello_nome_trovato = livello_nome.capitalize()
                            livello_num = livelli_val[livello_nome]
                            break
                livello = livello_nome_trovato if livello_nome_trovato else "Non valutabile"
            livelli.append(livello)

        dati_esercizio['livello'] = livelli

        # Prepara valori per il grafico
        x = pd.to_datetime(dati_esercizio['data'])
        y = dati_esercizio['valore']
        testo = [
            f"Valore: {v}<br>Livello: {l}" for v, l in zip(dati_esercizio['valore'], dati_esercizio['livello'])
        ]

        # Grafico a linee
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines+markers',
            marker=dict(size=10, color='rgba(0,123,255,0.8)'),
            line=dict(color='rgba(0,123,255,0.5)', width=2),
            text=testo,
            hoverinfo='text'
        ))
        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="Valore",
            title=f"Andamento nel tempo: {esercizio_sel}",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# Pagina: WOD
elif pagina == "📒 WOD":
    st.subheader("📒 Workout of the Day (WOD)")

    oggi = datetime.date.today()
    wod_oggi = wod_df[wod_df["data"] == pd.to_datetime(oggi)]

    if not wod_oggi.empty:
        wod = wod_oggi.iloc[0]
        st.subheader(f"🏋️‍♂️ WOD del giorno: {wod['nome']}")

        # Mostra i 3 livelli
        st.markdown("### Livelli disponibili:")
        st.markdown(f"**Principiante**: {wod['principiante']}")
        st.markdown(f"**Intermedio**: {wod['intermedio']}")
        st.markdown(f"**Avanzato**: {wod['avanzato']}")

        st.divider()
        st.subheader("📥 Inserisci il tuo risultato")

        livello = st.radio("Livello scelto", ["principiante", "intermedio", "avanzato"])
        tipo_valore = wod["tipo_valore"]

        if tipo_valore == "tempo":
            minuti = st.number_input("Minuti", min_value=0, max_value=59)
            secondi = st.number_input("Secondi", min_value=0, max_value=59)
            risultato = f"{int(minuti):02d}:{int(secondi):02d}"
        else:
            risultato = st.number_input("Risultato (reps o rounds)", step=1)

        if st.button("Salva risultato"):
            risultati_df = pd.read_csv("fitness_app/wod_risultati.csv") if os.path.exists("fitness_app/wod_risultati.csv") else pd.DataFrame(columns=["nome", "data_wod", "livello", "risultato", "tipo_valore"])
            nuovo_record = {
                "nome": utente["nome"],
                "data_wod": oggi.strftime("%Y-%m-%d"),
                "livello": livello,
                "risultato": risultato,
                "tipo_valore": tipo_valore
            }
            risultati_df = pd.concat([risultati_df, pd.DataFrame([nuovo_record])], ignore_index=True)
            risultati_df.to_csv("fitness_app/wod_risultati.csv", index=False)
            st.success("Risultato salvato!")

        st.divider()
        st.subheader("📊 Classifica del giorno")

        if os.path.exists("fitness_app/wod_risultati.csv"):
            risultati_df = pd.read_csv("fitness_app/wod_risultati.csv")
            classifica = risultati_df[risultati_df["data_wod"] == oggi.strftime("%Y-%m-%d")]

            if not classifica.empty:
                if tipo_valore == "tempo":
                    classifica["valore_sec"] = classifica["risultato"].apply(lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]))
                    classifica = classifica.sort_values("valore_sec")
                else:
                    classifica["valore_num"] = pd.to_numeric(classifica["risultato"], errors="coerce")
                    classifica = classifica.sort_values("valore_num", ascending=False)

                st.dataframe(classifica[["nome", "livello", "risultato"]].reset_index(drop=True))
            else:
                st.info("Nessun risultato registrato oggi.")
    else:
        st.info("Nessun WOD pubblicato per oggi.")

# Pagina: Dashboard iniziale
if pagina == "🏠 Dashboard":
    st.title("🏠 Dashboard Atleta")

    # Debug: Ensure the page is being rendered
    st.write("DEBUG: Rendering Dashboard Page")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/847/847969.png", width=80, caption="Avatar")
    with col2:
        st.markdown(f"**👤 Nome:** {utente['nome']}")
        eta = datetime.date.today().year - pd.to_datetime(utente['data_nascita']).year
        st.markdown(f"**🎂 Età:** {eta} anni")
        st.markdown(f"**⚖️ Peso:** {utente['peso']} kg")
        st.markdown(f"**🏅 Genere:** {utente['genere']}")

    st.divider()

    # Livello medio per area
    st.subheader("📊 Livello medio per area")
    test_utente = test_df[test_df["nome"] == utente["nome"]].copy()
    test_utente["data"] = pd.to_datetime(test_utente["data"])
    test_utente = test_utente.sort_values("data")

    livelli_val = {"base": 1, "principiante": 2, "intermedio": 3, "buono": 4, "elite": 5}
    radar_labels = []
    radar_values = []

    for cat in ["forza", "ginnastica", "metabolico"]:
        esercizi_cat = esercizi_df[esercizi_df["categoria"] == cat]["esercizio"].unique()
        test_cat = test_utente[test_utente["esercizio"].isin(esercizi_cat)]
        if not test_cat.empty:
            test_cat = test_cat.sort_values("data").groupby("esercizio").tail(1)
            livelli = []
            for _, row in test_cat.iterrows():
                benchmark = benchmark_df[(benchmark_df["esercizio"] == row["esercizio"]) & (benchmark_df["genere"] == utente["genere"])]
                if benchmark.empty:
                    continue
                benchmark = benchmark.squeeze()
                tipo = benchmark["tipo_valore"]
                if tipo == "kg_rel":
                    val = float(row["relativo"])
                elif tipo == "tempo":
                    m, s = map(int, row["valore"].split(":"))
                    val = m * 60 + s
                    benchmark = benchmark[["base", "principiante", "intermedio", "buono", "elite"]].apply(
                        lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1])
                    )
                else:
                    val = float(row["valore"])

                livello = "base"
                for nome_liv in reversed(livelli_val.keys()):
                    if tipo == "tempo" and val <= float(benchmark[nome_liv]):
                        livello = nome_liv
                    elif tipo != "tempo" and val >= float(benchmark[nome_liv]):
                        livello = nome_liv
                        break
                livelli.append(livelli_val.get(livello, 0))
            if livelli:
                radar_labels.append(cat.capitalize())
                radar_values.append(round(sum(livelli) / len(livelli), 2))

    if radar_labels:
        fig = go.Figure(data=go.Scatterpolar(r=radar_values, theta=radar_labels, fill="toself"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Test recenti
    st.subheader("📈 Test recenti")
    test_recenti = test_utente.sort_values("data", ascending=False).head(5)
    st.dataframe(test_recenti[["data", "esercizio", "valore"]])

    # Prossimi test consigliati (oltre 6 settimane fa)
    st.subheader("⏰ Test da ripetere")
    cutoff_date = datetime.date.today() - datetime.timedelta(weeks=6)
    test_scaduti = test_utente[test_utente["data"] < pd.to_datetime(cutoff_date)]
    test_scaduti = test_scaduti.groupby("esercizio").tail(1)
    if not test_scaduti.empty:
        st.warning("⚠️ Questi test andrebbero aggiornati:")
        st.dataframe(test_scaduti[["data", "esercizio", "valore"]])
    else:
        st.success("✅ Nessun test da aggiornare al momento.")
