from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'pgserver1.public.my_table',  # Название топика Debezium
    bootstrap_servers='localhost:29092',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='pg-consumer-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("🟢 Слушаем изменения из Kafka...\n")

for message in consumer:
    payload = message.value

    if payload.get("op") == "c":
        after = payload.get("after")
        print(f"🆕 Вставка: id={after['id']}, name={after['name']}, created_at={after['created_at']}")
    elif payload.get("op") == "u":
        print("🔁 Обновление:", payload)
    elif payload.get("op") == "d":
        print("❌ Удаление:", payload)
    else:
        print("ℹ️ Другое событие:", payload)