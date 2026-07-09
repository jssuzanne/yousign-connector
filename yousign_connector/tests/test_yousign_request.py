# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
import mock
from datetime import datetime

class TestYousignRequest(TransactionCase):

    def setUp(self):
        super(TestYousignRequest, self).setUp()
        self.Partner = self.env['res.partner']
        self.YousignRequest = self.env['yousign.request']
        self.YousignSignatory = self.env['yousign.request.signatory']

        self.partner = self.Partner.create({
            'name': 'John Doe',
            'email': 'john.doe@test.com',
            'mobile': '0600000000',
        })
        
        self.partner2 = self.Partner.create({
            'name': 'Jane Doe',
            'email': 'jane.doe@test.com',
            'mobile': '0611111111',
        })

        self.request = self.YousignRequest.create({
            'name': 'Test Request',
            'model': 'res.partner',
            'res_id': self.partner.id,
            'ys_identifier': 'ys12345',
            'expiration_delay_days': 10,
        })
        
        self.signatory = self.YousignSignatory.create({
            'parent_id': self.request.id,
            'partner_id': self.partner2.id,
            'firstname': 'Jane',
            'lastname': 'Doe',
            'email': 'jane.doe@test.com',
            'mobile': '0611111111',
            'auth_mode': 'otp_sms',
        })

    def test_yousign_init(self):
        from openerp.tools import config
        config['yousign_apikey'] = 'test_key'
        config['yousign_envir'] = 'demo'
        url_base, headers = self.request.yousign_init()
        self.assertTrue('authorization' in headers)
        self.assertIn('api-sandbox.yousign.app', url_base)

    @mock.patch('openerp.addons.yousign_connector.models.yousign_request.requests.request')
    def test_api_post_signature_requests(self, mock_request):
        mock_response = mock.Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'ys12345'}
        mock_request.return_value = mock_response

        res = self.request.api_post_signature_requests()
        self.assertEqual(res['id'], 'ys12345')
        self.assertTrue(mock_request.called)

    @mock.patch('openerp.addons.yousign_connector.models.yousign_request.requests.request')
    def test_api_get_signature_requests(self, mock_request):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'ys12345', 'status': 'done'}
        mock_request.return_value = mock_response

        res = self.request.api_get_signature_requests()
        self.assertEqual(res['status'], 'done')
        self.assertTrue(mock_request.called)

    @mock.patch('openerp.addons.yousign_connector.models.yousign_request.requests.request')
    def test_api_cancel_signature_requests(self, mock_request):
        mock_response = mock.Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        res = self.request.api_cancel_signature_requests()
        self.assertEqual(res, {})
        self.assertTrue(mock_request.called)

    @mock.patch('openerp.addons.yousign_connector.models.yousign_request.requests.request')
    def test_api_activate_signature_requests(self, mock_request):
        mock_response = mock.Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        res = self.request.api_activate_signature_requests()
        self.assertEqual(res, {})
        self.assertTrue(mock_request.called)

    def test_webhook_signature_request_done(self):
        data = {
            'signature_request': {
                'id': 'ys12345',
                'status': 'done',
                'documents': []
            }
        }
        self.request.webhook_signature_request_done(datetime.now(), data)
        self.assertEqual(self.request.state, 'done')

    def test_webhook_signature_request_expired(self):
        data = {
            'signature_request': {
                'id': 'ys12345',
                'status': 'expired'
            }
        }
        self.request.webhook_signature_request_expired(datetime.now(), data)
        self.assertEqual(self.request.state, 'cancel')

    def test_webhook_signature_request_declined(self):
        data = {
            'signature_request': {
                'id': 'ys12345',
                'status': 'declined',
                'custom_experience': {
                    'declined_reason': 'Refused by user'
                }
            }
        }
        self.request.webhook_signature_request_declined(datetime.now(), data)
        self.assertEqual(self.request.state, 'cancel')

    def test_webhook_signer_done(self):
        self.signatory.ys_identifier = 'sig123'
        data = {
            'signature_request': {
                'id': 'ys12345'
            },
            'signer': {
                'id': 'sig123',
                'status': 'signed'
            }
        }
        self.request.webhook_signer_done(datetime.now(), data)
        self.assertEqual(self.signatory.state, 'signed')

    def test_webhook_signer_declined(self):
        self.signatory.ys_identifier = 'sig123'
        data = {
            'signature_request': {
                'id': 'ys12345'
            },
            'signer': {
                'id': 'sig123',
                'status': 'declined'
            }
        }
        self.request.webhook_signer_declined(datetime.now(), data)
        self.assertEqual(self.signatory.state, 'refused')
