# 🟢 repo_buddy

**CTO in a Box & Security Intelligence Platform for AI-Built Applications**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Next.js 16](https://img.shields.io/badge/Frontend-Next.js%2016-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini 2.5](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange.svg)](https://aistudio.google.com/)
[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)]()

> **Paste repository URL → Analyze security risks → Live DAST Probes → Automated PR Fixes.**

**repo_buddy** is an enterprise-grade security intelligence platform engineered specifically for AI-assisted software development. It scans GitHub repositories built with platforms like **Lovable**, **Bolt.new**, or **Cursor**, transforming complex vulnerability vectors into non-technical, plain-English business risks, live proof-of-exploit demonstrations, and automated AI pull requests to patch security holes in production.

---

## 🎯 The Problem

Founders shipping products with modern AI code generation tools launch at unprecedented speeds. However, most non-technical founders lack a CTO, security engineer, or dedicated DevOps team. 
- Traditional scanners produce complex technical reports (*"SQL injection via un-parameterized ORM query in line 142"*).
- Founders need business-impact risk clarity (*"Anyone can download your entire customer database without logging in"*).

**repo_buddy bridges this gap** by converting raw code analysis into actionable security posture scores, real-time DAST HTTP probes, and instant auto-fix PRs.

---

## 🏗️ Architecture Overview

```mermaid
graph TD
    User["👤 Non-Technical Founder"] -->|Paste GitHub URL| FE["💻 Next.js 16 Frontend"]
    FE -->|REST API Requests| BE["⚡ FastAPI Backend"]
    
    subgraph Analysis_Engine["🔍 Security Analysis Engine"]
        BE -->|Semantic Indexing| VectorDB["📚 ChromaDB Vector Store"]
        BE -->|RAG Analysis| Gemini["🧠 Google Gemini 2.5 Flash"]
        BE -->|14-Point Probe| DAST["🛡️ Live DAST HTTP Probe"]
    end

    subgraph Remediation_Payments["🛠️ Fixes & Payments"]
        Gemini -->|Auto-Fix Patch| PR["octocat GitHub Auto-Fix PR"]
        BE -->|USD / INR Billing| Pay["💳 Stripe & Razorpay"]
    end
```

### Stack Components

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16, React 19, TypeScript, Lucide | Responsive security dashboard & shareable report pages |
| **Backend** | FastAPI, Python 3.9+, `slowapi` | High-performance async API server & rate limiting |
| **AI / RAG** | Gemini 2.5 Flash, ChromaDB, HuggingFace | Context-aware code analysis & auto-fix PR generation |
| **Security** | 14-Point DAST HTTP Prober, JWT Auth | Live SSL/CORS/SQLi/XSS checks & encrypted auth |
| **Database** | SQLite (WAL mode) | Low-latency scan result & report persistence |

---

## ⚡ Key Features

- **🧠 RAG Code Analysis**: Clones GitHub repos, embeds code vectors in ChromaDB, and calculates security health scores using Google Gemini 2.5 Flash.
- **🛡️ 14-Point DAST HTTP Probe**: Real-time vulnerability verification (HTTPS enforcement, Security Headers, CORS, SQLi/XSS, IDOR, and exposed secret tokens).
- **🤖 Automated PR Patching**: One-click AI pull request generation to fix discovered vulnerabilities directly on GitHub.
- **💳 Multi-Currency Support**: Automated geo-routing for global payments via **Stripe** (USD) and **Razorpay** (INR).

---

## 🚀 Quick Start Guide

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```
*Backend runs at `http://localhost:8000` (API Docs: `/docs`)*

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
*Frontend runs at `http://localhost:3000`*

---

## 👤 Author

**Adhvit Singh**
- **GitHub**: [@Adhvit-Singh](https://github.com/Adhvit-Singh)
- **Repository**: [Adhvit-Singh/repo_buddy](https://github.com/Adhvit-Singh/repo_buddy.git)

---

## 📄 License

Licensed under the [MIT License](LICENSE).




