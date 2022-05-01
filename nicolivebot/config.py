from pydantic import BaseSettings


class Config(BaseSettings):
    niconico_mail: str = "xxxxx@example.com"
    niconico_password: str = "hyper-secure-password"

    class Config:
        env_file = ".env"
