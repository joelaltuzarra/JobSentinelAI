import streamlit as st
from analyzer import calculate_skill_gap
from cv_parser import extract_text_from_pdf
from scraper import fetch_jobs

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
        job_limit = st.number_input("Cantidad a consultar", min_value=1, max_value=10, value=5)

    if st.button("Buscar Ofertas"):
        if job_query:
            with st.spinner("Buscando ofertas..."):
                api_jobs = fetch_jobs(job_query, limit=job_limit)
                st.session_state.jobs = api_jobs

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

        llm_choice = st.selectbox(
            "Selecciona el proveedor de IA",
            options=["groq", "gemini", "deepseek"],
            index=0,
        )

        default_models = {
            "groq": "llama-3.1-8b-instant",
            "gemini": "gemini-3.1-pro-preview",
            "deepseek": "deepseek-chat",
        }
        token_placeholders = {
            "gemini": "Ej: AIza...",
            "deepseek": "Ej: sk-...",
        }

        custom_api_key = ""
        custom_model_name = ""

        if llm_choice != "groq":
            st.info("Para Gemini y DeepSeek debes ingresar API token y nombre de modelo.")
            custom_api_key = st.text_input(
                "API Token",
                type="password",
                placeholder=token_placeholders.get(llm_choice, ""),
                help="Campo obligatorio para el proveedor seleccionado.",
            )
            custom_model_name = st.text_input(
                "Nombre del modelo",
                value=default_models.get(llm_choice, ""),
                help="Campo obligatorio. Puedes usar cualquier modelo válido del proveedor elegido.",
            )

        if st.button("Analizar Brechas"):
            if llm_choice == "groq":
                api_key_to_use = None
                model_name_to_use = None
            else:
                api_key_to_use = (custom_api_key or "").strip()
                model_name_to_use = (custom_model_name or "").strip()
                if not api_key_to_use or not model_name_to_use:
                    st.error("Para Gemini y DeepSeek debes completar API token y nombre del modelo.")
                    st.stop()

            with st.spinner("Analizando..."):
                try:
                    result = calculate_skill_gap(
                        st.session_state.cv_text,
                        st.session_state.jobs,
                        provider=llm_choice,
                        model_name=model_name_to_use,
                        api_key=api_key_to_use,
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