import streamlit as st
from analyzer import calculate_skill_gap
from cv_parser import extract_text_from_pdf
from scraper import fetch_jobs
from database import save_jobs, get_jobs_by_query

st.set_page_config(page_title="JobSentinelAI", page_icon="🎯", layout="wide")

def main():
    st.title("🎯 JobSentinelAI - Análisis de Brechas de Skills")
    st.write("Descubre qué habilidades te faltan para tu próximo empleo ideal, basado en ofertas reales.")

    if "jobs" not in st.session_state:
        st.session_state.jobs = []

    if "cv_text" not in st.session_state:
        st.session_state.cv_text = ""

    st.header("1️⃣ Buscar Ofertas Laborales")
    col1, col2 = st.columns([3, 1])

    with col1:
        job_query = st.text_input("Palabras clave para buscar ofertas", placeholder="Ej: Python Backend Develope")

    with col2:
        job_limit = st.number_input("Cantidad a consultar", min_value=1, max_value=20, value=5)

    if st.button("Buscar Ofertas"):
        if job_query:
            with st.spinner("Buscando ofertas..."):
                api_jobs = fetch_jobs(job_query, limit=job_limit)
                if api_jobs:
                    save_jobs(job_query, api_jobs)

                st.session_state.jobs = get_jobs_by_query(job_query)

        else:
            st.warning("Por favor, ingresa palabras clave para buscar ofertas.")

    if st.session_state.jobs:
        st.success(f"Se encontraron {len(st.session_state.jobs)} ofertas para '{job_query}'.")

        tabla_trabajos = [{"Titulo": j["title"], "URL": j["url"]} for j in st.session_state.jobs]
        st.dataframe(tabla_trabajos, use_container_width=True)

    st.header("2️⃣ Subir tu CV")
    uploaded_cv = st.file_uploader("Selecciona tu CV en formato PDF", type=["pdf"])

    if uploaded_cv is not None:
        st.session_state.cv_text = extract_text_from_pdf(uploaded_cv)
        if st.session_state.cv_text:
            st.success("CV procesado exitosamente.")
            
    if st.session_state.jobs and st.session_state.cv_text:
        st.header("3️⃣ Análisis de Brechas de Skills")
        st.write("Comparando tu CV con las ofertas encontradas...")

        llm_choice = st.selectbox("Selecciona el proveedor de LLM para el análisis", options=["gemini", "deepseek", "Ollama"])

        if st.button("Analizar Brechas"):
            with st.spinner("Analizando..."):
                try:
                    result = calculate_skill_gap(
                        st.session_state.cv_text, 
                        st.session_state.jobs, 
                        provider=llm_choice
                    )
                    st.success("Análisis completado. Revisa las brechas identificadas.")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Habilidades Actuales en tu CV")
                        st.info(", ".join(result["user_skills"]).title())

                    with col2:
                        st.subheader("Habilidades Faltantes (Ranking)")
                        missing = result["missing_skills_ranking"]
                        if missing:
                            tabla_missing = [{"Habilidad": m[0].title(), "Frecuencia en Ofertas": m[1]} for m in missing]
                            st.dataframe(tabla_missing, use_container_width=True)

                            st.bar_chart(data=tabla_missing, x="Habilidad", y="Frecuencia en Ofertas")
                        else:
                            st.success("¡No se identificaron habilidades faltantes! Tu CV está muy alineado con las ofertas encontradas.")

                except Exception as e:
                    st.error(f"Error al analizar las brechas: {e}")

if __name__ == "__main__":
    main()