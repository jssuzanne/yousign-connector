# -*- coding: utf-8 -*-

def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        WITH request AS (
            SELECT
               id AS id2,
               SUBSTRING(ys_identifier, 13) AS ys_identifier,
               'otp_' || ayth_mode as auth_mode
            FROM yousign_request
            WHERE ys_identifier != ''
        )
        UPDATE yousign_request
        SET
            ys_identifier=r.ys_identifier
            auth_mode=r.auth_mode
        FROM request r
        WHERE id=r.id2;
    """)
