# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import api, SUPERUSER_ID, _
_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Create a payment group for every existint payment
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    # payments = env['account.payment'].search(
    #     [('payment_type', '!=', 'transfer')])
    # on v10, on reconciling from statements, if not partner is choosen, then
    # a payment is created with no partner. We still make partners mandatory
    # on payment groups. So, we dont create payment groups for payments
    # without partner_id
    payments = env['account.payment'].search(
        [('partner_id', '!=', False)])

    if len(payments) != 0:
        #Whe have prior payments, so we must create receipts books for vendors and clients receipts
        # These receipts boooks will be used to create the corresponding account.payment.group groups

        #Normally in the post-init-hook we shouldn't have any receiptbook, but we test it anyhow
        _logger.info('Checking for receipts books')
        receipt_client = env['account.payment.receiptbook'].search(['partner_type','=','customer'])
        receipt_vendor = env['account.payment.receiptbook'].search(['partner_type','=','supplier'])

        if len(receipt_client) == 0:
            seq_vals = {
                'name': 'REP',
                'implementation': 'no_gap',
                'prefix': False,   
                'padding': 8,
                'number_increment': 1
            }
            _logger.info('creating receipt book for customers')
            sequence = env['ir.sequence'].create(seq_vals)
            document_type = env['l10n_latam.document.type'].search(['doc_code_prefix','=','RE-X'])
            vals = {
                'sequence': 10,
                'name': 'REP',
                'partner_type': 'customer',
                'sequence_type': 'automatic',
                'sequence_id': sequence.id,
                'document_type_id': document_type.id,
                'report_partner_id': False,
                'mail_template_id': False,
            }
            receipt_client = env['account.payment.receiptbook'].create(vals)
            _logger.info('Receipt book for customers created:  %s' % receipt_client.id)
        else:
            _logger.info('We should not have any receipts books on init, quiting...')
            return
        
        if len(receipt_vendor) == 0:
            seq_vals = {
                'name': 'OP',
                'implementation': 'no_gap',
                'prefix': False,   
                'padding': 8,
                'number_increment': 1
            }
            _logger.info('creating receipt book for customers')
            sequence = env['ir.sequence'].create(seq_vals)
            document_type = env['l10n_latam.document.type'].search(['doc_code_prefix','=','OP-X'])
            vals = {
                'sequence': 10,
                'name': 'OP',
                'partner_type': 'customer',
                'sequence_type': 'automatic',
                'sequence_id': sequence.id,
                'document_type_id': document_type.id,
                'report_partner_id': False,
                'mail_template_id': False,
            }
            receipt_client = env['account.payment.receiptbook'].create(vals)
            _logger.info('Receipt book for vendors created:  %s' % receipt_vendor.id)
        else:
            _logger.info('We should not have any receipts books on init, quiting...')
            return

    for payment in payments:

        _logger.info('creating payment group for payment %s' % payment.id)
        _state = payment.state in ['sent', 'reconciled'] and 'posted' or payment.state
        _state = _state if _state != 'cancelled' else 'cancel'
        env['account.payment.group'].create({
            'company_id': payment.company_id.id,
            'partner_type': payment.partner_type,
            'receipt_book_id': receipt_client.id if payment.partner_type == 'customer' else receipt_vendor.id,
            'partner_id': payment.partner_id.id,
            'payment_date': payment.date,
            'communication': payment.ref,
            'payment_ids': [(4, payment.id, False)],
            'state': _state,
        })
