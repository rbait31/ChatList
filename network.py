"""
Модуль для работы с API нейросетей.
Содержит классы для отправки запросов к различным API.
"""
import os
import requests
from typing import Optional
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class APIClient(ABC):
    """Базовый класс для работы с API нейросетей."""
    
    def __init__(self, api_url: str, api_key_env: str, timeout: int = 30):
        """
        Инициализация API-клиента.
        
        Args:
            api_url: URL API-эндпоинта
            api_key_env: Имя переменной окружения с API-ключом
            timeout: Таймаут запроса в секундах
        """
        self.api_url = api_url
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.api_key = os.getenv(api_key_env)
        
        if not self.api_key:
            raise ValueError(f"API ключ не найден в переменной окружения: {api_key_env}")
    
    @abstractmethod
    def send_request(self, prompt: str) -> str:
        """
        Отправить запрос к API.
        
        Args:
            prompt: Текст промта
            
        Returns:
            Текст ответа от API
            
        Raises:
            Exception: При ошибке запроса
        """
        pass
    
    def _make_request(self, method: str = "POST", **kwargs) -> requests.Response:
        """
        Выполнить HTTP-запрос.
        
        Args:
            method: HTTP-метод
            **kwargs: Дополнительные параметры для requests
            
        Returns:
            Response объект
            
        Raises:
            requests.RequestException: При ошибке запроса
        """
        try:
            response = requests.request(
                method,
                self.api_url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.Timeout:
            raise Exception(f"Таймаут запроса к {self.api_url}")
        except requests.RequestException as e:
            raise Exception(f"Ошибка запроса к API: {str(e)}")


class OpenAIClient(APIClient):
    """Клиент для работы с OpenAI API."""
    
    def __init__(self, api_key_env: str = "OPENAI_API_KEY", 
                 model: str = "gpt-3.5-turbo", timeout: int = 30):
        """
        Инициализация OpenAI клиента.
        
        Args:
            api_key_env: Имя переменной окружения с API-ключом
            model: Название модели OpenAI
            timeout: Таймаут запроса
        """
        super().__init__(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key_env=api_key_env,
            timeout=timeout
        )
        self.model = model
    
    def send_request(self, prompt: str) -> str:
        """
        Отправить запрос к OpenAI API.
        
        Args:
            prompt: Текст промта
            
        Returns:
            Текст ответа от модели
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = self._make_request("POST", headers=headers, json=data)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception("Неожиданный формат ответа от OpenAI API")


class DeepSeekClient(APIClient):
    """Клиент для работы с DeepSeek API."""
    
    def __init__(self, api_key_env: str = "DEEPSEEK_API_KEY",
                 model: str = "deepseek-chat", timeout: int = 30):
        """
        Инициализация DeepSeek клиента.
        
        Args:
            api_key_env: Имя переменной окружения с API-ключом
            model: Название модели DeepSeek
            timeout: Таймаут запроса
        """
        super().__init__(
            api_url="https://api.deepseek.com/v1/chat/completions",
            api_key_env=api_key_env,
            timeout=timeout
        )
        self.model = model
    
    def send_request(self, prompt: str) -> str:
        """
        Отправить запрос к DeepSeek API.
        
        Args:
            prompt: Текст промта
            
        Returns:
            Текст ответа от модели
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = self._make_request("POST", headers=headers, json=data)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception("Неожиданный формат ответа от DeepSeek API")


class GroqClient(APIClient):
    """Клиент для работы с Groq API."""
    
    def __init__(self, api_key_env: str = "GROQ_API_KEY",
                 model: str = "mixtral-8x7b-32768", timeout: int = 30):
        """
        Инициализация Groq клиента.
        
        Args:
            api_key_env: Имя переменной окружения с API-ключом
            model: Название модели Groq
            timeout: Таймаут запроса
        """
        super().__init__(
            api_url="https://api.groq.com/openai/v1/chat/completions",
            api_key_env=api_key_env,
            timeout=timeout
        )
        self.model = model
    
    def send_request(self, prompt: str) -> str:
        """
        Отправить запрос к Groq API.
        
        Args:
            prompt: Текст промта
            
        Returns:
            Текст ответа от модели
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = self._make_request("POST", headers=headers, json=data)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception("Неожиданный формат ответа от Groq API")


def create_api_client(model_name: str, api_url: str, api_key_env: str) -> APIClient:
    """
    Фабричная функция для создания API-клиента по типу модели.
    
    Args:
        model_name: Название модели
        api_url: URL API-эндпоинта
        api_key_env: Имя переменной окружения с API-ключом
        
    Returns:
        Экземпляр соответствующего API-клиента
    """
    # Определяем тип клиента по URL или названию модели
    model_lower = model_name.lower()
    
    if "openai" in api_url.lower() or "openai" in model_lower:
        return OpenAIClient(api_key_env=api_key_env)
    elif "deepseek" in api_url.lower() or "deepseek" in model_lower:
        return DeepSeekClient(api_key_env=api_key_env)
    elif "groq" in api_url.lower() or "groq" in model_lower:
        return GroqClient(api_key_env=api_key_env)
    else:
        # Для неизвестных типов создаем базовый клиент
        # В этом случае нужно будет переопределить send_request
        raise ValueError(f"Неизвестный тип модели: {model_name}. Используйте один из: OpenAI, DeepSeek, Groq")

