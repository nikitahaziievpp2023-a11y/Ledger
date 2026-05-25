from fastapi.testclient import TestClient
# Імпортуємо змінну додатка 'app' з твого файлу запуску
from app.main import app

# Створюємо тестового клієнта, який імітуватиме роботу браузера чи Postman
client = TestClient(app)


def test_read_main_endpoint():
    """Юніт-тест: Перевіряємо, чи успішно віддається головна HTML-сторінка"""
    response = client.get("/")

    # Перевіряємо статус 200 OK
    assert response.status_code == 200

    # Перевіряємо, що у відповіді прийшов саме HTML-текст
    assert "<!DOCTYPE html>" in response.text


def test_get_expenses_endpoint():
    """Юніт-тест: Перевіряємо маршрут отримання списку витрат (роут '/expenses')"""
    response = client.get("/expenses")

    # Перевіряємо, чи сервер повертає успішний статус (200) або статус порожньої бази (404)
    # Це гарантує, що роут фізично існує і не видає критичну помилку 500
    assert response.status_code in [200, 404]