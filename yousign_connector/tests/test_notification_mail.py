# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
import mock


class TestNotificationMail(TransactionCase):

    def setUp(self):
        super(TestNotificationMail, self).setUp()

        self.Mail = self.env['mail.mail']
        self.Partner = self.env['res.partner']
        self.User = self.env['res.users']

        self.partner1 = self.Partner.create({
            'name': 'Partner 1',
            'email': 'p1@test.com'
        })

        self.partner2 = self.Partner.create({
            'name': 'Partner 2',
            'email': 'p2@test.com'
        })

        self.partner3 = self.Partner.create({
            'name': 'Partner 3',
            'email': 'p3@test.com'
        })

        self.partner4 = self.Partner.create({
            'name': 'Partner 4',
            'email': 'p4@test.com'
        })

        self.user = self.User.browse(1)
        self.user.partner_id = self.partner1.id

        self.parent = self.env['yousign.request'].create({
            'model': 'res.partner',
            'res_id': self.partner1.id,
        })
        self.signatory = self.env['yousign.request.signatory'].create({
            'parent_id': self.parent.id,
            'partner_id': self.partner2.id
        })

        self.partner1.message_subscribe(
            partner_ids=[self.partner3.id]
        )

        Notif = self.env['yousign.request.notification']
        self.notif1 = Notif.create({
            'subject': 'Sujet test 1',
            'body': '<p>Message test 1</p>',
            'creator': True,
            'members': False,
            'subscribers': False,
            'parent_id': self.parent.id,
            'notif_type': "procedure.started",
        })
        self.notif1.write({'create_uid': self.user.id})

        self.notif2 = Notif.create({
            'subject': 'Sujet test 2',
            'body': '<p>Message test 2</p>',
            'creator': False,
            'members': True,
            'subscribers': False,
            'parent_id': self.parent.id,
            'notif_type': "procedure.finished",
        })
        self.notif3 = Notif.create({
            'subject': 'Sujet test 3',
            'body': '<p>Message test 3</p>',
            'creator': False,
            'members': False,
            'subscribers': True,
            'parent_id': self.parent.id,
            'notif_type': "procedure.refused",
        })
        self.notif4 = Notif.create({
            'subject': 'Sujet test 4',
            'body': '<p>Message test 4</p>',
            'creator': False,
            'members': False,
            'subscribers': False,
            'partner_ids': [(6, 0, [self.partner4.id])],
            'parent_id': self.parent.id,
            'notif_type': "procedure.expired",
        })

    def test_send_notif1(self):
        with mock.patch(
            'openerp.addons.base.ir.ir_mail_server.ir_mail_server.send_email'
        ) as mock_send:
            emails_to = self.notif1.send()[self.notif1.id]
            self.assertTrue(
                mock_send.called,
                "send_email() n'a pas été appelé"
            )
            self.assertTrue(self.partner1.email in emails_to)

    def test_send_notif2(self):
        with mock.patch(
            'openerp.addons.base.ir.ir_mail_server.ir_mail_server.send_email'
        ) as mock_send:
            emails_to = self.notif2.send()[self.notif2.id]
            self.assertTrue(
                mock_send.called,
                "mail.mail.send() n'a pas été appelé"
            )
            self.assertTrue(self.partner2.email in emails_to)

    def test_send_notif3(self):
        with mock.patch(
            'openerp.addons.base.ir.ir_mail_server.ir_mail_server.send_email'
        ) as mock_send:
            emails_to = self.notif3.send()[self.notif3.id]
            self.assertTrue(
                mock_send.called,
                "mail.mail.send() n'a pas été appelé"
            )
            self.assertTrue(self.partner3.email in emails_to)

    def test_send_notif4(self):
        with mock.patch(
            'openerp.addons.base.ir.ir_mail_server.ir_mail_server.send_email'
        ) as mock_send:
            emails_to = self.notif4.send()[self.notif4.id]
            self.assertTrue(
                mock_send.called,
                "mail.mail.send() n'a pas été appelé"
            )
            self.assertTrue(self.partner4.email in emails_to)

    def test_send_procedure_finished(self):
        with mock.patch(
            'openerp.addons.base.ir.ir_mail_server.ir_mail_server.send_email'
        ) as mock_send:
            emails_to = self.parent.send_notification('procedure.finished').values()[0]
            self.assertTrue(
                mock_send.called,
                "send_email() n'a pas été appelé"
            )
            self.assertTrue(self.partner2.email in emails_to)
