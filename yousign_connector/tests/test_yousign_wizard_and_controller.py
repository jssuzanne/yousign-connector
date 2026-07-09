# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.addons.yousign_connector.controllers.main import YouSignController, WebHookBadRequest
from openerp.tools import config
import mock
import hmac
import hashlib
import json

class TestYousignWizardAndController(TransactionCase):

    def setUp(self):
        super(TestYousignWizardAndController, self).setUp()
        self.Partner = self.env['res.partner']
        self.YousignRequest = self.env['yousign.request']

        self.partner = self.Partner.create({
            'name': 'Test Partner',
            'email': 'test@test.com',
            'mobile': '0600000000',
        })

        self.request = self.YousignRequest.create({
            'name': 'Test Request',
            'model': 'res.partner',
            'res_id': self.partner.id,
            'ys_identifier': 'ys12345',
            'expiration_delay_days': 10,
        })
        
        self.wizard_model = self.env['yousign.request.remind']
        
        config['yousign_secret'] = 'test_secret'
        self.controller = YouSignController()

    def test_wizard_run(self):
        wizard = self.wizard_model.with_context(active_model='yousign.request', active_ids=[self.request.id]).create({})
        
        # Test wizard run method
        with mock.patch.object(self.YousignRequest.__class__, 'remind', create=True) as mock_remind:
            wizard.run()
            self.assertTrue(mock_remind.called)

    @mock.patch('openerp.addons.yousign_connector.controllers.main.request')
    def test_controller_webhook_valid(self, mock_request):
        # Prepare valid payload
        payload = {
            "event_name": "signature_request.done",
            "event_time": "1740694692",
            "data": {
                "signature_request": {
                    "id": "ys12345"
                }
            }
        }
        raw_body = json.dumps(payload)
        digest = hmac.new(
            'test_secret'.encode("utf-8"),
            raw_body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        mock_request.jsonrequest = payload
        mock_request.original_request = raw_body
        mock_request.httprequest.headers.get.return_value = "sha256=" + digest
        mock_request.endpoint_arguments = {'db': self.env.cr.dbname}
        
        with mock.patch('openerp.addons.yousign_connector.controllers.main.RegistryManager.get') as mock_registry:
            mock_cr_context = mock.MagicMock()
            mock_cr_context.__enter__.return_value = self.env.cr
            mock_registry.return_value.cursor.return_value = mock_cr_context
            
            with mock.patch.object(self.YousignRequest.__class__, 'webhook_signature_request_done') as mock_webhook:
                mock_webhook.return_value = 'success'
                res = self.controller.webhook()
                self.assertEqual(res, 'success')
                self.assertTrue(mock_webhook.called)
                
    @mock.patch('openerp.addons.yousign_connector.controllers.main.request')
    def test_controller_webhook_invalid_signature(self, mock_request):
        payload = {
            "event_name": "signature_request.done",
            "event_time": "1740694692",
            "data": {
                "signature_request": {
                    "id": "ys12345"
                }
            }
        }
        raw_body = json.dumps(payload)
        
        mock_request.jsonrequest = payload
        mock_request.original_request = raw_body
        mock_request.httprequest.headers.get.return_value = "sha256=wrongsignature"
        
        res = self.controller.webhook()
        self.assertIsInstance(res, WebHookBadRequest)
