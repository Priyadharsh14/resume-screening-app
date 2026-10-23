from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Values come from environment variables; streamlit_app.py copies st.secrets into the environment first."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./resume_screening.db"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 5

    EMAIL_BACKEND: str = "smtp"  # smtp | sendgrid | none (log only, nothing is delivered)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = False
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "hr@example.com"

    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""


settings = Settings()
