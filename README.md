# EasyLife 🛡️⚡️
### Secure, Multi-User Personal Management System

EasyLife is a robust, Dockerized personal vault designed to manage your most sensitive credentials and notes with high security and privacy. 

---

## 🚀 Key Features
*   **Isolated Private Vaults**: Multiple users can register and manage their own independent, encrypted data.
*   **Privacy-First UI**: Passwords and sensitive fields are blurred by default (10px) and only reveal on hover.
*   **Safe Deletion**: High-stakes deletions require manual text-match confirmation.
*   **Smart Entry**: Quick-parse `username/password` pairs directly into your vault.
*   **Robust Excel Parser**: An inclusive, namespace-agnostic parser to import data from complex, multi-tab Excel spreadsheets.

---

## 🛠 Getting Started

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
*   Update `DJANGO_SECRET_KEY` and `DB_PASSWORD`.
*   Generate a Fernet encryption key for `ENCRYPTION_KEY`.

### 3. Start the Containers
EasyLife uses Docker Compose to orchestrate the web application and the MySQL database.
```bash
docker compose up -d --build
```

### 4. Create Your Account
Execute the following to set up your primary admin account:
```bash
docker compose exec web python manage.py createsuperuser
```

---

## 🧪 Security & Testing
EasyLife includes a **10-point Security Audit Suite** to ensure 100% data isolation and encryption integrity.

### Run the Suite
To verify your security configuration, run:
```bash
docker compose exec web python manage.py test credentials
```
*   **Fast-Track Mode**: Tests automatically use a local **SQLite** database to ensure blazing-fast performance and total isolation from your live MySQL data. ⚡️

---

## 🗄 Database & Infrastructure
*   **MySQL DB**: Runs inside a dedicated container on port **3306** (exposed as **3307** locally).
*   **Web App**: Listens on **[http://localhost:8010](http://localhost:8010)**.
*   **Auto-Restart**: Containers are configured to automatically start up after a computer reboot.

---

## 📊 Future Roadmap 🎯
1.  **Password Generator**: Built-in tool to create strong, random passwords.
2.  **Expense Module Re-design**: A refined parser for the "Spending" tabs with full CRUD visualization.
3.  **File Management**: Secure indexing and metadata storage for scanned documents.
4.  **Two-Factor Authentication (2FA)**: Extra security for every vault.
5.  **Audit Logs**: Complete history of every view and modification made to a credential.

---

## 🛡️ Data Privacy 🔑
This repository is sanitized—all local secrets (`.env`), raw logs (`processed.txt`, `error.txt`), and Excel data (`personal.xlsx`) are ignored via `.gitignore` and `.dockerignore`. 🛡️
