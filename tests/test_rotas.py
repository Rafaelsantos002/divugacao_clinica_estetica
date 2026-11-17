import unittest
from unittest.mock import patch

from app import Service, create_app, db


class TestRotaServicos(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "CLINIC_WHATSAPP": "+55 (11) 99999-9999",
            "RATELIMIT_ENABLED": False,
        })
        self.contexto = self.app.app_context()
        self.contexto.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.contexto.pop()

    def test_servicos_ativos_e_whatsapp_validado(self):
        db.session.add_all([
            Service(name="Limpeza de pele", description="Ativo", active=True),
            Service(name="Serviço oculto", description="Inativo", active=False),
        ])
        db.session.commit()

        with patch("app.render_template", return_value="Página de teste") as render:
            resposta = self.client.get("/servicos")

        self.assertEqual(resposta.status_code, 200)
        dados = render.call_args.kwargs
        self.assertEqual(dados["whatsapp"], "5511999999999")
        self.assertEqual(
            [servico.name for servico in dados["services"]],
            ["Limpeza de pele"],
        )


if __name__ == "__main__":
    unittest.main()
