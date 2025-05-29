import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import os

# Load CSVs
utenti_df = pd.read_csv("fitness_app/utenti.csv")
esercizi_df = pd.read_csv("fitness_app/esercizi.csv")
test_df = pd.read_csv("fitness_app/test.csv")
benchmark_df = pd.read_csv("fitness_app/benchmark.csv")

# Carica il CSV dei WOD (Workout Of the Day)
wod_path = "fitness_app/wod.csv"
if not os.path.exists(wod_path):
    pd.DataFrame(columns=["data", "titolo", "descrizione"]).to_csv(wod_path, index=False)
wod_df = pd.read_csv(wod_path)

st.set_page_config(page_title="Fitness Gauge", layout="wide")
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
        "📅 Calendario WOD",
        "➕ Inserisci nuovo test",
        "👤 Profilo Atleta",
        "⚙️ Gestione Esercizi",
        "📋 Storico Dati Utenti",
        "📊 Bilanciamento Atleti",
        "➕ Aggiungi Utente",
        "⚙️ Gestione Benchmark",
        "📊 Grafici"
    ]
else:
    pagine_sidebar = [
        "📅 Calendario WOD",
        "➕ Inserisci nuovo test",
        "👤 Profilo Atleta",
        "📊 Grafici",
        "📜 Storico Test"  # Nuova pagina per la storia dei test atleta
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
            st.session_state.pagina_attiva = pagina_nome

    # Pulsante per uscire
    if st.button("Esci", key="sidebar_logout_button"):
        logout()

pagina = st.session_state.pagina_attiva

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

    if st.button("Salva test"):
        relativo = None
        if tipo_valore == "kg_rel" and peso_corporeo > 0:
            relativo = round(float(valore) / float(peso_corporeo), 2)  # Calcolo del valore relativo
        nuovo_test = {
            "nome": nome_atleta,
            "esercizio": esercizio,
            "valore": valore,
            "tipo_valore": tipo_valore,
            "peso_corporeo": peso_corporeo,
            "relativo": relativo,
            "data": data_test.strftime("%Y-%m-%d"),
            "genere": genere  # Aggiunto il genere al test
        }
        test_df = pd.concat([test_df, pd.DataFrame([nuovo_test])], ignore_index=True)
        test_df.to_csv("fitness_app/test.csv", index=False)
        st.success("Test salvato correttamente!")

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
                (benchmarkDf['genere'] == genere_row)
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
                    (benchmarkDf['esercizio'] == row['esercizio']) &
                    (benchmarkDf['genere'] == row['genere'])
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
    tipo_valore = st.selectbox("Tipo di valore", ["kg", "kg_rel", "reps", "tempo", "valore"], key="aggiungi_tipo_valore")
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
        st.write(f"**Titolo:** {wod_giorno.iloc[0]['titolo']}")
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
    st.dataframe(wod_df.sort_values("data", ascending=False))
