# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError

class TestYousignTemplate(TransactionCase):

    def setUp(self):
        super(TestYousignTemplate, self).setUp()
        self.Partner = self.env['res.partner']
        self.Template = self.env['yousign.request.template']
        self.Signatory = self.env['yousign.request.template.signatory']
        self.Notification = self.env['yousign.request.template.notification']

        self.partner = self.Partner.create({
            'name': 'Test Partner',
            'email': 'test@test.com',
            'mobile': '0600000000',
        })
        
        self.model_res_partner = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        self.template = self.Template.create({
            'name': 'Partner Template',
            'model_id': self.model_res_partner.id,
            'expiration_delay_days': 15,
            'remind_auto': True,
            'remind_interval': 2,
            'remind_limit': 5,
        })

    def test_create_unlink_button(self):
        self.template.create_button()
        self.assertTrue(self.template.ir_act_window_id)
        self.assertTrue(self.template.ir_value_id)
        
        self.template.unlink_button()
        self.assertFalse(self.template.ir_act_window_id.exists())
        self.assertFalse(self.template.ir_value_id.exists())

    def test_template_prepare_template2request(self):
        vals = self.template.prepare_template2request()
        self.assertEqual(vals['remind_auto'], True)
        self.assertEqual(vals['expiration_delay_days'], 15)

    def test_signatory_static(self):
        sig = self.Signatory.create({
            'parent_id': self.template.id,
            'partner_type': 'static',
            'partner_id': self.partner.id,
            'auth_mode': 'otp_sms',
        })
        vals = sig.prepare_template2request('res.partner', self.partner.id)
        self.assertEqual(vals['partner_id'], self.partner.id)
        self.assertEqual(vals['auth_mode'], 'otp_sms')

    def test_signatory_dynamic(self):
        sig = self.Signatory.create({
            'parent_id': self.template.id,
            'partner_type': 'dynamic',
            'partner_tmpl': '${object.id}',
            'auth_mode': 'otp_sms',
        })
        vals = sig.prepare_template2request('res.partner', self.partner.id)
        self.assertEqual(vals['partner_id'], self.partner.id)

    def test_signatory_constraints(self):
        with self.assertRaises(ValidationError):
            self.Signatory.create({
                'parent_id': self.template.id,
                'partner_type': 'static',
                'partner_id': False,
            })
            
        with self.assertRaises(ValidationError):
            self.Signatory.create({
                'parent_id': self.template.id,
                'partner_type': 'dynamic',
                'partner_tmpl': False,
            })

    def test_notification_dynamic_partner(self):
        notif = self.Notification.create({
            'parent_id': self.template.id,
            'notif_type': 'procedure.started',
            'creator': False,
            'members': False,
            'subscribers': False,
            'partner_ids': [(6, 0, [])],
            'partner_tmpl': '${object.id}',
            'subject': 'Test Subject ${object.name}',
            'body': 'Test Body ${object.name}',
        })
        
        vals = notif.prepare_template2request('res.partner', self.partner.id)
        self.assertEqual(vals['subject'], 'Test Subject Test Partner')
        self.assertEqual(vals['body'], 'Test Body Test Partner')
        # Check that partner_id was resolved and appended
        self.assertIn(self.partner.id, vals['partner_ids'][0][2])

    def test_notification_constraints(self):
        with self.assertRaises(ValidationError):
            self.Notification.create({
                'parent_id': self.template.id,
                'notif_type': 'procedure.started',
                'creator': False,
                'members': False,
                'subscribers': False,
                'partner_ids': [(6, 0, [])],
                'subject': 'Test Subject',
                'body': 'Test Body',
            })
