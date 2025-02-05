import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
API_URL = "https://api.chat2desk.com/v1"
AUTH_TOKEN = os.getenv("CHAT2DESK_TOKEN")
HEADERS = {"Authorization": AUTH_TOKEN, "Content-Type": "application/json"}

class Chat2DeskHandler:
    @staticmethod
    def paginated_search(endpoint, condition, **kwargs):
        """Универсальный поиск с пагинацией"""
        offset = 0
        limit = 100
        while True:
            params = {"limit": limit, "offset": offset}
            response = requests.get(
                f"{API_URL}/{endpoint}",
                headers=HEADERS,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if result := condition(data, **kwargs):
                return result
                
            if data["meta"]["total"] <= offset + limit:
                return None
            offset += limit

    # Задача 1: Обработка триггера
    def handle_external_event(self, client_name):
        """Поиск клиента и отправка сообщения"""
        def client_condition(data, name):
            for client in data.get("data", []):
                if client.get("name") == name:
                    return client["id"]
            return None

        client_id = self.paginated_search("clients", client_condition, name=client_name)
        if not client_id:
            return False

        # Отправка сообщения
        requests.post(
            f"{API_URL}/messages",
            headers=HEADERS,
            json={
                "client_id": client_id,
                "text": f"Привет, {client_name}. Хорошего дня!",
                "dont_open_dialog": True,
                "transport": "whatsapp"
            }
        ).raise_for_status()

        # Добавление тега VIP
        def tag_condition(data, tag_name):
            for tag in data.get("data", []):
                if tag.get("label") == tag_name:
                    return tag["id"]
            return None

        if vip_tag_id := self.paginated_search("tags", tag_condition, tag_name="VIP"):
            requests.post(
                f"{API_URL}/clients/{client_id}/tags",
                headers=HEADERS,
                json={"tag_id": vip_tag_id}
            ).raise_for_status()
        
        return True

    # Задача 2: Обработка диалога
    def handle_dialog(self, client_id, dialog_id):
        """Поиск оператора для VIP клиента"""
        # Проверка тега VIP
        client_tags = requests.get(
            f"{API_URL}/clients/{client_id}/tags",
            headers=HEADERS
        ).json().get("data", [])
        
        if not any(tag.get("label") == "VIP" for tag in client_tags):
            return None

        # Поиск оператора
        def operator_condition(data):
            for operator in data.get("data", []):
                if operator.get("opened_dialogs", 0) < 5:
                    return operator["id"]
            return None

        operator_id = self.paginated_search("operators", operator_condition)
        
        if operator_id:
            # Системное сообщение
            requests.post(
                f"{API_URL}/messages",
                headers=HEADERS,
                json={
                    "dialog_id": dialog_id,
                    "text": "Оператор найден",
                    "type": "system"
                }
            ).raise_for_status()
            
            # Назначение оператора
            requests.patch(
                f"{API_URL}/dialogs/{dialog_id}",
                headers=HEADERS,
                json={"operator_id": operator_id}
            ).raise_for_status()
            return operator_id
        
        # Комментарий если операторов нет
        requests.post(
            f"{API_URL}/messages",
            headers=HEADERS,
            json={
                "dialog_id": dialog_id,
                "text": "Оператор не найден",
                "type": "comment",
                "internal": True
            }
        ).raise_for_status()
        return None

# Flask endpoints
handler = Chat2DeskHandler()

@app.route('/webhook/event', methods=['POST'])
def event_webhook():
    data = request.json
    if data.get("event") == "test_wa_card":
        if handler.handle_external_event(data["name"]):
            return jsonify({"status": "processed"})
    return jsonify({"status": "ignored"})

@app.route('/webhook/dialog-open', methods=['POST'])
def dialog_webhook():
    data = request.json
    result = handler.handle_dialog(data["client_id"], data["dialog_id"])
    return jsonify({"operator_id": result} if result else {"status": "no_operator"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
