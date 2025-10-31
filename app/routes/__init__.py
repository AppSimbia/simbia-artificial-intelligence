# Aqui engloba todos os blueprints, facilitando o init do app

from . import chat, match, healthcheck
chat_bp = chat.bp
match_bp = match.bp
healthcheck_bp = healthcheck.bp