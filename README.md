# EasyLife 🛡️⚡️
### Secure, Multi-User Personal Management System

EasyLife is a robust, Dockerized personal vault designed to manage your most sensitive credentials and notes with high security and privacy. 

---

## 🚀 Key Features
*   **Isolated Private Vaults**: Multiple users can register and manage their own independent, encrypted data. 🛡️
*   **Safety Lock**: Passwords stay 10px blurred and require a one-click password challenge to reveal. 🔐
*   **Selective Reveal**: Only re-blurs individual fields after 15 seconds. 💨
*   **Master Grace Period**: One verification unlocks your session for 15 minutes. 🛡️⚡️
*   **Safe Deletion**: High-stakes deletions require manual text-match confirmation. 🛡️
*   **Robust Excel Ingestion**: A namespace-agnostic parser to import data from complex Excel spreadsheets. 📊

---

## 🛠 Getting Started

> [!TIP]
> **Docker Commands**: Modern systems (Mac and Linux with Docker Compose V2) use `docker compose`. Legacy Linux installations may still use `docker-compose` (note the hyphen). 🐳

### 1. Clone the Repository
```bash
git clone https://github.com/malaybiswal/easyLife.git
cd easyLife
```

### 2. Configure Environment
Create a `.env` file based on the `.env.example` provided:
```bash
cp .env.example .env
```
*   Update `DJANGO_SECRET_KEY`, `DB_PASSWORD`, and `DB_HOST`.
*   Generate a Fernet encryption key for `ENCRYPTION_KEY`.

### 3. Start the Containers
```bash
docker compose up -d --build
```

### 4. Initialize Database Schema
Run the following after the containers are active to create your vault tables:
```bash
docker compose exec web python manage.py migrate
```

### 5. Create Your Account
Set up your primary account:
```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Ingest Excel Data (Optional)
To import your credentials from an Excel file (e.g., `personal.xlsx`):
```bash
docker compose exec web python manage.py parse_credentials personal.xlsx --user <YOUR_USERNAME>
```

---

## 🧪 Security & Testing
EasyLife includes a **13-point Security Audit Suite** to ensure 100% data isolation and encryption integrity.

### Run the Suite
```bash
docker compose exec web python manage.py test credentials
```
*   **Fast-Track Mode**: Tests automatically use a local **SQLite** database to ensure blazing-fast performance and total isolation. ⚡️

---

## 🗄 Database & Infrastructure
*   **MySQL DB**: Runs inside a container on port **3306** (exposed as **3307** locally).
*   **Web App**: Listens on **[http://localhost:8010](http://localhost:8010)**.
*   **Auto-Restart**: Containers start automatically after a computer reboot.

---

## 📊 Future Roadmap 🎯
1.  **Password Generator**: Built-in tool to create strong, random passwords.
2.  **Expense Module Re-design**: A refined parser for the "Spending" tabs with full CRUD visualization.
3.  **File Management**: Secure indexing and metadata storage for scanned documents.
4.  **Two-Factor Authentication (2FA)**: Extra security for every vault.

---

## 🛡️ Data Privacy 🔑
This repository is sanitized—secrets (`.env`), raw logs (`processed.txt`, `error.txt`), and Excel data are ignored via `.gitignore` and `.dockerignore`. 🛡️
