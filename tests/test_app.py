import pytest
from app import app


@pytest.fixture
def client():
    """Configuración del cliente de prueba."""
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'  # Usar una base de datos en memoria
    with app.test_client() as client:
        yield client


def test_index_redirects(client):
    """Prueba que la ruta de inicio redirige al login."""
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login'


def test_login_page(client):
    """Prueba que la página de login se carga correctamente."""
    response = client.get('/login')
    assert response.status_code == 200
    assert "iniciar sesión" in response.data.decode('utf-8').lower()


def test_login_post_invalid(client):
    """Prueba un intento de inicio de sesión inválido."""
    response = client.post('/login', data={'nombre': 'test', 'contraseña': 'wrong'})
    assert response.status_code == 200
    assert b"Credenciales incorrectas" in response.data
