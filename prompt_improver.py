"""
Модуль для улучшения промтов с помощью AI.
Использует нейросети для улучшения, переформулировки и адаптации промтов.
"""
import logging
import re
from typing import Dict, List, Optional
from models import ModelManager

logger = logging.getLogger(__name__)


class PromptImprover:
    """Класс для улучшения промтов с помощью AI."""
    
    # Системные промпты для разных типов улучшения
    SYSTEM_PROMPTS = {
        'improve': """Ты эксперт по написанию эффективных промптов для AI. 
Улучши следующий промпт, сделав его более четким, конкретным и структурированным.
Сохрани основную идею, но сделай формулировку более точной.
Верни только улучшенный вариант промпта, без дополнительных комментариев.""",
        
        'alternatives': """Ты эксперт по написанию промптов для AI.
Для следующего промпта предложи ровно 3 альтернативных варианта формулировки, сохраняя основную идею.
Каждый вариант должен подходить к задаче с разных сторон.
ВАЖНО: Верни только нумерованный список в формате:
1. Первый вариант промпта
2. Второй вариант промпта
3. Третий вариант промпта

Без дополнительных комментариев, объяснений или заголовков.""",
        
        'code': """Ты эксперт по написанию технических промптов для программирования.
Адаптируй следующий промпт для работы с кодом. Добавь технические детали, специфику языков программирования,
примеры кода, требования к формату ответа.
Верни только адаптированный промпт.""",
        
        'analysis': """Ты эксперт по аналитическим промптам.
Адаптируй следующий промпт для аналитических задач. Добавь структуру, критерии оценки,
формат вывода данных, требования к детальности анализа.
Верни только адаптированный промпт.""",
        
        'creative': """Ты эксперт по креативным промптам.
Адаптируй следующий промпт для творческих задач. Добавь образность, метафоры,
творческие элементы, требования к стилю и тону.
Верни только адаптированный промпт."""
    }
    
    def __init__(self, model_manager: ModelManager):
        """
        Инициализация улучшателя промтов.
        
        Args:
            model_manager: Менеджер моделей для отправки запросов
        """
        self.model_manager = model_manager
    
    def improve_prompt(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, any]:
        """
        Улучшить промт и получить все варианты.
        
        Args:
            prompt: Исходный промт
            model_name: Название модели для улучшения (если None, используется первая активная)
            
        Returns:
            Словарь с ключами:
                - improved: улучшенная версия
                - alternatives: список альтернативных вариантов
                - code_version: адаптация под код
                - analysis_version: адаптация под анализ
                - creative_version: адаптация под креатив
                - success: флаг успешности
                - error: сообщение об ошибке (если есть)
        """
        result = {
            'improved': '',
            'alternatives': [],
            'code_version': '',
            'analysis_version': '',
            'creative_version': '',
            'success': False,
            'error': None
        }
        
        if not prompt or not prompt.strip():
            result['error'] = "Промт не может быть пустым"
            return result
        
        try:
            # Определяем модель для использования
            active_models = self.model_manager.get_active_models()
            if not active_models:
                result['error'] = "Нет активных моделей для улучшения промта"
                return result
            
            # Выбираем модель
            selected_model = None
            if model_name:
                for model in active_models:
                    if model['name'] == model_name:
                        selected_model = model
                        break
            
            if not selected_model:
                selected_model = active_models[0]  # Используем первую активную модель
            
            logger.info(f"Используем модель {selected_model['name']} для улучшения промта")
            
            # Получаем улучшенную версию
            improved = self.get_improved_version(prompt, selected_model['id'])
            if improved:
                result['improved'] = improved
                result['success'] = True
            else:
                result['error'] = "Не удалось получить улучшенную версию"
                return result
            
            # Получаем альтернативные варианты
            alternatives = self.get_alternatives(prompt, selected_model['id'])
            if alternatives:
                result['alternatives'] = alternatives
            
            # Получаем адаптированные версии
            code_version = self.adapt_for_model_type(prompt, 'code', selected_model['id'])
            if code_version:
                result['code_version'] = code_version
            
            analysis_version = self.adapt_for_model_type(prompt, 'analysis', selected_model['id'])
            if analysis_version:
                result['analysis_version'] = analysis_version
            
            creative_version = self.adapt_for_model_type(prompt, 'creative', selected_model['id'])
            if creative_version:
                result['creative_version'] = creative_version
            
        except Exception as e:
            logger.error(f"Ошибка при улучшении промта: {str(e)}")
            result['error'] = f"Ошибка при улучшении промта: {str(e)}"
        
        return result
    
    def get_improved_version(self, prompt: str, model_id: Optional[int] = None) -> Optional[str]:
        """
        Получить улучшенную версию промта.
        
        Args:
            prompt: Исходный промт
            model_id: ID модели для использования
            
        Returns:
            Улучшенный промт или None при ошибке
        """
        try:
            system_prompt = self.SYSTEM_PROMPTS['improve']
            full_prompt = f"{system_prompt}\n\nИсходный промпт:\n{prompt}"
            
            if model_id:
                response = self.model_manager.send_to_model(model_id, full_prompt)
            else:
                # Используем первую активную модель
                active_models = self.model_manager.get_active_models()
                if not active_models:
                    return None
                response = self.model_manager.send_to_model(active_models[0]['id'], full_prompt)
            
            if response.get('success') and response.get('response'):
                improved_text = response['response'].strip()
                # Убираем возможные префиксы типа "Улучшенный промпт:" или "Вот улучшенный вариант:"
                improved_text = re.sub(r'^(Улучшенный промпт|Вот улучшенный вариант|Улучшенная версия):\s*', 
                                      '', improved_text, flags=re.IGNORECASE)
                return improved_text.strip()
            
            return None
        except Exception as e:
            logger.error(f"Ошибка получения улучшенной версии: {str(e)}")
            return None
    
    def get_alternatives(self, prompt: str, model_id: Optional[int] = None, count: int = 3) -> List[str]:
        """
        Получить альтернативные варианты промта.
        
        Args:
            prompt: Исходный промт
            model_id: ID модели для использования
            count: Количество альтернатив (по умолчанию 3)
            
        Returns:
            Список альтернативных вариантов
        """
        try:
            system_prompt = self.SYSTEM_PROMPTS['alternatives']
            full_prompt = f"{system_prompt}\n\nИсходный промпт:\n{prompt}"
            
            if model_id:
                response = self.model_manager.send_to_model(model_id, full_prompt)
            else:
                active_models = self.model_manager.get_active_models()
                if not active_models:
                    return []
                response = self.model_manager.send_to_model(active_models[0]['id'], full_prompt)
            
            if response.get('success') and response.get('response'):
                text = response['response'].strip()
                # Парсим нумерованный список
                alternatives = self._parse_numbered_list(text, count)
                return alternatives
            
            return []
        except Exception as e:
            logger.error(f"Ошибка получения альтернатив: {str(e)}")
            return []
    
    def adapt_for_model_type(self, prompt: str, model_type: str, model_id: Optional[int] = None) -> Optional[str]:
        """
        Адаптировать промт под тип модели.
        
        Args:
            prompt: Исходный промт
            model_type: Тип модели ('code', 'analysis', 'creative')
            model_id: ID модели для использования
            
        Returns:
            Адаптированный промт или None при ошибке
        """
        if model_type not in self.SYSTEM_PROMPTS:
            logger.warning(f"Неизвестный тип модели: {model_type}")
            return None
        
        try:
            system_prompt = self.SYSTEM_PROMPTS[model_type]
            full_prompt = f"{system_prompt}\n\nИсходный промпт:\n{prompt}"
            
            if model_id:
                response = self.model_manager.send_to_model(model_id, full_prompt)
            else:
                active_models = self.model_manager.get_active_models()
                if not active_models:
                    return None
                response = self.model_manager.send_to_model(active_models[0]['id'], full_prompt)
            
            if response.get('success') and response.get('response'):
                adapted_text = response['response'].strip()
                # Убираем возможные префиксы
                adapted_text = re.sub(r'^(Адаптированный промпт|Вот адаптированный вариант):\s*', 
                                     '', adapted_text, flags=re.IGNORECASE)
                return adapted_text.strip()
            
            return None
        except Exception as e:
            logger.error(f"Ошибка адаптации промта для типа {model_type}: {str(e)}")
            return None
    
    def _parse_numbered_list(self, text: str, max_items: int = 3) -> List[str]:
        """
        Парсить нумерованный список из текста.
        
        Args:
            text: Текст с нумерованным списком
            max_items: Максимальное количество элементов
            
        Returns:
            Список элементов
        """
        items = []
        
        # Паттерны для поиска нумерованного списка
        patterns = [
            r'^\d+[\.\)]\s+(.+)$',  # 1. текст или 1) текст
            r'^[-*]\s+(.+)$',  # - текст или * текст
        ]
        
        # Сначала пробуем разделить по паттерну начала нового пункта списка
        # Это более надежный способ для многострочных элементов
        parts = re.split(r'\n(?=\d+[\.\)]\s)', text)
        if len(parts) > 1:
            for part in parts[1:max_items+1]:  # Пропускаем первую часть (может быть пустой или заголовком)
                part = part.strip()
                if part:
                    # Убираем номер в начале
                    cleaned = re.sub(r'^\d+[\.\)]\s+', '', part, count=1).strip()
                    if cleaned and len(items) < max_items:
                        items.append(cleaned)
        
        # Если не получилось, пробуем построчно
        if not items:
            lines = text.split('\n')
            current_item = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_item:
                        item_text = ' '.join(current_item).strip()
                        if item_text and len(items) < max_items:
                            items.append(item_text)
                        current_item = []
                    continue
                
                # Проверяем, начинается ли строка с номера
                match = re.match(r'^\d+[\.\)]\s+(.+)$', line)
                if match:
                    # Сохраняем предыдущий элемент
                    if current_item:
                        item_text = ' '.join(current_item).strip()
                        if item_text and len(items) < max_items:
                            items.append(item_text)
                    # Начинаем новый
                    current_item = [match.group(1)]
                else:
                    # Продолжение текущего элемента
                    if current_item:
                        current_item.append(line)
                    else:
                        # Первая строка без номера - возможно начало списка
                        match_marker = re.match(r'^[-*•]\s+(.+)$', line)
                        if match_marker:
                            current_item = [match_marker.group(1)]
                        else:
                            current_item = [line]
            
            # Добавляем последний элемент
            if current_item:
                item_text = ' '.join(current_item).strip()
                if item_text and len(items) < max_items:
                    items.append(item_text)
        
        # Если все еще пусто, берем первые непустые строки
        if not items:
            lines = [line.strip() for line in text.split('\n') 
                    if line.strip() and not line.strip().lower().startswith(('вариант', 'альтернатива', 'version'))]
            items = lines[:max_items]
        
        # Очищаем от лишних пробелов
        items = [item.strip() for item in items if item.strip()]
        
        return items[:max_items]

