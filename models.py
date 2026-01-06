"""
Модуль для работы с конфигурацией моделей нейросетей.
Управляет загрузкой моделей из БД и отправкой запросов.
"""
import logging
from typing import List, Dict, Optional
from db import Database
from network import APIClient, OpenAIClient, DeepSeekClient, GroqClient, create_api_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelManager:
    """Класс для управления моделями нейросетей."""
    
    def __init__(self, db: Database):
        """
        Инициализация менеджера моделей.
        
        Args:
            db: Экземпляр класса Database
        """
        self.db = db
        self.api_clients: Dict[int, APIClient] = {}
        self._load_clients()
    
    def _load_clients(self):
        """Загрузить и создать API-клиенты для всех активных моделей."""
        active_models = self.db.get_active_models()
        self.api_clients.clear()
        
        for model in active_models:
            try:
                client = self._create_client(model)
                if client:
                    self.api_clients[model['id']] = client
                    logger.info(f"Загружен клиент для модели: {model['name']}")
            except Exception as e:
                logger.error(f"Ошибка создания клиента для модели {model['name']}: {str(e)}")
    
    def _create_client(self, model: Dict) -> Optional[APIClient]:
        """
        Создать API-клиент для модели.
        
        Args:
            model: Словарь с данными модели из БД
            
        Returns:
            Экземпляр API-клиента или None при ошибке
        """
        try:
            model_name = model['name'].lower()
            api_url = model['api_url'].lower()
            api_key_env = model['api_id']
            
            # Определяем тип клиента
            if "openai" in api_url or "openai" in model_name:
                return OpenAIClient(api_key_env=api_key_env)
            elif "deepseek" in api_url or "deepseek" in model_name:
                return DeepSeekClient(api_key_env=api_key_env)
            elif "groq" in api_url or "groq" in model_name:
                return GroqClient(api_key_env=api_key_env)
            else:
                # Пытаемся использовать фабричную функцию
                return create_api_client(model['name'], model['api_url'], api_key_env)
        except Exception as e:
            logger.error(f"Ошибка создания клиента: {str(e)}")
            return None
    
    def get_active_models(self) -> List[Dict]:
        """
        Получить список активных моделей.
        
        Returns:
            Список словарей с данными активных моделей
        """
        return self.db.get_active_models()
    
    def refresh_clients(self):
        """Обновить список клиентов (после изменения моделей в БД)."""
        self._load_clients()
    
    def send_to_all_models(self, prompt: str) -> List[Dict]:
        """
        Отправить промт во все активные модели.
        
        Args:
            prompt: Текст промта
            
        Returns:
            Список словарей с результатами:
                - model_id: ID модели
                - model_name: Название модели
                - response: Текст ответа
                - error: Текст ошибки (если есть)
                - success: Флаг успешности запроса
        """
        results = []
        active_models = self.db.get_active_models()
        
        logger.info(f"Отправка промта в {len(active_models)} активных моделей")
        
        for model in active_models:
            model_id = model['id']
            model_name = model['name']
            
            result = {
                'model_id': model_id,
                'model_name': model_name,
                'response': '',
                'error': None,
                'success': False
            }
            
            # Получаем или создаем клиент
            if model_id not in self.api_clients:
                client = self._create_client(model)
                if client:
                    self.api_clients[model_id] = client
                else:
                    result['error'] = "Не удалось создать API-клиент"
                    results.append(result)
                    continue
            
            client = self.api_clients[model_id]
            
            # Отправляем запрос
            try:
                logger.info(f"Отправка запроса к модели: {model_name}")
                response = client.send_request(prompt)
                result['response'] = response
                result['success'] = True
                logger.info(f"Успешный ответ от модели: {model_name}")
            except Exception as e:
                error_msg = str(e)
                result['error'] = error_msg
                result['success'] = False
                logger.error(f"Ошибка при запросе к модели {model_name}: {error_msg}")
            
            results.append(result)
        
        return results
    
    def send_to_model(self, model_id: int, prompt: str) -> Dict:
        """
        Отправить промт в конкретную модель.
        
        Args:
            model_id: ID модели
            prompt: Текст промта
            
        Returns:
            Словарь с результатом:
                - model_id: ID модели
                - model_name: Название модели
                - response: Текст ответа
                - error: Текст ошибки (если есть)
                - success: Флаг успешности запроса
        """
        model = self.db.get_model(model_id)
        if not model:
            return {
                'model_id': model_id,
                'model_name': 'Unknown',
                'response': '',
                'error': 'Модель не найдена',
                'success': False
            }
        
        # Получаем или создаем клиент
        if model_id not in self.api_clients:
            client = self._create_client(model)
            if client:
                self.api_clients[model_id] = client
            else:
                return {
                    'model_id': model_id,
                    'model_name': model['name'],
                    'response': '',
                    'error': 'Не удалось создать API-клиент',
                    'success': False
                }
        
        client = self.api_clients[model_id]
        
        # Отправляем запрос
        try:
            logger.info(f"Отправка запроса к модели: {model['name']}")
            response = client.send_request(prompt)
            logger.info(f"Успешный ответ от модели: {model['name']}")
            return {
                'model_id': model_id,
                'model_name': model['name'],
                'response': response,
                'error': None,
                'success': True
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка при запросе к модели {model['name']}: {error_msg}")
            return {
                'model_id': model_id,
                'model_name': model['name'],
                'response': '',
                'error': error_msg,
                'success': False
            }

