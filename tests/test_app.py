import unittest

from app import Admin, Service, create_app, db, normalizar_whatsapp


class TestWhatsApp(unittest.TestCase):
    def test_normaliza_numero_formatado(self):
        self.assertEqual(
            normalizar_whatsapp("+55 (11) 99999-9999"),
            "5511999999999",
        )

    def test_rejeita_numero_invalido(self):
        self.assertEqual(normalizar_whatsapp(""), "")
        self.assertEqual(normalizar_whatsapp("12345"), "")


class TestAplicacao(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
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

    def test_salva_servico_no_banco(self):
        servico = Service(name="Serviço de teste", description="Fictício")
        db.session.add(servico)
        db.session.commit()

        salvo = db.session.get(Service, servico.id)
        self.assertEqual(salvo.name, "Serviço de teste")

    def test_area_administrativa_exige_login(self):
        resposta = self.client.get("/admin")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/entrar", resposta.headers["Location"])

    def test_senha_e_guardada_com_hash(self):
        administrador = Admin(username="admin-teste")
        administrador.set_password("SenhaFicticia123!")
        db.session.add(administrador)
        db.session.commit()

        salvo = db.session.get(Admin, administrador.id)
        self.assertNotEqual(salvo.password_hash, "SenhaFicticia123!")
        self.assertTrue(salvo.check_password("SenhaFicticia123!"))


if __name__ == "__main__":
    unittest.main()
