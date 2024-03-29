import unittest
import base64
from flask import Flask, g
from flask_httpauth import HTTPBasicAuth


class HTTPAuthTestCase(unittest.TestCase):
    use_old_style_callback = False

    def setUp(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'my secret'

        basic_verify_auth = HTTPBasicAuth()

        @basic_verify_auth.verify_password
        def basic_verify_auth_verify_password(username, password):
            if self.use_old_style_callback:
                g.anon = False
                if username == 'john':
                    return password == 'hello'
                elif username == 'susan':
                    return password == 'bye'
                elif username == 'garçon':
                    return password == 'áéíóú'
                elif username == '':
                    g.anon = True
                    return True
                return False
            else:
                g.anon = False
                if username == 'john' and password == 'hello':
                    return 'john'
                elif username == 'susan' and password == 'bye':
                    return 'susan'
                elif username == 'garçon' and password == 'áéíóú':
                    return 'garçon'
                elif username == '':
                    g.anon = True
                    return ''

        @basic_verify_auth.error_handler
        def error_handler():
            self.assertIsNone(basic_verify_auth.current_user())
            return 'error', 403  # use a custom error status

        @app.route('/')
        def index():
            return 'index'

        @app.route('/basic-verify')
        @basic_verify_auth.login_required
        def basic_verify_auth_route():
            if self.use_old_style_callback:
                return 'basic_verify_auth:' + basic_verify_auth.username() + \
                    ' anon:' + str(g.anon)
            else:
                return 'basic_verify_auth:' + \
                    basic_verify_auth.current_user() + ' anon:' + str(g.anon)

        self.app = app
        self.basic_verify_auth = basic_verify_auth
        self.client = app.test_client()

    def test_verify_auth_login_valid(self):
        creds = base64.b64encode(b'susan:bye').decode()
        response = self.client.get(
            '/basic-verify', headers={'Authorization': 'Basic ' + creds})
        self.assertEqual(response.data, b'basic_verify_auth:susan anon:False')

    def test_verify_auth_login_valid_latin1(self):
        creds = base64.b64encode('garçon:áéíóú'.encode('latin1')).decode()
        response = self.client.get(
            '/basic-verify', headers={'Authorization': 'Basic ' + creds})
        self.assertEqual(response.data.decode(),
                         'basic_verify_auth:garçon anon:False')

    def test_verify_auth_login_empty(self):
        response = self.client.get('/basic-verify')
        self.assertEqual(response.data, b'basic_verify_auth: anon:True')

    def test_verify_auth_login_invalid(self):
        creds = base64.b64encode(b'john:bye').decode()
        response = self.client.get(
            '/basic-verify', headers={'Authorization': 'Basic ' + creds})
        self.assertEqual(response.status_code, 403)
        self.assertTrue('WWW-Authenticate' in response.headers)

    def test_verify_auth_login_malformed_password(self):
        creds = 'eyJhbGciOieyJp=='
        response = self.client.get('/basic-verify',
                                   headers={'Authorization': 'Basic ' + creds})
        self.assertEqual(response.status_code, 403)
        self.assertTrue('WWW-Authenticate' in response.headers)


class HTTPAuthTestCaseOldStyle(HTTPAuthTestCase):
    use_old_style_callback = True
