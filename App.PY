import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import pytz
import pandas as pd

# ── CONFIGURACIÓN ──────────────────────────────────────────────────
SPREADSHEET_ID = "1a2HIZ_kO6FlSG6FWG11Nfr8QAX0WNQgUBCfqaNvveKo"
TIMEZONE = pytz.timezone("America/Argentina/Buenos_Aires")

CARGOS = [
    "PRESIDENTE",
    "VICEPRESIDENTE",
    "SECRETARIO",
    "TESORERO",
    "CAPITÁN DE RUTA",
    "CAPELLÁN",
    "FIDEICOMISARIO 1",
    "FIDEICOMISARIO 2",
    "GUARDIÁN DE MEMBRESÍA",
    "SARGENTO DE ARMAS",
]

CARGOS_OBLIGATORIOS = ["PRESIDENTE", "VICEPRESIDENTE", "SECRETARIO", "TESORERO"]

# ── CONEXIÓN A GOOGLE SHEETS ───────────────────────────────────────
@st.cache_resource
def conectar_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def get_sheet(nombre):
    ss = conectar_sheets()
    try:
        return ss.worksheet(nombre)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=nombre, rows=500, cols=3)
        ws.append_row(["VOTANTE", "CANDIDATO", "TIMESTAMP"])
        ws.format("A1:C1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.18}
        })
        return ws

def get_config():
    ss = conectar_sheets()
    try:
        ws = ss.worksheet("CONFIG")
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title="CONFIG", rows=20, cols=2)
        ws.append_row(["CARGO", "ESTADO"])
        for c in CARGOS:
            ws.append_row([c, "CERRADO"])
    return ws

# ── LÓGICA DE VOTACIÓN ─────────────────────────────────────────────
def get_cargo_activo():
    ws = get_config()
    datos = ws.get_all_values()
    for fila in datos[1:]:
        if len(fila) >= 2 and fila[1] == "ABIERTO":
            return fila[0]
    return None

def abrir_cargo(cargo):
    ws = get_config()
    datos = ws.get_all_values()
    for i, fila in enumerate(datos[1:], start=2):
        if len(fila) >= 1:
            ws.update_cell(i, 2, "ABIERTO" if fila[0] == cargo else "CERRADO")
    get_sheet(cargo)  # Asegura que la hoja existe

def cerrar_cargo(cargo):
    ws = get_config()
    datos = ws.get_all_values()
    for i, fila in enumerate(datos[1:], start=2):
        if len(fila) >= 1 and fila[0] == cargo:
            ws.update_cell(i, 2, "CERRADO")

def resetear_cargo(cargo):
    ws = get_sheet(cargo)
    n_filas = ws.row_count
    if n_filas > 1:
        ws.delete_rows(2, n_filas)
    abrir_cargo(cargo)

def ya_voto(cargo, votante):
    ws = get_sheet(cargo)
    datos = ws.get_all_values()
    for fila in datos[1:]:
        if fila and fila[0].strip().lower() == votante.strip().lower():
            return True
    return False

def registrar_voto(cargo, votante, candidato):
    ws = get_sheet(cargo)
    ts = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M:%S")
    ws.append_row([votante.strip(), candidato.strip(), ts])

def get_resultados(cargo):
    ws = get_sheet(cargo)
    datos = ws.get_all_values()
    conteo = {}
    for fila in datos[1:]:
        if len(fila) >= 2 and fila[1]:
            c = fila[1].strip()
            conteo[c] = conteo.get(c, 0) + 1
    total = sum(conteo.values())
    ordenado = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    return ordenado, total

def get_votantes(cargo):
    ws = get_sheet(cargo)
    datos = ws.get_all_values()
    return [fila[0] for fila in datos[1:] if fila and fila[0]]

# ── UI ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WS GCA — Elecciones",
    page_icon="🏍️",
    layout="centered"
)

