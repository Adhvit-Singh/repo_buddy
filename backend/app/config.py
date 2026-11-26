import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# -- Auth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# -- LLM models (comma-separated, tried in order). Providers retire models
# regularly; override via env instead of editing code.
GEMINI_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.7-flash,gemini-3.6-flash").split(",")
    if m.strip()
]
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
ANTHROPIC_MODEL_DEEP = os.getenv("ANTHROPIC_MODEL_DEEP", "claude-sonnet-5-5")
ANTHROPIC_MODEL_FAST = os.getenv("ANTHROPIC_MODEL_FAST", "claude-haiku-5-5")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

# -- URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# -- Storage paths
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_STORAGE_PATH = os.getenv(
    "REPO_STORAGE_PATH",
    os.path.join(tempfile.gettempdir(), "repo_buddy_repos"),
)
os.makedirs(REPO_STORAGE_PATH, exist_ok=True)

# -- Database
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(BACKEND_ROOT, ".storage", "repo_buddy.db"),
)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# -- Queue
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")

# -- Webhooks
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# -- Stripe
# Create price IDs in stripe.com/dashboard → Products
# Starter: $7/mo recurring  Builder: $29/mo recurring
# For INR prices: separate Stripe prices in INR currency
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_STARTER_USD = os.getenv("STRIPE_PRICE_STARTER_USD", "")
STRIPE_PRICE_BUILDER_USD = os.getenv("STRIPE_PRICE_BUILDER_USD", "")
STRIPE_PRICE_STARTER_INR = os.getenv("STRIPE_PRICE_STARTER_INR", "")
STRIPE_PRICE_BUILDER_INR = os.getenv("STRIPE_PRICE_BUILDER_INR", "")

# -- Razorpay (India primary — simpler card flows, lower fees)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
# Razorpay plan IDs (create at dashboard.razorpay.com → Subscriptions → Plans)
RAZORPAY_PLAN_STARTER = os.getenv("RAZORPAY_PLAN_STARTER", "")
RAZORPAY_PLAN_BUILDER = os.getenv("RAZORPAY_PLAN_BUILDER", "")
