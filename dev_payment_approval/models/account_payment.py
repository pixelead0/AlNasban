# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection(
        [('draft', 'Draft'),
         ('first_approval', 'First Approval'),
         ('second_approval', 'Second Approval'),
         ('posted', 'Posted'),
         ('sent', 'Sent'),
         ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')],
        readonly=True, default='draft',
        copy=False, string="Status")

    # copy of default post() method of account_payment.py
    @api.multi
    def post_entry(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state not in ['draft', 'first_approval', 'second_approval']: # made change for dev_payment_approval in this line
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    @api.multi
    def post(self):
        for payment in self:
            ir_param = payment.env['ir.config_parameter'].sudo()
            is_double_enabled = bool(ir_param.get_param(
                'dev_payment_approval.payment_double_verify'))
            if is_double_enabled:
                double_validation_amount = float(ir_param.get_param(
                    'dev_payment_approval.payment_double_validation_amount'))
                user_has_double_approval_right = self.env.user.has_group(
                    'dev_payment_approval.double_verification_payment_right')
                is_triple_enabled = bool(ir_param.get_param(
                    'dev_payment_approval.payment_triple_verify'))
                triple_validation_amount = float(ir_param.get_param(
                    'dev_payment_approval.payment_triple_validation_amount'))
                user_has_triple_approval_right = self.env.user.has_group(
                    'dev_payment_approval.triple_verification_payment_right')
                if payment.amount < double_validation_amount or \
                        user_has_double_approval_right:
                    if is_triple_enabled:
                        if payment.amount < triple_validation_amount or \
                                user_has_triple_approval_right:
                            payment.post_entry()
                        else:
                            payment.write({'state': 'second_approval'})
                    else:
                        payment.post_entry()
                else:
                    payment.write({'state': 'first_approval'})
            else:
                payment.post_entry()

    @api.multi
    def second_to_post(self):
        for payment in self:
            ir_param = payment.env['ir.config_parameter'].sudo()
            is_triple_enabled = bool(ir_param.get_param(
                'dev_payment_approval.payment_triple_verify'))
            if is_triple_enabled:
                triple_validation_amount = float(ir_param.get_param(
                    'dev_payment_approval.payment_triple_validation_amount'))
                user_has_triple_approval_right = self.env.user.has_group(
                    'dev_payment_approval.triple_verification_payment_right')
                if payment.amount < triple_validation_amount or \
                        user_has_triple_approval_right:
                    payment.post_entry()
                else:
                    payment.write({'state': 'second_approval'})
            else:
                payment.post_entry()

    @api.multi
    def third_to_post(self):
        for payment in self:
            payment.post_entry()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: