```markdown
# PostgreSQL → Kafka → ClickHouse Pipeline с использованием Debezium

## Общее описание

Данный проект реализует систему фиксации изменений данных (Change Data Capture, CDC) на основе Debezium. Архитектура обеспечивает потоковую передачу изменений из PostgreSQL через Apache Kafka в аналитическую СУБД ClickHouse, что позволяет организовать эффективную интеграцию между транзакционной и аналитической системами.

---

## Назначение пайплайна

Система предназначена для:

1. Мониторинга изменений в таблице PostgreSQL посредством логической репликации.
2. Передачи событий изменения данных в Apache Kafka через Debezium Connector.
3. Потребления и обработки сообщений с использованием Python-приложения.
4. Фильтрации событий по типу операции (`UPDATE`).
5. Записи релевантных изменений в ClickHouse через HTTP-интерфейс.
6. Автоматического создания целевой таблицы при первом запуске.

---

## Архитектура системы

```
![img_1.png](img_1.png)
```

- **PostgreSQL** — источник данных с включённой логической репликацией.
- **Debezium** — захватывает изменения из WAL и публикует в Kafka.
- **Kafka** — брокер сообщений, обеспечивающий отказоустойчивость и буферизацию.
- **Python Consumer** — фильтрует и трансформирует события.
- **ClickHouse** — аналитическая СУБД для хранения и агрегации изменений.

---

## Функциональные возможности

- Отслеживание операций `UPDATE` в заданной таблице PostgreSQL.
- Фильтрация событий по типу операции (`op: "u"`).
- Автоматическое создание таблицы в ClickHouse при первом обращении.
- Вставка данных через HTTP API ClickHouse.
- Вывод последних 10 записей из целевой таблицы для верификации результата.
- Преобразование временных меток в формат `DateTime` (UTC).

---

## Требования к окружению

### Необходимые компоненты

| Компонент                   | Версия / Рекомендации                     | Документация |
|----------------------------|------------------------------------------|-------------|
| PostgreSQL                 | 12+ с включённой логической репликацией    | [PostgreSQL](https://www.postgresql.org/download/) |
| Apache Kafka               | 3.0+                                     | [Kafka Downloads](https://kafka.apache.org/downloads) |
| Apache ZooKeeper           | 3.5+ (если используется ZK, а не KRaft)   | [ZooKeeper](https://zookeeper.apache.org/) |
| Debezium PostgreSQL Connector | 2.0+                                   | [Debezium Docs](https://debezium.io/documentation/reference/stable/connectors.postgresql.html) |
| ClickHouse                 | 22.8+                                    | [ClickHouse Install](https://clickhouse.com/docs/en/install/) |

### Зависимости Python

```bash
pip install kafka-python requests
```

---

## Структура проекта

```
.
├── consumer.py           # Основной потребитель: чтение из Kafka, запись в ClickHouse
├── update_postgres.py    # Скрипт для имитации изменений в PostgreSQL
└── README.md             # Техническая документация
```

---

## Инструкция по развёртыванию

### 1. Подготовка инфраструктуры

Рекомендуется использовать `docker-compose.yml` для поднятия всех сервисов:

- `zookeeper`
- `kafka`
- `postgres`
- `debezium`
- `clickhouse`

### 2. Настройка Debezium Connector

Регистрация коннектора для отслеживания таблицы `public.my_table`:

```json
{
  "name": "pg-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.dbname": "mydb",
    "database.server.name": "pgserver",
    "table.include.list": "public.my_table",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_slot",
    "publication.name": "debezium_pub"
  }
}
```

### 3. Запуск потребителя

```bash
python consumer.py
```

> Приложение читает сообщения из Kafka за последние 20 секунд и обрабатывает только события `UPDATE`.

### 4. Генерация изменений

Имитация обновления данных:

```bash
python update_postgres.py
```

### 5. Проверка результата

После выполнения скрипт выводит:
- События, полученные из Kafka.
- Статус вставки в ClickHouse.
- Последние 10 строк из таблицы `changes`.

---

## Схема данных в ClickHouse

Целевая таблица создаётся автоматически:

```sql
CREATE TABLE IF NOT EXISTS changes (
    id UInt32,
    name String,
    created_at DateTime,
    op String,
    ts DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (id, ts);
```

### Пример содержимого

| id  | name       | created_at          | op  | ts                  |
|-----|------------|---------------------|-----|---------------------|
| 1   | Alice 5555 | 2024-01-01 00:00:00 | u   | 2025-04-05 12:00:00 |

---

## Особенности реализации

- Обрабатываются только операции `UPDATE` (`op == "u"`). Поддержка `INSERT` и `DELETE` может быть добавлена.
- Временные метки из поля `after.ts_ms` преобразуются в формат `DateTime`.
- При повторном запуске таблица не пересоздаётся, если уже существует.
- Используется HTTP API ClickHouse — подходит для прототипирования и средних нагрузок.

---

## Сценарии использования

- Аналитика изменений данных в реальном времени.
- Аудит и отслеживание модификаций.
- Миграция данных из OLTP в OLAP-системы.
- Синхронизация между распределёнными базами данных.
- Реализация event-driven архитектур и ETL-процессов.

---

## Планы по развитию

| Функциональность                             | Статус     |
|---------------------------------------------|-----------|
| Поддержка операций `INSERT`, `DELETE`        | В плане   |
| Конфигурация через `.env`-файл               | В плане   |
| Логирование с уровнем DEBUG/ERROR            | В плане   |
| Мониторинг (Prometheus, Grafana)             | В плане   |
| Использование `clickhouse-connect`           | В плане   |
| Бесконечный режим потребления из Kafka       | В плане   |
| Параллельная обработка партиций              | В плане   |

---

> Проект предназначен для демонстрации принципов построения потоковых CDC-пайплайнов.  
> © 2025 | Реализовано с использованием Debezium, Kafka и ClickHouse
```