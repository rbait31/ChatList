"""
Модуль для работы с конфигурацией моделей нейросетей.
Управляет загрузкой моделей из БД и отправкой запросов.
"""
import logging
from typing import List, Dict, Optional
from db import Database
from network import APIClient, OpenAIClient, DeepSeekClient, GroqClient, OpenRouterClient, create_api_client

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
        
        if not active_models:
            logger.warning("Нет активных моделей для загрузки")
            return
        
        loaded_count = 0
        failed_count = 0
        
        for model in active_models:
            try:
                client = self._create_client(model)
                if client:
                    self.api_clients[model['id']] = client
                    logger.info(f"Загружен клиент для модели: {model['name']}")
                    loaded_count += 1
                else:
                    logger.error(f"Не удалось создать клиент для модели {model['name']}")
                    failed_count += 1
            except ValueError as e:
                # Ошибка с API ключом - логируем подробно
                logger.error(f"Ошибка создания клиента для модели '{model['name']}': {str(e)}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Неизвестная ошибка создания клиента для модели '{model['name']}': {str(e)}")
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"Загружено клиентов: {loaded_count}, ошибок: {failed_count}")
        else:
            logger.info(f"Успешно загружено {loaded_count} клиентов")
    
    def _create_client(self, model: Dict) -> Optional[APIClient]:
        """
        Создать API-клиент для модели.
        
        Args:
            model: Словарь с данными модели из БД
            
        Returns:
            Экземпляр API-клиента или None при ошибке
        """
        try:
            model_name = model['name']
            model_name_lower = model_name.lower()
            api_url = model['api_url'].lower()
            api_key_env = model['api_id']
            
            # Проверяем наличие API ключа
            import os
            api_key = os.getenv(api_key_env)
            if not api_key:
                error_msg = (
                    f"API ключ не найден для модели '{model_name}'. "
                    f"Проверьте переменную окружения '{api_key_env}' в файле .env"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Определяем тип клиента
            if "openrouter" in api_url or "openrouter" in model_name_lower:
                return OpenRouterClient(api_key_env=api_key_env)
            elif "openai" in api_url or "openai" in model_name_lower:
                return OpenAIClient(api_key_env=api_key_env)
            elif "deepseek" in api_url or "deepseek" in model_name_lower:
                return DeepSeekClient(api_key_env=api_key_env)
            elif "groq" in api_url or "groq" in model_name_lower:
                return GroqClient(api_key_env=api_key_env)
            else:
                # Пытаемся использовать фабричную функцию
                return create_api_client(model['name'], model['api_url'], api_key_env)
        except ValueError as e:
            # Ошибка с API ключом - пробрасываем дальше с подробным сообщением
            logger.error(f"Ошибка создания клиента для модели '{model.get('name', 'Unknown')}': {str(e)}")
            raise
        except Exception as e:
            error_msg = f"Неизвестная ошибка при создании клиента для модели '{model.get('name', 'Unknown')}': {str(e)}"
            logger.error(error_msg)
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
        
        if not active_models:
            error_msg = "Не найдено активных моделей в базе данных. Добавьте модели через меню 'Настройки' → 'Управление моделями'."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
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
                try:
                    client = self._create_client(model)
                    if client:
                        self.api_clients[model_id] = client
                    else:
                        result['error'] = f"Не удалось создать API-клиент для модели '{model_name}'. Проверьте настройки модели."
                        logger.error(result['error'])
                        results.append(result)
                        continue
                except ValueError as e:
                    # Ошибка с API ключом - сохраняем подробное сообщение
                    result['error'] = str(e)
                    logger.error(f"Ошибка для модели '{model_name}': {result['error']}")
                    results.append(result)
                    continue
                except Exception as e:
                    result['error'] = f"Ошибка создания клиента для модели '{model_name}': {str(e)}"
                    logger.error(result['error'])
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
            error_msg = f"Модель с ID {model_id} не найдена в базе данных. Проверьте настройки моделей."
            logger.error(error_msg)
            return {
                'model_id': model_id,
                'model_name': 'Unknown',
                'response': '',
                'error': error_msg,
                'success': False
            }
        
        # Получаем или создаем клиент
        if model_id not in self.api_clients:
            try:
                client = self._create_client(model)
                if client:
                    self.api_clients[model_id] = client
                else:
                    error_msg = f"Не удалось создать API-клиент для модели '{model['name']}'. Проверьте настройки модели."
                    logger.error(error_msg)
                    return {
                        'model_id': model_id,
                        'model_name': model['name'],
                        'response': '',
                        'error': error_msg,
                        'success': False
                    }
            except ValueError as e:
                # Ошибка с API ключом
                error_msg = str(e)
                logger.error(f"Ошибка для модели '{model['name']}': {error_msg}")
                return {
                    'model_id': model_id,
                    'model_name': model['name'],
                    'response': '',
                    'error': error_msg,
                    'success': False
                }
            except Exception as e:
                error_msg = f"Ошибка создания клиента для модели '{model['name']}': {str(e)}"
                logger.error(error_msg)
                return {
                    'model_id': model_id,
                    'model_name': model['name'],
                    'response': '',
                    'error': error_msg,
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