# CSS personalizado
st.markdown("""
<style>
    .main-title { font-size: 1.4rem; font-weight: 600; margin-bottom: 0; }
    .sub-title { font-size: 0.9rem; color: #888; margin-bottom: 1.5rem; }
    .cargo-activo { 
        background: #1a1a2e; color: white; 
        padding: 1rem 1.5rem; border-radius: 10px; 
        text-align: center; margin-bottom: 1.5rem;
    }
    .cargo-activo h2 { font-size: 1.4rem; margin: 0; }
    .cargo-activo p { font-size: 0.8rem; opacity: 0.7; margin: 4px 0 0; }
    .sin-cargo {
        background: #f5f5f5; color: #888;
        padding: 1rem 1.5rem; border-radius: 10px;
        text-align: center; margin-bottom: 1.5rem;
    }
    .empate-alert {
        background: #fff3cd; border: 1px solid #ffc107;
        padding: 0.75rem 1rem; border-radius: 8px;
        color: #856404; margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏍️ Widows Sons GCA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistema de Elecciones 2025/2026</div>', unsafe_allow_html=True)

# Password de administrador
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "wsgca2025")

tab_votar, tab_admin, tab_resultados = st.tabs(["🗳️ Votar", "⚙️ Administrar", "📊 Resultados"])

# ── TAB VOTAR ──────────────────────────────────────────────────────
with tab_votar:
    cargo_activo = get_cargo_activo()

    if cargo_activo:
        st.markdown(f"""
        <div class="cargo-activo">
            <h2>{cargo_activo}</h2>
            <p>cargo abierto para votación</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_voto"):
            votante = st.text_input("Tu nombre completo", placeholder="Ej: Juan Pérez")
            candidato = st.text_input(
                f"¿A quién votás para {cargo_activo}?",
                placeholder="Escribí el nombre completo del candidato"
            )
            if cargo_activo not in CARGOS_OBLIGATORIOS:
                abstencion = st.checkbox("Me abstengo / voto en blanco")
            else:
                abstencion = False

            enviado = st.form_submit_button("Registrar voto", use_container_width=True, type="primary")

            if enviado:
                if not votante:
                    st.error("Escribí tu nombre completo.")
                elif not candidato and not abstencion:
                    st.error("Escribí el nombre del candidato o marcá abstención.")
                elif ya_voto(cargo_activo, votante):
                    st.error("Ya registraste tu voto para este cargo.")
                else:
                    voto_final = "ABSTENCIÓN" if abstencion else candidato
                    registrar_voto(cargo_activo, votante, voto_final)
                    st.success(f"✅ Voto registrado correctamente para {cargo_activo}.")
    else:
        st.markdown("""
        <div class="sin-cargo">
            <h3>Ningún cargo abierto</h3>
            <p>El administrador debe abrir un cargo para iniciar la votación.</p>
        </div>
        """, unsafe_allow_html=True)

# ── TAB ADMINISTRAR ────────────────────────────────────────────────
with tab_admin:
    pwd = st.text_input("Contraseña de administrador", type="password", key="admin_pwd")

    if pwd == ADMIN_PASSWORD:
        cargo_activo_admin = get_cargo_activo()

        if cargo_activo_admin:
            st.info(f"Cargo actualmente abierto: **{cargo_activo_admin}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🔒 Cerrar {cargo_activo_admin}", use_container_width=True):
                    cerrar_cargo(cargo_activo_admin)
                    st.success(f"Cargo {cargo_activo_admin} cerrado.")
                    st.rerun()
            with col2:
                if st.button(f"🔄 Resetear {cargo_activo_admin}", use_container_width=True):
                    resetear_cargo(cargo_activo_admin)
                    st.success(f"Votos de {cargo_activo_admin} reseteados. Cargo reabierto.")
                    st.rerun()
        else:
            st.info("Ningún cargo abierto actualmente.")

        st.divider()
        st.markdown("**Abrir cargo para votación:**")

        for i, cargo in enumerate(CARGOS):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"`{i+1:02d}` **{cargo}**")
            with col2:
                if st.button("Abrir", key=f"abrir_{i}", use_container_width=True):
                    abrir_cargo(cargo)
                    st.success(f"{cargo} abierto.")
                    st.rerun()
            with col3:
                if st.button("Reset", key=f"reset_{i}", use_container_width=True):
                    resetear_cargo(cargo)
                    st.success(f"{cargo} reseteado.")
                    st.rerun()
    elif pwd:
        st.error("Contraseña incorrecta.")

# ── TAB RESULTADOS ─────────────────────────────────────────────────
with tab_resultados:
    pwd_res = st.text_input("Contraseña para ver resultados", type="password", key="res_pwd")

    if pwd_res == ADMIN_PASSWORD:
        cargo_sel = st.selectbox("Seleccioná un cargo", CARGOS)

        if st.button("Ver resultados", use_container_width=True):
            resultados, total = get_resultados(cargo_sel)
            votantes = get_votantes(cargo_sel)

            st.markdown(f"**Total de votos:** {total}")

            if not resultados:
                st.warning("No hay votos registrados para este cargo.")
            else:
                for i, (candidato, votos) in enumerate(resultados):
                    pct = round((votos / total) * 100) if total > 0 else 0
                    label = f"{'🥇 ' if i == 0 else ''}{candidato}"
                    st.progress(pct / 100, text=f"{label} — {votos} voto{'s' if votos != 1 else ''} ({pct}%)")

                # Detectar empate
                if len(resultados) >= 2 and resultados[0][1] == resultados[1][1]:
                    st.markdown(f"""
                    <div class="empate-alert">
                        ⚠️ <strong>Empate detectado</strong> entre <strong>{resultados[0][0]}</strong> y 
                        <strong>{resultados[1][0]}</strong> con {resultados[0][1]} votos cada uno.<br>
                        Usá el botón "Reset" en Administrar para hacer un ballotage.
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()
                st.markdown("**Detalle de votos:**")
                df = pd.DataFrame(resultados, columns=["Candidato", "Votos"])
                df["%" ] = df["Votos"].apply(lambda v: f"{round(v/total*100)}%" if total > 0 else "0%")
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.divider()
                st.markdown(f"**Votantes ({len(votantes)}):**")
                st.write(", ".join(votantes))
    elif pwd_res:
        st.error("Contraseña incorrecta.")
