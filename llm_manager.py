import os
import json
from abc import ABC, abstractmethod
from dotenv import load_dotenv

import google.generativeai as genai
from openai import OpenAI

load_dotenv()
MAX_CV = 6000
MAX_JOB = 6000

class BaseLLMConnector(ABC):
    @abstractmethod
    def extract_skills_from_cv(self, cv_text: str) -> list:
        pass

    @abstractmethod
    def extract_skills_from_job(self, job_description: str) -> list:
        pass


class GeminiConnector(BaseLLMConnector):
    def __init__(
        self,
        model_name: str = "gemini-3.1-pro-preview",
        api_key: str | None = None,
    ):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY no encontrado en las variables de entorno."
            )
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def _call_api(self, prompt: str) -> list:
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            data = json.loads(response.text)
            return [s.lower().strip() for s in data.get("skills", [])]
        except Exception as e:
            print(f"Error al llamar a Gemini API: {e}")
            return []

    def extract_skills_from_cv(self, cv_text: str) -> list:        
        prompt = f"""
        Actúa como un experto en Recusos Humanos de TI. Lee el siguiente CV y extrae TODAS las 
        habilidades técnicas mencionadas (lenguajes, frameworks, metodologías).
        Ignora años de experiencia, nombres o empresas. Solo quiero las habilidades clave.
        Devuelve estrictamente un JSON con esta estructura: '{{"skills": ["skill1", "skill2"]}}'.
        \n\nTexto del CV:\n{cv_text[:MAX_CV]}
        """
        return self._call_api(prompt)

    def extract_skills_from_job(self, job_description: str) -> list:
        prompt = f"""
        Actúa como un reclutador técnico. Extrae de la siguiente descripción de trabajo
        todas las habilidades requeridas y deseadas. 
        - Sé conciso (ej. usa "aws" en lugar de "conocimiento avanzado en aws").
        - Trata las tecnologías empaquetadas como un solo item.
        Devuelve estrictamente un JSON con esta estructura: '{{"skills": ["skill1", "skill2"]}}'.
        \n\nDescripción del cargo:\n{job_description[:MAX_JOB]}
        """
        return self._call_api(prompt)


class DeepSeekConnector(BaseLLMConnector):
    def __init__(
        self,
        model_name: str = "deepseek-chat",
        api_key: str | None = None,
    ):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY no encontrada en .env")
        self.model_name = model_name

        # DeepSeek es compatible con el cliente de OpenAI cambiando la Base URL
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

    def _call_api(self, prompt: str) -> list:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output strict JSON holding a list of skills.",
                    },
                    {"role": "user", "content": prompt},
                ],
                # Forzamos JSON
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return [s.lower().strip() for s in data.get("skills", [])]
        except Exception as e:
            print(f"Error en DeepSeek API: {e}")
            return []

    def extract_skills_from_cv(self, cv_text: str) -> list:
        prompt = f"""Extrae las habilidades técnicas del CV.
        Devuelve JSON: {{"skills": ["skill1", "skill2"]}}.\nCV:\n{cv_text[:MAX_CV]}"""
        return self._call_api(prompt)

    def extract_skills_from_job(self, job_description: str) -> list:
        prompt = f"""Extrae las herramientas y requerimientos del cargo.
        - Sé conciso (ej. usa "aws" en lugar de "conocimiento avanzado en aws").
        - Trata las tecnologías empaquetadas como un solo item.
        Devuelve JSON: {{"skills": ["skill1", "skill2"]}}.\nCargo:\n{job_description[:MAX_JOB]}"""
        return self._call_api(prompt)


class GroqConnector(BaseLLMConnector):
    def __init__(
        self,
        model_name: str = "llama-3.1-8b-instant",
        api_key: str | None = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no encontrada en .env")
        self.model_name = model_name
        self.client = OpenAI(
            api_key=self.api_key, base_url="https://api.groq.com/openai/v1"
        )

    def _call_api(self, prompt: str) -> list:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output strict JSON holding a list of skills.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return [s.lower().strip() for s in data.get("skills", [])]
        except Exception as e:
            print(f"Error en Groq API: {e}")
            return []

    def extract_skills_from_cv(self, cv_text: str) -> list:
        prompt = f"""Extrae las habilidades técnicas del CV.
        Devuelve JSON: {{"skills": ["skill1", "skill2"]}}. CV: {cv_text[:MAX_CV]}"""
        return self._call_api(prompt)

    def extract_skills_from_job(self, job_description: str) -> list:
        prompt = f"""Extrae las herramientas y requerimientos del cargo.
        - Sé conciso (ej. usa "aws" en lugar de "conocimiento avanzado en aws").
        - Trata las tecnologías empaquetadas como un solo item.
        Devuelve JSON: {{"skills": ["skill1", "skill2"]}}. Cargo: {job_description[:MAX_JOB]}"""
        return self._call_api(prompt)


class OllamaConnector(BaseLLMConnector):
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def _call_api(self, prompt: str) -> list:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output strict JSON holding a list of skills.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return [s.lower().strip() for s in data.get("skills", [])]
        except Exception as e:
            print(f"Error en Ollama API: {e}")
            return []

    def extract_skills_from_cv(self, cv_text: str) -> list:
        prompt = f"""Extrae TODAS las habilidades técnicas del CV. 
        Ignora los nombres, fechas y empresas.
        Devuelve estrictamente JSON: {{"skills": ["skill1", "skill2", "skill3"]}}.\nCV:\n{cv_text[:MAX_CV]}"""
        return self._call_api(prompt)

    def extract_skills_from_job(self, job_description: str) -> list:
        prompt = f"""Extrae TODAS las habilidades técnicas requeridas para el cargo.
        - Sé conciso (ej. usa "aws" en lugar de "conocimiento avanzado en aws").
        - Trata las tecnologías empaquetadas como un solo item.
        Devuelve estrictamente JSON: {{"skills": ["skill1", "skill2", "skill3"]}}.\nCargo:\n{job_description[:MAX_JOB]}"""
        return self._call_api(prompt)


def get_llm_connector(
    provider: str,
    model_name: str | None = None,
    api_key: str | None = None,
) -> BaseLLMConnector:
    """
    Factory function: Devuelve el conector basado en el string que elijas.
    """
    provider = provider.lower()
    if provider == "gemini":
        return GeminiConnector(
            model_name=model_name or "gemini-3.1-pro-preview",
            api_key=api_key,
        )
    elif provider == "deepseek":
        print(f"Using DeepSeek with model: {model_name or 'deepseek-chat'} and API key: {api_key}")
        return DeepSeekConnector(
            model_name=model_name or "deepseek-chat",
            api_key=api_key,
        )
    elif provider == "groq":
        return GroqConnector(
            model_name=model_name or "llama-3.1-8b-instant",
            api_key=api_key,
        )
    elif provider == "ollama":
        return OllamaConnector(
            model_name="llama3.1:8b"
        )  # Puedes cambiar el modelo si tienes otro disponible
    else:
        raise ValueError(f"Proveedor '{provider}' no soportado.")
